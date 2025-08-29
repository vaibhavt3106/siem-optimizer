import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from fastapi.testclient import TestClient
import app
from app import app, get_db
from db.database import SessionLocal

client = TestClient(app)

# Fixture for DB session
@pytest.fixture(scope="module")
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

def test_list_rules(db):
    resp = client.get("/rules")
    assert resp.status_code == 200
    rules = resp.json()
    assert isinstance(rules, list)
    assert any("id" in r for r in rules)

def test_autofix_rule():
    resp = client.post("/rules/Block_Brute_Force/autofix")
    assert resp.status_code == 200
    data = resp.json()
    assert "rule_id" in data
    assert "suggested_fix" in data

def test_apply_fix():
    fix = {
        "suggested_fix": "index=auth action=failure earliest=-24h latest=now "
                         "| stats count as failure_count by user "
                         "| where failure_count > 10 "
                         "| sort -failure_count | head 10"
    }
    resp = client.post("/rules/Block_Brute_Force/apply_fix", json=fix)
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "Rule updated with suggested fix"

def test_history():
    resp = client.get("/rules/Block_Brute_Force/history")
    assert resp.status_code == 200
    history = resp.json()
    assert isinstance(history, list)
    assert any("action" in h for h in history)

def test_rollback():
    resp = client.post("/rules/Block_Brute_Force/rollback")
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "Rollback applied successfully"
