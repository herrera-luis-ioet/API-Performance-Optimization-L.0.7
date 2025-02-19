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
        remaining -= 1