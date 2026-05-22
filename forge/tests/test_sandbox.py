import pytest

from forge.experiments.models import Experiment


def test_experiment_creation():
    exp = Experiment(name="test-exp", node_count=3)
    assert exp.name == "test-exp"
    assert exp.node_count == 3
    assert exp.status.value == "pending"


@pytest.mark.asyncio
async def test_orchestrator_create():
    from forge.orchestrator.manager import orchestrator
    exp = Experiment(name="integration-test", node_count=2)
    result = await orchestrator.create_experiment(exp)
    assert result.id is not None
    assert result.status.value == "pending"
    assert result.name == "integration-test"
