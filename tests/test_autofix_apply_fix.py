import pytest
from fastapi.testclient import TestClient
from app import app
from db.models import RuleDB

client = TestClient(app)


def test_autofix_creates_drift(db):
    rule_id = "Block_Brute_Force"
    # Ensure the rule exists in DB
    if not db.query(RuleDB).filter(RuleDB.id == rule_id).first():
        db.add(RuleDB(
            id=rule_id,
            name="Block Brute Force",
            query="index=auth action=failure | stats count by user",
            source="Splunk"
        ))
        db.commit()

    response = client.post(f"/rules/{rule_id}/autofix")
    assert response.status_code == 200
    body = response.json()
    assert body["rule_id"] == rule_id
    assert "suggested_fix" in body
    assert "drift" in body


def test_apply_fix_creates_drift(db):
    rule_id = "Block_Brute_Force"
    suggested_fix = "index=auth action=failure | stats count by user | where count > 5"

    response = client.post(
        f"/rules/{rule_id}/apply_fix",
        json={"suggested_fix": suggested_fix},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["rule_id"] == rule_id
    assert body["new_query"] == suggested_fix
    assert "drift" in body
