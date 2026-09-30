"""Health check route."""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Health check endpoint confirming backend service operational state."""
    return {
        "status": "ok",
        "service": "Multi-Document RAG Service Platform",
        "version": "1.0.0",
    }
