"""Test configuration and fixtures."""
import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from redis import asyncio as aioredis

from app.core.security import get_password_hash, create_access_token
from app.main import app
from app.config import Settings
from app.models.user import User
from app.models.base import Base

# Test settings
settings = Settings()
settings.DATABASE_URL = "sqlite+aiosqlite:///./test.db"
settings.REDIS_URL = "redis://localhost:6379/1"  # Use a different Redis DB for testing

# Create async engine for testing
test_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

# Create test session factory
test_async_session = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create Redis test client
test_redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Create a test database engine."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Get a test database session."""
    async with test_async_session() as session:
        yield session
        await session.rollback()
        await session.close()

@pytest_asyncio.fixture(scope="session")
async def redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    """Get a test Redis client."""
    await test_redis.flushdb()  # Clear test database
    yield test_redis
    await test_redis.flushdb()  # Clean up after tests
    await test_redis.close()

@pytest.fixture(scope="module")
def test_app():
    """Create a test FastAPI application."""
    return app

@pytest.fixture(scope="module")
def test_client(test_app):
    """Create a test client using the test application."""
    return TestClient(test_app)

@pytest_asyncio.fixture(scope="module")
async def async_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client using the test application."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture(scope="function")
async def normal_user(db_session: AsyncSession) -> User:
    """Create a normal test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        is_superuser=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture(scope="function")
async def superuser(db_session: AsyncSession) -> User:
    """Create a superuser test user."""
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        is_superuser=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def normal_user_token(normal_user: User) -> str:
    """Create an authentication token for the normal test user."""
    return create_access_token({"sub": normal_user.username})

@pytest.fixture(scope="function")
def superuser_token(superuser: User) -> str:
    """Create an authentication token for the superuser test user."""
    return create_access_token({"sub": superuser.username})

@pytest.fixture(scope="function")
def normal_user_auth_headers(normal_user_token: str) -> dict:
    """Create authentication headers for the normal test user."""
    return {"Authorization": f"Bearer {normal_user_token}"}

@pytest.fixture(scope="function")
def superuser_auth_headers(superuser_token: str) -> dict:
    """Create authentication headers for the superuser test user."""
    return {"Authorization": f"Bearer {superuser_token}"}

# Helper functions for test data generation
def create_test_item_data(owner_id: int = None) -> dict:
    """Create test data for an item."""
    return {
        "title": "Test Item",
        "description": "This is a test item",
        "owner_id": owner_id
    }

def create_test_user_data() -> dict:
    """Create test data for a user."""
    return {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "newpass123"
    }