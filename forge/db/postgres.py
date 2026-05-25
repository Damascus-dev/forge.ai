"""
PostgreSQL database operations for Forge.

Handles async connections, migrations, and queries.
"""

from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


class PostgresDB:
    """PostgreSQL database manager."""

    def __init__(self, database_url: str):
        """Initialize database connection.

        Args:
            database_url: Async SQLAlchemy connection string
                         (postgresql+asyncpg://user:pass@host:port/db)
        """
        self.database_url = database_url
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def get_session(self) -> AsyncSession:
        """Get new database session.

        Returns:
            AsyncSession for queries
        """
        return self.async_session()

    async def close(self):
        """Close all connections."""
        await self.engine.dispose()

    async def health_check(self) -> bool:
        """Check database connectivity.

        Returns:
            True if database is accessible
        """
        try:
            session = await self.get_session()
            await session.execute(sa.text("SELECT 1"))
            await session.close()
            return True
        except Exception:
            return False

    async def insert_action(
        self,
        experiment_id: str,
        agent_id: str,
        action_type: str,
        content: str,
        embedding: list[float],
    ) -> int:
        """Insert agent action with embedding."""
        session = await self.get_session()
        try:
            # Convert embedding list to pgvector string format
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            
            query = sa.text("""
                INSERT INTO agent_actions (experiment_id, agent_id, action_type, content, embedding)
                VALUES (:exp_id, :agent_id, :action_type, :content, CAST(:embedding AS vector))
                RETURNING id
            """)
            result = await session.execute(
                query,
                {
                    "exp_id": experiment_id,
                    "agent_id": agent_id,
                    "action_type": action_type,
                    "content": content,
                    "embedding": embedding_str,
                }
            )
            row_id = result.scalar()
            await session.commit()
            return row_id
        finally:
            await session.close()

    async def semantic_search(
        self,
        experiment_id: str,
        query_embedding: list[float],
        limit: int = 10,
    ) -> list[dict]:
        """Search similar actions by embedding."""
        session = await self.get_session()
        try:
            # Convert embedding list to pgvector string format
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
            
            query = sa.text("""
                SELECT id, experiment_id, agent_id, action_type, content, created_at,
                       1 - (embedding <=> CAST(:query_embedding AS vector)) as similarity
                FROM agent_actions
                WHERE experiment_id = :exp_id
                ORDER BY similarity DESC
                LIMIT :limit
            """)
            result = await session.execute(
                query,
                {
                    "query_embedding": embedding_str,
                    "exp_id": experiment_id,
                    "limit": limit,
                }
            )
            rows = result.fetchall()
            return [
                {
                    "id": row[0],
                    "experiment_id": row[1],
                    "agent_id": row[2],
                    "action_type": row[3],
                    "content": row[4],
                    "created_at": row[5],
                    "similarity": float(row[6]),
                }
                for row in rows
            ]
        finally:
            await session.close()
