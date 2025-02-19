"""Test cases for item management endpoints including CRUD operations, caching, and authorization."""
import pytest
from fastapi import status
from app.core.cache import redis_client

# Test fixtures
@pytest.fixture
async def test_item(authorized_client, test_user, db_session):
    """Create a test item."""
    response = await authorized_client.post(
        "/api/v1/items/",
        json={
            "title": "Test Item",
            "description": "Test Description"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

@pytest.fixture
async def other_user_item(async_client, normal_user_auth_headers, db_session):
    """Create a test item owned by another user."""
    response = await async_client.post(
        "/api/v1/items/",
        json={
            "title": "Other User's Item",
            "description": "This item belongs to another user"
        },
        headers=normal_user_auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

# Test item creation
@pytest.mark.asyncio
async def test_create_item_success(authorized_client):
    """Test successful item creation."""
    item_data = {
        "title": "New Item",
        "description": "Item Description"
    }
    response = await authorized_client.post("/api/v1/items/", json=item_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == item_data["title"]
    assert data["description"] == item_data["description"]
    assert "id" in data
    assert "owner_id" in data

@pytest.mark.asyncio
async def test_create_item_invalid_data(authorized_client):
    """Test item creation with invalid data."""
    # Test empty title
    response = await authorized_client.post(
        "/api/v1/items/",
        json={"title": "", "description": "Description"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test missing required field
    response = await authorized_client.post(
        "/api/v1/items/",
        json={"description": "Description"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# Test item listing and filtering
@pytest.mark.asyncio
async def test_list_items_empty(authorized_client):
    """Test listing items when no items exist."""
    response = await authorized_client.get("/api/v1/items/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

@pytest.mark.asyncio
async def test_list_items_with_data(authorized_client, test_item):
    """Test listing items with existing data."""
    response = await authorized_client.get("/api/v1/items/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(item["id"] == test_item["id"] for item in data)

@pytest.mark.asyncio
async def test_list_items_pagination(authorized_client):
    """Test items pagination functionality."""
    # Create multiple items
    items = []
    for i in range(15):
        response = await authorized_client.post(
            "/api/v1/items/",
            json={
                "title": f"Item {i}",
                "description": f"Description {i}"
            }
        )
        items.append(response.json())

    # Test first page
    response = await authorized_client.get("/api/v1/items/?skip=0&limit=10")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 10

    # Test second page
    response = await authorized_client.get("/api/v1/items/?skip=10&limit=10")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 5

    # Test invalid pagination parameters
    response = await authorized_client.get("/api/v1/items/?skip=-1")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    response = await authorized_client.get("/api/v1/items/?limit=0")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    response = await authorized_client.get("/api/v1/items/?limit=101")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_list_items_filter(authorized_client):
    """Test items filtering by title."""
    # Create items with different titles
    items = [
        {"title": "Apple", "description": "A fruit"},
        {"title": "Banana", "description": "Another fruit"},
        {"title": "Apple Pie", "description": "A dessert"}
    ]
    for item in items:
        await authorized_client.post("/api/v1/items/", json=item)

    # Test exact match
    response = await authorized_client.get("/api/v1/items/?title=Apple")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2  # Should match both "Apple" and "Apple Pie"
    assert all("Apple" in item["title"] for item in data)

    # Test case insensitive match
    response = await authorized_client.get("/api/v1/items/?title=apple")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2

    # Test no matches
    response = await authorized_client.get("/api/v1/items/?title=Orange")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0

# Test item retrieval and caching
@pytest.mark.asyncio
async def test_get_item_with_caching(authorized_client, test_item):
    """Test getting item by ID with caching."""
    # First request - should cache the result
    response = await authorized_client.get(f"/api/v1/items/{test_item['id']}")
    assert response.status_code == status.HTTP_200_OK
    first_response = response.json()
    assert first_response["id"] == test_item["id"]
    assert first_response["title"] == test_item["title"]
    assert first_response["description"] == test_item["description"]

    # Verify cache exists
    cache_key = f"item:{test_item['id']}"
    assert await redis_client.exists(cache_key)

    # Second request - should use cache
    response = await authorized_client.get(f"/api/v1/items/{test_item['id']}")
    assert response.status_code == status.HTTP_200_OK
    cached_response = response.json()
    assert cached_response == first_response

@pytest.mark.asyncio
async def test_get_item_not_found(authorized_client):
    """Test getting non-existent item."""
    response = await authorized_client.get("/api/v1/items/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

# Test item updates
@pytest.mark.asyncio
async def test_update_item_success(authorized_client, test_item):
    """Test successful item update."""
    update_data = {
        "title": "Updated Title",
        "description": "Updated Description"
    }
    response = await authorized_client.put(
        f"/api/v1/items/{test_item['id']}",
        json=update_data
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["description"] == update_data["description"]

    # Verify cache is invalidated
    cache_key = f"item:{test_item['id']}"
    assert not await redis_client.exists(cache_key)

@pytest.mark.asyncio
async def test_update_item_partial(authorized_client, test_item):
    """Test partial item update."""
    # Update only title
    response = await authorized_client.put(
        f"/api/v1/items/{test_item['id']}",
        json={"title": "New Title"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "New Title"
    assert data["description"] == test_item["description"]

    # Update only description
    response = await authorized_client.put(
        f"/api/v1/items/{test_item['id']}",
        json={"description": "New Description"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "New Title"  # Should keep the previously updated title
    assert data["description"] == "New Description"

@pytest.mark.asyncio
async def test_update_item_not_owner(authorized_client, other_user_item):
    """Test updating item without ownership."""
    update_data = {
        "title": "Updated Title",
        "description": "Updated Description"
    }
    response = await authorized_client.put(
        f"/api/v1/items/{other_user_item['id']}",
        json=update_data
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_update_item_not_found(authorized_client):
    """Test updating non-existent item."""
    update_data = {
        "title": "Updated Title",
        "description": "Updated Description"
    }
    response = await authorized_client.put(
        "/api/v1/items/99999",
        json=update_data
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

# Test item deletion
@pytest.mark.asyncio
async def test_delete_item_success(authorized_client, test_item):
    """Test successful item deletion."""
    response = await authorized_client.delete(f"/api/v1/items/{test_item['id']}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify item is deleted
    response = await authorized_client.get(f"/api/v1/items/{test_item['id']}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Verify cache is cleared
    cache_key = f"item:{test_item['id']}"
    assert not await redis_client.exists(cache_key)

@pytest.mark.asyncio
async def test_delete_item_not_owner(authorized_client, other_user_item):
    """Test deleting item without ownership."""
    response = await authorized_client.delete(f"/api/v1/items/{other_user_item['id']}")
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Verify item still exists
    response = await authorized_client.get(f"/api/v1/items/{other_user_item['id']}")
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_delete_item_not_found(authorized_client):
    """Test deleting non-existent item."""
    response = await authorized_client.delete("/api/v1/items/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

# Test caching behavior
@pytest.mark.asyncio
async def test_item_cache_invalidation(authorized_client, test_item):
    """Test cache invalidation on item updates."""
    # Initial request to cache the item
    response = await authorized_client.get(f"/api/v1/items/{test_item['id']}")
    assert response.status_code == status.HTTP_200_OK
    first_response = response.json()

    # Verify cache exists
    cache_key = f"item:{test_item['id']}"
    assert await redis_client.exists(cache_key)

    # Update item
    update_data = {
        "title": "Updated Title",
        "description": "Updated Description"
    }
    response = await authorized_client.put(
        f"/api/v1/items/{test_item['id']}",
        json=update_data
    )
    assert response.status_code == status.HTTP_200_OK

    # Verify cache is invalidated
    assert not await redis_client.exists(cache_key)

    # New request should get fresh data
    response = await authorized_client.get(f"/api/v1/items/{test_item['id']}")
    assert response.status_code == status.HTTP_200_OK
    new_response = response.json()
    assert new_response != first_response
    assert new_response["title"] == update_data["title"]
    assert new_response["description"] == update_data["description"]

@pytest.mark.asyncio
async def test_cache_expiration(authorized_client, test_item):
    """Test cache expiration."""
    # Initial request to cache the item
    response = await authorized_client.get(f"/api/v1/items/{test_item['id']}")
    assert response.status_code == status.HTTP_200_OK

    # Verify cache exists
    cache_key = f"item:{test_item['id']}"
    assert await redis_client.exists(cache_key)

    # Verify TTL is set (should be 300 seconds)
    ttl = await redis_client.ttl(cache_key)
    assert 0 < ttl <= 300
