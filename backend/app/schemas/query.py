"""Schemas for query processing, semantic retrieval, and context construction."""


from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    """Represents a chunk retrieved from the vector database with its similarity score."""
    chunk_id: str
    document_id: str
    document_name: str
    chunk_index: int
    page_number: int | None = None
    text: str
    score: float


class SourceReference(BaseModel):
    """Represents source reference metadata for citation."""
    document: str
    page: int | None = None
    score: float


class ConstructedContext(BaseModel):
    """Structured context constructed from retrieved chunks, formatted for LLM consumption."""
    formatted_text: str
    chunks: list[RetrievedChunk] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)
    question: str


class QueryRequest(BaseModel):
    """Incoming user query request with user isolation and filtering parameters."""
    question: str
    user_id: str
    document_id: str | None = None
    top_k: int | None = None
    similarity_threshold: float | None = None
