"""
Weekly summary generation from semantic action logs.

Generates summaries by clustering actions and extracting themes.
"""

from datetime import datetime, timedelta
from typing import Optional
import json

from forge.db.postgres import PostgresDB
from forge.semantic.embeddings import EmbeddingEngine
from forge.semantic.processor import SemanticProcessor


class SummaryGenerator:
    """Generates weekly summaries from agent actions."""

    def __init__(
        self,
        db: PostgresDB,
        embedding_engine: EmbeddingEngine,
    ):
        """Initialize summary generator.

        Args:
            db: PostgreSQL database instance
            embedding_engine: Embedding engine for clustering
        """
        self.db = db
        self.embeddings = embedding_engine

    def _get_week_boundaries(self, date: Optional[datetime] = None) -> tuple[str, str]:
        """Get week start and end dates (Monday-Sunday).
        
        Args:
            date: Reference date (defaults to today)
            
        Returns:
            (week_start, week_end) as ISO date strings
        """
        if not date:
            date = datetime.now()
        
        # Monday = 0, Sunday = 6
        days_since_monday = date.weekday()
        week_start = date - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=6)
        
        return week_start.date().isoformat(), week_end.date().isoformat()

    async def generate_summary(
        self,
        experiment_id: str,
        week_start: Optional[str] = None,
    ) -> Optional[dict]:
        """Generate weekly summary for experiment.

        Args:
            experiment_id: ID of experiment
            week_start: Start date (ISO format, defaults to this week)

        Returns:
            Summary record or None if no actions
        """
        # Determine week boundaries
        if not week_start:
            week_start, week_end = self._get_week_boundaries()
        else:
            # Parse provided week_start and get the end
            start_date = datetime.fromisoformat(week_start)
            _, week_end = self._get_week_boundaries(start_date)
            week_start = start_date.date().isoformat()

        # Get actions for this week
        session = await self.db.get_session()
        try:
            import sqlalchemy as sa
            from datetime import date
            
            # Convert ISO strings to date objects for PostgreSQL
            week_start_date = datetime.fromisoformat(week_start).date()
            week_end_date = datetime.fromisoformat(week_end).date()
            
            query = sa.text("""
                SELECT id, content, action_type, agent_id
                FROM agent_actions
                WHERE experiment_id = :exp_id
                  AND created_at::date >= :week_start
                  AND created_at::date <= :week_end
                ORDER BY created_at
            """)
            result = await session.execute(
                query,
                {
                    "exp_id": experiment_id,
                    "week_start": week_start_date,
                    "week_end": week_end_date,
                }
            )
            actions = [
                {
                    "id": row[0],
                    "content": row[1],
                    "action_type": row[2],
                    "agent_id": row[3],
                }
                for row in result.fetchall()
            ]
        finally:
            await session.close()

        if not actions:
            return None

        # Extract themes from action types
        themes = list(set(a["action_type"] for a in actions))

        # Generate summary text from action contents
        summary_text = self._generate_summary_text(actions)

        # Create metrics
        key_metrics = {
            "total_actions": len(actions),
            "by_type": self._count_by_type(actions),
            "by_agent": self._count_by_agent(actions),
        }

        # Store in database
        summary_id = await self.db.insert_weekly_summary(
            experiment_id=experiment_id,
            week_start=week_start,
            week_end=week_end,
            summary_text=summary_text,
            themes=themes,
            key_metrics=json.dumps(key_metrics),
            total_actions=len(actions),
        )

        return {
            "id": summary_id,
            "experiment_id": experiment_id,
            "week_start": week_start,
            "week_end": week_end,
            "summary_text": summary_text,
            "themes": themes,
            "key_metrics": key_metrics,
            "total_actions": len(actions),
        }

    def _generate_summary_text(self, actions: list[dict]) -> str:
        """Generate human-readable summary from actions.

        Args:
            actions: List of action records

        Returns:
            Summary text
        """
        if not actions:
            return "No actions recorded this week."

        action_types = {}
        for action in actions:
            atype = action["action_type"]
            action_types[atype] = action_types.get(atype, 0) + 1

        type_str = ", ".join(
            f"{count} {atype}" for atype, count in sorted(action_types.items())
        )

        agents = set(a["agent_id"] for a in actions)
        agent_str = ", ".join(sorted(agents)) if agents else "unknown"

        summary = (
            f"Week recorded {len(actions)} total actions across {len(agents)} agent(s). "
            f"Breakdown: {type_str}. "
            f"Primary agents: {agent_str}."
        )
        return summary

    def _count_by_type(self, actions: list[dict]) -> dict:
        """Count actions by type."""
        counts = {}
        for action in actions:
            atype = action["action_type"]
            counts[atype] = counts.get(atype, 0) + 1
        return counts

    def _count_by_agent(self, actions: list[dict]) -> dict:
        """Count actions by agent."""
        counts = {}
        for action in actions:
            agent = action["agent_id"]
            counts[agent] = counts.get(agent, 0) + 1
        return counts

    async def get_summaries(
        self,
        experiment_id: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """Get weekly summaries.

        Args:
            experiment_id: Filter by experiment (optional)
            limit: Max results
            offset: Pagination offset

        Returns:
            (summaries, total_count)
        """
        return await self.db.get_weekly_summaries(
            experiment_id=experiment_id,
            limit=limit,
            offset=offset,
        )
