"""
APScheduler setup for periodic tasks.

Handles weekly summary generation and other scheduled work.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler


def setup_scheduler() -> AsyncIOScheduler:
    """Set up APScheduler for periodic tasks.

    Returns:
        AsyncIOScheduler instance configured with jobs

    Jobs scheduled:
    - Weekly summary: Friday 18:00 UTC
    """
    scheduler = AsyncIOScheduler()

    # TODO: Implement in Phase 6
    #  @scheduler.scheduled_job('cron', day_of_week='fri', hour=18, minute=0)
    #  async def weekly_summary_job():
    #      """Auto-generate weekly summary"""
    #      pass

    return scheduler
