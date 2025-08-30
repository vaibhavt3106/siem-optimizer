# tests/conftest.py
import sys, os, tempfile, pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

# --- Ensure project root in path ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Test DB ---
temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
temp_db.close()
TEST_DATABASE_URL = f"sqlite:///{temp_db.name}"

os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

import db.database
db.database.engine = engine
db.database.SessionLocal = TestingSessionLocal

from db.database import Base
from db.models import RuleDB
import app
from app import get_db

app_instance = app.app

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app_instance.dependency_overrides[get_db] = override_get_db

# --- Fixtures ---
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    # Insert baseline rules once for all tests
    db = TestingSessionLocal()
    for rid, name, query in [
        ("Block_Brute_Force", "Block Brute Force", "index=auth action=failure | stats count by user"),
        ("Rare_Process_Spawn", "Rare Process Spawn", "index=proc parent=cmd.exe | stats count by process_name"),
    ]:
        if not db.query(RuleDB).filter(RuleDB.id == rid).first():
            db.add(RuleDB(id=rid, name=name, query=query, source="Splunk"))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)
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
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Provide explicit sample_rules for tests that request it
@pytest.fixture
def sample_rules(db):
    return db.query(RuleDB).all()

# --- Mock OpenAI ---
@pytest.fixture(autouse=True)
def mock_openai():
    import app
    app.client = MagicMock()
    fake_choice = MagicMock()
    fake_choice.message.content = "mocked fix"
    app.client.chat.completions.create.return_value = MagicMock(choices=[fake_choice])
    yield app.client
