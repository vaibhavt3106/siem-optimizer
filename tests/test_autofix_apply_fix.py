import sys, os
import pytest
from fastapi.testclient import TestClient

# Ensure project root is on sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, get_db
from db.models import RuleDB, DriftStatsDB
from db.database import SessionLocal


client = TestClient(app)


@pytest.fixture(scope="function")
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_autofix_creates_drift(db):
    rule_id = "Block_Brute_Force"
    if not db.query(RuleDB).filter(RuleDB.id == rule_id).first():
        db.add(RuleDB(id=rule_id, name="Block Brute Force",
                      query="index=auth action=failure | stats count by user",
                      source="Splunk"))
        db.commit()

    response = client.post(f"/rules/{rule_id}/autofix")
    assert response.status_code == 200
    data = response.json()
    assert "suggested_fix" in data

    drift = (db.query(DriftStatsDB)
               .filter(DriftStatsDB.rule_id == rule_id)
               .order_by(DriftStatsDB.last_checked.desc())
               .first())
    assert drift is not None
    assert drift.drift_type == "rule"


def test_apply_fix_creates_drift(db):
    rule_id = "Block_Brute_Force"
    suggested_fix = "index=auth action=failure earliest=-1h latest=now | stats count by user"

    response = client.post(
        f"/rules/{rule_id}/apply_fix",
        json={"suggested_fix": suggested_fix}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["new_query"] == suggested_fix

    drift = (db.query(DriftStatsDB)
               .filter(DriftStatsDB.rule_id == rule_id)
               .order_by(DriftStatsDB.last_checked.desc())
               .first())
    assert drift is not None
    assert drift.drift_type == "rule"

