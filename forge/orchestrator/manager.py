import uuid
from datetime import datetime, timezone

from forge.agents.loop import AgentRuntime
from forge.chaos.engine import ChaosEngine
from forge.events.store import EventStore, create_event_store
from forge.experiments.models import (
    AgentConfig,
    AgentLog,
    Experiment,
    ExperimentEvent,
    ExperimentStatus,
    FaultConfig,
    Node,
)
from forge.replay.engine import ReplayEngine
from forge.runtime.node import NodeRuntime
from forge.telemetry.metrics import MetricsCollector


class Orchestrator:
    def __init__(self, event_store: EventStore | None = None):
        self.experiments: dict[str, Experiment] = {}
        self.nodes: dict[str, dict[str, Node]] = {}
        self.node_runtime = NodeRuntime()
        self.replay_engine = ReplayEngine()
        self.metrics = MetricsCollector()
        self._event_store = event_store
        self.chaos_engine = ChaosEngine(node_runtime=self.node_runtime)
        self.agents: dict[str, AgentRuntime] = {}

    async def init_event_store(self) -> None:
        if self._event_store is None:
            self._event_store = await create_event_store()

    async def create_experiment(self, experiment: Experiment) -> Experiment:
        experiment.id = uuid.uuid4().hex[:12]
        experiment.status = ExperimentStatus.pending
        experiment.created_at = datetime.now(timezone.utc)
        self.experiments[experiment.id] = experiment
        self.nodes[experiment.id] = {}
        self.metrics.record_experiment_created()
        await self._log_event(
            experiment.id, "experiment.created", "system", {"name": experiment.name}
        )
        return experiment

    def list_experiments(self) -> list[Experiment]:
        return list(self.experiments.values())

    def get_experiment(self, experiment_id: str) -> Experiment | None:
        return self.experiments.get(experiment_id)

    async def start_experiment(self, experiment_id: str) -> dict:
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return {"error": "not found"}
        experiment.status = ExperimentStatus.running
        nodes = await self.node_runtime.launch_nodes(experiment)
        for node in nodes:
            self.nodes[experiment_id][node.id] = node
        self.metrics.set_nodes_active(len(nodes))
        await self._log_event(experiment_id, "experiment.started", "system", {})
        return {"status": "started", "experiment_id": experiment_id}

    async def terminate_experiment(self, experiment_id: str) -> dict:
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return {"error": "not found"}
        experiment.status = ExperimentStatus.completed
        await self.node_runtime.teardown_nodes(experiment_id)
        await self._log_event(experiment_id, "experiment.terminated", "system", {})
        return {"status": "terminated", "experiment_id": experiment_id}

    async def inject_fault(
        self, experiment_id: str, target_node: str, fault_type: str, params: dict
    ) -> dict:
        config = FaultConfig(
            experiment_id=experiment_id,
            target_node=target_node,
            fault_type=fault_type,
            params=params,
        )
        result = await self.chaos_engine.inject_fault(config)
        await self._log_event(experiment_id, f"fault.{fault_type}", target_node, params)
        return result

    def list_nodes(self, experiment_id: str) -> list:
        nodes = self.nodes.get(experiment_id, {})
        return list(nodes.values())

    async def get_events(self, experiment_id: str, limit: int = 100) -> list:
        store = await self._get_event_store()
        events = await store.get_events(experiment_id, limit)
        return [
            {
                "id": e.id,
                "experiment_id": e.experiment_id,
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type,
                "source": e.source,
                "data": e.data,
            }
            for e in events
        ]

    async def replay_experiment(self, experiment_id: str) -> dict | None:
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return None
        store = await self._get_event_store()
        events = await store.get_events(experiment_id, limit=1000)
        return await self.replay_engine.replay(experiment, events)

    async def get_timeline(self, experiment_id: str) -> list | None:
        store = await self._get_event_store()
        events = await store.get_timeline(experiment_id)
        if not events:
            return None
        return [
            {
                "timestamp": e.timestamp.isoformat(),
                "type": e.event_type,
                "source": e.source,
                "data": e.data,
            }
            for e in events
        ]

    async def start_agent(self, experiment_id: str, config: AgentConfig) -> dict:
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return {"error": "experiment not found"}
        agent_id = f"agent-{uuid.uuid4().hex[:8]}"
        agent = AgentRuntime(
            agent_id=agent_id,
            model=config.model,
            system_prompt=config.system_prompt or "",
            node_runtime=self.node_runtime,
        )
        self.agents[agent_id] = agent
        await self._log_event(experiment_id, "agent.started", agent_id, {"model": config.model})
        return {"agent_id": agent_id, "status": "started"}

    async def run_agent_step(self, experiment_id: str, agent_id: str) -> dict:
        experiment = self.experiments.get(experiment_id)
        agent = self.agents.get(agent_id)
        if not experiment:
            return {"error": "experiment not found"}
        if not agent:
            return {"error": "agent not found"}
        result = await agent.run_step(experiment)
        await self._log_event(experiment_id, "agent.step", agent_id, {"step": result["step"]})
        return result

    def get_agent_logs(self, experiment_id: str, agent_id: str) -> list[AgentLog]:
        agent = self.agents.get(agent_id)
        if not agent:
            return []
        return agent.logs

    async def _get_event_store(self) -> EventStore:
        if self._event_store is None:
            self._event_store = await create_event_store()
        return self._event_store

    async def _log_event(self, experiment_id: str, event_type: str, source: str, data: dict):
        event = ExperimentEvent(
            experiment_id=experiment_id,
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            source=source,
            data=data,
        )
        store = await self._get_event_store()
        await store.append_event(experiment_id, event)
        self.metrics.record_event(event)


orchestrator = Orchestrator()
