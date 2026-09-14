"""Qdrant vector database service for chunk storage and retrieval."""

import logging
import uuid
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from backend.app.core.config import settings
from backend.app.schemas.document import DocumentChunk, QdrantPayload
from backend.app.schemas.query import RetrievedChunk

logger = logging.getLogger(__name__)


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
        if self._client is None:
            if self.url == ":memory:":
                self._client = QdrantClient(location=":memory:")
            elif self.url.startswith("http://localhost") or self.url.startswith("http://127.0.0.1"):
                try:
                    client = QdrantClient(url=self.url, api_key=self.api_key, timeout=2.0)
                    client.get_collections()
                    self._client = client
                except Exception as e:
                    logger.info(
                        f"Local Qdrant server not detected at {self.url} ({e}). "
                        f"Using embedded local disk storage at './qdrant_storage'."
                    )
                    self._client = QdrantClient(path="./qdrant_storage")
            elif self.url.startswith("http://") or self.url.startswith("https://"):
                self._client = QdrantClient(url=self.url, api_key=self.api_key)
            else:
                self._client = QdrantClient(path=self.url)
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
