"""FastAPI main application entrypoint."""

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.routes import chat_router, documents_router, health_router
from backend.app.core.config import settings
from backend.app.utils.validator import DocumentValidationError

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rag_api")

app = FastAPI(
    title="Multi-Document RAG ChatBot API",
    description="Production-ready FastAPI backend for Multi-Document RAG with Gemini & Qdrant.",
    version="1.0.0",
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in settings.CORS_ORIGINS else settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Section 12 Error Response Standardizer
@app.exception_handler(DocumentValidationError)
async def document_validation_error_handler(request: Request, exc: DocumentValidationError):
    """Handle document validation errors according to Section 12 specification."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Normalize HTTP exceptions into standard error envelope."""
    code = "NOT_FOUND" if exc.status_code == 404 else "REQUEST_ERROR"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": str(exc.detail)}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Normalize Pydantic request validation errors."""
    error_msgs = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        error_msgs.append(f"{field}: {err.get('msg', 'Invalid value')}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "; ".join(error_msgs),
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions."""
    logger.exception(f"Unhandled server error on {request.url.path}: {exc}")
    detail_msg = str(exc).strip()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": detail_msg if detail_msg else "An unexpected error occurred on the server.",
            }
        },
    )



# Register API routers under /api/v1
app.include_router(health_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
def root():
    """Root endpoint providing service information."""
    return {
        "service": "Multi-Document RAG ChatBot API",
        "status": "online",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@app.get("/health", tags=["Root"])
@app.post("/health", tags=["Root"])
@app.get("/ping", tags=["Root"])
@app.post("/ping", tags=["Root"])
def quick_ping():
    """Convenience health/ping endpoint for uptime monitors and keep-alive jobs."""
    return {"status": "ok", "message": "pong"}
