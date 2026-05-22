from fastapi import APIRouter, HTTPException

from forge.orchestrator.manager import orchestrator

router = APIRouter()


@router.post("/{experiment_id}/start")
async def replay_experiment(experiment_id: str):
    result = await orchestrator.replay_experiment(experiment_id)
    if not result:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return result


@router.get("/{experiment_id}/timeline")
async def get_timeline(experiment_id: str):
    timeline = orchestrator.get_timeline(experiment_id)
    if timeline is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"experiment_id": experiment_id, "timeline": timeline}
