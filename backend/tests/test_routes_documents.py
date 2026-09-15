"""Integration tests for document management routes."""

from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.app.api.routes.documents import get_document_service, get_qdrant_service
from backend.app.main import app
from backend.app.schemas.document import Document, DocumentStatus, IngestionResult

client = TestClient(app)


@pytest.fixture
def mock_document_service():
    service = MagicMock()
    service.ingest_files.return_value = [
        IngestionResult(
            document_id="doc_123",
            document_name="test.txt",
            user_id="test_user_001",
            status=DocumentStatus.READY,
            chunk_count=2,
            total_tokens=150,
        )
    ]
    return service


@pytest.fixture
def mock_qdrant_service():
    service = MagicMock()
    service.list_user_documents.return_value = [
        Document(
            document_id="doc_123",
            user_id="test_user_001",
            document_name="test.txt",
            file_type="txt",
            file_size=1024,
            status=DocumentStatus.READY,
        )
    ]
    service.get_user_document.side_effect = lambda user_id, document_id: (
        Document(
            document_id="doc_123",
            user_id="test_user_001",
            document_name="test.txt",
            file_type="txt",
            file_size=1024,
            status=DocumentStatus.READY,
        )
        if document_id == "doc_123"
        else None
    )
    return service


def test_health_check():
    """Verify /api/v1/health returns status ok."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_documents(mock_document_service):
    """Verify document upload endpoint calls DocumentService and returns results."""
    app.dependency_overrides[get_document_service] = lambda: mock_document_service

    response = client.post(
        "/api/v1/documents/upload",
        files=[("files", ("test.txt", b"Hello world text content", "text/plain"))],
        headers={"X-User-Id": "test_user_001"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    res_data = response.json()
    assert len(res_data) == 1
    assert res_data[0]["document_id"] == "doc_123"
    assert res_data[0]["status"] == "READY"


def test_list_documents(mock_qdrant_service):
    """Verify listing documents for user."""
    app.dependency_overrides[get_qdrant_service] = lambda: mock_qdrant_service

    response = client.get(
        "/api/v1/documents",
        headers={"X-User-Id": "test_user_001"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 1
    assert docs[0]["document_id"] == "doc_123"


def test_get_document_success(mock_qdrant_service):
    """Verify get document by ID returns document schema."""
    app.dependency_overrides[get_qdrant_service] = lambda: mock_qdrant_service

    response = client.get(
        "/api/v1/documents/doc_123",
        headers={"X-User-Id": "test_user_001"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["document_id"] == "doc_123"


def test_get_document_not_found(mock_qdrant_service):
    """Verify 404 response format for missing document."""
    app.dependency_overrides[get_qdrant_service] = lambda: mock_qdrant_service

    response = client.get(
        "/api/v1/documents/non_existent_doc",
        headers={"X-User-Id": "test_user_001"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 404
    err = response.json()
    assert "error" in err
    assert err["error"]["code"] == "NOT_FOUND"


def test_delete_document(mock_qdrant_service):
    """Verify delete document calls QdrantService.delete_document."""
    app.dependency_overrides[get_qdrant_service] = lambda: mock_qdrant_service

    response = client.delete(
        "/api/v1/documents/doc_123",
        headers={"X-User-Id": "test_user_001"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["document_id"] == "doc_123"
    mock_qdrant_service.delete_document.assert_called_once_with(
        document_id="doc_123", user_id="test_user_001"
    )
