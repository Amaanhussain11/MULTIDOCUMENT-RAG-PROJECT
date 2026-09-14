"""Configuration management for the RAG service."""

from typing import Optional, Set
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
    GEMINI_GENERATION_MODEL: str = "gemini-3.7-flash"

    # Qdrant settings
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "rag_documents"

    # Text Chunking Settings (Spec Section 5.5 & 10: 800-1200 tokens, 100-200 overlap)
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150

    # Validation Settings
    MAX_FILE_SIZE_MB: int = 25
    SUPPORTED_EXTENSIONS: Set[str] = {".pdf", ".docx", ".txt"}

    # Retrieval & Search Settings (Spec Section 5.6 & 15: Top-K = 5, configurable threshold)
    DEFAULT_TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.5

    # Concurrency and batching
    MAX_EMBEDDING_CONCURRENCY: int = 5
    EMBEDDING_BATCH_SIZE: int = 20


settings = Settings()
