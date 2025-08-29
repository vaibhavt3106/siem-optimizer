from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

class Rule(BaseModel):
    id: str
    name: str
    query: str
    source: str

from typing import Optional

class DriftStats(BaseModel):
    id: Optional[int] = None
    rule_id: Optional[str] = None
    fp_rate: float
    tp_rate: float
    alert_volume: int
    drift_score: float
    last_checked: datetime
    drift_type: str


class SchemaRequest(BaseModel):
    schema_def: Dict[str, Any]   # ✅ renamed from schema → schema_def

class SchemaRegistry(BaseModel):
    source: str
    schema_def: Dict[str, Any]   # ✅ same rename here
    version: str
    last_updated: datetime





