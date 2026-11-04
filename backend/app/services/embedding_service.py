"""Gemini embedding service for document chunks and queries."""

import logging
import re
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
            if i > 0:
                time.sleep(2.0)  # Gentle inter-batch pacing to avoid burst rate limits

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
        """Execute embed_content with exponential backoff and rate-limit window resets."""
        attempt = 0
        backoff_delay = 1.0

        while True:
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
                err_str = str(e)

                # Check if this is a rate-limit / quota exhaustion (HTTP 429)
                is_rate_limit = (
                    getattr(e, "code", None) == 429
                    or "RESOURCE_EXHAUSTED" in err_str
                    or "quota" in err_str.lower()
                    or "rate-limit" in err_str.lower()
                )

                if is_rate_limit:
                    # Allow up to 8 attempts for rate limit resets (covers multiple quota rollover windows)
                    rate_limit_max_retries = max(max_retries, 8)
                    if attempt >= rate_limit_max_retries:
                        logger.error(f"Gemini API rate limit exceeded after {attempt} retries: {e}")
                        raise

                    # Extract recommended delay from Google error (e.g., 'retryDelay': '53s' or 'retry in 53.01s')
                    delay_match = re.search(
                        r"(?:retryDelay|retry in)['\":\s]+(\d+(?:\.\d+)?)s?",
                        err_str,
                        re.IGNORECASE,
                    )
                    if delay_match:
                        wait_time = float(delay_match.group(1)) + 2.0
                    else:
                        wait_time = max(backoff_delay, 30.0)

                    logger.warning(
                        f"Gemini API quota rate-limit (429) hit. Pausing for {wait_time:.1f}s "
                        f"until quota window resets (attempt {attempt}/{rate_limit_max_retries})..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.warning(
                        f"Gemini API transient error on attempt {attempt}/{max_retries}: {e}. "
                        f"Retrying in {backoff_delay}s..."
                    )
                    if attempt >= max_retries:
                        raise
                    time.sleep(backoff_delay)
                    backoff_delay *= 2.0

            except Exception as e:
                # Do not retry non-API configuration/argument errors
                logger.error(f"Failed to generate embeddings: {e}")
                raise
