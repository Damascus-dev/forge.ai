from fastapi import APIRouter, Query

from forge.orchestrator.manager import orchestrator

router = APIRouter()


@router.get(
    "/{experiment_id}",
    summary="Get experiment events",
    description="Returns events for an experiment, ordered by time (newest first). Supports pagination via limit parameter.",
)
async def get_events(
    experiment_id: str,
    limit: int = Query(100, description="Maximum number of events to return", ge=1, le=10000),
    event_type: str | None = Query(None, description="Filter by event type (e.g. experiment.created, fault.latency)"),
):
    events = await orchestrator.get_events(experiment_id, limit)
    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]
    return events
