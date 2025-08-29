# tests/conftest.py
import sys, os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# --- Ensure project root is in sys.path ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set testing environment first - use file-based SQLite so app and tests share same DB
import tempfile
temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
temp_db.close()
TEST_DATABASE_URL = f"sqlite:///{temp_db.name}"

os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Create test engine BEFORE importing anything else
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the database module BEFORE importing app to prevent original engine creation
import db.database
db.database.engine = engine
db.database.SessionLocal = TestingSessionLocal

# Now import database components
from db.database import Base
from db.models import RuleDB, RuleHistoryDB, DriftStatsDB

# Import app after overriding database
import app
from app import get_db

# FastAPI app instance
app_instance = app.app

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override the database dependency
app_instance.dependency_overrides[get_db] = override_get_db

# --- Fixtures ---
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all database tables for testing"""
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup: Drop tables and remove temp file
    Base.metadata.drop_all(bind=engine)
    import os
    try:
        os.unlink(temp_db.name)
    except:
        pass

@pytest.fixture
def client():
    with TestClient(app_instance) as c:
        yield c

@pytest.fixture
def db():
    """Create a database session for testing"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def sample_rules():
    """Create sample rules for testing"""
    db = TestingSessionLocal()
    try:
        # Check if rules already exist, if not create them
        existing_rule1 = db.query(RuleDB).filter(RuleDB.id == "Block_Brute_Force").first()
        existing_rule2 = db.query(RuleDB).filter(RuleDB.id == "Rare_Process_Spawn").first()
        
        if not existing_rule1:
            rule1 = RuleDB(
                id="Block_Brute_Force",
                name="Block Brute Force", 
                query="index=auth action=failure | stats count by user",
                source="Splunk"
            )
            db.add(rule1)
        else:
            rule1 = existing_rule1
            
        if not existing_rule2:
            rule2 = RuleDB(
                id="Rare_Process_Spawn",
                name="Rare Process Spawn",
                query="index=proc parent=cmd.exe | stats count by process_name", 
                source="Splunk"
            )
            db.add(rule2)
        else:
            rule2 = existing_rule2
            
        db.commit()
        yield [rule1, rule2]
    finally:
        db.close()
