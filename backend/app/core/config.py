"""Configuration management for the RAG service."""


import json

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Gemini settings
    GEMINI_API_KEY: str = "AQ.Ab8RN6LGyQ8C_OjSnURHHeI0jYkxUp8IhYmF3OwJWgVt6qQczw"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    GEMINI_GENERATION_MODEL: str = "gemini-3.5-flash-lite"

    # Qdrant settings
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION_NAME: str = "rag_documents"

    # Text Chunking Settings (Spec Section 5.5 & 10: 800-1200 tokens, 100-200 overlap)
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150

    # Validation Settings
    MAX_FILE_SIZE_MB: int = 25
    SUPPORTED_EXTENSIONS: set[str] = {".pdf", ".docx", ".txt"}

    # Retrieval & Search Settings (Spec Section 5.6 & 15: Top-K = 5, configurable threshold)
    DEFAULT_TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.5

    # Concurrency and batching
    MAX_EMBEDDING_CONCURRENCY: int = 5
    EMBEDDING_BATCH_SIZE: int = 20

    # User & API defaults
    DEFAULT_USER_ID: str = "default_user"
    CORS_ORIGINS: list[str] | str = [
        "*",
        "https://mutli-document-rag-service.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: list[str] | str) -> list[str]:
        """Support raw string '*', JSON arrays '[\"*\"]', or comma-separated URLs, stripping trailing slashes."""
        raw_list: list[str] = []
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        raw_list = [str(x) for x in parsed]
                except Exception:
                    pass
            if not raw_list:
                if "," in v:
                    raw_list = [item.strip() for item in v.split(",") if item.strip()]
                else:
                    raw_list = [v]
        elif isinstance(v, (list, tuple, set)):
            raw_list = [str(x) for x in v]
        else:
            raw_list = [str(v)]

        cleaned: list[str] = []
        for origin in raw_list:
            origin_clean = origin.strip()
            if origin_clean != "*" and origin_clean.endswith("/"):
                origin_clean = origin_clean.rstrip("/")
            if origin_clean and origin_clean not in cleaned:
                cleaned.append(origin_clean)
        return cleaned or ["*"]


settings = Settings()
