"""
Unit tests for the FastAPI application endpoints.
"""

from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)


def test_healthz():
    response = client.get("/v1/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metadata():
    response = client.get("/v1/metadata")
    assert response.status_code == 200
    assert "version" in response.json()


def test_context_push():
    payload = {
        "scope": "merchant",
        "context_id": "test_m1",
        "version": 1,
        "payload": {"identity": {"name": "Test"}},
        "delivered_at": "2026-07-11T00:00:00Z"
    }
    
    # First push should succeed
    response = client.post("/v1/context", json=payload)
    assert response.status_code == 200
    assert response.json()["accepted"] is True
    
    # Push with lower version should fail
    payload["version"] = 0
    response2 = client.post("/v1/context", json=payload)
    assert response2.status_code == 409
    assert response2.json()["accepted"] is False
    
    # Push with higher version should succeed
    payload["version"] = 2
    response3 = client.post("/v1/context", json=payload)
    assert response3.status_code == 200
    assert response3.json()["accepted"] is True


def test_tick_and_suppression():
    client.post("/v1/teardown")
    
    client.post("/v1/context", json={
        "scope": "category", "context_id": "c1", "version": 1,
        "payload": {"slug": "c1"}, "delivered_at": "2026-07-11T00:00:00Z"
    })
    client.post("/v1/context", json={
        "scope": "merchant", "context_id": "m1", "version": 1,
        "payload": {"category_slug": "c1", "identity": {"name": "M1"}}, "delivered_at": "2026-07-11T00:00:00Z"
    })
    client.post("/v1/context", json={
        "scope": "trigger", "context_id": "t1", "version": 1,
        "payload": {"merchant_id": "m1", "kind": "test", "suppression_key": "test_key"}, "delivered_at": "2026-07-11T00:00:00Z"
    })
    
    # First tick should generate action
    resp = client.post("/v1/tick", json={"now": "2026-07-11T00:00:00Z", "available_triggers": ["t1"]})
    assert resp.status_code == 200
    actions = resp.json().get("actions", [])
    assert len(actions) == 1
    
    # Second tick should not generate action due to suppression
    resp2 = client.post("/v1/tick", json={"now": "2026-07-11T00:00:00Z", "available_triggers": ["t1"]})
    actions2 = resp2.json().get("actions", [])
    assert len(actions2) == 0
