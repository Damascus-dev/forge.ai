"""
Semantic logging system for Forge.

Handles embedding generation, semantic search, and weekly summaries.
"""

from .embeddings import EmbeddingEngine
from .processor import SemanticProcessor
from .scheduler import setup_scheduler

__all__ = ["EmbeddingEngine", "SemanticProcessor", "setup_scheduler"]
