from sqlalchemy import Column, Integer, String, JSON, DateTime
from datetime import datetime
from db.database import Base

class SchemaRegistryDB(Base):
    __tablename__ = "schema_registry"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source = Column(String, index=True)   # Splunk / Sentinel / OEM
    schema = Column(JSON)                 # store fields as JSON
    version = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)
