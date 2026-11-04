"""Schemas for query processing, semantic retrieval, and context construction."""


from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    """Represents a chunk retrieved from the vector database with its similarity score."""
    chunk_id: str
    document_id: str
    document_name: str
    chunk_index: int
    page_number: int | None = None
    page_start: int | None = None
    page_end: int | None = None
    source_id: str | None = None
    text: str
    score: float


class SourceReference(BaseModel):
    """Represents source reference metadata for citation."""
    document: str
    page: int | None = None
    score: float
    source_id: str | None = None
    chunk_text: str | None = None


class Citation(BaseModel):
    """Represents a verified grounded citation supporting an answer claim."""
    source_id: str
    document_id: str
    document_name: str
    page_number: int | None = None
    page_start: int | None = None
    page_end: int | None = None
    chunk_id: str
    chunk_index: int
    text: str
    score: float = 0.0


class ConstructedContext(BaseModel):
    """Structured context constructed from retrieved chunks, formatted for LLM consumption."""
    formatted_text: str
    chunks: list[RetrievedChunk] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)
    question: str


class QueryRequest(BaseModel):
    """Incoming user query request with user isolation and filtering parameters."""
    question: str
    user_id: str = "default_user"
    document_id: str | None = None
    document_ids: list[str] | None = None
    top_k: int | None = 5
    similarity_threshold: float | None = None


class ChatResponse(BaseModel):
    """Response returned by the /api/v1/chat endpoint including top-k retrieved chunks and grounded citations."""
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)
    chunks: list[RetrievedChunk] = Field(default_factory=list)
    question: str | None = None
