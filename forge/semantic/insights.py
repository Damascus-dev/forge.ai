"""
Semantic insights generator for anomaly detection and pattern extraction.

Analyzes action embeddings to find anomalies and patterns.
"""

import math

from forge.db.postgres import PostgresDB
from forge.semantic.embeddings import EmbeddingEngine


class InsightsGenerator:
    """Generates semantic insights including anomalies and patterns."""

    def __init__(
        self,
        db: PostgresDB,
        embedding_engine: EmbeddingEngine,
    ):
        """Initialize insights generator.

        Args:
            db: PostgreSQL database instance
            embedding_engine: Embedding engine for analysis
        """
        self.db = db
        self.embeddings = embedding_engine

    async def get_insights(self, experiment_id: str) -> dict:
        """Generate semantic insights for an experiment.

        Args:
            experiment_id: ID of experiment

        Returns:
            Dictionary with themes, anomalies, and patterns
        """
        # Get all actions for the experiment
        session = await self.db.get_session()
        try:
            import sqlalchemy as sa
            query = sa.text("""
                SELECT id, action_type, content, embedding
                FROM agent_actions
                WHERE experiment_id = :exp_id
                ORDER BY created_at
            """)
            result = await session.execute(
                query,
                {"exp_id": experiment_id}
            )
            actions = [
                {
                    "id": row[0],
                    "action_type": row[1],
                    "content": row[2],
                    "embedding": row[3],
                }
                for row in result.fetchall()
            ]
        finally:
            await session.close()

        if not actions:
            return {
                "experiment_id": experiment_id,
                "themes": [],
                "anomalies": [],
                "patterns": [],
                "total_actions": 0,
            }

        # Extract themes (action types)
        themes = self._extract_themes(actions)

        # Detect anomalies (statistical outliers)
        anomalies = self._detect_anomalies(actions)

        # Extract patterns
        patterns = self._extract_patterns(actions)

        return {
            "experiment_id": experiment_id,
            "themes": themes,
            "anomalies": anomalies,
            "patterns": patterns,
            "total_actions": len(actions),
        }

    def _extract_themes(self, actions: list[dict]) -> list[dict]:
        """Extract dominant themes from actions.

        Args:
            actions: List of action records

        Returns:
            List of themes with counts
        """
        type_counts = {}
        for action in actions:
            atype = action["action_type"]
            type_counts[atype] = type_counts.get(atype, 0) + 1

        # Return sorted by frequency
        themes = [
            {"theme": atype, "count": count}
            for atype, count in sorted(
                type_counts.items(),
                key=lambda x: -x[1]
            )
        ]
        return themes

    def _detect_anomalies(self, actions: list[dict]) -> list[dict]:
        """Detect anomalous actions using statistical methods.

        Uses isolation forest-like approach: actions with unusual
        content length or infrequent types are flagged.

        Args:
            actions: List of action records

        Returns:
            List of anomalous actions
        """
        anomalies = []

        if len(actions) < 5:
            return anomalies

        # Calculate content length statistics
        lengths = [len(a["content"]) for a in actions]
        mean_len = sum(lengths) / len(lengths)
        variance = sum((x - mean_len) ** 2 for x in lengths) / len(lengths)
        std_dev = math.sqrt(variance) if variance > 0 else 1

        # Get action type frequencies
        type_counts = {}
        for action in actions:
            atype = action["action_type"]
            type_counts[atype] = type_counts.get(atype, 0) + 1

        rare_threshold = len(actions) * 0.1  # Bottom 10% is rare

        # Flag anomalies
        for i, action in enumerate(actions):
            score = 0

            # Content length anomaly (>2 std devs)
            if abs(lengths[i] - mean_len) > 2 * std_dev:
                score += 1

            # Rare action type
            if type_counts.get(action["action_type"], 0) <= rare_threshold:
                score += 1

            if score >= 1:
                anomalies.append({
                    "id": action["id"],
                    "action_type": action["action_type"],
                    "content": action["content"][:50] + "..." if len(action["content"]) > 50 else action["content"],
                    "anomaly_score": score / 2.0,
                })

        return anomalies[:10]  # Return top 10 anomalies

    def _extract_patterns(self, actions: list[dict]) -> list[dict]:
        """Extract recurring patterns from actions.

        Args:
            actions: List of action records

        Returns:
            List of patterns
        """
        patterns = []

        if len(actions) < 2:
            return patterns

        # Pattern 1: Recurring action sequences
        sequence_map = {}
        for i in range(len(actions) - 1):
            seq = (actions[i]["action_type"], actions[i + 1]["action_type"])
            sequence_map[seq] = sequence_map.get(seq, 0) + 1

        # Get sequences that occur 2+ times
        recurring_seqs = [
            {
                "pattern": f"{s[0]} -> {s[1]}",
                "frequency": count
            }
            for s, count in sequence_map.items()
            if count >= 2
        ]

        patterns.extend(sorted(
            recurring_seqs,
            key=lambda x: -x["frequency"]
        )[:5])

        # Pattern 2: Dominant action type
        type_counts = {}
        for action in actions:
            atype = action["action_type"]
            type_counts[atype] = type_counts.get(atype, 0) + 1

        if type_counts:
            dominant = max(type_counts.items(), key=lambda x: x[1])
            patterns.append({
                "pattern": f"Dominant action type: {dominant[0]}",
                "frequency": dominant[1]
            })

        return patterns
