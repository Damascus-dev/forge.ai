"""
Embedding engine for semantic logging.

Generates embeddings via local Ollama instance.
"""

import httpx
from typing import Optional


class EmbeddingEngine:
    """Generates embeddings using Ollama (nomic-embed-text)."""

    def __init__(
        self,
        model: str = "nomic-embed-text:latest",
        ollama_url: str = "http://localhost:11434",
    ):
        """Initialize embedding engine.

        Args:
            model: Ollama model name
            ollama_url: Base URL for Ollama API
        """
        self.model = model
        self.ollama_url = ollama_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for single text.

        Args:
            text: Text to embed

        Returns:
            768-dimensional embedding vector

        Raises:
            httpx.HTTPError: If Ollama API fails
        """
        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to generate embedding: {e}") from e

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts (async).

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Note:
            Processes sequentially to avoid overwhelming Ollama.
        """
        embeddings = []
        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)
        return embeddings

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
