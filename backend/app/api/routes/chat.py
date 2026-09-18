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
    document_id: str | None = Field(None, description="Optional document ID filter")
    top_k: int | None = Field(None, description="Maximum chunks to retrieve")


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    query: str


@router.post("", response_model=ChatResponse)
def chat_query(
    request: ChatRequest,
    x_user_id: str | None = Header(None, alias="x-user-id"),
):
    """
    Process user query, retrieve relevant document chunks from Qdrant,
    and generate a strictly grounded answer with citations using Gemini.
    """
    cleaned_question = request.question.strip()
    if not cleaned_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    user_id = x_user_id or settings.DEFAULT_USER_ID

    retrieval_service = get_retrieval_service()
    generation_service = get_generation_service()

    try:
        # Step 1: Embed question, retrieve chunks, and build grounded context
        context = retrieval_service.retrieve_context(
            question=cleaned_question,
            user_id=user_id,
            document_id=request.document_id,
            top_k=request.top_k or settings.DEFAULT_TOP_K,
            similarity_threshold=settings.SIMILARITY_THRESHOLD,
        )

        # Step 2: Synthesize grounded response using Gemini
        result = generation_service.generate_answer(
            question=cleaned_question,
            context=context,
        )

        return ChatResponse(
            answer=result["answer"],
            sources=result.get("sources", []),
            query=cleaned_question,
        )
    except Exception as e:
        logger.exception(f"Chat query processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat query: {str(e)}",
        )

