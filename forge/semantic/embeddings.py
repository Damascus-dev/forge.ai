"""
Embedding engine for semantic logging.

Generates embeddings via local Ollama instance with graceful fallback.
"""

import logging

import httpx

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """Generates embeddings using Ollama (nomic-embed-text)."""

    def __init__(
        self,
        model: str = "nomic-embed-text:latest",
        ollama_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.ollama_url = ollama_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self._available = False

    async def health_check(self) -> bool:
        """Check if Ollama is reachable.

        Returns:
            True if Ollama responds, False otherwise.
        """
        try:
            response = await self.client.get(f"{self.ollama_url}/api/tags", timeout=5.0)
            self._available = response.status_code == 200
            return self._available
        except Exception:
            self._available = False
            return False

    @property
    def available(self) -> bool:
        return self._available

    async def embed(self, text: str) -> list[float]:
        if not self._available:
            ok = await self.health_check()
            if not ok:
                raise RuntimeError("Ollama embedding service is not available")
        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except httpx.HTTPError as e:
            self._available = False
            raise RuntimeError(f"Failed to generate embedding: {e}") from e

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)
        return embeddings

    async def close(self):
        await self.client.aclose()
