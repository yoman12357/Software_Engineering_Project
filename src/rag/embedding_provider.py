"""Embedding provider abstraction for RAG.

Phase 4 implements the OllamaNomicEmbeddingProvider using nomic-embed-text
via the local Ollama instance. No external APIs are used.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod

import httpx

from ..core.config import Settings

logger = logging.getLogger(__name__)


class EmbeddingProviderError(Exception):
    """Raised when embedding generation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Embedding generation failed: {message}")


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers.

    Implementations must provide an `embed` method that takes a list of
    texts and returns a list of embedding vectors (list of floats).
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name for logging/metadata."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name used for embeddings."""

    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Return the dimension of the embedding vectors."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (list of floats).

        Raises:
            EmbeddingProviderError: If embedding generation fails.
        """

    def embed_sync(self, texts: list[str]) -> list[list[float]]:
        """Synchronous wrapper for embed."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.embed(texts))


class OllamaNomicEmbeddingProvider(EmbeddingProvider):
    """Ollama-backed embedding provider using nomic-embed-text.

    Communicates exclusively with the local Ollama instance.
    """

    provider_name = "ollama"
    model_name = "nomic-embed-text"
    embedding_dimension = 768  # nomic-embed-text produces 768-dim vectors

    def __init__(self, settings: Settings) -> None:
        """Initialize the provider with settings.

        Args:
            settings: Application settings containing Ollama configuration.
        """
        self._settings = settings
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.embedding_model or "nomic-embed-text"
        # Increase timeout for large batches - default 5 minutes
        self._timeout = httpx.Timeout(300.0, connect=30.0, read=300.0, write=30.0)
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)

    async def __aenter__(self) -> OllamaNomicEmbeddingProvider:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._client.aclose()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using Ollama's /api/embeddings endpoint.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors.

        Raises:
            EmbeddingProviderError: If embedding generation fails.
        """
        if not texts:
            return []

        embeddings = []
        max_retries = 2
        base_delay = 2.0

        for i, text in enumerate(texts):
            # Skip texts that are too long (exceed model context)
            estimated_tokens = len(text) // 4
            if estimated_tokens > 8000:  # nomic-embed-text context is ~8192
                logger.warning(
                    "Skipping text index %s: estimated %s tokens exceeds model context (8192)",
                    i,
                    estimated_tokens,
                )
                # Use a zero vector as placeholder
                embeddings.append([0.0] * self.embedding_dimension)
                continue

            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    payload = {
                        "model": self._model,
                        "prompt": text,
                    }
                    response = await self._client.post("/api/embeddings", json=payload)
                    response.raise_for_status()
                    data = response.json()

                    embedding = data.get("embedding")
                    if embedding is None:
                        raise EmbeddingProviderError(f"No embedding in response for text index {i}")

                    if not isinstance(embedding, list) or not all(
                        isinstance(x, (int, float)) for x in embedding
                    ):
                        raise EmbeddingProviderError(f"Invalid embedding format for text index {i}")

                    if len(embedding) != self.embedding_dimension:
                        logger.warning(
                            "Embedding dimension mismatch: expected %s, got %s",
                            self.embedding_dimension,
                            len(embedding),
                        )

                    embeddings.append([float(x) for x in embedding])
                    break  # Success, exit retry loop

                except httpx.ConnectError as e:
                    last_error = EmbeddingProviderError(
                        f"Cannot connect to Ollama at {self._base_url}: {e}"
                    )
                except httpx.TimeoutException as e:
                    last_error = EmbeddingProviderError(
                        f"Embedding request timed out for text index {i}: {e}"
                    )
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        raise EmbeddingProviderError(
                            f"Model '{self._model}' not found in Ollama. "
                            f"Run: ollama pull {self._model}"
                        ) from e
                    if e.response.status_code == 500:
                        # Check if it's a context length error
                        error_text = e.response.text.lower()
                        if "context length" in error_text or "input length" in error_text:
                            logger.warning(
                                "Text index %s exceeds model context length, skipping", i
                            )
                            embeddings.append([0.0] * self.embedding_dimension)
                            break  # Don't retry, just skip
                    last_error = EmbeddingProviderError(
                        f"Ollama HTTP error {e.response.status_code}: {e.response.text}"
                    )
                except Exception as e:
                    last_error = EmbeddingProviderError(
                        f"Unexpected error embedding text index {i}: {e}"
                    )

                # Retry with exponential backoff
                if attempt < max_retries:
                    delay = base_delay * (2**attempt)
                    logger.warning(
                        "Retrying embedding for text index %s (attempt %s/%s) after %ss: %s",
                        i,
                        attempt + 1,
                        max_retries + 1,
                        delay,
                        last_error,
                    )
                    await asyncio.sleep(delay)
                else:
                    # All retries exhausted
                    if last_error:
                        raise last_error
                    else:
                        raise EmbeddingProviderError(
                            f"Failed to embed text index {i} after {max_retries + 1} attempts"
                        )

        logger.info(
            "Generated %s embeddings using %s/%s",
            len(embeddings),
            self.provider_name,
            self._model,
        )
        return embeddings


def create_embedding_provider(settings: Settings) -> EmbeddingProvider:
    """Factory function to create the configured embedding provider.

    Args:
        settings: Application settings.

    Returns:
        An EmbeddingProvider instance.

    Raises:
        ValueError: If the provider is not supported.
    """
    provider = settings.embedding_provider.strip().lower()
    if provider == "ollama":
        return OllamaNomicEmbeddingProvider(settings)

    raise ValueError(f"Unsupported CYBERSRS_EMBEDDING_PROVIDER '{provider}'. Supported: ollama")
