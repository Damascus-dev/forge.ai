from fastapi import APIRouter, HTTPException, Query

from forge.experiments.models import Experiment, ExperimentUpdate, ExportFormat
from forge.orchestrator.manager import orchestrator

router = APIRouter()


@router.post(
    "/",
    response_model=Experiment,
    summary="Create a new experiment",
    description="Creates an experiment with the given name, node count, and optional config. Returns the created experiment with assigned ID.",
)
async def create_experiment(experiment: Experiment):
    return await orchestrator.create_experiment(experiment)


@router.get(
    "/",
    response_model=list[Experiment],
    summary="List all experiments",
    description="Returns a list of all experiments. Supports optional status filtering.",
)
async def list_experiments(
    status: str | None = Query(None, description="Filter by experiment status (pending, running, completed, failed)"),
):
    exps = await orchestrator.list_experiments()
    if status:
        exps = [e for e in exps if e.status.value == status]
    return exps


@router.get(
    "/{experiment_id}",
    response_model=Experiment,
    summary="Get experiment details",
    description="Returns the full experiment object by ID, including status, node count, tags, and config.",
)
async def get_experiment(experiment_id: str):
    exp = await orchestrator.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp


@router.patch(
    "/{experiment_id}",
    response_model=Experiment,
    summary="Update experiment",
    description="Updates experiment fields (name, description, config, tags). Only provided fields are modified.",
)
async def update_experiment(experiment_id: str, updates: ExperimentUpdate):
    updates_dict = updates.model_dump(exclude_none=True)
    if not updates_dict:
        raise HTTPException(status_code=400, detail="No fields to update")
    exp = await orchestrator.update_experiment(experiment_id, updates_dict)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp


@router.delete(
    "/{experiment_id}",
    summary="Delete experiment",
    description="Permanently deletes an experiment, its nodes, agent sessions, and events.",
)
async def delete_experiment(experiment_id: str):
    result = await orchestrator.delete_experiment(experiment_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post(
    "/{experiment_id}/start",
    summary="Start experiment",
    description="Launches the experiment: spawns container nodes and transitions status to 'running'.",
)
async def start_experiment(experiment_id: str):
    return await orchestrator.start_experiment(experiment_id)


@router.post(
    "/{experiment_id}/terminate",
    summary="Terminate experiment",
    description="Stops the experiment: tears down all container nodes and transitions status to 'completed'.",
)
async def terminate_experiment(experiment_id: str):
    return await orchestrator.terminate_experiment(experiment_id)


@router.get(
    "/{experiment_id}/metrics",
    summary="Get experiment metrics",
    description="Returns aggregated metrics for an experiment: event counts by type and severity, runtime duration, node count.",
)
async def get_experiment_metrics(experiment_id: str):
    metrics = await orchestrator.get_experiment_metrics(experiment_id)
    if "error" in metrics:
        raise HTTPException(status_code=404, detail=metrics["error"])
    return metrics


@router.get(
    "/{experiment_id}/events/stats",
    summary="Get event statistics",
    description="Returns event statistics broken down by type, source, and severity. Useful for visualizing event distributions.",
)
async def get_event_stats(experiment_id: str):
    return await orchestrator.get_event_stats(experiment_id)


@router.get(
    "/{experiment_id}/export",
    summary="Export experiment data",
    description="Exports all experiment data (experiment, nodes, events) as JSON for backup or analysis.",
)
async def export_experiment(
    experiment_id: str,
    format: ExportFormat = Query(ExportFormat.json, description="Export format (json, csv, markdown)"),
):
    result = await orchestrator.export_experiment(experiment_id, format)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
