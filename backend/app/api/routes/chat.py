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
    document_id: str | None = Field(None, description="Optional document ID to scope the search to a single document")
    top_k: int = Field(5, ge=1, le=20, description="Number of top chunks to return (1–20, default 5)")


class ChunkDetail(BaseModel):
    chunk_id: str = Field(..., description="Unique identifier of this chunk")
    document_id: str = Field(..., description="ID of the parent document")
    document_name: str = Field(..., description="Filename of the source document")
    chunk_index: int = Field(..., description="Position of this chunk within the document")
    page_number: int | None = Field(None, description="Page number this chunk came from (None for TXT files)")
    text: str = Field(..., description="Full text content of the chunk")
    score: float = Field(..., description="Cosine similarity score (0–1, higher = more relevant)")


class ChunksResponse(BaseModel):
    question: str = Field(..., description="The question that was used for retrieval")
    total_retrieved: int = Field(..., description="Number of chunks returned")
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
    """
    cleaned_question = request.question.strip()
    if not cleaned_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty or whitespace only.",
        )

    user_id = x_user_id or settings.DEFAULT_USER_ID
    retrieval_svc = get_retrieval_service()

    try:
        context = retrieval_svc.retrieve_context(
            question=cleaned_question,
            user_id=user_id,
            document_id=request.document_id,
            top_k=request.top_k,
        )

        chunk_details = [
            ChunkDetail(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                document_name=chunk.document_name,
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                text=chunk.text,
                score=round(chunk.score, 6),
            )
            for chunk in context.chunks
        ]

        logger.info(
            f"[/chat/chunks] Retrieved {len(chunk_details)} chunk(s) "
            f"for question='{cleaned_question[:60]}' user_id='{user_id}'"
        )

        return ChunksResponse(
            question=cleaned_question,
            total_retrieved=len(chunk_details),
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