"""Thread-safe persistent document metadata store."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock

from backend.app.schemas.document import Document, DocumentStatus

logger = logging.getLogger(__name__)


class MetadataStore:
    """Stores and manages document lifecycle metadata on disk in JSON format."""

    def __init__(self, file_path: str | Path = "backend/data/documents.json"):
        self.file_path = Path(file_path)
        self._lock = Lock()
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.file_path.exists():
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump({}, f)
        except Exception as e:
            logger.warning(f"Could not initialize metadata file at {self.file_path}: {e}")

    def _load_all(self) -> dict[str, dict]:
        if not self.file_path.exists():
            return {}
        try:
            with open(self.file_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read metadata file: {e}")
            return {}

    def _save_all(self, data: dict[str, dict]) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to write metadata file: {e}")

    def save_document(self, doc: Document) -> Document:
        with self._lock:
            data = self._load_all()
            data[doc.document_id] = doc.model_dump(mode="json")
            self._save_all(data)
            return doc

    def update_status(
        self,
        document_id: str,
        user_id: str,
        status: DocumentStatus,
    ) -> Document | None:
        with self._lock:
            data = self._load_all()
            doc_data = data.get(document_id)
            if not doc_data or doc_data.get("user_id") != user_id:
                return None
            doc_data["status"] = status.value if hasattr(status, "value") else str(status)
            doc_data["updated_at"] = datetime.now(UTC).isoformat()
            data[document_id] = doc_data
            self._save_all(data)
            return Document(**doc_data)

    def get_document(self, document_id: str, user_id: str) -> Document | None:
        with self._lock:
            data = self._load_all()
            doc_data = data.get(document_id)
            if not doc_data:
                return None
            if doc_data.get("user_id") != user_id:
                return None
            return Document(**doc_data)

    def list_documents(self, user_id: str) -> list[Document]:
        with self._lock:
            data = self._load_all()
            docs = []
            for item in data.values():
                if item.get("user_id") == user_id:
                    docs.append(Document(**item))
            docs.sort(key=lambda d: d.created_at, reverse=True)
            return docs

    def delete_document(self, document_id: str, user_id: str) -> bool:
        with self._lock:
            data = self._load_all()
            doc_data = data.get(document_id)
            if not doc_data or doc_data.get("user_id") != user_id:
                return False
            del data[document_id]
            self._save_all(data)
            return True
