"""Integration tests for FastAPI routes (Health, Documents, Chat)."""

import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.main import app
from backend.app.schemas.document import Document, DocumentStatus, IngestionResult
from backend.app.schemas.query import ConstructedContext, RetrievedChunk, SourceReference
from backend.app.services.document_service import DocumentService
from backend.app.services.generation_service import GenerationService
from backend.app.services.metadata_store import MetadataStore
from backend.app.services.retrieval_service import RetrievalService


@pytest.fixture
def client(tmp_path):
    """Create test client with isolated temp metadata store."""
    temp_metadata = tmp_path / "test_docs.json"
    store = MetadataStore(file_path=temp_metadata)
    
    mock_doc_service = MagicMock(spec=DocumentService)
    mock_doc_service.metadata_store = store

    with patch("backend.app.api.routes.documents.get_document_service", return_value=mock_doc_service):
        yield TestClient(app), mock_doc_service, store


def test_root_endpoint():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Multi-Document RAG ChatBot API"
    assert data["status"] == "online"


def test_health_check_endpoint():
    client = TestClient(app)
    # Test GET
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "services" in data

    # Test POST for keep-alive pingers
    post_resp = client.post("/api/v1/health")
    assert post_resp.status_code == 200
    assert post_resp.json()["status"] == "ok"

    # Test root ping POST
    ping_resp = client.post("/ping")
    assert ping_resp.status_code == 200
    assert ping_resp.json()["status"] == "ok"


def test_list_documents_empty(client):
    test_client, mock_service, _ = client
    mock_service.list_documents.return_value = []

    response = test_client.get("/api/v1/documents")
    assert response.status_code == 200
    assert response.json() == []


def test_get_document_found_and_not_found(client):
    test_client, mock_service, _ = client

    # Case 1: Found
    mock_doc = Document(
        document_id="doc_123",
        user_id=settings.DEFAULT_USER_ID,
        document_name="test.txt",
        file_type="txt",
        file_size=100,
        status=DocumentStatus.READY,
    )
    mock_service.get_document.return_value = mock_doc

    response = test_client.get("/api/v1/documents/doc_123")
    assert response.status_code == 200
    assert response.json()["document_id"] == "doc_123"

    # Case 2: Not found
    mock_service.get_document.return_value = None
    response = test_client.get("/api/v1/documents/non_existent")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"


def test_upload_documents_success(client):
    test_client, mock_service, _ = client

    mock_result = IngestionResult(
        document_id="doc_test_1",
        document_name="notes.txt",
        user_id=settings.DEFAULT_USER_ID,
        status=DocumentStatus.READY,
        chunk_count=2,
        total_tokens=150,
    )
    mock_service.ingest_files.return_value = [mock_result]

    files = [
        ("files", ("notes.txt", io.BytesIO(b"Important notes content for RAG testing."), "text/plain"))
    ]

    response = test_client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 201
    results = response.json()
    assert len(results) == 1
    assert results[0]["document_id"] == "doc_test_1"
    assert results[0]["status"] == "READY"


def test_delete_document_success_and_not_found(client):
    test_client, mock_service, _ = client

    # Case 1: Successfully deleted
    mock_service.delete_document.return_value = True
    response = test_client.delete("/api/v1/documents/doc_123")
    assert response.status_code == 204

    # Case 2: Not found
    mock_service.delete_document.return_value = False
    response = test_client.delete("/api/v1/documents/doc_missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_chat_query_endpoint():
    test_client = TestClient(app)

    mock_context = ConstructedContext(
        formatted_text="[Doc: notes.txt | Page 1]\nRAG pipeline combines FastAPI and Qdrant.",
        chunks=[
            RetrievedChunk(
                chunk_id="chk_1",
                document_id="doc_1",
                document_name="notes.txt",
                chunk_index=0,
                page_number=1,
                text="RAG pipeline combines FastAPI and Qdrant.",
                score=0.92,
            )
        ],
        sources=[
            SourceReference(document="notes.txt", page=1, score=0.92)
        ],
        question="What does the pipeline combine?",
    )

    mock_retrieval = MagicMock(spec=RetrievalService)
    mock_retrieval.retrieve_context.return_value = mock_context

    mock_generation = MagicMock(spec=GenerationService)
    mock_generation.generate_answer.return_value = {
        "answer": "The pipeline combines FastAPI and Qdrant.",
        "sources": [{"document": "notes.txt", "page": 1, "chunk_text": "RAG pipeline combines FastAPI and Qdrant.", "score": 0.92}],
    }

    with patch("backend.app.api.routes.chat.get_retrieval_service", return_value=mock_retrieval), \
         patch("backend.app.api.routes.chat.get_generation_service", return_value=mock_generation):

        payload = {"question": "What does the pipeline combine?"}
        response = test_client.post("/api/v1/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "The pipeline combines FastAPI and Qdrant."
        assert len(data["sources"]) == 1
        assert data["sources"][0]["document"] == "notes.txt"
        assert data["query"] == "What does the pipeline combine?"


def test_chat_query_empty_question_returns_400():
    test_client = TestClient(app)
    response = test_client.post("/api/v1/chat", json={"question": "   "})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "REQUEST_ERROR"
