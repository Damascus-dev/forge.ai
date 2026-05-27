"""
Integration tests for semantic logging module.

Tests end-to-end workflows:
- Insert action → embed → search
- Multiple actions with similarity ranking
- Different experiment IDs
- Error handling
- API endpoint integration
"""

import time
import uuid

import pytest
from pytest_asyncio import fixture as async_fixture

from forge.configs.settings import settings
from forge.db.postgres import PostgresDB
from forge.semantic.embeddings import EmbeddingEngine
from forge.semantic.processor import SemanticProcessor


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
    """Fixture: Embedding engine (Ollama integration)."""
    engine = EmbeddingEngine()
    yield engine


@async_fixture
async def semantic_processor(embedding_engine, db):
    """Fixture: SemanticProcessor with DB."""
    return SemanticProcessor(
        embedding_engine=embedding_engine,
        db=db,
    )


def generate_test_exp_id(prefix: str = "test") -> str:
    """Generate unique experiment ID for test isolation."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}-{int(time.time() * 1000)}"


@pytest.mark.asyncio
async def test_semantic_processor_init(embedding_engine):
    """Test SemanticProcessor initialization without DB."""
    processor = SemanticProcessor(embedding_engine=embedding_engine, db=None)
    assert processor.embeddings is not None
    assert processor.db is None


@pytest.mark.asyncio
async def test_semantic_processor_init_with_db(semantic_processor):
    """Test SemanticProcessor initialization with DB."""
    assert semantic_processor.embeddings is not None
    assert semantic_processor.db is not None


@pytest.mark.asyncio
async def test_embedding_generation(embedding_engine):
    """Test embedding generation via Ollama."""
    text = "Agent observed 3 nodes running with 2GB each"
    embedding = await embedding_engine.embed(text)

    assert embedding is not None
    assert len(embedding) == 768  # nomic-embed-text is 768-dim
    assert all(isinstance(x, float) for x in embedding)


@pytest.mark.asyncio
async def test_process_action_without_db(embedding_engine):
    """Test processing action without database."""
    processor = SemanticProcessor(embedding_engine=embedding_engine, db=None)

    result = await processor.process_action(
        experiment_id="exp-1",
        agent_id="agent-1",
        action_type="observe",
        content="Agent observed nodes running",
    )

    # Should return -1 when DB is None
    assert result == -1


@pytest.mark.asyncio
async def test_process_action_with_db(semantic_processor):
    """Test processing action with database (end-to-end)."""
    result = await semantic_processor.process_action(
        experiment_id="test-exp-1",
        agent_id="agent-1",
        action_type="observe",
        content="Agent observed 3 nodes running with 2GB each",
    )

    # Should return valid row ID
    assert isinstance(result, int)
    assert result > 0


@pytest.mark.asyncio
async def test_semantic_search_without_db(embedding_engine):
    """Test semantic search without database."""
    processor = SemanticProcessor(embedding_engine=embedding_engine, db=None)

    results = await processor.semantic_search(
        experiment_id="exp-1",
        query="how many nodes running",
        limit=5,
    )

    # Should return empty list when DB is None
    assert results == []


@pytest.mark.asyncio
async def test_semantic_search_single_action(semantic_processor):
    """Test semantic search with single action."""
    exp_id = generate_test_exp_id("single-action")

    # Insert action
    action_id = await semantic_processor.process_action(
        experiment_id=exp_id,
        agent_id="agent-1",
        action_type="observe",
        content="Agent observed 3 nodes running with 2GB each",
    )
    assert action_id > 0

    # Search for similar content
    results = await semantic_processor.semantic_search(
        experiment_id=exp_id,
        query="how many nodes running",
        limit=5,
    )

    # Should find the action with high similarity
    assert len(results) >= 1
    assert results[0]["id"] == action_id
    assert results[0]["content"] == "Agent observed 3 nodes running with 2GB each"
    assert 0.0 <= results[0]["similarity"] <= 1.0
    assert results[0]["similarity"] > 0.5  # Should be fairly similar


@pytest.mark.asyncio
async def test_semantic_search_multiple_actions(semantic_processor):
    """Test semantic search with multiple actions (similarity ranking)."""
    exp_id = generate_test_exp_id("multi-action")

    # Insert 3 actions
    action_1_id = await semantic_processor.process_action(
        experiment_id=exp_id,
        agent_id="agent-1",
        action_type="observe",
        content="Agent observed 3 nodes running with 2GB each",
    )

    await semantic_processor.process_action(
        experiment_id=exp_id,
        agent_id="agent-1",
        action_type="reason",
        content="Nodes are healthy and responding to network requests",
    )

    await semantic_processor.process_action(
        experiment_id=exp_id,
        agent_id="agent-1",
        action_type="decide",
        content="Decision: apply CPU scaling policy",
    )

    # Search for query about nodes
    results = await semantic_processor.semantic_search(
        experiment_id=exp_id,
        query="how many nodes running",
        limit=10,
    )

    # Should return multiple results
    assert len(results) >= 3

    # Should be ranked by similarity
    for i in range(len(results) - 1):
        assert results[i]["similarity"] >= results[i + 1]["similarity"]

    # First result should be most similar (about node count)
    assert results[0]["id"] == action_1_id
    assert results[0]["similarity"] > results[2]["similarity"]


@pytest.mark.asyncio
async def test_semantic_search_experiment_isolation(semantic_processor):
    """Test that semantic search respects experiment boundaries."""
    exp_id_1 = generate_test_exp_id("isolation-1")
    exp_id_2 = generate_test_exp_id("isolation-2")

    # Insert action in experiment 1
    action_exp1 = await semantic_processor.process_action(
        experiment_id=exp_id_1,
        agent_id="agent-1",
        action_type="observe",
        content="Experiment 1: Agent observed 3 nodes",
    )

    # Insert action in experiment 2
    action_exp2 = await semantic_processor.process_action(
        experiment_id=exp_id_2,
        agent_id="agent-1",
        action_type="observe",
        content="Experiment 2: Agent observed 5 nodes",
    )

    # Search in experiment 1 only
    results_exp1 = await semantic_processor.semantic_search(
        experiment_id=exp_id_1,
        query="how many nodes",
        limit=10,
    )

    # Search in experiment 2 only
    results_exp2 = await semantic_processor.semantic_search(
        experiment_id=exp_id_2,
        query="how many nodes",
        limit=10,
    )

    # Each should contain only their own action
    assert len(results_exp1) == 1
    assert results_exp1[0]["id"] == action_exp1
    assert results_exp1[0]["experiment_id"] == exp_id_1

    assert len(results_exp2) == 1
    assert results_exp2[0]["id"] == action_exp2
    assert results_exp2[0]["experiment_id"] == exp_id_2


@pytest.mark.asyncio
async def test_semantic_search_with_limit(semantic_processor):
    """Test semantic search result limit."""
    # Insert 5 actions
    for i in range(5):
        await semantic_processor.process_action(
            experiment_id="test-exp-5",
            agent_id="agent-1",
            action_type="observe",
            content=f"Agent observed metric {i}: {i * 100} requests per second",
        )

    # Search with limit=2
    results = await semantic_processor.semantic_search(
        experiment_id="test-exp-5",
        query="requests per second",
        limit=2,
    )

    # Should respect limit
    assert len(results) <= 2


@pytest.mark.asyncio
async def test_semantic_search_empty_experiment(semantic_processor):
    """Test semantic search on experiment with no actions."""
    results = await semantic_processor.semantic_search(
        experiment_id="test-exp-nonexistent",
        query="any query",
        limit=10,
    )

    # Should return empty list
    assert results == []


@pytest.mark.asyncio
async def test_database_health_check(db):
    """Test database health check."""
    is_healthy = await db.health_check()
    assert is_healthy is True


@pytest.mark.asyncio
async def test_action_metadata_preserved(semantic_processor):
    """Test that action metadata is preserved during storage."""
    exp_id = generate_test_exp_id("metadata")
    agent_id = "agent-test"
    action_type = "analyze"
    content = "Test action content for metadata"

    action_id = await semantic_processor.process_action(
        experiment_id=exp_id,
        agent_id=agent_id,
        action_type=action_type,
        content=content,
    )

    # Search to retrieve the action
    results = await semantic_processor.semantic_search(
        experiment_id=exp_id,
        query=content,
        limit=1,
    )

    assert len(results) == 1
    result = results[0]

    # All metadata should be preserved
    assert result["id"] == action_id
    assert result["experiment_id"] == exp_id
    assert result["agent_id"] == agent_id
    assert result["action_type"] == action_type
    assert result["content"] == content
    assert result["created_at"] is not None


@pytest.mark.asyncio
async def test_embedding_consistency(embedding_engine):
    """Test that embedding the same text produces consistent results."""
    text = "Consistent text for embedding test"

    embedding_1 = await embedding_engine.embed(text)
    embedding_2 = await embedding_engine.embed(text)

    # Should produce identical embeddings
    assert len(embedding_1) == len(embedding_2)
    for v1, v2 in zip(embedding_1, embedding_2):
        assert abs(v1 - v2) < 1e-6  # Allow for floating point rounding


@pytest.mark.asyncio
async def test_semantic_similarity_semantics(semantic_processor):
    """Test that semantically similar queries return expected results."""
    # Insert action about nodes
    await semantic_processor.process_action(
        experiment_id="test-exp-7",
        agent_id="agent-1",
        action_type="observe",
        content="The cluster has 3 worker nodes",
    )

    # Similar query
    results_similar = await semantic_processor.semantic_search(
        experiment_id="test-exp-7",
        query="How many worker machines are in the cluster?",
        limit=1,
    )

    # Dissimilar query
    results_dissimilar = await semantic_processor.semantic_search(
        experiment_id="test-exp-7",
        query="What color is the sky?",
        limit=1,
    )

    assert len(results_similar) == 1
    assert len(results_dissimilar) == 1

    # Similar query should have higher similarity
    assert results_similar[0]["similarity"] > results_dissimilar[0]["similarity"]


@pytest.mark.asyncio
async def test_concurrent_insertions(semantic_processor):
    """Test concurrent action insertions."""
    import asyncio

    exp_id = generate_test_exp_id("concurrent")

    # Create concurrent tasks
    tasks = [
        semantic_processor.process_action(
            experiment_id=exp_id,
            agent_id=f"agent-{i}",
            action_type="observe",
            content=f"Action {i}: {text}",
        )
        for i, text in enumerate([
            "Node A is healthy",
            "Node B is healthy",
            "Node C is healthy",
            "CPU usage is normal",
            "Memory usage is normal",
        ])
    ]

    # Execute concurrently
    results = await asyncio.gather(*tasks)

    # All should succeed
    assert all(isinstance(r, int) and r > 0 for r in results)

    # Verify all were stored
    search_results = await semantic_processor.semantic_search(
        experiment_id=exp_id,
        query="node health",
        limit=10,
    )
    assert len(search_results) == 5


@pytest.mark.asyncio
async def test_special_characters_in_content(semantic_processor):
    """Test handling of special characters and unicode."""
    content = "Special chars: !@#$%^&*() and unicode: 你好, مرحبا, γεια"

    action_id = await semantic_processor.process_action(
        experiment_id="test-exp-9",
        agent_id="agent-1",
        action_type="observe",
        content=content,
    )

    assert action_id > 0

    # Should be retrievable
    results = await semantic_processor.semantic_search(
        experiment_id="test-exp-9",
        query="special characters",
        limit=1,
    )

    assert len(results) == 1
    assert results[0]["content"] == content
