"""Main FastAPI application entry point."""

import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.routes import chat, documents, health
from backend.app.core.config import settings
from backend.app.utils.validator import DocumentValidationError

logger = logging.getLogger(__name__)

from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="Multi-Document RAG Service Platform",
    description="Backend API platform for multi-document parsing, vector indexing, semantic retrieval, and grounded generation.",
    version="1.0",
    openapi_version="3.0.3",
)


def custom_openapi():
    """Custom OpenAPI schema generator enforcing Swagger UI file upload picker compatibility."""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["openapi"] = "3.0.3"
    for schema in openapi_schema.get("components", {}).get("schemas", {}).values():
        if "properties" in schema:
            for prop in schema["properties"].values():
                if prop.get("type") == "array" and "items" in prop:
                    prop["items"]["format"] = "binary"
                elif prop.get("contentMediaType") == "application/octet-stream":
                    prop["format"] = "binary"
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers (supporting /health and /api/v1/* endpoints)
app.include_router(health.router)
app.include_router(health.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")


@app.get("/", tags=["root"], include_in_schema=False)
async def root():
    """Root landing endpoint providing API status and documentation links."""
    return {
        "message": "Welcome to Multi-Document RAG Service Platform API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/health",
        "version": "1.0",
    }


# Global Exception Handlers enforcing Spec Section 12.1 error format:
# {"error": {"code": "...", "message": "..."}}

@app.exception_handler(DocumentValidationError)
async def document_validation_exception_handler(request: Request, exc: DocumentValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.code or "DOCUMENT_VALIDATION_ERROR",
                "message": exc.message or str(exc),
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        422: "UNPROCESSABLE_ENTITY",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": str(exc.detail),
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameter structure.",
            }
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred on the server.",
            }
        },
    )
