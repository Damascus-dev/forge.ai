"""
Background job scheduler for semantic logging tasks.

Handles automatic summary generation on a schedule.
"""

import asyncio
import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from forge.db.postgres import PostgresDB
from forge.semantic.embeddings import EmbeddingEngine
from forge.semantic.summary import SummaryGenerator

logger = logging.getLogger(__name__)


class SemanticScheduler:
    """Manages background tasks for semantic logging."""

    def __init__(
        self,
        db: Optional[PostgresDB] = None,
        embedding_engine: Optional[EmbeddingEngine] = None,
    ):
        """Initialize scheduler.

        Args:
            db: PostgreSQL database instance
            embedding_engine: Embedding engine instance
        """
        self.db = db
        self.embedding_engine = embedding_engine
        self.scheduler = BackgroundScheduler()
        self.summary_gen = None

        if db and embedding_engine:
            self.summary_gen = SummaryGenerator(db, embedding_engine)

    def start(self):
        """Start the background scheduler."""
        if not self.scheduler.running:
            # Schedule Friday 18:00 (6 PM) summary generation
            self.scheduler.add_job(
                self._generate_weekly_summaries,
                trigger=CronTrigger(day_of_week="fri", hour=18, minute=0),
                id="weekly_summary_generator",
                name="Weekly Summary Generator",
                replace_existing=True,
            )
            self.scheduler.start()
            logger.info("Semantic scheduler started with Friday 18:00 summary generation")

    def stop(self):
        """Stop the background scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Semantic scheduler stopped")

    def _generate_weekly_summaries(self):
        """Generate summaries for all experiments."""
        if not self.summary_gen:
            logger.warning("Summary generator not initialized, skipping summary generation")
            return

        try:
            # Run async code in event loop
            asyncio.run(self._async_generate_summaries())
        except Exception as e:
            logger.error(f"Error generating weekly summaries: {e}")

    async def _async_generate_summaries(self):
        """Async implementation of summary generation."""
        try:
            # Get all unique experiment IDs with recent actions
            session = await self.db.get_session()
            try:
                from datetime import datetime, timedelta

                import sqlalchemy as sa

                # Get experiments with actions in the past week
                week_ago = datetime.now() - timedelta(days=7)
                query = sa.text("""
                    SELECT DISTINCT experiment_id
                    FROM agent_actions
                    WHERE created_at >= :week_ago
                    ORDER BY experiment_id
                """)
                result = await session.execute(
                    query,
                    {"week_ago": week_ago}
                )
                experiment_ids = [row[0] for row in result.fetchall()]
            finally:
                await session.close()

            # Generate summaries for each experiment
            generated_count = 0
            for exp_id in experiment_ids:
                try:
                    summary = await self.summary_gen.generate_summary(exp_id)
                    if summary:
                        generated_count += 1
                        logger.info(f"Generated summary for experiment: {exp_id}")
                except Exception as e:
                    logger.error(f"Error generating summary for {exp_id}: {e}")

            logger.info(f"Weekly summary generation complete: {generated_count} summaries")
        except Exception as e:
            logger.error(f"Async summary generation error: {e}")

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self.scheduler.running
