from fastapi import APIRouter

from forge.orchestrator.manager import orchestrator

router = APIRouter()


@router.get("/{experiment_id}")
async def get_events(experiment_id: str, limit: int = 100):
    return await orchestrator.get_events(experiment_id, limit)
