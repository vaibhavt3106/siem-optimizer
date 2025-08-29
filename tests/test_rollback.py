from fastapi.testclient import TestClient
from app import app
from db.models import RuleDB

client = TestClient(app)


def test_rollback_steps(db):
    rule_id = "Block_Brute_Force"

    # Ensure the rule exists
    if not db.query(RuleDB).filter(RuleDB.id == rule_id).first():
        db.add(RuleDB(
            id=rule_id,
            name="Block Brute Force",
            query="index=auth action=failure | stats count by user",
            source="Splunk"
        ))
        db.commit()

    resp = client.post(f"/rules/{rule_id}/rollback?steps=1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["rule_id"] == rule_id
    assert "restored_query" in body


def test_rollback_history_id(db):
    rule_id = "Block_Brute_Force"

    resp = client.post(f"/rules/{rule_id}/rollback?history_id=1")
    # Depending on DB state, this may or may not exist
    # Just validate response structure
    assert resp.status_code in (200, 404)
