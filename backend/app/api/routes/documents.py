import logging
import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Header,
    HTTPException,
    Response,
    UploadFile,
    status,
)

from backend.app.core.config import settings
from backend.app.schemas.document import Document, DocumentStatus, IngestionResult
from backend.app.services.document_service import DocumentService
from backend.app.utils.validator import validate_document_file

logger = logging.getLogger(__name__)

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


def _process_upload_files_background(
    file_paths: list[Path],
    user_id: str,
    doc_ids: list[str],
    temp_dir: Path,
    service: DocumentService,
):
    """Background worker to ingest files without blocking the HTTP upload response."""
    try:
        for path, doc_id in zip(file_paths, doc_ids):
            service.ingest_file(
                file_path=path,
                user_id=user_id,
                document_id=doc_id,
            )
    except Exception as e:
        logger.error(f"Unhandled error in background ingestion: {e}", exc_info=True)
    finally:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


@router.post("/upload", response_model=list[IngestionResult], status_code=status.HTTP_201_CREATED)
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    x_user_id: str | None = Header(None, alias="x-user-id"),
):
    """
    Upload and ingest multiple documents (PDF, DOCX, TXT) into the vector store.
    Validates files synchronously and offloads heavy parsing/embedding to a background worker
    to prevent reverse-proxy / Cloudflare 100-second timeouts on large documents.
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
    initial_results: list[IngestionResult] = []
    doc_ids: list[str] = []

    try:
        for file in files:
            file_name = Path(file.filename).name if file.filename else "uploaded_document.txt"
            temp_file_path = temp_dir / file_name

            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Pre-validate file existence, format, and size synchronously
            validate_document_file(temp_file_path)

            doc_id = f"doc_{uuid.uuid4().hex[:12]}"
            doc_ids.append(doc_id)
            saved_paths.append(temp_file_path)

            file_size = temp_file_path.stat().st_size
            doc_record = Document(
                document_id=doc_id,
                user_id=user_id,
                document_name=file_name,
                file_type=temp_file_path.suffix.lstrip("."),
                file_size=file_size,
                status=DocumentStatus.PROCESSING,
            )
            service.metadata_store.save_document(doc_record)

            initial_results.append(
                IngestionResult(
                    document_id=doc_id,
                    document_name=file_name,
                    user_id=user_id,
                    status=DocumentStatus.PROCESSING,
                    chunk_count=0,
                    total_tokens=0,
                )
            )

        # Dispatch background ingestion task
        background_tasks.add_task(
            _process_upload_files_background,
            saved_paths,
            user_id,
            doc_ids,
            temp_dir,
            service,
        )

        return initial_results

    except Exception:
        # Clean up temp_dir if synchronous validation failed
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise



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
