"""Main FastAPI application entry point for the Multi-Document RAG Service."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes.chat import router as chat_router
from backend.app.api.routes.documents import router as documents_router, sync_vector_store
from backend.app.api.routes.health import router as health_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Multi-Document RAG backend and synchronizing vector store...")
    try:
        purged = sync_vector_store()
        logger.info(f"Startup vector synchronization complete. Purged {purged} orphaned document(s).")
    except Exception as e:
        logger.warning(f"Startup vector synchronization note: {e}")
    yield


app = FastAPI(
    title="Multi-Document RAG Service Platform",
    description="High-performance multi-document retrieval and grounded generation platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend Vite dev server (port 5173) and local clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router prefix
app.include_router(health_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "Multi-Document RAG Service API is active",
        "docs_url": "/docs",
        "api_v1": "/api/v1",
    }
