#!/usr/bin/env python3
"""
Weekly summary generator for Forge.

Runs every Friday 18:00 UTC via APScheduler (see semantic/scheduler.py).
Can also be run manually via CLI.

Usage:
    python forge/scripts/weekly_summary.py [--week-start YYYY-MM-DD]
"""

import argparse
import asyncio
import logging
from datetime import datetime, timezone

from forge.configs.settings import settings
from forge.db.postgres import PostgresDB
from forge.semantic.embeddings import EmbeddingEngine
from forge.semantic.summary import SummaryGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_weekly_summary(week_start: datetime | None = None) -> str:
    if not settings.database_url:
        logger.error("No database_url configured. Set FORGE_DATABASE_URL.")
        return ""

    db = PostgresDB(settings.database_url)
    engine = EmbeddingEngine()
    gen = SummaryGenerator(db, engine)

    try:
        summaries = []
        experiments = await _get_experiments(db)
        for exp_id in experiments:
            summary = await gen.generate_summary(exp_id, reference_date=week_start)
            if summary:
                summaries.append(summary)
                logger.info("Generated summary for %s", exp_id)

        path = f"logs/week-summary-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
        with open(path, "w") as f:
            f.write(f"# Weekly Summary — {datetime.now(timezone.utc).date()}\n\n")
            for s in summaries:
                f.write(f"## Experiment {s['experiment_id']}\n")
                f.write(f"{s['summary_text']}\n\n")
        logger.info("Summary written to %s", path)
        return path
    finally:
        await db.close()


async def _get_experiments(db) -> list[str]:
    import sqlalchemy as sa
    session = await db.get_session()
    try:
        result = await session.execute(sa.text("SELECT DISTINCT experiment_id FROM agent_actions"))
        return [row[0] for row in result.fetchall()]
    finally:
        await session.close()


def main():
    parser = argparse.ArgumentParser(description="Generate weekly Forge summary")
    parser.add_argument("--week-start", type=str, default=None, help="Week start date (YYYY-MM-DD)")
    args = parser.parse_args()

    week_start = datetime.fromisoformat(args.week_start) if args.week_start else None
    path = asyncio.run(generate_weekly_summary(week_start))
    if path:
        print(f"✓ Weekly summary saved: {path}")


if __name__ == "__main__":
    main()
