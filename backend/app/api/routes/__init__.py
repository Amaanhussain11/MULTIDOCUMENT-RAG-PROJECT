"""API Routes package."""

from backend.app.api.routes.chat import router as chat_router
from backend.app.api.routes.documents import router as documents_router
from backend.app.api.routes.health import router as health_router

__all__ = [
    "chat_router",
    "documents_router",
    "health_router",
]
