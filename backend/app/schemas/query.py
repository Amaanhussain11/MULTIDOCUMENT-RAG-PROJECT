"""Schemas for query processing, semantic retrieval, and context construction."""

from typing import List, Optional
from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    """Represents a chunk retrieved from the vector database with its similarity score."""
    chunk_id: str
    document_id: str
    document_name: str
    chunk_index: int
    page_number: Optional[int] = None
    text: str
    score: float


class SourceReference(BaseModel):
    """Represents source reference metadata for citation."""
    document: str
    page: Optional[int] = None
    score: float


class ConstructedContext(BaseModel):
    """Structured context constructed from retrieved chunks, formatted for LLM consumption."""
    formatted_text: str
    chunks: List[RetrievedChunk] = Field(default_factory=list)
    sources: List[SourceReference] = Field(default_factory=list)
    question: str


class QueryRequest(BaseModel):
    """Incoming user query request with user isolation and filtering parameters."""
    question: str
    user_id: str
    document_id: Optional[str] = None
    top_k: Optional[int] = None
    similarity_threshold: Optional[float] = None


class ChatQueryRequest(BaseModel):
    """Incoming user query for chat endpoint."""
    question: str
    document_id: Optional[str] = None


class GeneratedAnswer(BaseModel):
    """Result of LLM answer generation with attached source references."""
    answer: str
    sources: List[SourceReference] = Field(default_factory=list)

