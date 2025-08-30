from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, case
from typing import Optional
from datetime import datetime, timedelta
import random
import pandas as pd
import os

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Connectors
from connectors.splunk_connector import SplunkConnector
from connectors.sentinel_connector import SentinelConnector

# Core
from core.drift_engine import analyze_rule
from core.models import Rule, SchemaRegistry, SchemaRequest

# Database
from db.database import SessionLocal, engine, Base
from db.models import RuleDB, DriftStatsDB, RuleHistoryDB
from db.schema_registry import SchemaRegistryDB

# Utils
from core.schema_utils import diff_schemas

# --------------------------------------------------
# OpenAI Setup
# --------------------------------------------------
client = None
try:
    import openai  # <-- expose for tests
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key != "dummy-key-for-tests":
        client = OpenAI(api_key=api_key)
except ImportError:
    openai = None  # still expose name

from pydantic import BaseModel

# --------------------------------------------------
# FastAPI app
# --------------------------------------------------
app = FastAPI(title="Next-Gen SIEM Optimizer")

# Create tables (skip in test mode)
if not os.getenv("TESTING"):
    Base.metadata.create_all(bind=engine)

# Export Base for tests
__all__ = ["app", "Base", "get_db"]

# --------------------------------------------------
# DB Session Dependency
# --------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------------------------------------------------
# Connectors
# --------------------------------------------------
splunk = SplunkConnector(
    base_url="https://splunk-instance:8089",
    username="admin",
    password="password"
)

sentinel = SentinelConnector(
    base_url="https://management.azure.com",
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-secret"
)

# --------------------------------------------------
# System
# --------------------------------------------------
@app.get("/health", summary="Health Check", tags=["System"])
def health_check():
    return {"status": "ok"}

# --------------------------------------------------
# Rules
# --------------------------------------------------
@app.get("/rules", summary="List Detection Rules", tags=["Rules"])
def list_rules(db: Session = Depends(get_db)):
    rules = splunk.get_rules()
    for r in rules:
        if not db.query(RuleDB).filter(RuleDB.id == r["id"]).first():
            new_rule = RuleDB(
                id=r["id"],
                name=r["id"].replace("_", " ").title(),
                query=r["query"],
                source="Splunk"
            )
            db.add(new_rule)
    db.commit()
    return db.query(RuleDB).all()

@app.get("/rules/{rule_id}/drift", summary="Check Rule Drift", tags=["Drift Analysis"])
def check_rule_drift(rule_id: str, db: Session = Depends(get_db)):
    fp_rate = round(random.uniform(0, 0.5), 2)
    tp_rate = round(random.uniform(0, 1.0), 2)
    alert_volume = random.randint(0, 500)
    drift_score = round(fp_rate * 5 + (1 - tp_rate) * 5 + (alert_volume / 100), 2)

    drift_db = DriftStatsDB(
        rule_id=rule_id,
        fp_rate=fp_rate,
        tp_rate=tp_rate,
        alert_volume=alert_volume,
        drift_score=drift_score,
        last_checked=datetime.utcnow(),
        drift_type="rule"
    )
    db.add(drift_db)
    db.commit()
    db.refresh(drift_db)

    return {
        "id": drift_db.id,
        "rule_id": drift_db.rule_id,
        "fp_rate": drift_db.fp_rate,
        "tp_rate": drift_db.tp_rate,
        "alert_volume": drift_db.alert_volume,
        "drift_score": drift_db.drift_score,
        "last_checked": drift_db.last_checked,
        "drift_type": drift_db.drift_type
    }

# --------------------------------------------------
# Schema Registry
# --------------------------------------------------
@app.post("/schema/{source}", response_model=SchemaRegistry, tags=["Schema Registry"])
def store_schema(source: str, body: SchemaRequest, version: str, db: Session = Depends(get_db)):
    entry = SchemaRegistryDB(source=source, schema=body.schema_data, version=version)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

@app.get("/schema/{source}", response_model=SchemaRegistry, tags=["Schema Registry"])
def get_latest_schema(source: str, db: Session = Depends(get_db)):
    entry = (
        db.query(SchemaRegistryDB)
        .filter(SchemaRegistryDB.source == source)
        .order_by(SchemaRegistryDB.last_updated.desc())
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail=f"No schema found for {source}")
    return entry

@app.get("/schema/{source}/history", response_model=list[SchemaRegistry], tags=["Schema Registry"])
def get_schema_history(source: str, db: Session = Depends(get_db)):
    return (
        db.query(SchemaRegistryDB)
        .filter(SchemaRegistryDB.source == source)
        .order_by(SchemaRegistryDB.last_updated.desc())
        .all()
    )

@app.get("/schema/{source}/diff", tags=["Schema Registry"])
def schema_diff(source: str, from_version: str, to_version: str, db: Session = Depends(get_db)):
    from_schema = db.query(SchemaRegistryDB).filter_by(source=source, version=from_version).first()
    to_schema = db.query(SchemaRegistryDB).filter_by(source=source, version=to_version).first()

    if not from_schema or not to_schema:
        return {"error": f"Schemas not found for versions {from_version} and {to_version}"}

    diff = diff_schemas(from_schema.schema["schema"], to_schema.schema["schema"])

    drift_record = DriftStatsDB(
        rule_id=None,
        fp_rate=0.0,
        tp_rate=0.0,
        alert_volume=0,
        drift_score=len(diff["added"]) + len(diff["removed"]),
        drift_type="schema"
    )
    db.add(drift_record)
    db.commit()
    db.refresh(drift_record)

    return {"diff": diff, "drift_event_id": drift_record.id, "drift_score": drift_record.drift_score}

# --------------------------------------------------
# Multi-SIEM
# --------------------------------------------------
@app.get("/siems", summary="List Supported SIEMs", tags=["SIEM"])
def list_siems():
    return {"supported_siems": ["Splunk", "Sentinel"]}

@app.get("/siem/{name}/rules", summary="List Rules from a SIEM", tags=["SIEM"])
def list_siem_rules(name: str):
    if name.lower() == "splunk":
        return splunk.get_rules()
    elif name.lower() == "sentinel":
        return sentinel.get_rules()
    else:
        return {"error": f"SIEM '{name}' not supported"}

# --------------------------------------------------
# Rule Fix/Autofix/Rollback
# --------------------------------------------------
class ApplyFixRequest(BaseModel):
    suggested_fix: str

@app.post("/rules/{rule_id}/autofix", tags=["Rules"])
def autofix_rule(rule_id: str, db: Session = Depends(get_db)):
    if not client:
        raise HTTPException(status_code=503, detail="OpenAI client not configured. Set OPENAI_API_KEY environment variable.")

    rule = db.query(RuleDB).filter(RuleDB.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a SIEM detection engineer. Return ONLY the fixed SIEM query as plain text."},
                {"role": "user", "content": f"Fix this SIEM rule query:\n{rule.query}"}
            ],
            temperature=0.3
        )
        fixed_query = response.choices[0].message.content.strip()
        db.add(RuleHistoryDB(rule_id=rule_id, query=rule.query, action="autofix"))
        rule.query = fixed_query
        db.commit()
        db.refresh(rule)

        fp_rate = round(random.uniform(0, 0.5), 2)
        tp_rate = round(random.uniform(0, 1.0), 2)
        alert_volume = random.randint(0, 500)
        drift_score = round(fp_rate * 5 + (1 - tp_rate) * 5 + (alert_volume / 100), 2)

        drift_db = DriftStatsDB(
            rule_id=rule_id, fp_rate=fp_rate, tp_rate=tp_rate,
            alert_volume=alert_volume, drift_score=drift_score,
            last_checked=datetime.utcnow(), drift_type="rule"
        )
        db.add(drift_db)
        db.commit()

        return {"rule_id": rule_id, "original_query": rule.query, "suggested_fix": fixed_query,
                "drift": {"fp_rate": fp_rate, "tp_rate": tp_rate, "alert_volume": alert_volume,
                          "drift_score": drift_score, "last_checked": datetime.utcnow(), "drift_type": "rule"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")

# (apply_fix, rollback, drift endpoints remain same as your version)
# --------------------------------------------------
# [Keep the rest of your endpoints unchanged]
# --------------------------------------------------
# --------------------------------------------------
# Apply Fix
# --------------------------------------------------
class ApplyFixRequest(BaseModel):
    suggested_fix: str

@app.post("/rules/{rule_id}/apply_fix", tags=["Rules"])
def apply_fix(rule_id: str, body: ApplyFixRequest, db: Session = Depends(get_db)):
    rule = db.query(RuleDB).filter(RuleDB.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    sanitized_query = body.suggested_fix.strip()
    if sanitized_query.startswith("```"):
        sanitized_query = sanitized_query.strip("`").replace("spl\n", "").strip()

    db.add(RuleHistoryDB(rule_id=rule_id, query=rule.query, action="apply_fix"))
    previous_query = rule.query
    rule.query = sanitized_query
    db.commit()
    db.refresh(rule)

    # --- Add drift stats like autofix ---
    fp_rate = round(random.uniform(0, 0.5), 2)
    tp_rate = round(random.uniform(0, 1.0), 2)
    alert_volume = random.randint(0, 500)
    drift_score = round(fp_rate * 5 + (1 - tp_rate) * 5 + (alert_volume / 100), 2)

    drift_db = DriftStatsDB(
        rule_id=rule_id,
        fp_rate=fp_rate,
        tp_rate=tp_rate,
        alert_volume=alert_volume,
        drift_score=drift_score,
        last_checked=datetime.utcnow(),
        drift_type="rule"
    )
    db.add(drift_db)
    db.commit()

    return {
        "rule_id": rule_id,
        "previous_query": previous_query,
        "new_query": sanitized_query,
        "message": "Rule updated with suggested fix",
        "drift": {
            "fp_rate": fp_rate,
            "tp_rate": tp_rate,
            "alert_volume": alert_volume,
            "drift_score": drift_score,
            "last_checked": datetime.utcnow(),
            "drift_type": "rule"
        }
    }


# --------------------------------------------------
# Rollback
# --------------------------------------------------
@app.post("/rules/{rule_id}/rollback", tags=["Rules"])
def rollback_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    steps: int = Query(1, ge=1),
    history_id: Optional[int] = Query(None)
):
    rule = db.query(RuleDB).filter(RuleDB.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    query = db.query(RuleHistoryDB).filter(RuleHistoryDB.rule_id == rule_id)

    if history_id:
        target = query.filter(RuleHistoryDB.id == history_id).first()
        if not target:
            raise HTTPException(status_code=404, detail=f"No history entry with id {history_id}")
    else:
        history_entries = query.order_by(RuleHistoryDB.timestamp.desc()).all()
        if len(history_entries) < steps:
            raise HTTPException(status_code=400, detail=f"Not enough history entries (only {len(history_entries)} available)")
        target = history_entries[steps - 1]

    db.add(RuleHistoryDB(rule_id=rule_id, query=rule.query, action="rollback"))
    rule.query = target.query
    db.commit()
    db.refresh(rule)

    return {
        "rule_id": rule_id,
        "restored_query": rule.query,
        "rolled_back_to": target.id,
        "steps_back": steps if not history_id else None,
        "message": "Rollback applied successfully"
    }

# --------------------------------------------------
# Rule History
# --------------------------------------------------
@app.get("/rules/{rule_id}/history", tags=["Rules"])
def get_rule_history(rule_id: str, db: Session = Depends(get_db)):
    history = (
        db.query(RuleHistoryDB)
        .filter(RuleHistoryDB.rule_id == rule_id)
        .order_by(RuleHistoryDB.timestamp.desc())
        .all()
    )
    return [
        {"query": h.query, "action": h.action, "timestamp": h.timestamp}
        for h in history
    ]

# --------------------------------------------------
# Drift Analysis
# --------------------------------------------------
@app.get("/drift/history", tags=["Drift Analysis"])
def drift_history(db: Session = Depends(get_db)):
    return {"events": db.query(DriftStatsDB).all()}

@app.get("/drift/dashboard", tags=["Drift Analysis"])
def drift_dashboard(db: Session = Depends(get_db)):
    total_events = db.query(DriftStatsDB).count()
    schema_drifts = db.query(DriftStatsDB).filter(DriftStatsDB.drift_type == "schema").count()
    rule_drifts = db.query(DriftStatsDB).filter(DriftStatsDB.drift_type == "rule").count()
    avg_drift_score = db.query(func.avg(DriftStatsDB.drift_score)).scalar() or 0

    low = db.query(DriftStatsDB).filter(DriftStatsDB.drift_score > 0, DriftStatsDB.drift_score <= 2).count()
    medium = db.query(DriftStatsDB).filter(DriftStatsDB.drift_score > 2, DriftStatsDB.drift_score <= 5).count()
    high = db.query(DriftStatsDB).filter(DriftStatsDB.drift_score > 5).count()

    return {
        "total_events": total_events,
        "schema_drifts": schema_drifts,
        "rule_drifts": rule_drifts,
        "avg_drift_score": round(avg_drift_score, 2),
        "severity_buckets": {"low": low, "medium": medium, "high": high}
    }

