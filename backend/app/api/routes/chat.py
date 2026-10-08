"""Chat and RAG query processing route."""

import logging

from fastapi import APIRouter, HTTPException

from backend.app.schemas.query import ChatResponse, QueryRequest
from backend.app.services.generation_service import GenerationService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])
generation_service = GenerationService()


@router.post("/chat", response_model=ChatResponse)
async def chat_query(request: QueryRequest):
    """
    RAG Chat Query Endpoint:
    1. Retrieves top-k (default 5) semantic chunks across multiple documents.
    2. Constructs grounded context.
    3. Synthesizes factual answer via Gemini 3.7 Flash.
    4. Returns answer, verified source citations, and the top-k retrieved chunks.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        target_doc_ids = request.document_ids
        if not request.document_id and target_doc_ids is None:
            from backend.app.api.routes.documents import DOCUMENT_REGISTRY
            from backend.app.schemas.document import DocumentStatus

            target_doc_ids = [
                doc_id
                for doc_id, doc in DOCUMENT_REGISTRY.items()
                if doc.status == DocumentStatus.READY
            ]

        response = generation_service.answer_query(
            question=request.question,
            user_id=request.user_id or "default_user",
            document_id=request.document_id,
            document_ids=target_doc_ids,
            top_k=request.top_k or 5,
            similarity_threshold=request.similarity_threshold,
        )
        return response
    except Exception as e:
        logger.error(f"Error handling chat query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}",
        )
