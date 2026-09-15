"""Chat and RAG query routing endpoint."""

from fastapi import APIRouter, Depends, Header

from backend.app.schemas.query import ChatQueryRequest, GeneratedAnswer
from backend.app.services.generation_service import GenerationService
from backend.app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/chat", tags=["chat"])

def get_retrieval_service() -> RetrievalService:
    """Dependency provider for RetrievalService."""
    return RetrievalService()


def get_generation_service() -> GenerationService:
    """Dependency provider for GenerationService."""
    return GenerationService()


# TODO: Per Spec Section 14.8, client-provided user_id from headers (X-User-Id) must NOT be trusted
# as proof of identity in production. Replace this header extraction with a proper JWT/session authorization layer.


@router.post("", response_model=GeneratedAnswer)
@router.post("/", response_model=GeneratedAnswer, include_in_schema=False)
@router.post("/query", response_model=GeneratedAnswer)
async def query_chat(
    request: ChatQueryRequest,
    user_id: str = Header(default="test_user_001", alias="X-User-Id"),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    generation_service: GenerationService = Depends(get_generation_service),
):
    """
    Execute semantic document retrieval followed by Gemini LLM grounded answer generation.
    """
    # Step 1: Semantic vector retrieval with user isolation
    retrieved_context = retrieval_service.retrieve_context(
        question=request.question,
        user_id=user_id,
        document_id=request.document_id,
    )

    # Step 2: Grounded answer generation via GenerationService
    answer_result = generation_service.generate_answer(
        question=request.question,
        context=retrieved_context.formatted_text,
        sources=retrieved_context.sources,
    )

    return answer_result
