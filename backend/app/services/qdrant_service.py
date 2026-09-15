import logging
import uuid
from pathlib import Path
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from backend.app.core.config import settings
from backend.app.schemas.document import Document, DocumentChunk, DocumentStatus, QdrantPayload
from backend.app.schemas.query import RetrievedChunk


logger = logging.getLogger(__name__)


_shared_disk_client: Optional[QdrantClient] = None
_shared_memory_client: Optional[QdrantClient] = None
_remote_connection_failed: bool = False


class QdrantService:
    """Service for interacting with the Qdrant vector database."""

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: Optional[str] = None,
        client: Optional[QdrantClient] = None,
    ):
        self.url = url or settings.QDRANT_URL
        self.api_key = api_key or settings.QDRANT_API_KEY
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME
        self._client = client

    @property
    def client(self) -> QdrantClient:
        """Lazy QdrantClient initialization with fallback to local disk storage if localhost is offline."""
        global _shared_disk_client, _shared_memory_client, _remote_connection_failed

        if self._client is None:
            if self.url == ":memory:":
                if _shared_memory_client is None:
                    _shared_memory_client = QdrantClient(location=":memory:")
                self._client = _shared_memory_client
            elif self.url.startswith("http://localhost") or self.url.startswith("http://127.0.0.1"):
                if not _remote_connection_failed:
                    try:
                        client = QdrantClient(url=self.url, api_key=self.api_key, timeout=0.5)
                        client.get_collections()
                        self._client = client
                        return self._client
                    except Exception as e:
                        _remote_connection_failed = True
                        logger.info(
                            f"Local Qdrant server not detected at {self.url} ({e}). "
                            f"Using embedded local disk storage at './qdrant_storage'."
                        )

                if _shared_disk_client is None:
                    try:
                        _shared_disk_client = QdrantClient(path="./qdrant_storage")
                    except Exception as disk_err:
                        logger.warning(
                            f"Unable to lock local disk storage './qdrant_storage' ({disk_err}). "
                            "Falling back to in-memory Qdrant instance."
                        )
                        if _shared_memory_client is None:
                            _shared_memory_client = QdrantClient(location=":memory:")
                        _shared_disk_client = _shared_memory_client

                self._client = _shared_disk_client
            elif self.url.startswith("http://") or self.url.startswith("https://"):
                self._client = QdrantClient(url=self.url, api_key=self.api_key)
            else:
                if _shared_disk_client is None:
                    try:
                        _shared_disk_client = QdrantClient(path=self.url)
                    except Exception as disk_err:
                        logger.warning(f"Disk storage error for {self.url}: {disk_err}. Falling back to :memory:")
                        if _shared_memory_client is None:
                            _shared_memory_client = QdrantClient(location=":memory:")
                        _shared_disk_client = _shared_memory_client
                self._client = _shared_disk_client
        return self._client

    def ensure_collection(self, vector_size: int) -> None:
        """Create the rag_documents collection if it doesn't exist, and index metadata fields."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            logger.info(f"Creating Qdrant collection '{self.collection_name}' with vector size {vector_size}...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(
                    size=vector_size,
                    distance=qmodels.Distance.COSINE
                )
            )
            # Create payload indices for fast user and document isolation filtering
            self._create_payload_indices()

    def _create_payload_indices(self) -> None:
        """Create keyword indices for user_id and document_id to support efficient filtering."""
        import warnings
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning, message=".*Payload indexes have no effect in the local Qdrant.*")
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="user_id",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD
                )
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="document_id",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD
                )
        except Exception as e:
            logger.debug(f"Payload index creation note: {e}")

    def upsert_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
        document_name: str,
    ) -> int:
        """
        Store chunks and their vector embeddings into Qdrant.
        
        Args:
            chunks: List of DocumentChunk objects.
            embeddings: Corresponding list of vector embeddings.
            document_name: Name of the originating document.
            
        Returns:
            Number of points upserted.
        """
        if not chunks:
            return 0

        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Mismatch: received {len(chunks)} chunks but {len(embeddings)} embeddings."
            )

        # Ensure collection exists using vector dimension of first embedding
        vector_dim = len(embeddings[0])
        self.ensure_collection(vector_size=vector_dim)

        points: List[qmodels.PointStruct] = []
        for chunk, vector in zip(chunks, embeddings):
            # Deterministic UUID based on chunk_id so upserts are idempotent
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id))

            payload = QdrantPayload(
                user_id=chunk.user_id,
                document_id=chunk.document_id,
                document_name=document_name,
                chunk_id=chunk.chunk_id,
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                text=chunk.text
            ).model_dump()

            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            )

        # Batch upsert points
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True
        )

        logger.info(f"Upserted {len(points)} chunks into '{self.collection_name}'.")
        return len(points)

    def delete_document(self, document_id: str, user_id: str) -> None:
        """Delete all chunks belonging to a document under a specific user."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="document_id",
                            match=qmodels.MatchValue(value=document_id)
                        ),
                        qmodels.FieldCondition(
                            key="user_id",
                            match=qmodels.MatchValue(value=user_id)
                        )
                    ]
                )
            )
        )

    def search_chunks(
        self,
        query_vector: List[float],
        user_id: str,
        document_id: Optional[str] = None,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        """
        Search for the most similar chunks in Qdrant with mandatory user isolation.

        Args:
            query_vector: Dense embedding vector for the question.
            user_id: Authenticated user ID (strictly required for isolation).
            document_id: Optional specific document ID to filter search within.
            top_k: Maximum number of chunks to return (default 5).
            score_threshold: Minimum similarity score threshold.

        Returns:
            List of RetrievedChunk models ordered by similarity.
        """
        # Ensure collection exists before querying
        collections = self.client.get_collections().collections
        if not any(c.name == self.collection_name for c in collections):
            logger.warning(f"Collection '{self.collection_name}' does not exist.")
            return []

        # Strict user isolation filter
        filter_conditions = [
            qmodels.FieldCondition(
                key="user_id",
                match=qmodels.MatchValue(value=user_id)
            )
        ]

        if document_id:
            filter_conditions.append(
                qmodels.FieldCondition(
                    key="document_id",
                    match=qmodels.MatchValue(value=document_id)
                )
            )

        query_filter = qmodels.Filter(must=filter_conditions)

        if hasattr(self.client, "query_points"):
            query_res = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=top_k,
                score_threshold=score_threshold,
            )
            scored_points = query_res.points
        elif hasattr(self.client, "search"):
            scored_points = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=top_k,
                score_threshold=score_threshold,
            )
        else:
            raise RuntimeError("QdrantClient has neither query_points nor search method.")

        retrieved: List[RetrievedChunk] = []
        for point in scored_points:
            payload = point.payload or {}
            retrieved.append(
                RetrievedChunk(
                    chunk_id=str(payload.get("chunk_id", point.id)),
                    document_id=str(payload.get("document_id", "")),
                    document_name=str(payload.get("document_name", "")),
                    chunk_index=int(payload.get("chunk_index", 0)),
                    page_number=payload.get("page_number"),
                    text=str(payload.get("text", "")),
                    score=float(point.score),
                )
            )

        return retrieved

    def list_user_documents(self, user_id: str) -> List[Document]:
        """
        Scan payload metadata in Qdrant to list all distinct documents belonging to a user.
        """
        collections = self.client.get_collections().collections
        if not any(c.name == self.collection_name for c in collections):
            return []

        scroll_filter = qmodels.Filter(
            must=[
                qmodels.FieldCondition(
                    key="user_id",
                    match=qmodels.MatchValue(value=user_id)
                )
            ]
        )

        docs_map = {}
        offset = None

        while True:
            scroll_res = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=scroll_filter,
                limit=250,
                with_payload=True,
                with_vectors=False,
                offset=offset,
            )
            points, next_offset = scroll_res
            for point in points:
                payload = point.payload or {}
                doc_id = payload.get("document_id")
                if doc_id and doc_id not in docs_map:
                    doc_name = payload.get("document_name", "unknown")
                    ext = Path(doc_name).suffix.lstrip(".") if "." in doc_name else "txt"
                    docs_map[doc_id] = Document(
                        document_id=doc_id,
                        user_id=user_id,
                        document_name=doc_name,
                        file_type=ext,
                        file_size=0,
                        status=DocumentStatus.READY,
                    )
            if next_offset is None or not points:
                break
            offset = next_offset

        return list(docs_map.values())

    def get_user_document(self, user_id: str, document_id: str) -> Optional[Document]:
        """
        Retrieve document metadata for a single document ID under a user.
        """
        docs = self.list_user_documents(user_id)
        for doc in docs:
            if doc.document_id == document_id:
                return doc
        return None
