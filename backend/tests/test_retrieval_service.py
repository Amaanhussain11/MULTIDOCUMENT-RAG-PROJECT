"""Unit and integration tests for the RetrievalService and query pipeline."""

import pytest
from backend.app.schemas.document import DocumentChunk
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.qdrant_service import QdrantService
from backend.app.services.retrieval_service import RetrievalService


class MockEmbeddingService(EmbeddingService):
    def __init__(self, vector_map=None, default_vector=None):
        super().__init__(api_key="mock", model_name="gemini-embedding-001")
        self.vector_map = vector_map or {}
        self.default_vector = default_vector or [0.1] * 768

    def embed_texts(self, texts, batch_size=None, max_retries=3):
        results = []
        for text in texts:
            results.append(self.vector_map.get(text, self.default_vector))
        return results

    def embed_single(self, text: str):
        return self.vector_map.get(text, self.default_vector)


@pytest.fixture
def test_setup():
    """Setup in-memory Qdrant instance and Mock Embedding Service."""
    qdrant = QdrantService(url=":memory:", collection_name="rag_documents")

    # Seed vectors:
    # Vector A: highly aligned with query
    vec_a = [1.0] + [0.0] * 767
    # Vector B: somewhat aligned
    vec_b = [0.8] + [0.1] * 767
    # Vector C: orthogonal / irrelevant
    vec_c = [0.0] + [1.0] + [0.0] * 766

    embedding = MockEmbeddingService(default_vector=vec_a)
    retrieval = RetrievalService(embedding_service=embedding, qdrant_service=qdrant)

    return qdrant, embedding, retrieval, vec_a, vec_b, vec_c


def test_empty_question_returns_empty_context(test_setup):
    _, _, retrieval, _, _, _ = test_setup
    res = retrieval.retrieve_context(question="   ", user_id="user_1")
    assert res.formatted_text == ""
    assert res.chunks == []
    assert res.sources == []


def test_multi_document_and_user_isolation(test_setup):
    qdrant, _, retrieval, vec_a, vec_b, _ = test_setup

    # User 1: Doc 1
    chunks_u1_d1 = [
        DocumentChunk(
            chunk_id="u1_d1_c0",
            document_id="doc_alpha",
            user_id="user_1",
            chunk_index=0,
            text="Alpha research methodology on RAG.",
            page_number=3,
        )
    ]
    qdrant.upsert_chunks(chunks_u1_d1, [vec_a], document_name="alpha.pdf")

    # User 1: Doc 2 (Multi-document support)
    chunks_u1_d2 = [
        DocumentChunk(
            chunk_id="u1_d2_c0",
            document_id="doc_beta",
            user_id="user_1",
            chunk_index=0,
            text="Beta dataset notes and evaluation metrics.",
            page_number=7,
        )
    ]
    qdrant.upsert_chunks(chunks_u1_d2, [vec_a], document_name="beta.pdf")

    # User 2: Confidential Doc (User isolation test)
    chunks_u2 = [
        DocumentChunk(
            chunk_id="u2_d1_c0",
            document_id="doc_secret",
            user_id="user_2",
            chunk_index=0,
            text="Secret confidential information belonging to User 2.",
            page_number=1,
        )
    ]
    qdrant.upsert_chunks(chunks_u2, [vec_a], document_name="secret.pdf")

    # Query as User 1 across all documents
    context = retrieval.retrieve_context(
        question="What is the methodology?",
        user_id="user_1",
        top_k=10,
        similarity_threshold=0.1,
    )

    # User 1 should see chunks from alpha.pdf and beta.pdf
    doc_names = {c.document_name for c in context.chunks}
    assert "alpha.pdf" in doc_names
    assert "beta.pdf" in doc_names

    # User 1 must NEVER see secret.pdf belonging to User 2
    assert "secret.pdf" not in doc_names
    for chunk in context.chunks:
        assert chunk.document_id != "doc_secret"


def test_document_id_filter(test_setup):
    qdrant, _, retrieval, vec_a, _, _ = test_setup

    chunks_d1 = [
        DocumentChunk(
            chunk_id="c_doc1",
            document_id="doc_1",
            user_id="user_1",
            chunk_index=0,
            text="Content from document 1.",
            page_number=1,
        )
    ]
    chunks_d2 = [
        DocumentChunk(
            chunk_id="c_doc2",
            document_id="doc_2",
            user_id="user_1",
            chunk_index=0,
            text="Content from document 2.",
            page_number=2,
        )
    ]
    qdrant.upsert_chunks(chunks_d1, [vec_a], document_name="doc1.txt")
    qdrant.upsert_chunks(chunks_d2, [vec_a], document_name="doc2.txt")

    # Query scoped specifically to doc_1
    context = retrieval.retrieve_context(
        question="Find info",
        user_id="user_1",
        document_id="doc_1",
        top_k=5,
        similarity_threshold=0.1,
    )

    assert len(context.chunks) == 1
    assert context.chunks[0].document_id == "doc_1"
    assert context.chunks[0].document_name == "doc1.txt"


def test_similarity_threshold_filtering(test_setup):
    qdrant, _, retrieval, vec_a, _, vec_c = test_setup

    # vec_a is identical to query (cosine ~ 1.0)
    # vec_c is orthogonal to query (cosine ~ 0.0)
    chunks = [
        DocumentChunk(
            chunk_id="c_high",
            document_id="doc_test",
            user_id="user_threshold",
            chunk_index=0,
            text="High similarity chunk.",
            page_number=1,
        ),
        DocumentChunk(
            chunk_id="c_low",
            document_id="doc_test",
            user_id="user_threshold",
            chunk_index=1,
            text="Irrelevant chunk with orthogonal vector.",
            page_number=2,
        ),
    ]
    qdrant.upsert_chunks(chunks, [vec_a, vec_c], document_name="test.pdf")

    context = retrieval.retrieve_context(
        question="Query text",
        user_id="user_threshold",
        similarity_threshold=0.5,
    )

    # Only high similarity chunk should survive threshold filtering
    assert len(context.chunks) == 1
    assert context.chunks[0].chunk_id == "c_high"


def test_context_construction_format(test_setup):
    qdrant, _, retrieval, vec_a, _, _ = test_setup

    chunks = [
        DocumentChunk(
            chunk_id="c1",
            document_id="doc_1",
            user_id="user_format",
            chunk_index=0,
            text="This is page 12 content.",
            page_number=12,
        ),
        DocumentChunk(
            chunk_id="c2",
            document_id="doc_2",
            user_id="user_format",
            chunk_index=0,
            text="This is general doc content with no page.",
            page_number=None,
        ),
    ]
    qdrant.upsert_chunks(chunks, [vec_a, vec_a], document_name="guide.pdf")

    context = retrieval.retrieve_context(
        question="Format check",
        user_id="user_format",
        similarity_threshold=0.1,
    )

    # Check exact formatting: [doc_name | Page X]
    assert "[guide.pdf | Page 12]" in context.formatted_text
    assert "This is page 12 content." in context.formatted_text
    assert len(context.sources) >= 1
    assert context.sources[0].document == "guide.pdf"
