import sys, os
import pytest
from fastapi.testclient import TestClient

# ✅ Ensure project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app

client = TestClient(app)

def test_drift_endpoint():
    resp = client.get("/rules")
    assert resp.status_code == 200
    rules = resp.json()
    assert len(rules) > 0
    rule_id = rules[0]["id"]

    resp = client.get(f"/rules/{rule_id}/drift")
    assert resp.status_code == 200
    data = resp.json()
    assert data["rule_id"] == rule_id
    assert "drift_score" in data

def test_populate_drift():
    resp = client.post("/test/populate_drift?days=3&events_per_day=2")
    assert resp.status_code == 200
    data = resp.json()
    assert "Inserted" in data["message"]

def test_drift_history():
    resp = client.get("/drift/history")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert isinstance(data["events"], list)

def test_drift_dashboard():
    resp = client.get("/drift/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_events" in data
    assert "schema_drifts" in data
    assert "rule_drifts" in data

def test_drift_trends():
    resp = client.get("/drift/trends-enhanced")
    assert resp.status_code == 200
    data = resp.json()
    assert "window_days" in data
    assert "trends" in data
