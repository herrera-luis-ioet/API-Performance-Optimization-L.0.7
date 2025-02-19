"""Test cases for item CRUD operations and caching."""
import pytest
from fastapi import status
from app.core.cache import redis_client

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

@pytest.mark.asyncio
async def test_create_item(authorized_client):
    """Test item creation."""
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
async def test_list_items(authorized_client, test_item):
    """Test listing items."""
    response = await authorized_client.get("/api/v1/items/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(item["id"] == test_item["id"] for item in data)

@pytest.mark.asyncio
async def test_list_items_pagination(authorized_client):
    """Test items pagination."""
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

@pytest.mark.asyncio
async def test_list_items_filter(authorized_client):
    """Test items filtering by title."""
    # Create items with different titles
    await authorized_client.post(
        "/api/v1/items/",
        json={
            "title": "Apple",
            "description": "A fruit"
        }
    )
    await authorized_client.post(
        "/api/v1/items/",
        json={
            "title": "Banana",
            "description": "Another fruit"
        }
    )

    response = await authorized_client.get("/api/v1/items/?title=Apple")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Apple"

@pytest.mark.asyncio
async def test_get_item(authorized_client, test_item):
    """Test getting item by ID."""
    response = await authorized_client.get(f"/api/v1/items/{test_item['id']}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_item["id"]
    assert data["title"] == test_item["title"]
    assert data["description"] == test_item["description"]

@pytest.mark.asyncio
async def test_get_item_not_found(authorized_client):
    """Test getting non-existent item."""
    response = await authorized_client.get("/api/v1/items/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_update_item(authorized_client, test_item):
    """Test updating item."""
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

@pytest.mark.asyncio
async def test_delete_item(authorized_client, test_item):
    """Test deleting item."""
    response = await authorized_client.delete(f"/api/v1/items/{test_item['id']}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify item is deleted
    response = await authorized_client.get(f"/api/v1/items/{test_item['id']}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_item_not_found(authorized_client):
    """Test deleting non-existent item."""
    response = await authorized_client.delete("/api/v1/items/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_item_caching(authorized_client, test_item):
    """Test item caching functionality."""
    # First request should cache the result
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

    # Cache should be invalidated
    assert not await redis_client.exists(cache_key)

    # New request should get updated data
    response = await authorized_client.get(f"/api/v1/items/{test_item['id']}")
    assert response.status_code == status.HTTP_200_OK
    new_response = response.json()
    assert new_response != first_response
    assert new_response["title"] == update_data["title"]