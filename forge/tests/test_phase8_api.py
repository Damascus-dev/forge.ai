import pytest

from forge.experiments.models import (
    EventSeverity,
    Experiment,
    ExperimentEvent,
    ExportFormat,
    HealthCheck,
)


class TestEnhancedModels:
    def test_event_with_severity(self):
        e = ExperimentEvent(experiment_id="e1", event_type="test", source="s1", severity=EventSeverity.warning)
        assert e.severity == EventSeverity.warning

    def test_event_with_tags(self):
        e = ExperimentEvent(experiment_id="e1", event_type="test", source="s1", tags=["network", "latency"])
        assert "network" in e.tags

    def test_event_with_metadata(self):
        e = ExperimentEvent(experiment_id="e1", event_type="test", source="s1", metadata={"region": "us-east"})
        assert e.metadata["region"] == "us-east"

    def test_experiment_with_tags(self):
        exp = Experiment(name="tagged-exp", tags=["chaos", "network"])
        assert len(exp.tags) == 2

    def test_export_format_enum(self):
        assert ExportFormat.json.value == "json"
        assert ExportFormat.csv.value == "csv"
        assert ExportFormat.markdown.value == "markdown"

    def test_health_check_model(self):
        from forge.experiments.models import HealthComponent
        comp = HealthComponent(name="api", status="healthy")
        hc = HealthCheck(status="healthy", version="1.0", components=[comp])
        assert hc.status == "healthy"
        assert len(hc.components) == 1


@pytest.mark.asyncio(loop_scope="function")
async def test_delete_experiment():
    from forge.events.store import InMemoryEventStore
    from forge.orchestrator.manager import Orchestrator
    orch = Orchestrator(event_store=InMemoryEventStore())
    exp = Experiment(name="delete-me")
    created = await orch.create_experiment(exp)
    result = await orch.delete_experiment(created.id)
    assert result["status"] == "deleted"
    assert await orch.get_experiment(created.id) is None


@pytest.mark.asyncio(loop_scope="function")
async def test_update_experiment():
    from forge.events.store import InMemoryEventStore
    from forge.orchestrator.manager import Orchestrator
    orch = Orchestrator(event_store=InMemoryEventStore())
    exp = Experiment(name="original")
    created = await orch.create_experiment(exp)
    updated = await orch.update_experiment(created.id, {"name": "updated"})
    assert updated.name == "updated"
    assert updated.description == ""


@pytest.mark.asyncio(loop_scope="function")
async def test_get_experiment_metrics():
    from forge.events.store import InMemoryEventStore
    from forge.orchestrator.manager import Orchestrator
    orch = Orchestrator(event_store=InMemoryEventStore())
    exp = Experiment(name="metrics-test")
    created = await orch.create_experiment(exp)
    metrics = await orch.get_experiment_metrics(created.id)
    assert metrics["experiment_id"] == created.id
    assert metrics["total_events"] >= 1
    assert "experiment.created" in metrics["event_types"]


@pytest.mark.asyncio(loop_scope="function")
async def test_get_event_stats():
    from forge.events.store import InMemoryEventStore
    from forge.orchestrator.manager import Orchestrator
    orch = Orchestrator(event_store=InMemoryEventStore())
    exp = Experiment(name="stats-test")
    created = await orch.create_experiment(exp)
    stats = await orch.get_event_stats(created.id)
    assert stats["total"] >= 1
    assert "experiment.created" in stats["by_type"]
    assert "system" in stats["by_source"]


@pytest.mark.asyncio(loop_scope="function")
async def test_export_experiment_json():
    from forge.events.store import InMemoryEventStore
    from forge.orchestrator.manager import Orchestrator
    orch = Orchestrator(event_store=InMemoryEventStore())
    exp = Experiment(name="export-test")
    created = await orch.create_experiment(exp)
    exported = await orch.export_experiment(created.id, ExportFormat.json)
    assert exported["experiment"]["name"] == "export-test"
    assert "events" in exported
    assert "nodes" in exported
    assert exported["export_format"] == ExportFormat.json.value


@pytest.mark.asyncio(loop_scope="function")
async def test_orch_list_empty():
    from forge.events.store import InMemoryEventStore
    from forge.orchestrator.manager import Orchestrator
    orch = Orchestrator(event_store=InMemoryEventStore())
    exps = await orch.list_experiments()
    assert exps == []


@pytest.mark.asyncio(loop_scope="function")
async def test_delete_nonexistent():
    from forge.events.store import InMemoryEventStore
    from forge.orchestrator.manager import Orchestrator
    orch = Orchestrator(event_store=InMemoryEventStore())
    result = await orch.delete_experiment("nonexistent")
    assert "error" in result


@pytest.mark.asyncio(loop_scope="function")
async def test_update_nonexistent():
    from forge.events.store import InMemoryEventStore
    from forge.orchestrator.manager import Orchestrator
    orch = Orchestrator(event_store=InMemoryEventStore())
    result = await orch.update_experiment("nonexistent", {"name": "nope"})
    assert result is None


class TestEventSeverityMapping:
    def test_fault_config_default_severity(self):
        from forge.experiments.models import FaultConfig
        fc = FaultConfig(experiment_id="e1", target_node="n1", fault_type="latency")
        assert fc.severity == EventSeverity.warning

    def test_severity_values(self):
        assert [s.value for s in EventSeverity] == ["info", "warning", "error", "critical"]
