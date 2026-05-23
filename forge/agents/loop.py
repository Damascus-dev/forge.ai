import json

from litellm import acompletion

from forge.experiments.models import AgentLog, Experiment
from forge.runtime.node import NodeRuntime
from forge.tools.base import AgentTools

DEFAULT_SYSTEM_PROMPT = (
    "You are an AI agent operating in a distributed infrastructure sandbox. "
    "You have access to nodes. You can run shell commands, read files, and restart services. "
    "Examine the environment and take appropriate actions based on your task."
)


class AgentRuntime:
    def __init__(
        self,
        agent_id: str,
        model: str = "ollama/qwen2.5:0.5b",
        system_prompt: str = "",
        node_runtime: NodeRuntime | None = None,
    ):
        self.agent_id = agent_id
        self.model = model
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.tools = AgentTools(node_runtime=node_runtime)
        self.logs: list[AgentLog] = []
        self._step = 0

    async def observe(self, experiment: Experiment) -> dict:
        return {
            "experiment_id": experiment.id,
            "experiment_name": experiment.name,
            "node_count": experiment.node_count,
            "status": experiment.status.value,
            "config": experiment.config,
        }

    async def reason(self, observation: dict, tool_defs: list[dict]) -> str:
        try:
            response = await acompletion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": json.dumps(observation, indent=2)},
                ],
                tools=tool_defs,
                tool_choice="auto",
                keep_alive=0,
            )
            message = response.choices[0].message

            if message.tool_calls:
                return json.dumps([
                    {"name": tc.function.name, "arguments": tc.function.arguments}
                    for tc in message.tool_calls
                ])

            return message.content or "no response"

        except Exception as e:
            return f"error calling LLM: {e}"

    async def act(self, decision: str) -> dict:
        try:
            calls = json.loads(decision)
        except (json.JSONDecodeError, TypeError):
            return {"action": "text", "content": decision}

        results = []
        for call in calls:
            name = call.get("name", "")
            args = json.loads(call.get("arguments", "{}"))

            if name == "exec_command":
                result = await self.tools.exec_command(
                    args.get("node", ""), args.get("command", "")
                )
            elif name == "read_file":
                result = await self.tools.read_file(args.get("path", ""))
            elif name == "restart_service":
                result = await self.tools.restart_service(
                    args.get("node", ""), args.get("service", "")
                )
            else:
                result = {"error": f"unknown tool: {name}"}

            results.append({"tool": name, "args": args, "result": result})

        return {"action": "tool_calls", "results": results}

    def log(self, observation: dict, decision: str, result: dict):
        self._step += 1
        entry = AgentLog(
            experiment_id=observation.get("experiment_id", ""),
            agent_id=self.agent_id,
            step=self._step,
            observation=observation,
            decision=decision,
            action=result.get("action", ""),
            result=result,
        )
        self.logs.append(entry)

    async def run_step(self, experiment: Experiment) -> dict:
        obs = await self.observe(experiment)
        tool_defs = self.tools.get_tool_definitions()
        decision = await self.reason(obs, tool_defs)
        result = await self.act(decision)
        self.log(obs, decision, result)
        return {
            "step": self._step,
            "observation": obs,
            "decision": decision,
            "result": result,
        }
