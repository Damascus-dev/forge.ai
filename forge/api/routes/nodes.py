from fastapi import APIRouter, Query

from forge.orchestrator.manager import orchestrator

router = APIRouter()


@router.get(
    "/{experiment_id}",
    summary="List experiment nodes",
    description="Returns all container nodes for a given experiment, including their status, type, and container ID.",
)
async def list_nodes(experiment_id: str):
    nodes = await orchestrator.list_nodes(experiment_id)
    return nodes


@router.post(
    "/{experiment_id}/inject",
    summary="Inject fault into node",
    description="Injects a fault (latency, packet_loss, crash, disconnect) into a target node with optional parameters.",
)
async def inject_fault(
    experiment_id: str,
    fault_type: str = Query(..., description="Type of fault: latency, packet_loss, crash, disconnect"),
    target_node: str = Query(..., description="Target node ID"),
    params: str = "{}",
):
    import json
    try:
        parsed = json.loads(params)
    except json.JSONDecodeError:
        parsed = {}
    return await orchestrator.inject_fault(experiment_id, target_node, fault_type, parsed)
