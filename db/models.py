from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base


class RuleDB(Base):
    __tablename__ = "rules"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    query = Column(Text)
    source = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationship with history
    history = relationship("RuleHistoryDB", back_populates="rule", cascade="all, delete-orphan")


class DriftStatsDB(Base):
    __tablename__ = "drift_stats"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rule_id = Column(String, index=True)
    fp_rate = Column(Float)
    tp_rate = Column(Float)
    alert_volume = Column(Integer)
    drift_score = Column(Float)
    last_checked = Column(DateTime, default=datetime.utcnow)
    drift_type = Column(String, nullable=False)  # "schema" or "rule"


class RuleHistoryDB(Base):
    __tablename__ = "rule_history"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String, ForeignKey("rules.id"), nullable=False)
    query = Column(Text, nullable=False)
    action = Column(String, nullable=False)  # e.g. "created", "autofix", "apply_fix", "rollback"
    timestamp = Column(DateTime, default=datetime.utcnow)

    rule = relationship("RuleDB", back_populates="history")




