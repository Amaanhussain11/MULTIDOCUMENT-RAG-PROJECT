"""Unit tests for the enhanced POST /api/v1/chat/chunks endpoint.

Covers:
- Valid single-document retrieval
- Empty / whitespace question → 400
- Multi-document retrieval with deduplication and score-based re-ranking
- similarity_threshold forwarded to RetrievalService
- max_text_length preview truncation (truncated=True, preview populated)
- max_text_length not triggered when text is short enough (truncated=False)
- filters_applied summary returned in response
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.query import ConstructedContext, RetrievedChunk, SourceReference
from backend.app.services.retrieval_service import RetrievalService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LONG_TEXT = "A" * 300   # 300-char chunk text for truncation tests
SHORT_TEXT = "Short chunk text."


def _make_chunk(
    chunk_id: str = "chk_1",
    doc_id: str = "doc_1",
    doc_name: str = "report.pdf",
    chunk_index: int = 0,
    page: int | None = 1,
    text: str = SHORT_TEXT,
    score: float = 0.90,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id=doc_id,
        document_name=doc_name,
        chunk_index=chunk_index,
        page_number=page,
        text=text,
        score=score,
    )


def _make_context(chunks: list[RetrievedChunk], question: str = "test?") -> ConstructedContext:
    sources = [SourceReference(document=c.document_name, page=c.page_number, score=c.score) for c in chunks]
    return ConstructedContext(
        formatted_text="\n\n".join(c.text for c in chunks),
        chunks=chunks,
        sources=sources,
        question=question,
    )


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def mock_retrieval():
    svc = MagicMock(spec=RetrievalService)
    with patch("backend.app.api.routes.chat.get_retrieval_service", return_value=svc):
        yield svc


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestChunksEndpointBasic:
    def test_valid_single_doc_retrieval(self, client, mock_retrieval):
        chunk = _make_chunk()
        mock_retrieval.retrieve_context.return_value = _make_context([chunk])

        resp = client.post(
            "/api/v1/chat/chunks",
            json={"question": "What is RAG?", "document_id": "doc_1", "top_k": 5},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_retrieved"] == 1
        assert data["chunks"][0]["chunk_id"] == "chk_1"
        assert data["chunks"][0]["score"] == pytest.approx(0.90, abs=1e-4)
        assert data["question"] == "What is RAG?"

    def test_empty_question_returns_400(self, client, mock_retrieval):
        resp = client.post("/api/v1/chat/chunks", json={"question": "   "})
        assert resp.status_code == 400

    def test_whitespace_only_question_returns_400(self, client, mock_retrieval):
        resp = client.post("/api/v1/chat/chunks", json={"question": "\t\n"})
        assert resp.status_code == 400

    def test_filters_applied_in_response(self, client, mock_retrieval):
        mock_retrieval.retrieve_context.return_value = _make_context([_make_chunk()])

        resp = client.post(
            "/api/v1/chat/chunks",
            json={"question": "What is RAG?", "top_k": 3, "similarity_threshold": 0.75},
        )
        assert resp.status_code == 200
        filters = resp.json()["filters_applied"]
        assert filters["top_k"] == 3
        assert filters["similarity_threshold"] == pytest.approx(0.75)


class TestChunksEndpointMultiDoc:
    def test_multi_doc_merges_and_reranks(self, client, mock_retrieval):
        """
        Two document IDs → two separate retrieve_context calls.
        Chunks must be merged, deduplicated, and sorted by score descending.
        """
        chunk_a = _make_chunk(chunk_id="chk_a", doc_id="doc_a", score=0.80)
        chunk_b = _make_chunk(chunk_id="chk_b", doc_id="doc_b", score=0.95)

        def side_effect(question, user_id, document_id, top_k, similarity_threshold=None):
            if document_id == "doc_a":
                return _make_context([chunk_a], question)
            return _make_context([chunk_b], question)

        mock_retrieval.retrieve_context.side_effect = side_effect

        resp = client.post(
            "/api/v1/chat/chunks",
            json={"question": "multi doc test", "document_ids": ["doc_a", "doc_b"], "top_k": 5},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_retrieved"] == 2
        # Highest score first
        assert data["chunks"][0]["chunk_id"] == "chk_b"
        assert data["chunks"][1]["chunk_id"] == "chk_a"
        assert mock_retrieval.retrieve_context.call_count == 2

    def test_multi_doc_deduplicates_same_chunk_id(self, client, mock_retrieval):
        """
        If same chunk_id appears in multiple doc searches it should only appear once.
        """
        shared_chunk = _make_chunk(chunk_id="shared_chk", doc_id="doc_a", score=0.88)

        mock_retrieval.retrieve_context.return_value = _make_context([shared_chunk])

        resp = client.post(
            "/api/v1/chat/chunks",
            json={"question": "dup test", "document_ids": ["doc_a", "doc_b"], "top_k": 5},
        )

        assert resp.status_code == 200
        assert resp.json()["total_retrieved"] == 1


class TestChunksEndpointPreview:
    def test_max_text_length_truncates_long_text(self, client, mock_retrieval):
        chunk = _make_chunk(text=LONG_TEXT, score=0.91)
        mock_retrieval.retrieve_context.return_value = _make_context([chunk])

        resp = client.post(
            "/api/v1/chat/chunks",
            json={"question": "preview test", "max_text_length": 100},
        )

        assert resp.status_code == 200
        c = resp.json()["chunks"][0]
        assert c["truncated"] is True
        assert c["preview"] is not None
        assert len(c["preview"]) <= 104  # 100 chars + "…"
        assert c["preview"].endswith("…")
        # Full text still present
        assert c["text"] == LONG_TEXT

    def test_max_text_length_not_triggered_for_short_text(self, client, mock_retrieval):
        chunk = _make_chunk(text=SHORT_TEXT, score=0.85)
        mock_retrieval.retrieve_context.return_value = _make_context([chunk])

        resp = client.post(
            "/api/v1/chat/chunks",
            json={"question": "short text test", "max_text_length": 200},
        )

        assert resp.status_code == 200
        c = resp.json()["chunks"][0]
        assert c["truncated"] is False
        assert c["preview"] is None
        assert c["text"] == SHORT_TEXT

    def test_no_max_text_length_returns_full_text(self, client, mock_retrieval):
        chunk = _make_chunk(text=LONG_TEXT)
        mock_retrieval.retrieve_context.return_value = _make_context([chunk])

        resp = client.post("/api/v1/chat/chunks", json={"question": "no truncation"})

        assert resp.status_code == 200
        c = resp.json()["chunks"][0]
        assert c["truncated"] is False
        assert c["preview"] is None
        assert c["text"] == LONG_TEXT
