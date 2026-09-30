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
        max_retries: int = 5
    ) -> list[list[float]]:
        """
        Convert a list of text strings into vector embeddings using batching and rate limiting.
        
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

        total_batches = (len(texts) + effective_batch_size - 1) // effective_batch_size

        for b_idx, i in enumerate(range(0, len(texts), effective_batch_size)):
            batch = texts[i : i + effective_batch_size]
            batch_embeddings = self._embed_batch_with_retry(batch, max_retries=max_retries)
            all_embeddings.extend(batch_embeddings)

            # Throttle between batches to strictly adhere to Gemini Free Tier (15 RPM)
            if b_idx < total_batches - 1 and settings.EMBEDDING_DELAY_SECONDS > 0:
                time.sleep(settings.EMBEDDING_DELAY_SECONDS)

        return all_embeddings

    def embed_single(self, text: str) -> list[float]:
        """Embed a single text string."""
        results = self.embed_texts([text], max_retries=5)
        if not results:
            raise RuntimeError("Failed to generate embedding for text.")
        return results[0]

    def _embed_batch_with_retry(
        self,
        batch: list[str],
        max_retries: int = 5
    ) -> list[list[float]]:
        """Execute embed_content with exponential backoff for transient and rate-limit (429) errors."""
        attempt = 0
        backoff_delays = [3.0, 7.0, 15.0, 30.0, 45.0]

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
                attempt += 1
                delay = backoff_delays[min(attempt - 1, len(backoff_delays) - 1)]
                logger.warning(
                    f"Gemini API rate limit or error on attempt {attempt}/{max_retries}: {e}. Backing off for {delay}s..."
                )
                if attempt >= max_retries:
                    raise
                time.sleep(delay)
            except Exception as e:
                # Do not retry non-API configuration/argument errors
                logger.error(f"Failed to generate embeddings: {e}")
                raise
