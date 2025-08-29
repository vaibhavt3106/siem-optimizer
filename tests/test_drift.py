import pytest
from fastapi.testclient import TestClient
from app import app, get_db
from core.models import DriftStats

client = TestClient(app)


@pytest.fixture(scope="module")
def db():
    db_gen = get_db()
    db = next(db_gen)
    try:
        yield db
    finally:
        db.close()


def test_drift_endpoint(db):
    # Ensure drift stats can be queried for a rule
    rule_id = "Block_Brute_Force"
    resp = client.get(f"/rules/{rule_id}/drift")
    assert resp.status_code == 200
    data = resp.json()
    assert "drift_score" in data
    assert data["rule_id"] == rule_id


def test_drift_history(db):
    # Drift history now returns a dict with "events"
    resp = client.get("/drift/history")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "events" in data
    assert isinstance(data["events"], list)
    if data["events"]:
        first = data["events"][0]
        assert "drift_score" in first
        assert "drift_type" in first


def test_drift_dashboard(db):
    # Dashboard now returns "avg_drift_score"
    resp = client.get("/drift/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "avg_drift_score" in data
    assert "rule_drifts" in data
    assert "schema_drifts" in data


@pytest.mark.skip(reason="Endpoint not implemented in API")
def test_populate_drift(db):
    resp = client.get("/drift/populate")
    assert resp.status_code == 200


@pytest.mark.skip(reason="Endpoint not implemented in API")
def test_drift_trends(db):
    resp = client.get("/drift/trends")
    assert resp.status_code == 200
