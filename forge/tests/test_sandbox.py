import pytest

from forge.agents.loop import AgentRuntime
from forge.chaos.engine import ChaosEngine
from forge.events.store import InMemoryEventStore
from forge.experiments.models import AgentConfig, Experiment, FaultConfig


def test_experiment_creation():
    exp = Experiment(name="test-exp", node_count=3)
    assert exp.name == "test-exp"
    assert exp.node_count == 3
    assert exp.status.value == "pending"


@pytest.mark.asyncio
async def test_orchestrator_create():
    from forge.orchestrator.manager import Orchestrator
    store = InMemoryEventStore()
    orchestrator = Orchestrator(event_store=store)
    exp = Experiment(name="integration-test", node_count=2)
    result = await orchestrator.create_experiment(experiment=exp)
    assert result.id is not None
    assert result.status.value == "pending"
    assert result.name == "integration-test"


@pytest.mark.asyncio
async def test_orchestrator_events():
    from forge.orchestrator.manager import Orchestrator
    store = InMemoryEventStore()
    orchestrator = Orchestrator(event_store=store)
    exp = Experiment(name="event-test", node_count=1)
    result = await orchestrator.create_experiment(experiment=exp)
    events = await orchestrator.get_events(result.id)
    assert len(events) == 1
    assert events[0]["event_type"] == "experiment.created"
    assert events[0]["data"]["name"] == "event-test"


@pytest.mark.asyncio
async def test_orchestrator_timeline():
    from forge.orchestrator.manager import Orchestrator
    store = InMemoryEventStore()
    orchestrator = Orchestrator(event_store=store)
    exp = Experiment(name="timeline-test", node_count=1)
    result = await orchestrator.create_experiment(experiment=exp)
    await orchestrator.start_experiment(result.id)
    timeline = await orchestrator.get_timeline(result.id)
    assert timeline is not None
    assert len(timeline) == 2
    assert timeline[0]["type"] == "experiment.created"
    assert timeline[1]["type"] == "experiment.started"


@pytest.mark.asyncio
async def test_chaos_engine_latency_without_runtime():
    engine = ChaosEngine()
    config = FaultConfig(
        experiment_id="test", target_node="node-1",
        fault_type="latency", params={"delay_ms": 50},
    )
    result = await engine.inject_fault(config)
    assert result["status"] == "injected"
    assert result["fault_type"] == "latency"
    assert "node runtime not available" in result["output"]


@pytest.mark.asyncio
async def test_chaos_engine_packet_loss_without_runtime():
    engine = ChaosEngine()
    config = FaultConfig(
        experiment_id="test", target_node="node-1",
        fault_type="packet_loss", params={"loss_pct": 10},
    )
    result = await engine.inject_fault(config)
    assert result["status"] == "injected"
    assert result["fault_type"] == "packet_loss"
    assert "node runtime not available" in result["output"]


@pytest.mark.asyncio
async def test_chaos_engine_unknown_fault():
    engine = ChaosEngine()
    config = FaultConfig(
        experiment_id="test", target_node="node-1",
        fault_type="unknown_fault", params={},
    )
    result = await engine.inject_fault(config)
    assert result["status"] == "unknown"


@pytest.mark.asyncio
async def test_agent_observe():
    agent = AgentRuntime(agent_id="test-agent")
    exp = Experiment(name="agent-test", node_count=2)
    obs = await agent.observe(exp)
    assert obs["experiment_id"] == exp.id
    assert obs["experiment_name"] == "agent-test"
    assert obs["node_count"] == 2


@pytest.mark.asyncio
async def test_agent_reason():
    agent = AgentRuntime(agent_id="test-agent")
    exp = Experiment(name="reason-test", node_count=1)
    obs = await agent.observe(exp)
    decision = await agent.reason(obs, [])
    assert decision is not None
    assert len(decision) > 0


@pytest.mark.asyncio
async def test_agent_act_text_response():
    agent = AgentRuntime(agent_id="test-agent")
    result = await agent.act("I will investigate the system")
    assert result["action"] == "text"
    assert result["content"] == "I will investigate the system"


@pytest.mark.asyncio
async def test_agent_log():
    agent = AgentRuntime(agent_id="test-agent")
    exp = Experiment(name="log-test", node_count=1)
    obs = await agent.observe(exp)
    result = await agent.act("reasoning step")
    agent.log(obs, "decision text", result)
    assert len(agent.logs) == 1
    assert agent.logs[0].step == 1
    assert agent.logs[0].agent_id == "test-agent"


@pytest.mark.asyncio
async def test_orchestrator_agent_lifecycle():
    from forge.orchestrator.manager import Orchestrator
    store = InMemoryEventStore()
    orchestrator = Orchestrator(event_store=store)
    exp = Experiment(name="agent-lifecycle", node_count=1)
    result = await orchestrator.create_experiment(experiment=exp)

    agent_result = await orchestrator.start_agent(
        result.id, AgentConfig(model="ollama/qwen2.5:0.5b")
    )
    assert "agent_id" in agent_result
    assert agent_result["status"] == "started"

    logs = orchestrator.get_agent_logs(result.id, agent_result["agent_id"])
    assert len(logs) == 0

    step_result = await orchestrator.run_agent_step(result.id, agent_result["agent_id"])
    assert "step" in step_result
    assert step_result["step"] == 1


@pytest.mark.asyncio
async def test_node_runtime_launch_and_teardown():
    from forge.runtime.node import NodeRuntime
    runtime = NodeRuntime()
    client = runtime._get_client()
    if client is None:
        pytest.skip("Docker not available")

    exp = Experiment(name="docker-test", node_count=1)
    from forge.events.store import InMemoryEventStore
    from forge.orchestrator.manager import Orchestrator
    store = InMemoryEventStore()
    orchestrator = Orchestrator(event_store=store)
    await orchestrator.create_experiment(exp)

    nodes = await runtime.launch_nodes(exp)
    assert len(nodes) == 1
    assert nodes[0].container_id is not None
    assert nodes[0].status == "running"

    container = client.containers.get(nodes[0].container_id)
    assert container.status == "running"

    result = await runtime.exec_on_node(nodes[0].name, ["echo", "hello"])
    assert "hello" in result

    await runtime.teardown_nodes(exp.id)
    import docker.errors
    try:
        c = client.containers.get(nodes[0].container_id)
        assert c.status != "running"
    except docker.errors.NotFound:
        pass
