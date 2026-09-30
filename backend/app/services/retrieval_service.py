"""Retrieval service orchestrating query embedding, semantic search, filtering, and context construction."""

import logging
from collections.abc import Callable

from backend.app.core.config import settings
from backend.app.schemas.query import (
    ConstructedContext,
    RetrievedChunk,
    SourceReference,
)
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.qdrant_service import QdrantService

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Orchestrates the Query Processing Pipeline:
    1. Query Validation
    2. Query Embedding Generation (Gemini gemini-embedding-001)
    3. Qdrant Semantic Similarity Search (with user isolation)
    4. Context Filtering (Top-K & Similarity Threshold)
    5. Context Construction (Formatted source blocks)
    """

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        qdrant_service: QdrantService | None = None,
    ):
        self.embedding_service = embedding_service or EmbeddingService()
        self.qdrant_service = qdrant_service or QdrantService()

    def retrieve_context(
        self,
        question: str,
        user_id: str,
        document_id: str | None = None,
        document_ids: list[str] | None = None,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
        on_step: Callable[[str, str], None] | None = None,
    ) -> ConstructedContext:
        """
        Execute the query processing pipeline to retrieve relevant chunks and construct context.

        Args:
            question: User natural-language question.
            user_id: Authenticated user ID for logical multi-tenant isolation.
            document_id: Optional specific document ID to scope search.
            document_ids: Optional list of document IDs to scope search across multiple selected files.
            top_k: Maximum number of chunks to retrieve (defaults to settings.DEFAULT_TOP_K).
            similarity_threshold: Minimum cosine similarity score (defaults to settings.SIMILARITY_THRESHOLD).
            on_step: Optional callback receiving (step_name, detail_message).

        Returns:
            ConstructedContext with formatted context text, chunks, and source references.
        """
        effective_top_k = top_k if top_k is not None else settings.DEFAULT_TOP_K
        effective_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else settings.SIMILARITY_THRESHOLD
        )

        def report(step: str, msg: str):
            logger.info(f"[{step}] {msg}")
            if on_step:
                on_step(step, msg)

        # Step 1: Validate Query
        cleaned_question = question.strip() if question else ""
        if not cleaned_question:
            report("1_VALIDATE", "Question is empty. Returning empty context.")
            return ConstructedContext(
                formatted_text="",
                chunks=[],
                sources=[],
                question=question,
            )
        report("1_VALIDATE", f"Question validated: '{cleaned_question}'")

        # Step 2: Generate Query Embedding Vector
        report(
            "2_EMBED",
            f"Generating query embedding vector using '{self.embedding_service.model_name}'...",
        )
        query_vector = self.embedding_service.embed_single(cleaned_question)
        report("2_EMBED", f"Generated query vector with dimension {len(query_vector)}.")

        # Step 3: Qdrant Similarity Search with User Isolation
        if document_id:
            filter_scope = f"user_id='{user_id}' and document_id='{document_id}'"
        elif document_ids is not None:
            filter_scope = f"user_id='{user_id}' and document_ids={document_ids}"
        else:
            filter_scope = f"user_id='{user_id}' (all documents)"

        report(
            "3_SEARCH",
            f"Searching Qdrant collection '{self.qdrant_service.collection_name}' with filter: {filter_scope}...",
        )
        retrieved_chunks = self.qdrant_service.search_chunks(
            query_vector=query_vector,
            user_id=user_id,
            document_id=document_id,
            document_ids=document_ids,
            top_k=effective_top_k,
            score_threshold=effective_threshold,
        )
        report("3_SEARCH", f"Retrieved {len(retrieved_chunks)} raw candidate chunk(s).")

        # Step 4: Context Filtering (Threshold & Top-K)
        report(
            "4_FILTER",
            f"Filtering chunks (min_score={effective_threshold}, top_k={effective_top_k})...",
        )
        filtered_chunks = [c for c in retrieved_chunks if c.score >= effective_threshold]
        filtered_chunks = filtered_chunks[:effective_top_k]
        report("4_FILTER", f"Retained {len(filtered_chunks)} relevant chunk(s) after filtering.")

        # Step 5: Context Construction
        report("5_CONSTRUCT", "Constructing structured context with source attribution...")
        formatted_context, sources = self._construct_context(filtered_chunks)
        report(
            "5_CONSTRUCT",
            f"Constructed context containing {len(sources)} source reference(s).",
        )

        return ConstructedContext(
            formatted_text=formatted_context,
            chunks=filtered_chunks,
            sources=sources,
            question=cleaned_question,
        )

    def _construct_context(
        self, chunks: list[RetrievedChunk]
    ) -> tuple[str, list[SourceReference]]:
        """
        Convert retrieved chunks into structured context adhering to Section 5.8:

        [research.pdf | Page 12]
        <chunk text>

        [notes.docx | Page 4]
        <chunk text>
        """
        if not chunks:
            return "", []

        context_blocks: list[str] = []
        sources: list[SourceReference] = []
        seen_sources = set()

        for chunk in chunks:
            # Build header: [doc_name | Page X] or [doc_name]
            if chunk.page_number is not None:
                header = f"[{chunk.document_name} | Page {chunk.page_number}]"
            else:
                header = f"[{chunk.document_name}]"

            block = f"{header}\n{chunk.text.strip()}"
            context_blocks.append(block)

            # Record unique sources for citation
            source_key = (chunk.document_name, chunk.page_number)
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                sources.append(
                    SourceReference(
                        document=chunk.document_name,
                        page=chunk.page_number,
                        score=round(chunk.score, 4),
                    )
                )

        formatted_text = "\n\n".join(context_blocks)
        return formatted_text, sources
