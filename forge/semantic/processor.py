"""
Semantic processor for analyzing agent actions.

Generates embeddings, detects patterns, and creates weekly summaries.
"""

from typing import Optional

from forge.db.postgres import PostgresDB
from forge.semantic.embeddings import EmbeddingEngine


class SemanticProcessor:
    """Processes agent actions and generates semantic insights."""

    def __init__(
        self,
        embedding_engine: EmbeddingEngine,
        db: Optional[PostgresDB] = None,
    ):
        """Initialize processor.

        Args:
            embedding_engine: Embedding engine for generating vectors
            db: PostgreSQL database instance
        """
        self.embeddings = embedding_engine
        self.db = db

    async def process_action(
        self,
        experiment_id: str,
        agent_id: str,
        action_type: str,
        content: str,
    ) -> int:
        """Process single agent action with embedding.

        Args:
            experiment_id: ID of experiment
            agent_id: ID of agent
            action_type: Type of action
            content: Action text

        Returns:
            Row ID in database (or -1 if no db)
        """
        # Generate embedding
        embedding = await self.embeddings.embed(content)

        # Store in postgres if available
        if self.db:
            row_id = await self.db.insert_action(
                experiment_id=experiment_id,
                agent_id=agent_id,
                action_type=action_type,
                content=content,
                embedding=embedding,
            )
            return row_id
        return -1

    async def semantic_search(
        self,
        experiment_id: str,
        query: str,
        limit: int = 10,
    ) -> list[dict]:
        """Search agent actions via semantic similarity.

        Args:
            experiment_id: ID of experiment
            query: Natural language query
            limit: Max results to return

        Returns:
            List of similar actions with similarity scores
        """
        if not self.db:
            return []

        # Generate query embedding
        query_embedding = await self.embeddings.embed(query)

        # Search in postgres
        return await self.db.semantic_search(
            experiment_id=experiment_id,
            query_embedding=query_embedding,
            limit=limit,
        )
        # TODO: Implement in Phase 6
        #  1. Embed the query
        #  2. Search pgvector for similar embeddings
        #  3. Return ranked results
        return []
