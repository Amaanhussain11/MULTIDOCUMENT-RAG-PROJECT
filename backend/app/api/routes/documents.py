"""Document management and ingestion routes."""

import logging
import os
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.app.schemas.document import Document, DocumentStatus, IngestionResult
from backend.app.services.document_service import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])
document_service = DocumentService()

UPLOAD_DIR = Path("./uploaded_documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
REGISTRY_FILE = UPLOAD_DIR / "registry.json"


def load_registry() -> dict[str, Document]:
    if REGISTRY_FILE.exists():
        try:
            import json
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {k: Document(**v) for k, v in data.items()}
        except Exception as e:
            logger.warning(f"Could not load registry.json: {e}")
    return {}


def save_registry() -> None:
    try:
        import json
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            data = {k: v.model_dump(mode="json") for k, v in DOCUMENT_REGISTRY.items()}
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.warning(f"Could not save registry.json: {e}")


DOCUMENT_REGISTRY: dict[str, Document] = load_registry()


@router.get("", response_model=list[Document])
async def list_documents():
    """List all tracked documents in the system."""
    return list(DOCUMENT_REGISTRY.values())


@router.get("/{document_id}", response_model=Document)
async def get_document(document_id: str):
    """Retrieve metadata for a specific document by its unique ID."""
    doc = DOCUMENT_REGISTRY.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")
    return doc


@router.post("/upload", response_model=list[IngestionResult])
async def upload_documents(files: list[UploadFile] = File(...)):
    """
    Upload and ingest multiple documents simultaneously:
    Parses, cleans, chunks, embeds, and stores into Qdrant.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    results: list[IngestionResult] = []

    for file in files:
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        temp_path = UPLOAD_DIR / f"{doc_id}_{file.filename}"

        try:
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            doc_entry = Document(
                document_id=doc_id,
                user_id="default_user",
                document_name=file.filename,
                file_type=file.content_type or "application/octet-stream",
                file_size=os.path.getsize(temp_path),
                status=DocumentStatus.PROCESSING,
            )
            DOCUMENT_REGISTRY[doc_id] = doc_entry

            try:
                ingestion_result = document_service.ingest_file(
                    file_path=temp_path,
                    user_id="default_user",
                    document_id=doc_id,
                )
                if ingestion_result.status == DocumentStatus.FAILED:
                    doc_entry.status = DocumentStatus.FAILED
                    doc_entry.error = ingestion_result.error
                else:
                    doc_entry.status = DocumentStatus.READY
                    doc_entry.chunk_count = ingestion_result.chunk_count
                results.append(ingestion_result)
            except Exception as ingest_err:
                logger.error(f"Ingestion failed for {file.filename}: {ingest_err}")
                doc_entry.status = DocumentStatus.FAILED
                doc_entry.error = str(ingest_err)
                results.append(
                    IngestionResult(
                        document_id=doc_id,
                        document_name=file.filename,
                        user_id="default_user",
                        status=DocumentStatus.FAILED,
                        error=str(ingest_err),
                    )
                )
        except Exception as e:
            logger.error(f"Upload error: {e}")
            results.append(
                IngestionResult(
                    document_id=doc_id,
                    document_name=file.filename or "unknown",
                    user_id="default_user",
                    status=DocumentStatus.FAILED,
                    error=str(e),
                )
            )

    save_registry()
    return results


def sync_vector_store() -> int:
    """Purge any Qdrant points and physical files whose document_id is no longer in DOCUMENT_REGISTRY."""
    valid_ids = list(DOCUMENT_REGISTRY.keys())
    
    # 1. Clean up orphaned vectors in Qdrant
    purged_count = 0
    try:
        purged_count = document_service.qdrant_service.purge_orphaned_documents(
            valid_document_ids=valid_ids,
            user_id="default_user",
        )
    except Exception as e:
        logger.error(f"Error purging orphaned vectors in Qdrant: {e}")

    # 2. Clean up orphaned files on local disk
    try:
        for file_path in UPLOAD_DIR.glob("doc_*"):
            # doc files are named "{doc_id}_{filename}"
            doc_id_part = file_path.name.split("_", 2)
            if len(doc_id_part) >= 2:
                inferred_id = f"{doc_id_part[0]}_{doc_id_part[1]}"
                if inferred_id not in valid_ids:
                    logger.info(f"Removing orphaned file: {file_path.name}")
                    file_path.unlink(missing_ok=True)
    except Exception as e:
        logger.warning(f"Error cleaning orphaned files: {e}")

    return purged_count


@router.post("/sync", response_model=dict)
async def sync_documents():
    """Synchronize Qdrant vector storage and disk storage with active DOCUMENT_REGISTRY."""
    purged_count = sync_vector_store()
    return {
        "status": "synchronized",
        "active_documents": list(DOCUMENT_REGISTRY.keys()),
        "purged_orphans": purged_count,
    }


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str):
    """Delete a document from the registry, local disk, and Qdrant vector index."""
    if document_id in DOCUMENT_REGISTRY:
        # 1. Delete vector embeddings from Qdrant
        try:
            document_service.qdrant_service.delete_document(document_id, user_id="default_user")
            logger.info(f"Deleted vector chunks for document '{document_id}' from Qdrant.")
        except Exception as e:
            logger.error(f"Failed to delete Qdrant vectors for document '{document_id}': {e}")

        # 2. Delete physical file from disk
        try:
            for file_path in UPLOAD_DIR.glob(f"{document_id}_*"):
                if file_path.is_file():
                    file_path.unlink(missing_ok=True)
                    logger.info(f"Deleted physical file '{file_path.name}'.")
        except Exception as e:
            logger.warning(f"Failed to delete physical file for '{document_id}': {e}")

        # 3. Remove from registry and persist
        del DOCUMENT_REGISTRY[document_id]
        save_registry()
        return None
    raise HTTPException(status_code=404, detail="Document not found.")
