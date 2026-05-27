import uuid
from datetime import datetime, timezone

from forge.agents.loop import AgentRuntime
from forge.chaos.engine import ChaosEngine
from forge.events.store import EventStore, InMemoryEventStore, create_event_store
from forge.experiments.models import (
    AgentConfig,
    AgentLog,
    EventSeverity,
    Experiment,
    ExperimentEvent,
    ExperimentStatus,
    ExportFormat,
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

        # Broadcast chaos update to WebSocket clients
        try:
            from forge.api.routes.ws import manager as ws_manager
            await ws_manager.broadcast(experiment_id, {
                "type": "chaos",
                "payload": {
                    "nodeId": target_node,
                    "type": fault_type,
                    "params": params,
                    "startTime": datetime.now(timezone.utc).isoformat(),
                },
            })
        except Exception:
            pass

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

        # Broadcast agent state update to WebSocket clients
        try:
            from forge.api.routes.ws import manager as ws_manager
            logs = agent.logs
            latest = logs[-1] if logs else None
            if latest:
                await ws_manager.broadcast(experiment_id, {
                    "type": "agent_state",
                    "payload": {
                        "state": "acting",
                        "step": latest.step,
                        "observation": latest.observation,
                        "decision": latest.decision,
                        "action": latest.action,
                    },
                })
        except Exception:
            pass

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

    async def delete_experiment(self, experiment_id: str) -> dict:
        experiment = self.experiments.pop(experiment_id, None)
        if not experiment:
            return {"error": "not found"}
        self.nodes.pop(experiment_id, None)
        for aid in list(self.agents.keys()):
            self.agents.pop(aid, None)
        self.metrics.record_experiment_deleted()
        return {"status": "deleted", "experiment_id": experiment_id}

    async def update_experiment(self, experiment_id: str, updates: dict) -> Experiment | None:
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return None
        for key, value in updates.items():
            if value is not None and hasattr(experiment, key):
                setattr(experiment, key, value)
        await self._log_event(experiment_id, "experiment.updated", "system", {"updates": list(updates.keys())})
        return experiment

    async def get_experiment_metrics(self, experiment_id: str) -> dict:
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return {"error": "not found"}
        store = await self._get_event_store()
        events = await store.get_events(experiment_id, limit=10000)
        event_types = {}
        severities = {}
        for e in events:
            event_types[e.event_type] = event_types.get(e.event_type, 0) + 1
            sev = getattr(e, 'severity', 'info')
            if isinstance(sev, EventSeverity):
                sev = sev.value
            severities[sev] = severities.get(sev, 0) + 1
        return {
            "experiment_id": experiment_id,
            "status": experiment.status.value,
            "total_events": len(events),
            "event_types": event_types,
            "severities": severities,
            "node_count": experiment.node_count,
            "runtime_seconds": (datetime.now(timezone.utc) - experiment.created_at).total_seconds(),
        }

    async def get_event_stats(self, experiment_id: str) -> dict:
        store = await self._get_event_store()
        events = await store.get_events(experiment_id, limit=10000)
        if not events:
            return {"total": 0, "by_type": {}, "by_source": {}, "by_severity": {}}
        by_type = {}
        by_source = {}
        by_severity = {}
        for e in events:
            by_type[e.event_type] = by_type.get(e.event_type, 0) + 1
            by_source[e.source] = by_source.get(e.source, 0) + 1
            sev = getattr(e, 'severity', 'info')
            if isinstance(sev, EventSeverity):
                sev = sev.value
            by_severity[sev] = by_severity.get(sev, 0) + 1
        return {
            "total": len(events),
            "by_type": by_type,
            "by_source": by_source,
            "by_severity": by_severity,
        }

    async def export_experiment(self, experiment_id: str, fmt: ExportFormat = ExportFormat.json) -> dict:
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return {"error": "not found"}
        store = await self._get_event_store()
        events = await store.get_events(experiment_id, limit=10000)
        nodes = list(self.nodes.get(experiment_id, {}).values())
        return {
            "experiment": experiment.model_dump(),
            "nodes": [n.model_dump() for n in nodes],
            "events": [
                {
                    "id": e.id,
                    "timestamp": e.timestamp.isoformat(),
                    "event_type": e.event_type,
                    "source": e.source,
                    "data": e.data,
                    "severity": getattr(e, 'severity', EventSeverity.info).value if hasattr(e, 'severity') else 'info',
                }
                for e in events
            ],
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "export_format": fmt,
        }

    async def _log_event(self, experiment_id: str, event_type: str, source: str, data: dict, severity: EventSeverity = EventSeverity.info):
        event = ExperimentEvent(
            experiment_id=experiment_id,
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            source=source,
            data=data,
            severity=severity,
        )
        store = await self._get_event_store()
        await store.append_event(experiment_id, event)
        self.metrics.record_event(event)

        # Broadcast to WebSocket clients
        try:
            from forge.api.routes.ws import manager as ws_manager
            await ws_manager.broadcast(experiment_id, {
                "type": "event",
                "payload": {
                    "id": event.id,
                    "experiment_id": event.experiment_id,
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "source": event.source,
                    "data": event.data,
                },
            })
        except Exception:
            pass  # WebSocket broadcast is non-critical


orchestrator = Orchestrator(event_store=InMemoryEventStore())
