"""Test configuration and fixtures."""
import asyncio
from typing import AsyncGenerator, Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.user import User

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def db():
    """Session-wide test database."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db):
    """Creates a new database session for a test."""
    connection = db.connection()
    transaction = connection.begin()
    
    try:
        yield db
    finally:
        transaction.rollback()
        connection.close()

@pytest.fixture
def client(db_session):
    """Create a test client with a clean database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LcdYxEGhKgQoAgpX.",  # password = test123
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_superuser(db_session):
    """Create a test superuser."""
    user = User(
        email="admin@example.com",
        username="admin",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LcdYxEGhKgQoAgpX.",  # password = test123
        is_active=True,
        is_superuser=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def user_token(test_user):
    """Create a valid token for test user."""
    return create_access_token(data={"sub": test_user.username})

@pytest.fixture
def superuser_token(test_superuser):
    """Create a valid token for test superuser."""
    return create_access_token(data={"sub": test_superuser.username})

@pytest.fixture
def authorized_client(client, user_token):
    """Create a test client with user authorization."""
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {user_token}"
    }
    return client

@pytest.fixture
def superuser_client(client, superuser_token):
    """Create a test client with superuser authorization."""
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {superuser_token}"
    }
    return client