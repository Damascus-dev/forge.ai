from fastapi import APIRouter, HTTPException

from forge.orchestrator.manager import orchestrator

router = APIRouter()


@router.post(
    "/{experiment_id}/start",
    summary="Start experiment replay",
    description="Triggers a deterministic replay of the experiment's event timeline.",
)
async def replay_experiment(experiment_id: str):
    result = await orchestrator.replay_experiment(experiment_id)
    if not result:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return result


@router.get(
    "/{experiment_id}/timeline",
    summary="Get event timeline",
    description="Returns the chronological timeline of all events for an experiment, used by the frontend replay system.",
)
async def get_timeline(experiment_id: str):
    timeline = await orchestrator.get_timeline(experiment_id)
    if timeline is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"experiment_id": experiment_id, "timeline": timeline}
