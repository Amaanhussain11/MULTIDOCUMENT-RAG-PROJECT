"""Qdrant vector database service for chunk storage and retrieval."""

import logging
import re
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from backend.app.core.config import settings
from backend.app.schemas.document import DocumentChunk, QdrantPayload
from backend.app.schemas.query import RetrievedChunk

logger = logging.getLogger(__name__)


_SHARED_QDRANT_CLIENT: QdrantClient | None = None


def get_shared_qdrant_client(url: str, api_key: str | None = None) -> QdrantClient:
    """Thread-safe singleton for local and remote Qdrant storage."""
    global _SHARED_QDRANT_CLIENT
    if _SHARED_QDRANT_CLIENT is not None:
        return _SHARED_QDRANT_CLIENT

    if url == ":memory:":
        _SHARED_QDRANT_CLIENT = QdrantClient(location=":memory:")
    elif url.startswith("http://localhost") or url.startswith("http://127.0.0.1"):
        try:
            client = QdrantClient(url=url, api_key=api_key, timeout=1.5)
            client.get_collections()
            _SHARED_QDRANT_CLIENT = client
        except Exception as e:
            logger.info(
                f"Local Qdrant server not detected at {url} ({e}). "
                f"Using embedded local disk storage at './qdrant_storage'."
            )
            _SHARED_QDRANT_CLIENT = QdrantClient(path="./qdrant_storage")
    elif url.startswith("http://") or url.startswith("https://"):
        _SHARED_QDRANT_CLIENT = QdrantClient(url=url, api_key=api_key)
    else:
        _SHARED_QDRANT_CLIENT = QdrantClient(path=url)

    return _SHARED_QDRANT_CLIENT


class QdrantService:
    """Service for interacting with the Qdrant vector database."""

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        collection_name: str | None = None,
        client: QdrantClient | None = None,
    ):
        self.url = url or settings.QDRANT_URL
        self.api_key = api_key or settings.QDRANT_API_KEY
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME
        self._client = client

    @property
    def client(self) -> QdrantClient:
        """Lazy QdrantClient initialization using shared singleton to avoid storage file lock contention."""
        if self._client is not None:
            return self._client
        return get_shared_qdrant_client(self.url, self.api_key)

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
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
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

        points: list[qmodels.PointStruct] = []
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

    def delete_document(self, document_id: str, user_id: str = "default_user") -> None:
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
            ),
            wait=True,
        )

    def purge_orphaned_documents(self, valid_document_ids: list[str], user_id: str = "default_user") -> int:
        """Delete all points in Qdrant for this user whose document_id is NOT in valid_document_ids."""
        collections = self.client.get_collections().collections
        if not any(c.name == self.collection_name for c in collections):
            return 0

        valid_set = set(valid_document_ids)
        orphaned_ids = set()
        offset = None

        try:
            while True:
                scroll_res = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key="user_id",
                                match=qmodels.MatchValue(value=user_id)
                            )
                        ]
                    ),
                    limit=100,
                    with_payload=True,
                    with_vectors=False,
                    offset=offset,
                )
                points, next_offset = scroll_res
                for pt in points:
                    payload = pt.payload or {}
                    d_id = payload.get("document_id")
                    if d_id and d_id not in valid_set:
                        orphaned_ids.add(d_id)
                if next_offset is None or not points:
                    break
                offset = next_offset

            if orphaned_ids:
                logger.info(f"Purging {len(orphaned_ids)} orphaned document(s) from Qdrant: {orphaned_ids}")
                for o_id in orphaned_ids:
                    self.delete_document(o_id, user_id)
            return len(orphaned_ids)
        except Exception as e:
            logger.error(f"Error purging orphaned documents from Qdrant: {e}")
            return 0

    def search_chunks(
        self,
        query_vector: list[float],
        user_id: str,
        document_id: str | None = None,
        document_ids: list[str] | None = None,
        top_k: int = 5,
        score_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        """
        Search for the most similar chunks in Qdrant with mandatory user isolation.

        Args:
            query_vector: Dense embedding vector for the question.
            user_id: Authenticated user ID (strictly required for isolation).
            document_id: Optional single document ID to filter search within.
            document_ids: Optional list of document IDs to filter search within.
            top_k: Maximum number of chunks to return (default 5).
            score_threshold: Minimum similarity score threshold.

        Returns:
            List of RetrievedChunk models ordered by similarity.
        """
        # If document_ids is explicitly provided as empty list, no documents are in scope
        if document_ids is not None and len(document_ids) == 0:
            return []

        # Ensure collection exists before querying
        collections = self.client.get_collections().collections
        if not any(c.name == self.collection_name for c in collections):
            logger.warning(f"Collection '{self.collection_name}' does not exist.")
            return []

        # Strict user isolation filter
        filter_conditions: list[qmodels.Condition] = [
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
        elif document_ids is not None:
            filter_conditions.append(
                qmodels.FieldCondition(
                    key="document_id",
                    match=qmodels.MatchAny(any=document_ids)
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

        retrieved: list[RetrievedChunk] = []
        for point in scored_points:
            payload = point.payload or {}
            raw_doc_name = str(payload.get("document_name", ""))
            clean_doc_name = re.sub(r"^(doc_[a-zA-Z0-9]+_)+", "", raw_doc_name)
            retrieved.append(
                RetrievedChunk(
                    chunk_id=str(payload.get("chunk_id", point.id)),
                    document_id=str(payload.get("document_id", "")),
                    document_name=clean_doc_name,
                    chunk_index=int(payload.get("chunk_index", 0)),
                    page_number=payload.get("page_number"),
                    text=str(payload.get("text", "")),
                    score=float(point.score),
                )
            )

        return retrieved
