from fastapi import APIRouter, HTTPException

from forge.experiments.models import AgentConfig
from forge.orchestrator.manager import orchestrator

router = APIRouter()


@router.post("/{experiment_id}/agent/start")
async def start_agent(experiment_id: str, config: AgentConfig):
    result = await orchestrator.start_agent(experiment_id, config)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/{experiment_id}/agent/{agent_id}/step")
async def agent_step(experiment_id: str, agent_id: str):
    result = await orchestrator.run_agent_step(experiment_id, agent_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/{experiment_id}/agent/{agent_id}/logs")
async def agent_logs(experiment_id: str, agent_id: str):
    logs = orchestrator.get_agent_logs(experiment_id, agent_id)
    if not logs:
        raise HTTPException(status_code=404, detail="Agent not found")
    return logs
