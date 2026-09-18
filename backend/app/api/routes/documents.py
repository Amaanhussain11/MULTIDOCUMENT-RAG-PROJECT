"""Document management endpoints."""

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Header, HTTPException, Response, UploadFile, status

from backend.app.core.config import settings
from backend.app.schemas.document import Document, IngestionResult
from backend.app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])

# Reusable service instance
_document_service: DocumentService | None = None


def get_document_service() -> DocumentService:
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service


@router.get("", response_model=list[Document])
def list_documents(
    x_user_id: str | None = Header(None, alias="x-user-id"),
):
    """Retrieve all indexed documents for the current user."""
    user_id = x_user_id or settings.DEFAULT_USER_ID
    service = get_document_service()
    return service.list_documents(user_id)


@router.get("/{document_id}", response_model=Document)
def get_document(
    document_id: str,
    x_user_id: str | None = Header(None, alias="x-user-id"),
):
    """Get metadata for a specific document."""
    user_id = x_user_id or settings.DEFAULT_USER_ID
    service = get_document_service()
    doc = service.get_document(document_id, user_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' was not found.",
        )
    return doc


@router.post("/upload", response_model=list[IngestionResult], status_code=status.HTTP_201_CREATED)
async def upload_documents(
    files: list[UploadFile] = File(...),
    x_user_id: str | None = Header(None, alias="x-user-id"),
):
    """
    Upload and ingest multiple documents (PDF, DOCX, TXT) into the vector store.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided for upload.",
        )

    user_id = x_user_id or settings.DEFAULT_USER_ID
    service = get_document_service()

    temp_dir = Path(tempfile.mkdtemp(prefix="rag_upload_"))
    saved_paths: list[Path] = []

    try:
        for file in files:
            file_name = Path(file.filename).name if file.filename else "uploaded_document.txt"
            temp_file_path = temp_dir / file_name

            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            saved_paths.append(temp_file_path)

        # Ingest all uploaded files through the pipeline
        results = service.ingest_files(saved_paths, user_id=user_id)
        return results

    finally:
        # Clean up temporary upload files
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    x_user_id: str | None = Header(None, alias="x-user-id"),
):
    """Delete a document and all its indexed vector chunks."""
    user_id = x_user_id or settings.DEFAULT_USER_ID
    service = get_document_service()
    deleted = service.delete_document(document_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
