"""Test cases for rate limiting middleware."""
import pytest
import asyncio
from fastapi import status
from app.config import settings

@pytest.fixture
def rate_limit_client(client):
    """Create a client with rate limiting enabled."""
    settings.RATE_LIMIT_ENABLED = True
    settings.RATE_LIMIT_REQUESTS = 5
    settings.RATE_LIMIT_WINDOW = 10
    return client

@pytest.mark.asyncio
async def test_rate_limit_exceeded(rate_limit_client):
    """Test rate limit being exceeded."""
    # Make requests up to the limit
    for _ in range(settings.RATE_LIMIT_REQUESTS):
        response = await rate_limit_client.get("/api/v1/items/")
        assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS
        assert "X-RateLimit-Remaining" in response.headers

    # Next request should be rate limited
    response = await rate_limit_client.get("/api/v1/items/")
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert response.json()["detail"] == "Too many requests. Please try again later."

@pytest.mark.asyncio
async def test_rate_limit_headers(rate_limit_client):
    """Test rate limit headers."""
    response = await rate_limit_client.get("/api/v1/items/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED  # Due to no auth
    
    # Check rate limit headers
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
    
    assert int(response.headers["X-RateLimit-Limit"]) == settings.RATE_LIMIT_REQUESTS
    assert int(response.headers["X-RateLimit-Remaining"]) == settings.RATE_LIMIT_REQUESTS - 1
    assert int(response.headers["X-RateLimit-Reset"]) == settings.RATE_LIMIT_WINDOW

@pytest.mark.asyncio
async def test_rate_limit_window_reset(rate_limit_client):
    """Test rate limit window reset."""
    # Make requests up to the limit
    for _ in range(settings.RATE_LIMIT_REQUESTS):
        response = await rate_limit_client.get("/api/v1/items/")
        assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS

    # Wait for the window to reset
    await asyncio.sleep(settings.RATE_LIMIT_WINDOW)

    # Should be able to make requests again
    response = await rate_limit_client.get("/api/v1/items/")
    assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS

@pytest.mark.asyncio
async def test_rate_limit_disabled(client):
    """Test when rate limiting is disabled."""
    settings.RATE_LIMIT_ENABLED = False
    
    # Make more requests than the limit
    for _ in range(settings.RATE_LIMIT_REQUESTS + 1):
        response = await client.get("/api/v1/items/")
        assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS
        assert "X-RateLimit-Remaining" not in response.headers

@pytest.mark.asyncio
async def test_rate_limit_per_client(rate_limit_client):
    """Test rate limiting is applied per client."""
    # Simulate requests from different IP addresses
    headers1 = {"X-Forwarded-For": "1.2.3.4"}
    headers2 = {"X-Forwarded-For": "5.6.7.8"}

    # Make requests up to the limit for first client
    for _ in range(settings.RATE_LIMIT_REQUESTS):
        response = await rate_limit_client.get("/api/v1/items/", headers=headers1)
        assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS

    # First client should be rate limited
    response = await rate_limit_client.get("/api/v1/items/", headers=headers1)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    # Second client should still be able to make requests
    response = await rate_limit_client.get("/api/v1/items/", headers=headers2)
    assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS

@pytest.mark.asyncio
async def test_rate_limit_remaining_count(rate_limit_client):
    """Test rate limit remaining count decreases correctly."""
    remaining = settings.RATE_LIMIT_REQUESTS
    
    for _ in range(settings.RATE_LIMIT_REQUESTS):
        response = await rate_limit_client.get("/api/v1/items/")
        assert int(response.headers["X-RateLimit-Remaining"]) == remaining - 1
        remaining -= 1"""Test suite for rate limiting middleware."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from redis.exceptions import RedisError
from unittest.mock import patch, MagicMock
from app.middleware.rate_limiter import RateLimitMiddleware
from app.config import settings

@pytest.fixture
def app():
    """Create a test FastAPI application with rate limiting middleware."""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    return app

@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    with patch('app.middleware.rate_limiter.redis_client') as mock:
        # Setup mock time response
        mock.time.return_value = [1000, 0]
        yield mock

def test_basic_rate_limit_enforcement(client, mock_redis):
    """Test basic rate limit enforcement."""
    # Setup mock responses for rate limit checks
    mock_redis.zcard.side_effect = [0] * settings.RATE_LIMIT_REQUESTS + [settings.RATE_LIMIT_REQUESTS]
    mock_redis.zadd.return_value = True
    mock_redis.expire.return_value = True
    mock_redis.zremrangebyscore.return_value = 0
    
    # Make requests up to the limit
    for i in range(settings.RATE_LIMIT_REQUESTS):
        response = client.get("/test")
        assert response.status_code == 200
        assert int(response.headers["X-RateLimit-Remaining"]) == settings.RATE_LIMIT_REQUESTS - i - 1
    
    # Next request should be rate limited
    response = client.get("/test")
    assert response.status_code == 429
    assert response.json()["detail"] == "Too many requests. Please try again later."

def test_rate_limit_headers(client, mock_redis):
    """Test rate limit headers in responses."""
    mock_redis.zcard.return_value = 0
    mock_redis.zadd.return_value = True
    mock_redis.expire.return_value = True
    mock_redis.zremrangebyscore.return_value = 0
    
    response = client.get("/test")
    assert response.status_code == 200
    
    # Verify headers
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
    
    assert int(response.headers["X-RateLimit-Limit"]) == settings.RATE_LIMIT_REQUESTS
    assert int(response.headers["X-RateLimit-Remaining"]) == settings.RATE_LIMIT_REQUESTS - 1
    assert int(response.headers["X-RateLimit-Reset"]) == settings.RATE_LIMIT_WINDOW

def test_sliding_window_behavior(client, mock_redis):
    """Test sliding window behavior for rate limiting."""
    # Setup initial time
    current_time = 1000
    mock_redis.time.return_value = [current_time, 0]
    mock_redis.zcard.return_value = 0
    mock_redis.zadd.return_value = True
    mock_redis.expire.return_value = True
    mock_redis.zremrangebyscore.return_value = 0
    
    # Make initial request
    response = client.get("/test")
    assert response.status_code == 200
    
    # Simulate time passing to just before window expires
    mock_redis.time.return_value = [current_time + settings.RATE_LIMIT_WINDOW - 1, 0]
    response = client.get("/test")
    assert response.status_code == 200
    
    # Simulate time passing beyond window
    mock_redis.time.return_value = [current_time + settings.RATE_LIMIT_WINDOW + 1, 0]
    mock_redis.zcard.return_value = 0  # Old requests should be cleared
    response = client.get("/test")
    assert response.status_code == 200

def test_per_client_rate_limiting(client, mock_redis):
    """Test rate limiting isolation between different clients."""
    mock_redis.zcard.return_value = 0
    mock_redis.zadd.return_value = True
    mock_redis.expire.return_value = True
    mock_redis.zremrangebyscore.return_value = 0
    
    # Test with different client IPs
    headers_client1 = {"X-Forwarded-For": "1.2.3.4"}
    headers_client2 = {"X-Forwarded-For": "5.6.7.8"}
    
    # Both clients should be able to make requests independently
    response1 = client.get("/test", headers=headers_client1)
    assert response1.status_code == 200
    
    response2 = client.get("/test", headers=headers_client2)
    assert response2.status_code == 200
    
    # Verify different rate limit keys were used
    mock_redis.zadd.assert_any_call("rate_limit:1.2.3.4", {"1000": 1000})
    mock_redis.zadd.assert_any_call("rate_limit:5.6.7.8", {"1000": 1000})

def test_redis_failure_handling(client, mock_redis):
    """Test system behavior when Redis is unavailable."""
    mock_redis.zcard.side_effect = RedisError("Connection failed")
    
    # System should still allow requests when Redis fails
    response = client.get("/test")
    assert response.status_code == 200
    assert int(response.headers["X-RateLimit-Remaining"]) == settings.RATE_LIMIT_REQUESTS

def test_rate_limit_bypass(client, mock_redis):
    """Test rate limit bypass when disabled in settings."""
    with patch('app.middleware.rate_limiter.settings.RATE_LIMIT_ENABLED', False):
        # Redis operations should not be called when disabled
        response = client.get("/test")
        assert response.status_code == 200
        mock_redis.zcard.assert_not_called()
        mock_redis.zadd.assert_not_called()
