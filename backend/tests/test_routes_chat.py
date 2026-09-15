"""Integration tests for chat RAG query route."""

from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.api.routes.chat import get_generation_service, get_retrieval_service
from backend.app.main import app
from backend.app.schemas.query import ConstructedContext, GeneratedAnswer, SourceReference

client = TestClient(app)


@pytest.fixture
def mock_retrieval_service():
    service = MagicMock()
    service.retrieve_context.return_value = ConstructedContext(
        formatted_text="[doc.pdf | Page 1]\nThe system architecture follows RAG principles.",
        chunks=[],
        sources=[SourceReference(document="doc.pdf", page=1, score=0.92)],
        question="What principles does the system follow?",
    )
    return service


@pytest.fixture
def mock_generation_service():
    service = MagicMock()
    service.generate_answer.return_value = GeneratedAnswer(
        answer="The system architecture follows RAG principles.",
        sources=[SourceReference(document="doc.pdf", page=1, score=0.92)],
    )
    return service


def test_chat_query_success(mock_retrieval_service, mock_generation_service):
    """Verify chat query calls retrieval then generation service and returns answer schema."""
    app.dependency_overrides[get_retrieval_service] = lambda: mock_retrieval_service
    app.dependency_overrides[get_generation_service] = lambda: mock_generation_service

    payload = {
        "question": "What principles does the system follow?",
        "document_id": "doc_123",
    }
    response = client.post(
        "/api/v1/chat/query",
        json=payload,
        headers={"X-User-Id": "user_001"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["answer"] == "The system architecture follows RAG principles."
    assert len(res_data["sources"]) == 1
    assert res_data["sources"][0]["document"] == "doc.pdf"

    mock_retrieval_service.retrieve_context.assert_called_once_with(
        question="What principles does the system follow?",
        user_id="user_001",
        document_id="doc_123",
    )


def test_chat_query_alias_endpoint(mock_retrieval_service, mock_generation_service):
    """Verify POST /api/v1/chat works identically to /api/v1/chat/query."""
    app.dependency_overrides[get_retrieval_service] = lambda: mock_retrieval_service
    app.dependency_overrides[get_generation_service] = lambda: mock_generation_service

    payload = {"question": "What principles does the system follow?"}
    response = client.post(
        "/api/v1/chat",
        json=payload,
        headers={"X-User-Id": "user_001"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["answer"] == "The system architecture follows RAG principles."
