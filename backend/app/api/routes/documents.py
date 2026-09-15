"""Document management API endpoints."""

import os
import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile

from backend.app.schemas.document import Document, IngestionResult
from backend.app.services.document_service import DocumentService
from backend.app.services.qdrant_service import QdrantService

router = APIRouter(prefix="/documents", tags=["documents"])

# Global singleton service instances for default route dependencies
_document_service_instance = DocumentService()
_qdrant_service_instance = QdrantService()


def get_document_service() -> DocumentService:
    """Dependency provider for DocumentService."""
    return _document_service_instance


def get_qdrant_service() -> QdrantService:
    """Dependency provider for QdrantService."""
    return _qdrant_service_instance


# TODO: Per Spec Section 14.8, client-provided user_id from headers (X-User-Id) must NOT be trusted
# as proof of identity in production. Replace this header extraction with a proper JWT/session authorization layer.


@router.post("/upload", response_model=List[IngestionResult])
async def upload_documents(
    files: List[UploadFile] = File(...),
    user_id: str = Header(default="test_user_001", alias="X-User-Id"),
    service: DocumentService = Depends(get_document_service),
):
    """
    Upload and ingest multiple documents into the vector database.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided for upload.")

    temp_dir = tempfile.mkdtemp(prefix="rag_upload_")
    temp_paths: List[Path] = []
    try:
        for file in files:
            safe_filename = Path(file.filename or "upload.tmp").name
            target_path = Path(temp_dir) / safe_filename
            with open(target_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            temp_paths.append(target_path)

        results = service.ingest_files(file_paths=temp_paths, user_id=user_id)
        return results
    finally:
        for p in temp_paths:
            if p.exists():
                try:
                    os.remove(p)
                except Exception:
                    pass
        if os.path.exists(temp_dir):
            try:
                os.rmdir(temp_dir)
            except Exception:
                pass


@router.get("", response_model=List[Document])
@router.get("/", response_model=List[Document], include_in_schema=False)
async def list_documents(
    user_id: str = Header(default="test_user_001", alias="X-User-Id"),
    service: QdrantService = Depends(get_qdrant_service),
):
    """
    List all processed documents belonging to the authenticated user.
    """
    return service.list_user_documents(user_id=user_id)


@router.get("/{document_id}", response_model=Document)
async def get_document(
    document_id: str,
    user_id: str = Header(default="test_user_001", alias="X-User-Id"),
    service: QdrantService = Depends(get_qdrant_service),
):
    """
    Retrieve single document metadata by ID for the authenticated user.
    """
    doc = service.get_user_document(user_id=user_id, document_id=document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")
    return doc


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    user_id: str = Header(default="test_user_001", alias="X-User-Id"),
    service: QdrantService = Depends(get_qdrant_service),
):
    """
    Delete all chunks for a document from Qdrant vector storage.
    """
    service.delete_document(document_id=document_id, user_id=user_id)
    return {"message": "Document deleted successfully", "document_id": document_id}
