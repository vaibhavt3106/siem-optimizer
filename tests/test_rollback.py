import sys, os
import pytest
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app, get_db
from db.database import SessionLocal
from db.models import RuleDB, RuleHistoryDB

client = TestClient(app)


@pytest.fixture(scope="function")
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def setup_rule(db):
    """Helper: Insert a test rule into DB if not exists."""
    rule_id = "Rollback_Test_Rule"
    rule = db.query(RuleDB).filter(RuleDB.id == rule_id).first()
    if not rule:
        rule = RuleDB(
            id=rule_id,
            name="Rollback Test Rule",
            query="index=auth action=failure | stats count by user",
            source="Splunk"
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
    return rule_id


def test_rollback_steps(db):
    """Ensure rollback works using steps parameter."""
    rule_id = setup_rule(db)

    # Apply 2 fixes
    client.post(f"/rules/{rule_id}/apply_fix", json={"suggested_fix": "query v1"})
    client.post(f"/rules/{rule_id}/apply_fix", json={"suggested_fix": "query v2"})

    # Rollback 2 steps back
    resp = client.post(f"/rules/{rule_id}/rollback?steps=2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["rule_id"] == rule_id
    assert data["steps_back"] == 2
    assert "restored_query" in data


def test_rollback_history_id(db):
    """Ensure rollback works using history_id parameter."""
    rule_id = setup_rule(db)

    # Apply a fix
    client.post(f"/rules/{rule_id}/apply_fix", json={"suggested_fix": "query v3"})

    # Get history
    history = client.get(f"/rules/{rule_id}/history").json()
    assert len(history) > 0

    target_id = db.query(RuleHistoryDB).filter(RuleHistoryDB.rule_id == rule_id).first().id

    # Rollback to that history_id
    resp = client.post(f"/rules/{rule_id}/rollback?history_id={target_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["rule_id"] == rule_id
    assert data["rolled_back_to"] == target_id

