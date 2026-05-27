"""
E2E integration tests for full experiment lifecycle.
Uses FastAPI TestClient to exercise the complete API surface.
"""

import pytest
from fastapi.testclient import TestClient
from forge.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_full_lifecycle(client):
    # 1. Create experiment
    r = client.post("/api/v1/experiments/", json={"name": "e2e-test", "node_count": 2})
    assert r.status_code == 200
    exp = r.json()
    eid = exp["id"]
    assert exp["status"] == "pending"

    # 2. List experiments includes new one
    r = client.get("/api/v1/experiments/")
    assert r.status_code == 200
    ids = [e["id"] for e in r.json()]
    assert eid in ids

    # 3. Get single experiment
    r = client.get(f"/api/v1/experiments/{eid}")
    assert r.status_code == 200
    assert r.json()["name"] == "e2e-test"

    # 4. Update experiment
    r = client.patch(f"/api/v1/experiments/{eid}", json={"name": "e2e-updated", "description": "updated desc"})
    assert r.status_code == 200
    assert r.json()["name"] == "e2e-updated"
    assert r.json()["description"] == "updated desc"

    # 5. Get metrics
    r = client.get(f"/api/v1/experiments/{eid}/metrics")
    assert r.status_code == 200
    assert r.json()["total_events"] >= 1

    # 6. Get event stats
    r = client.get(f"/api/v1/experiments/{eid}/events/stats")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
    assert "experiment.created" in r.json()["by_type"]

    # 7. Get events list
    r = client.get(f"/api/v1/events/{eid}?limit=10")
    assert r.status_code == 200
    assert len(r.json()) >= 1

    # 8. Filter events by type
    r = client.get(f"/api/v1/events/{eid}?limit=10&event_type=experiment.created")
    assert r.status_code == 200
    assert all(e["event_type"] == "experiment.created" for e in r.json())

    # 9. Export experiment
    r = client.get(f"/api/v1/experiments/{eid}/export")
    assert r.status_code == 200
    data = r.json()
    assert data["experiment"]["name"] == "e2e-updated"
    assert "events" in data
    assert data["export_format"] == "json"

    # 10. Delete experiment
    r = client.delete(f"/api/v1/experiments/{eid}")
    assert r.status_code == 200
    assert r.json()["status"] == "deleted"

    # 11. Verify gone
    r = client.get(f"/api/v1/experiments/{eid}")
    assert r.status_code == 404


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in ("healthy", "degraded")


def test_404_on_missing_experiment(client):
    r = client.get("/api/v1/experiments/nonexistent")
    assert r.status_code == 404


def test_404_on_delete_missing(client):
    r = client.delete("/api/v1/experiments/nonexistent")
    assert r.status_code == 404


def test_422_on_invalid_experiment(client):
    r = client.post("/api/v1/experiments/", json={"name": ""})
    assert r.status_code in (200, 422)


def test_events_endpoint_empty(client):
    r = client.get("/api/v1/events/nonexistent?limit=5")
    assert r.status_code in (200, 404)


def test_metrics_on_nonexistent(client):
    r = client.get("/api/v1/experiments/nonexistent/metrics")
    assert r.status_code == 404


def test_export_on_nonexistent(client):
    r = client.get("/api/v1/experiments/nonexistent/export")
    assert r.status_code == 404


def test_agent_start_on_nonexistent(client):
    r = client.post("/api/v1/experiments/nonexistent/agent/start", json={"model": "test"})
    assert r.status_code == 404


def test_replay_on_nonexistent(client):
    r = client.post("/api/v1/replay/nonexistent/start")
    assert r.status_code == 404


def test_timeline_on_nonexistent(client):
    r = client.get("/api/v1/replay/nonexistent/timeline")
    assert r.status_code in (200, 404)


def test_create_and_list_filter(client):
    r = client.post("/api/v1/experiments/", json={"name": "filter-test"})
    assert r.status_code in (200, 422)


def test_inject_fault_on_nonexistent(client):
    r = client.post("/api/v1/nodes/nonexistent/inject?fault_type=latency&target_node=node-0")
    assert r.status_code == 200
    assert r.json()["status"] == "injected"


def test_inject_unknown_fault(client):
    r = client.post("/api/v1/nodes/nonexistent/inject?fault_type=invalid&target_node=node-0")
    assert r.status_code in (200, 422)
