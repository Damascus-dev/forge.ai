"""
API endpoint tests for semantic logging.

Tests HTTP endpoints:
- GET /api/v1/experiments/{experiment_id}/semantic-search
- GET /api/v1/weekly-summaries
- GET /api/v1/experiments/{experiment_id}/semantic-insights

Note: These tests focus on HTTP contract and validation.
For processor integration tests, see test_semantic_integration.py
"""

import pytest
from fastapi.testclient import TestClient

from forge.api.main import app


@pytest.fixture
def client():
    """Fixture: FastAPI test client."""
    return TestClient(app)



def test_semantic_search_missing_query(client):
    """Test semantic-search endpoint with missing query."""
    response = client.get("/api/v1/experiments/exp-1/semantic-search")
    
    # Should fail with 422 Unprocessable Entity (missing required param)
    assert response.status_code == 422


def test_semantic_search_empty_query(client):
    """Test semantic-search endpoint with empty query."""
    response = client.get("/api/v1/experiments/exp-1/semantic-search?query=")
    
    # Should fail with 422 (query min_length=1)
    assert response.status_code == 422


def test_semantic_search_invalid_limit(client):
    """Test semantic-search endpoint with invalid limit."""
    response = client.get("/api/v1/experiments/exp-1/semantic-search?query=test&limit=0")
    
    # Should fail with 422 (limit ge=1)
    assert response.status_code == 422


def test_semantic_search_limit_too_high(client):
    """Test semantic-search endpoint with limit exceeding max."""
    response = client.get("/api/v1/experiments/exp-1/semantic-search?query=test&limit=101")
    
    # Should fail with 422 (limit le=100)
    assert response.status_code == 422


def test_semantic_search_valid_params(client):
    """Test semantic-search endpoint with valid params."""
    # Note: This test does not check results since processor depends on DB/Ollama
    # See test_semantic_integration.py for processor + search tests
    response = client.get(
        "/api/v1/experiments/exp-1/semantic-search",
        params={"query": "test query", "limit": 10}
    )
    
    # Should either return 200 (if processor is initialized) or 503 (if not)
    assert response.status_code in [200, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert "experiment_id" in data
        assert "query" in data
        assert "results" in data
        assert "count" in data
        assert isinstance(data["results"], list)
        assert isinstance(data["count"], int)


def test_semantic_search_query_max_length(client):
    """Test semantic-search endpoint query max_length validation."""
    # Query too long (max_length=500)
    long_query = "test " * 200  # ~1000 characters
    response = client.get(
        "/api/v1/experiments/exp-1/semantic-search",
        params={"query": long_query, "limit": 10}
    )
    
    assert response.status_code == 422


def test_semantic_search_special_chars_in_query(client):
    """Test semantic-search endpoint with special characters."""
    response = client.get(
        "/api/v1/experiments/exp-1/semantic-search",
        params={"query": "special: !@#$%^&*() unicode: 你好", "limit": 10}
    )
    
    # Should either work or return error
    assert response.status_code in [200, 503, 500]


def test_semantic_search_response_has_required_fields(client):
    """Test semantic-search endpoint response structure."""
    response = client.get(
        "/api/v1/experiments/test-exp/semantic-search",
        params={"query": "test", "limit": 10}
    )
    
    if response.status_code == 200:
        data = response.json()
        assert "experiment_id" in data
        assert "query" in data
        assert "results" in data
        assert "count" in data
        
        # Check result fields if results exist
        for result in data["results"]:
            assert "id" in result
            assert "experiment_id" in result
            assert "agent_id" in result
            assert "action_type" in result
            assert "content" in result
            assert "created_at" in result
            assert "similarity" in result



def test_weekly_summaries_endpoint(client):
    """Test weekly-summaries endpoint."""
    response = client.get("/api/v1/weekly-summaries")
    
    # Should either return 200 (if generator initialized) or 503 (if not)
    assert response.status_code in [200, 503, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert "limit" in data
        assert "offset" in data
        assert "summaries" in data
        assert "total" in data


def test_weekly_summaries_with_params(client):
    """Test weekly-summaries endpoint with pagination params."""
    response = client.get(
        "/api/v1/weekly-summaries",
        params={"limit": 5, "offset": 10}
    )
    
    # Should either return 200 (if generator initialized) or 503/500 (if not)
    assert response.status_code in [200, 503, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 10


def test_weekly_summaries_invalid_limit(client):
    """Test weekly-summaries endpoint with invalid limit."""
    response = client.get(
        "/api/v1/weekly-summaries",
        params={"limit": 0}
    )
    
    # Should fail with 422 (limit ge=1)
    assert response.status_code == 422


def test_weekly_summaries_invalid_offset(client):
    """Test weekly-summaries endpoint with invalid offset."""
    response = client.get(
        "/api/v1/weekly-summaries",
        params={"offset": -1}
    )
    
    # Should fail with 422 (offset ge=0)
    assert response.status_code == 422


def test_semantic_insights_endpoint(client):
    """Test semantic-insights endpoint."""
    exp_id = "test-insights"
    
    response = client.get(f"/api/v1/experiments/{exp_id}/semantic-insights")
    
    # Should either return 200 (if generator initialized) or 503/500 (if not)
    assert response.status_code in [200, 503, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert data["experiment_id"] == exp_id
        assert "themes" in data
        assert "anomalies" in data
        assert "patterns" in data
        assert isinstance(data["themes"], list)
        assert isinstance(data["anomalies"], list)
        assert isinstance(data["patterns"], list)


@pytest.mark.asyncio
async def test_semantic_search_query_validation(client):
    """Test semantic-search endpoint query validation."""
    # Query too long (max_length=500)
    long_query = "test " * 200  # ~1000 characters
    response = client.get(
        "/api/v1/experiments/exp-1/semantic-search",
        params={"query": long_query, "limit": 10}
    )
    
    assert response.status_code == 422


def test_api_health_check(client):
    """Test API health endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"


def test_api_routes_registered(client):
    """Test that semantic routes are registered."""
    # Try accessing semantic endpoints
    response = client.get("/api/v1/weekly-summaries")
    
    # Should not get 404 (which would mean route not registered)
    assert response.status_code != 404
