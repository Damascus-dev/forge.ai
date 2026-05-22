from fastapi import APIRouter

from forge.orchestrator.manager import orchestrator

router = APIRouter()


@router.post("/{experiment_id}/inject")
async def inject_fault(experiment_id: str, fault_type: str, target_node: str, params: dict = {}):
    return await orchestrator.inject_fault(experiment_id, target_node, fault_type, params)


@router.get("/{experiment_id}")
async def list_nodes(experiment_id: str):
    return orchestrator.list_nodes(experiment_id)
