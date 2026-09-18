"""Data schemas for documents, chunks, and Qdrant payloads."""

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class Document(BaseModel):
    document_id: str
    user_id: str
    document_name: str
    file_type: str
    file_size: int
    status: DocumentStatus = DocumentStatus.QUEUED
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    user_id: str
    chunk_index: int
    text: str
    page_number: int | None = None


class QdrantPayload(BaseModel):
    user_id: str
    document_id: str
    document_name: str
    chunk_id: str
    chunk_index: int
    page_number: int | None = None
    text: str


class IngestionResult(BaseModel):
    document_id: str
    document_name: str
    user_id: str
    status: DocumentStatus
    chunk_count: int = 0
    total_tokens: int = 0
    error: str | None = None
