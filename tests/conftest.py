import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app as fastapi_app
from app.db import Base, get_db
import app.db
import app.models # Ensure models are loaded
import app.sync # Ensure sync module loaded for patching
from app.provider_client import ProviderClient

# Use in-memory SQLite with StaticPool so all connections share the same memory DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Monkeypatch the app's SessionLocal to use our test engine/session factory
app.db.SessionLocal = TestingSessionLocal
app.sync.SessionLocal = TestingSessionLocal # Patch imported reference in sync.py

@pytest.fixture(scope="function")
def db():
    # Reset provider rate limits just in case
    from app.provider_mock import reset_ratelimits
    reset_ratelimits()
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
            
    fastapi_app.dependency_overrides[get_db] = override_get_db
    
    # Create a TestClient. This client will be used for making requests to the app.
    # Importantly, we also want the ProviderClient (used internally by sync)
    # to make requests that hit THIS app (specifically the /provider routes).
    # Since ProviderClient uses httpx, we can patch it to return a TestClient 
    # instead of a raw httpx.Client. TestClient inherits from httpx.Client.
    
    test_client = TestClient(fastapi_app, base_url="http://127.0.0.1:8000")
    
    original_get_client = ProviderClient._get_client
    
    def mock_get_client(self):
        # Return a new TestClient instance to ensure thread safety/isolation if needed,
        # or reuse the existing one. For simple synchronous tests, reusing or new is fine.
        # However, TestClient(app) is context-managed? initializing it here is fine.
        return TestClient(fastapi_app, base_url="http://127.0.0.1:8000")
    
    ProviderClient._get_client = mock_get_client
    
    yield test_client
    
    # Teardown
    ProviderClient._get_client = original_get_client
    fastapi_app.dependency_overrides.clear()
