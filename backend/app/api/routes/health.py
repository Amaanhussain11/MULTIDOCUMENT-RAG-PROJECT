"""Health check endpoints."""

from fastapi import APIRouter

from backend.app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
@router.post("")
def health_check():
    """Health check endpoint confirming API status and external service configurations."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "services": {
            "gemini_api_configured": bool(settings.GEMINI_API_KEY),
            "qdrant_url": settings.QDRANT_URL,
        },
    }
