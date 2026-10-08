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


@router.post("", response_model=ChatResponse)
def chat_query(
    request: ChatRequest,
    x_user_id: str | None = Header(None, alias="x-user-id"),
):
    user_id = x_user_id or settings.DEFAULT_USER_ID

    retrieval_svc = get_retrieval_service()
    gen_svc = get_generation_service()

    target_doc_id = request.document_id
    if not target_doc_id and request.document_ids and len(request.document_ids) == 1:
        target_doc_id = request.document_ids[0]

    try:
        retrieved_context = retrieval_svc.retrieve_context(
            query=request.question,
            user_id=user_id,
            document_id=target_doc_id,
            top_k=request.top_k or 5,
        )

        gen_result = gen_svc.generate_answer(
            query=request.question,
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
            query=request.question,
        )
    except Exception as exc:
        logger.error(f"Error handling chat request: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat query processing failed: {str(exc)}",
        ) from exc