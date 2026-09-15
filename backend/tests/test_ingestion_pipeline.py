"""End-to-end test for document ingestion pipeline."""

from pathlib import Path
from backend.app.schemas.document import DocumentStatus
from backend.app.services.document_service import DocumentService
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.qdrant_service import QdrantService


class DummyEmbeddingService(EmbeddingService):
    def embed_texts(self, texts, batch_size=None, max_retries=3):
        # Deterministic 768-dim mock vector for each chunk
        return [[0.1 * ((i % 10) + 1)] * 768 for i in range(len(texts))]


def test_end_to_end_ingestion(tmp_path: Path):
    # 1. Create a sample text file
    sample_file = tmp_path / "research_notes.txt"
    sample_file.write_text(
        "Introduction to Retrieval-Augmented Generation.\n\n"
        "RAG combines information retrieval with large language models.\n"
        "Documents are parsed, cleaned, chunked, and embedded.\n"
        "Vectors are stored in Qdrant for semantic search."
    )

    # 2. Setup services with in-memory Qdrant and dummy embeddings
    qdrant_service = QdrantService(url=":memory:", collection_name="rag_documents")
    embedding_service = DummyEmbeddingService()
    document_service = DocumentService(
        embedding_service=embedding_service,
        qdrant_service=qdrant_service
    )

    # 3. Ingest the file
    recorded_steps = []
    def on_step_callback(step: str, msg: str):
        recorded_steps.append(step)

    result = document_service.ingest_file(
        file_path=sample_file,
        user_id="user_test_42",
        on_step=on_step_callback
    )

    # 4. Verify results
    assert result.status == DocumentStatus.READY
    assert result.chunk_count > 0
    assert result.user_id == "user_test_42"
    assert result.document_name == "research_notes.txt"

    # Verify all 7 steps executed in order
    assert "1_UPLOAD" in recorded_steps
    assert "2_VALIDATE" in recorded_steps
    assert "3_PARSE" in recorded_steps
    assert "4_CLEAN" in recorded_steps
    assert "5_CHUNK" in recorded_steps
    assert "6_EMBED" in recorded_steps
    assert "7_STORE" in recorded_steps

    # Verify points stored in Qdrant with payload
    points_res = qdrant_service.client.scroll(
        collection_name="rag_documents",
        limit=10,
        with_payload=True
    )
    points, _ = points_res
    assert len(points) == result.chunk_count
    first_payload = points[0].payload
    assert first_payload["user_id"] == "user_test_42"
    assert first_payload["document_name"] == "research_notes.txt"
    assert "text" in first_payload
