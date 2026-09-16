"""Gemini embedding service for document chunks and queries."""

import logging
import time

from google import genai
from google.genai import errors

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service responsible for generating semantic vectors via Gemini API."""

    def __init__(self, api_key: str | None = None, model_name: str | None = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_EMBEDDING_MODEL
        self._client: genai.Client | None = None

    @property
    def client(self) -> genai.Client:
        """Lazy client initialization."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "GEMINI_API_KEY is not configured. Please set it in .env or environment variables."
                )
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def embed_texts(
        self,
        texts: list[str],
        batch_size: int | None = None,
        max_retries: int = 3
    ) -> list[list[float]]:
        """
        Convert a list of text strings into vector embeddings using batching.
        
        Args:
            texts: List of text strings to embed.
            batch_size: Batch size for requests (defaults to settings.EMBEDDING_BATCH_SIZE).
            max_retries: Number of retries on transient errors.
            
        Returns:
            List of vector embeddings (each a list of floats).
        """
        if not texts:
            return []

        effective_batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE
        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), effective_batch_size):
            batch = texts[i : i + effective_batch_size]
            batch_embeddings = self._embed_batch_with_retry(batch, max_retries=max_retries)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def embed_single(self, text: str) -> list[float]:
        """Embed a single text string."""
        results = self.embed_texts([text])
        if not results:
            raise RuntimeError("Failed to generate embedding for text.")
        return results[0]

    def _embed_batch_with_retry(
        self,
        batch: list[str],
        max_retries: int = 3
    ) -> list[list[float]]:
        """Execute embed_content with exponential backoff for transient errors."""
        attempt = 0
        backoff_delay = 1.0

        while attempt < max_retries:
            try:
                response = self.client.models.embed_content(
                    model=self.model_name,
                    contents=batch,
                )
                
                # Extract embeddings from response
                if hasattr(response, "embeddings") and response.embeddings:
                    return [emb.values for emb in response.embeddings]
                elif hasattr(response, "embedding") and response.embedding:
                    return [response.embedding.values]
                else:
                    raise RuntimeError("Unexpected embedding response format from Gemini API.")

            except errors.APIError as e:
                status_code = getattr(e, "code", None)
                if status_code in (400, 401, 403, 404):
                    logger.error(f"Permanent Gemini API error ({status_code}): {e}")
                    raise RuntimeError(
                        f"Permanent Gemini API error ({status_code}): {e}"
                    ) from None

                attempt += 1
                logger.warning(
                    f"Gemini API error on attempt {attempt}/{max_retries}: {e}. Retrying in {backoff_delay}s..."
                )
                if attempt >= max_retries:
                    raise
                time.sleep(backoff_delay)
                backoff_delay *= 2.0
            except Exception as e:
                # Do not retry non-API configuration/argument errors
                logger.error(f"Failed to generate embeddings: {e}")
                raise
