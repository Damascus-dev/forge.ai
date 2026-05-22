from fastapi import APIRouter, HTTPException

from forge.experiments.models import Experiment
from forge.orchestrator.manager import orchestrator

router = APIRouter()


@router.post("/", response_model=Experiment)
async def create_experiment(experiment: Experiment):
    return await orchestrator.create_experiment(experiment)


@router.get("/", response_model=list[Experiment])
async def list_experiments():
    return orchestrator.list_experiments()


@router.get("/{experiment_id}", response_model=Experiment)
async def get_experiment(experiment_id: str):
    exp = orchestrator.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp


@router.post("/{experiment_id}/start")
async def start_experiment(experiment_id: str):
    return await orchestrator.start_experiment(experiment_id)


@router.post("/{experiment_id}/terminate")
async def terminate_experiment(experiment_id: str):
    return await orchestrator.terminate_experiment(experiment_id)
