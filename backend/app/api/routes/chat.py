import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.services.generation_service import GenerationService
from backend.app.services.retrieval_service import RetrievalService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])

# Service instances
_retrieval_service: RetrievalService | None = None
_generation_service: GenerationService | None = None


def get_retrieval_service() -> RetrievalService:
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service


def get_generation_service() -> GenerationService:
    global _generation_service
    if _generation_service is None:
        _generation_service = GenerationService()
    return _generation_service


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question to query over documents")
    document_id: str | None = Field(None, description="Optional single document ID filter")
    document_ids: list[str] | None = Field(None, description="Optional multiple document IDs filter")
    top_k: int | None = Field(5, description="Maximum chunks to retrieve")


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    chunks: list[dict[str, Any]] = Field(default_factory=list)
    query: str


# ─── New: Chunk Retrieval Models ───────────────────────────────────────────────

class ChunksRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question to retrieve relevant chunks for")
    document_id: str | None = Field(
        None, description="Optional single document ID to scope the search"
    )
    document_ids: list[str] | None = Field(
        None,
        description=(
            "Optional list of document IDs to search across multiple documents. "
            "Results are merged and re-ranked by similarity score. "
            "Takes precedence over document_id when both are supplied."
        ),
    )
    top_k: int = Field(5, ge=1, le=20, description="Number of top chunks to return (1–20, default 5)")
    similarity_threshold: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum cosine similarity score a chunk must have to be included (0–1). "
            "Defaults to the server-configured threshold when omitted."
        ),
    )
    max_text_length: int | None = Field(
        None,
        ge=50,
        description=(
            "If set, truncate each chunk's text to this many characters and expose "
            "the full text separately. Useful for preview / list views."
        ),
    )


class ChunkDetail(BaseModel):
    chunk_id: str = Field(..., description="Unique identifier of this chunk")
    document_id: str = Field(..., description="ID of the parent document")
    document_name: str = Field(..., description="Filename of the source document")
    chunk_index: int = Field(..., description="Position of this chunk within the document")
    page_number: int | None = Field(None, description="Page number this chunk came from (None for TXT files)")
    text: str = Field(..., description="Full text content of the chunk")
    preview: str | None = Field(
        None,
        description="Truncated preview of the chunk text (populated when max_text_length is set)",
    )
    score: float = Field(..., description="Cosine similarity score (0–1, higher = more relevant)")
    truncated: bool = Field(
        False,
        description="True when the text was truncated to max_text_length; preview holds the short version",
    )


class ChunksResponse(BaseModel):
    question: str = Field(..., description="The question that was used for retrieval")
    total_retrieved: int = Field(..., description="Number of chunks returned")
    filters_applied: dict[str, Any] = Field(
        default_factory=dict,
        description="Summary of filters and parameters used for this retrieval",
    )
    chunks: list[ChunkDetail] = Field(..., description="Top-K retrieved chunks, sorted by similarity score")


# ─── New Endpoint: POST /api/v1/chat/chunks ────────────────────────────────────

@router.post(
    "/chunks",
    response_model=ChunksResponse,
    summary="Retrieve top-K chunks for a question",
    description=(
        "Performs semantic vector search against uploaded documents and returns "
        "the top-K most relevant chunks for the given question. "
        "No LLM answer is generated — this is a pure retrieval inspection endpoint."
    ),
)
def get_chunks_for_question(
    request: ChunksRequest,
    x_user_id: str | None = Header(None, alias="x-user-id"),
):
    """
    Retrieve the top-K most relevant document chunks for a given question
    using Gemini embedding + Qdrant vector similarity — WITHOUT generating an LLM answer.

    Useful for:
    - Inspecting what the RAG system retrieves before answering
    - Debugging retrieval quality
    - Understanding which documents/pages are most relevant
    - Preview mode: set max_text_length to receive truncated chunk previews

    Filtering priority:
    1. ``document_ids`` (list)  — search each document separately, merge results
    2. ``document_id`` (single) — scope to a single document
    3. No filter              — search across all user documents
    """
    cleaned_question = request.question.strip()
    if not cleaned_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty or whitespace only.",
        )

    user_id = x_user_id or settings.DEFAULT_USER_ID
    retrieval_svc = get_retrieval_service()

    # Resolve which document IDs to search
    target_doc_ids: list[str | None]
    if request.document_ids:
        # de-duplicate while preserving order
        seen: set[str] = set()
        target_doc_ids = []
        for doc_id in request.document_ids:
            if doc_id not in seen:
                seen.add(doc_id)
                target_doc_ids.append(doc_id)
    elif request.document_id:
        target_doc_ids = [request.document_id]
    else:
        target_doc_ids = [None]  # None → search across all documents

    try:
        all_raw_chunks = []
        seen_chunk_ids: set[str] = set()

        for doc_id in target_doc_ids:
            context = retrieval_svc.retrieve_context(
                question=cleaned_question,
                user_id=user_id,
                document_id=doc_id,
                top_k=request.top_k,
                similarity_threshold=request.similarity_threshold,
            )
            for chunk in context.chunks:
                if chunk.chunk_id not in seen_chunk_ids:
                    seen_chunk_ids.add(chunk.chunk_id)
                    all_raw_chunks.append(chunk)

        # Re-rank merged results by score descending and apply global top_k cap
        all_raw_chunks.sort(key=lambda c: c.score, reverse=True)
        all_raw_chunks = all_raw_chunks[: request.top_k]

        # Build response details, applying optional preview truncation
        chunk_details: list[ChunkDetail] = []
        for chunk in all_raw_chunks:
            full_text = chunk.text
            is_truncated = False
            preview_text: str | None = None

            if request.max_text_length and len(full_text) > request.max_text_length:
                preview_text = full_text[: request.max_text_length].rstrip() + "…"
                is_truncated = True

            chunk_details.append(
                ChunkDetail(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    document_name=chunk.document_name,
                    chunk_index=chunk.chunk_index,
                    page_number=chunk.page_number,
                    text=full_text,
                    preview=preview_text,
                    score=round(chunk.score, 6),
                    truncated=is_truncated,
                )
            )

        filters_applied: dict[str, Any] = {
            "top_k": request.top_k,
            "similarity_threshold": request.similarity_threshold,
            "document_ids": request.document_ids or ([request.document_id] if request.document_id else None),
            "max_text_length": request.max_text_length,
        }

        logger.info(
            "[/chat/chunks] Retrieved %d chunk(s) for question='%s' "
            "user_id='%s' filters=%s",
            len(chunk_details),
            cleaned_question[:60],
            user_id,
            filters_applied,
        )

        return ChunksResponse(
            question=cleaned_question,
            total_retrieved=len(chunk_details),
            filters_applied=filters_applied,
            chunks=chunk_details,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error retrieving chunks for question: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chunk retrieval failed: {str(exc)}",
        ) from exc


# ─── Existing Endpoint: POST /api/v1/chat ─────────────────────────────────────

@router.post("", response_model=ChatResponse)
def chat_query(
    request: ChatRequest,
    x_user_id: str | None = Header(None, alias="x-user-id"),
):
    cleaned_question = request.question.strip()
    if not cleaned_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty or whitespace only",
        )

    user_id = x_user_id or settings.DEFAULT_USER_ID

    retrieval_svc = get_retrieval_service()
    gen_svc = get_generation_service()

    target_doc_id = request.document_id
    if not target_doc_id and request.document_ids and len(request.document_ids) == 1:
        target_doc_id = request.document_ids[0]

    try:
        retrieved_context = retrieval_svc.retrieve_context(
            question=cleaned_question,
            user_id=user_id,
            document_id=target_doc_id,
            top_k=request.top_k or 5,
        )

        gen_result = gen_svc.generate_answer(
            question=cleaned_question,
            context=retrieved_context,
        )

        formatted_chunks = [
            chunk.model_dump() if hasattr(chunk, "model_dump") else dict(chunk)
            for chunk in getattr(retrieved_context, "chunks", [])
        ]

        formatted_sources = [
            source.model_dump() if hasattr(source, "model_dump") else dict(source)
            for source in getattr(retrieved_context, "sources", [])
        ]

        return ChatResponse(
            answer=gen_result.get("answer", "") if isinstance(gen_result, dict) else getattr(gen_result, "answer", ""),
            sources=formatted_sources,
            chunks=formatted_chunks,
            query=cleaned_question,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error handling chat request: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat query processing failed: {str(exc)}",
        ) from exc