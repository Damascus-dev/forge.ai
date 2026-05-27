"""
Embedding engine for semantic logging.

Generates embeddings via local Ollama instance with a lightweight
bag-of-words fallback when Ollama is unavailable.
"""

import logging
import re
from collections import Counter

import httpx

logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"\w+")


def _bag_of_words(text: str, dim: int = 768) -> list[float]:
    """Generate a simple term-frequency vector as a fallback embedding.

    Uses word-level TF hashed into a fixed-dimension vector via
    modular hashing. Provides basic semantic similarity based on
    word overlap — less accurate than Ollama but dependency-free.
    """
    words = _WORD_RE.findall(text.lower())
    if not words:
        return [0.0] * dim
    counts = Counter(words)
    max_count = max(counts.values())
    vec = [0.0] * dim
    for word, count in counts.items():
        h = hash(word) % dim
        vec[h] = count / max_count
    return vec


class EmbeddingEngine:
    """Generates embeddings using Ollama (nomic-embed-text) with fallback."""

    def __init__(
        self,
        model: str = "nomic-embed-text:latest",
        ollama_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.ollama_url = ollama_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self._available = False
        self._using_fallback = False

    async def health_check(self) -> bool:
        try:
            response = await self.client.get(f"{self.ollama_url}/api/tags", timeout=5.0)
            self._available = response.status_code == 200
            if self._available:
                self._using_fallback = False
            return self._available
        except Exception:
            self._available = False
            self._using_fallback = True
            return False

    @property
    def available(self) -> bool:
        return self._available

    @property
    def using_fallback(self) -> bool:
        return self._using_fallback

    async def embed(self, text: str) -> list[float]:
        if not self._available and not self._using_fallback:
            ok = await self.health_check()
            if not ok:
                logger.info("Embedding: using bag-of-words fallback (Ollama unavailable)")
                return _bag_of_words(text)
        if self._using_fallback:
            return _bag_of_words(text)
        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except httpx.HTTPError as e:
            self._available = False
            self._using_fallback = True
            logger.warning("Embedding: Ollama failed, falling back: %s", e)
            return _bag_of_words(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(t) for t in texts]

    async def close(self):
        await self.client.aclose()
