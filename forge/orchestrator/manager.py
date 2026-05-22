import uuid
from datetime import datetime, timezone

from forge.chaos.engine import ChaosEngine
from forge.experiments.models import (
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
    def __init__(self):
        self.experiments: dict[str, Experiment] = {}
        self.nodes: dict[str, dict[str, Node]] = {}
        self.events: dict[str, list[ExperimentEvent]] = {}
        self.node_runtime = NodeRuntime()
        self.chaos_engine = ChaosEngine()
        self.replay_engine = ReplayEngine()
        self.metrics = MetricsCollector()

    async def create_experiment(self, experiment: Experiment) -> Experiment:
        experiment.id = uuid.uuid4().hex[:12]
        experiment.status = ExperimentStatus.pending
        experiment.created_at = datetime.now(timezone.utc)
        self.experiments[experiment.id] = experiment
        self.nodes[experiment.id] = {}
        self.events[experiment.id] = []
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
        await self.node_runtime.launch_nodes(experiment)
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

    def get_events(self, experiment_id: str, limit: int = 100) -> list:
        events = self.events.get(experiment_id, [])
        return events[-limit:]

    async def replay_experiment(self, experiment_id: str) -> dict | None:
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return None
        events = self.events.get(experiment_id, [])
        return await self.replay_engine.replay(experiment, events)

    def get_timeline(self, experiment_id: str) -> list | None:
        if experiment_id not in self.events:
            return None
        return [
            {
                "timestamp": e.timestamp.isoformat(),
                "type": e.event_type,
                "source": e.source,
                "data": e.data,
            }
            for e in self.events[experiment_id]
        ]

    async def _log_event(self, experiment_id: str, event_type: str, source: str, data: dict):
        event = ExperimentEvent(
            experiment_id=experiment_id,
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            source=source,
            data=data,
        )
        if experiment_id in self.events:
            self.events[experiment_id].append(event)
        self.metrics.record_event(event)


orchestrator = Orchestrator()
