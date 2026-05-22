import json
from typing import Callable


class AgentRuntime:
    def __init__(self, agent_id: str, model: str = "ollama/qwen2.5:7b"):
        self.agent_id = agent_id
        self.model = model
        self.tools: dict[str, Callable] = {}
        self.event_log: list[dict] = []

    def register_tool(self, name: str, fn: Callable):
        self.tools[name] = fn

    async def observe(self, context: dict) -> dict:
        return {"state": "observed", "context": context}

    async def reason(self, observation: dict) -> str:
        return f"analyzed: {json.dumps(observation)[:100]}"

    async def act(self, decision: str) -> dict:
        return {"action": "executed", "decision": decision}

    def log(self, event: dict):
        self.event_log.append(event)

    async def run_loop(self, context: dict):
        obs = await self.observe(context)
        decision = await self.reason(obs)
        result = await self.act(decision)
        self.log({"observation": obs, "decision": decision, "result": result})
        return result
