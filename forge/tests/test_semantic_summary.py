"""
Tests for weekly summary generation.

Tests SummaryGenerator functionality:
- Week boundary calculation
- Summary generation from actions
- Storage and retrieval
"""

import pytest
import time
import uuid
from datetime import datetime, timedelta
from pytest_asyncio import fixture as async_fixture

from forge.configs.settings import settings
from forge.db.postgres import PostgresDB
from forge.semantic.embeddings import EmbeddingEngine
from forge.semantic.processor import SemanticProcessor
from forge.semantic.summary import SummaryGenerator


@async_fixture
async def db():
    """Fixture: PostgreSQL database connection."""
    database = PostgresDB(settings.database_url)
    
    # Check if database is available
    is_healthy = await database.health_check()
    if not is_healthy:
        pytest.skip("PostgreSQL database not available")
    
    yield database
    await database.close()


@async_fixture
async def embedding_engine():
    """Fixture: Embedding engine."""
    engine = EmbeddingEngine()
    yield engine


@async_fixture
async def semantic_processor(embedding_engine, db):
    """Fixture: SemanticProcessor."""
    return SemanticProcessor(
        embedding_engine=embedding_engine,
        db=db,
    )


@async_fixture
async def summary_generator(db, embedding_engine):
    """Fixture: SummaryGenerator."""
    return SummaryGenerator(db, embedding_engine)


def generate_test_exp_id(prefix: str = "summary-test") -> str:
    """Generate unique experiment ID."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}-{int(time.time() * 1000)}"


@pytest.mark.asyncio
async def test_summary_generator_init(summary_generator):
    """Test SummaryGenerator initialization."""
    assert summary_generator.db is not None
    assert summary_generator.embeddings is not None


@pytest.mark.asyncio
async def test_week_boundaries_today():
    """Test week boundary calculation for today."""
    gen = SummaryGenerator(None, None)
    week_start, week_end = gen._get_week_boundaries()
    
    # week_start should be a Monday
    start_date = datetime.fromisoformat(week_start)
    assert start_date.weekday() == 0  # Monday
    
    # week_end should be 6 days after start
    end_date = datetime.fromisoformat(week_end)
    diff = (end_date - start_date).days
    assert diff == 6  # Sunday is 6 days after Monday


@pytest.mark.asyncio
async def test_week_boundaries_custom_date():
    """Test week boundary calculation for custom date."""
    gen = SummaryGenerator(None, None)
    
    # Use a known date: 2026-05-15 (Friday)
    test_date = datetime(2026, 5, 15)
    week_start, week_end = gen._get_week_boundaries(test_date)
    
    # Should get the Monday of that week (2026-05-11)
    assert week_start == "2026-05-11"
    # Should get the Sunday of that week (2026-05-17)
    assert week_end == "2026-05-17"


@pytest.mark.asyncio
async def test_count_by_type():
    """Test counting actions by type."""
    gen = SummaryGenerator(None, None)
    
    actions = [
        {"action_type": "observe", "agent_id": "a1", "content": "c1"},
        {"action_type": "observe", "agent_id": "a1", "content": "c2"},
        {"action_type": "reason", "agent_id": "a1", "content": "c3"},
        {"action_type": "act", "agent_id": "a1", "content": "c4"},
    ]
    
    counts = gen._count_by_type(actions)
    assert counts["observe"] == 2
    assert counts["reason"] == 1
    assert counts["act"] == 1


@pytest.mark.asyncio
async def test_count_by_agent():
    """Test counting actions by agent."""
    gen = SummaryGenerator(None, None)
    
    actions = [
        {"action_type": "observe", "agent_id": "agent-1", "content": "c1"},
        {"action_type": "observe", "agent_id": "agent-1", "content": "c2"},
        {"action_type": "reason", "agent_id": "agent-2", "content": "c3"},
        {"action_type": "act", "agent_id": "agent-2", "content": "c4"},
        {"action_type": "act", "agent_id": "agent-3", "content": "c5"},
    ]
    
    counts = gen._count_by_agent(actions)
    assert counts["agent-1"] == 2
    assert counts["agent-2"] == 2
    assert counts["agent-3"] == 1


@pytest.mark.asyncio
async def test_generate_summary_text_empty():
    """Test summary text generation with no actions."""
    gen = SummaryGenerator(None, None)
    text = gen._generate_summary_text([])
    
    assert "No actions recorded" in text


@pytest.mark.asyncio
async def test_generate_summary_text_with_actions():
    """Test summary text generation with actions."""
    gen = SummaryGenerator(None, None)
    
    actions = [
        {"action_type": "observe", "agent_id": "agent-1", "content": "c1"},
        {"action_type": "observe", "agent_id": "agent-1", "content": "c2"},
        {"action_type": "reason", "agent_id": "agent-2", "content": "c3"},
    ]
    
    text = gen._generate_summary_text(actions)
    
    assert "3" in text  # Total actions
    assert "2" in text  # Number of agents
    assert "observe" in text  # Action type
    assert "reason" in text  # Action type


@pytest.mark.asyncio
async def test_generate_summary_no_actions(summary_generator):
    """Test summary generation with no actions."""
    exp_id = generate_test_exp_id("no-actions")
    
    result = await summary_generator.generate_summary(exp_id)
    
    # Should return None if no actions
    assert result is None


@pytest.mark.asyncio
async def test_generate_summary_with_actions(summary_generator, semantic_processor):
    """Test summary generation with actions."""
    exp_id = generate_test_exp_id("with-actions")
    
    # Insert some actions
    await semantic_processor.process_action(
        experiment_id=exp_id,
        agent_id="agent-1",
        action_type="observe",
        content="Observed system state",
    )
    
    await semantic_processor.process_action(
        experiment_id=exp_id,
        agent_id="agent-1",
        action_type="reason",
        content="Analyzed metrics",
    )
    
    # Generate summary for current week
    summary = await summary_generator.generate_summary(exp_id)
    
    assert summary is not None
    assert summary["experiment_id"] == exp_id
    assert summary["total_actions"] == 2
    assert "observe" in summary["themes"]
    assert "reason" in summary["themes"]
    assert summary["summary_text"] is not None


@pytest.mark.asyncio
async def test_summary_stored_in_database(summary_generator, semantic_processor):
    """Test that generated summaries are stored in database."""
    exp_id = generate_test_exp_id("db-storage")
    
    # Insert action
    await semantic_processor.process_action(
        experiment_id=exp_id,
        agent_id="agent-1",
        action_type="test",
        content="Test action",
    )
    
    # Generate summary
    summary = await summary_generator.generate_summary(exp_id)
    assert summary is not None
    
    # Retrieve from database
    summaries, total = await summary_generator.get_summaries(
        experiment_id=exp_id,
        limit=10,
        offset=0,
    )
    
    assert total >= 1
    assert len(summaries) >= 1
    assert summaries[0]["experiment_id"] == exp_id


@pytest.mark.asyncio
async def test_get_summaries_pagination(summary_generator, semantic_processor):
    """Test pagination of summaries."""
    exp_id = generate_test_exp_id("pagination")
    
    # Insert actions for multiple weeks
    for i in range(5):
        await semantic_processor.process_action(
            experiment_id=exp_id,
            agent_id="agent-1",
            action_type="observe",
            content=f"Action {i}",
        )
    
    # Generate summary for current week
    await summary_generator.generate_summary(exp_id)
    
    # Test pagination with limit=2
    summaries_1, total = await summary_generator.get_summaries(
        experiment_id=exp_id,
        limit=2,
        offset=0,
    )
    
    assert len(summaries_1) <= 2


@pytest.mark.asyncio
async def test_get_summaries_filter_by_experiment(summary_generator, semantic_processor):
    """Test filtering summaries by experiment."""
    exp_id_1 = generate_test_exp_id("filter-1")
    exp_id_2 = generate_test_exp_id("filter-2")
    
    # Insert actions in exp 1
    await semantic_processor.process_action(
        experiment_id=exp_id_1,
        agent_id="agent-1",
        action_type="observe",
        content="Action 1",
    )
    
    # Insert actions in exp 2
    await semantic_processor.process_action(
        experiment_id=exp_id_2,
        agent_id="agent-1",
        action_type="observe",
        content="Action 2",
    )
    
    # Generate summaries
    await summary_generator.generate_summary(exp_id_1)
    await summary_generator.generate_summary(exp_id_2)
    
    # Get summaries for exp 1 only
    summaries_1, _ = await summary_generator.get_summaries(
        experiment_id=exp_id_1,
        limit=10,
        offset=0,
    )
    
    # All should be from exp 1
    for summary in summaries_1:
        assert summary["experiment_id"] == exp_id_1


@pytest.mark.asyncio
async def test_summary_themes_extracted(summary_generator, semantic_processor):
    """Test that action types are extracted as themes."""
    exp_id = generate_test_exp_id("themes")
    
    # Insert actions with different types
    await semantic_processor.process_action(
        experiment_id=exp_id,
        agent_id="agent-1",
        action_type="observe",
        content="Observation",
    )
    
    await semantic_processor.process_action(
        experiment_id=exp_id,
        agent_id="agent-1",
        action_type="reason",
        content="Reasoning",
    )
    
    await semantic_processor.process_action(
        experiment_id=exp_id,
        agent_id="agent-1",
        action_type="decide",
        content="Decision",
    )
    
    summary = await summary_generator.generate_summary(exp_id)
    
    assert len(summary["themes"]) == 3
    assert "observe" in summary["themes"]
    assert "reason" in summary["themes"]
    assert "decide" in summary["themes"]


@pytest.mark.asyncio
async def test_summary_metrics(summary_generator, semantic_processor):
    """Test that summary metrics are generated."""
    exp_id = generate_test_exp_id("metrics")
    
    # Insert actions
    await semantic_processor.process_action(
        experiment_id=exp_id,
        agent_id="agent-1",
        action_type="observe",
        content="A",
    )
    
    await semantic_processor.process_action(
        experiment_id=exp_id,
        agent_id="agent-2",
        action_type="reason",
        content="B",
    )
    
    summary = await summary_generator.generate_summary(exp_id)
    
    metrics = summary["key_metrics"]
    assert metrics["total_actions"] == 2
    assert "by_type" in metrics
    assert "by_agent" in metrics
    assert metrics["by_agent"]["agent-1"] == 1
    assert metrics["by_agent"]["agent-2"] == 1


@pytest.mark.asyncio
async def test_summary_idempotent(summary_generator, semantic_processor):
    """Test that generating summary twice is idempotent."""
    exp_id = generate_test_exp_id("idempotent")
    
    # Insert action
    await semantic_processor.process_action(
        experiment_id=exp_id,
        agent_id="agent-1",
        action_type="observe",
        content="Test",
    )
    
    # Generate summary twice
    summary_1 = await summary_generator.generate_summary(exp_id)
    summary_2 = await summary_generator.generate_summary(exp_id)
    
    # Should have same ID (upsert)
    assert summary_1["id"] == summary_2["id"]
    assert summary_1["summary_text"] == summary_2["summary_text"]
