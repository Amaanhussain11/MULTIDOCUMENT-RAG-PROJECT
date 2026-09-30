"""Document ingestion pipeline orchestrating validation, parsing, cleaning, chunking, embedding, and storage."""

import logging
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from backend.app.core.config import settings
from backend.app.parsers import get_parser
from backend.app.schemas.document import DocumentStatus, IngestionResult
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.qdrant_service import QdrantService
from backend.app.utils.chunker import create_chunks
from backend.app.utils.cleaner import clean_text
from backend.app.utils.validator import DocumentValidationError, validate_document_file

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Coordinates the end-to-end document ingestion pipeline.
    
    Steps:
    1. Ingestion / Upload
    2. Validation
    3. Parsing
    4. Text Cleaning
    5. Chunking
    6. Embedding Generation
    7. Qdrant Vector Storage
    """

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        qdrant_service: QdrantService | None = None,
    ):
        self.embedding_service = embedding_service or EmbeddingService()
        self.qdrant_service = qdrant_service or QdrantService()

    def ingest_file(
        self,
        file_path: Path,
        user_id: str,
        document_id: str | None = None,
        on_step: Callable[[str, str], None] | None = None,
    ) -> IngestionResult:
        """
        Execute the 7-step ingestion pipeline for a single local file.
        
        Args:
            file_path: Path to the document on the local device.
            user_id: Authenticated user identifier (for multi-tenant isolation).
            document_id: Optional unique document id (auto-generated if omitted).
            on_step: Optional callback receiving (step_name, detail_message).
        """
        file_path = Path(file_path).resolve()
        doc_id = document_id or f"doc_{uuid.uuid4().hex[:12]}"
        doc_name = file_path.name

        def report(step: str, msg: str):
            logger.info(f"[{doc_name}] [{step}] {msg}")
            if on_step:
                on_step(step, msg)

        try:
            # Step 1: Upload / Ingest from device
            report("1_UPLOAD", f"Loaded file '{doc_name}' from {file_path}")

            # Step 2: Validate Document
            report("2_VALIDATE", "Validating file existence, format, and size...")
            validate_document_file(file_path)

            # Step 3: Parse Document
            report("3_PARSE", f"Parsing document using format-specific parser for '{file_path.suffix}'...")
            parser = get_parser(file_path.suffix)
            raw_pages = parser.parse_file(file_path)
            report("3_PARSE", f"Extracted {len(raw_pages)} page(s)/section(s).")

            # Step 4: Clean Document
            report("4_CLEAN", "Cleaning and normalizing extracted text (Unicode, whitespace, artifacts)...")
            cleaned_pages = []
            for p in raw_pages:
                cleaned_str = clean_text(p.text)
                if cleaned_str:
                    p.text = cleaned_str
                    cleaned_pages.append(p)

            if not cleaned_pages:
                raise DocumentValidationError(
                    code="NO_EXTRACTABLE_TEXT",
                    message=f"Document '{doc_name}' contains no readable or extractable text."
                )

            # Step 5: Chunk Document
            report(
                "5_CHUNK",
                f"Chunking text (Target: {settings.CHUNK_SIZE} tokens, Overlap: {settings.CHUNK_OVERLAP} tokens)..."
            )
            chunks = create_chunks(
                pages=cleaned_pages,
                document_id=doc_id,
                user_id=user_id,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )
            if settings.MAX_CHUNKS_PER_DOCUMENT > 0 and len(chunks) > settings.MAX_CHUNKS_PER_DOCUMENT:
                report("5_CHUNK", f"Capping chunks at {settings.MAX_CHUNKS_PER_DOCUMENT} (out of {len(chunks)}) to preserve API quota.")
                chunks = chunks[:settings.MAX_CHUNKS_PER_DOCUMENT]

            report("5_CHUNK", f"Prepared {len(chunks)} chunk(s) for indexing.")

            # Step 6: Embed Vectors
            report(
                "6_EMBED",
                f"Generating embeddings with Gemini '{settings.GEMINI_EMBEDDING_MODEL}'..."
            )
            chunk_texts = [c.text for c in chunks]
            embeddings = self.embedding_service.embed_texts(chunk_texts)
            report("6_EMBED", f"Generated {len(embeddings)} embedding vector(s).")

            # Step 7: Store into Qdrant Database
            report(
                "7_STORE",
                f"Storing vectors and metadata payload into Qdrant collection '{self.qdrant_service.collection_name}'..."
            )
            upsert_count = self.qdrant_service.upsert_chunks(
                chunks=chunks,
                embeddings=embeddings,
                document_name=doc_name,
            )
            report("7_STORE", f"Successfully indexed {upsert_count} chunk(s) in Qdrant.")

            return IngestionResult(
                document_id=doc_id,
                document_name=doc_name,
                user_id=user_id,
                status=DocumentStatus.READY,
                chunk_count=len(chunks),
                total_tokens=sum(len(c.text.split()) for c in chunks),
            )

        except Exception as e:
            error_msg = str(e)
            report("FAILED", f"Ingestion failed: {error_msg}")
            return IngestionResult(
                document_id=doc_id,
                document_name=doc_name,
                user_id=user_id,
                status=DocumentStatus.FAILED,
                error=error_msg,
            )

    def ingest_files(
        self,
        file_paths: list[Path],
        user_id: str,
        max_workers: int = 3,
        on_step: Callable[[str, str], None] | None = None,
    ) -> list[IngestionResult]:
        """
        Concurrently ingest multiple documents with bounded concurrency and partial failure tolerance.
        """
        results: list[IngestionResult] = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self.ingest_file, path, user_id, None, on_step): path
                for path in file_paths
            }
            for future in as_completed(future_to_file):
                results.append(future.result())

        return results
