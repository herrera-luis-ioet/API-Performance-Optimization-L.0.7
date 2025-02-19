"""Test cases for user CRUD operations."""
import pytest
from fastapi import status

def test_list_users_superuser(superuser_client, test_user):
    """Test listing users as superuser."""
    response = superuser_client.get("/api/v1/users/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(user["email"] == test_user.email for user in data)

def test_list_users_regular_user(authorized_client):
    """Test listing users as regular user (should fail)."""
    response = authorized_client.get("/api/v1/users/")
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_list_users_unauthorized(client):
    """Test listing users without authorization."""
    response = client.get("/api/v1/users/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_create_user(client):
    """Test user creation."""
    user_data = {
        "email": "newuser@example.com",
        "password": "testpass123",
        "full_name": "New User",
        "is_superuser": False
    }
    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert data["is_superuser"] == user_data["is_superuser"]
    assert "id" in data
    assert "hashed_password" not in data

def test_create_user_existing_email(client, test_user):
    """Test user creation with existing email."""
    user_data = {
        "email": test_user.email,
        "password": "testpass123",
        "full_name": "Another User",
        "is_superuser": False
    }
    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "exists" in response.json()["detail"].lower()

def test_get_user_by_id(authorized_client, test_user):
    """Test getting user by ID."""
    response = authorized_client.get(f"/api/v1/users/{test_user.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == test_user.id

def test_get_user_not_found(authorized_client):
    """Test getting non-existent user."""
    response = authorized_client.get("/api/v1/users/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_other_user_regular_user(authorized_client, test_superuser):
    """Test getting another user's data as regular user (should fail)."""
    response = authorized_client.get(f"/api/v1/users/{test_superuser.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_get_other_user_superuser(superuser_client, test_user):
    """Test getting another user's data as superuser."""
    response = superuser_client.get(f"/api/v1/users/{test_user.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_user.email

def test_update_user(authorized_client, test_user):
    """Test updating user."""
    update_data = {
        "full_name": "Updated Name",
        "password": "newpassword123"
    }
    response = authorized_client.put(
        f"/api/v1/users/{test_user.id}",
        json=update_data
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == update_data["full_name"]
    assert "password" not in data

def test_update_other_user(authorized_client, test_superuser):
    """Test updating another user's data (should fail)."""
    update_data = {"full_name": "Hacked Name"}
    response = authorized_client.put(
        f"/api/v1/users/{test_superuser.id}",
        json=update_data
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_update_user_not_found(authorized_client):
    """Test updating non-existent user."""
    update_data = {"full_name": "Nobody"}
    response = authorized_client.put(
        "/api/v1/users/99999",
        json=update_data
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_user_superuser(superuser_client, test_user):
    """Test deleting user as superuser."""
    response = superuser_client.delete(f"/api/v1/users/{test_user.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify user is deleted
    response = superuser_client.get(f"/api/v1/users/{test_user.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_user_regular_user(authorized_client, test_superuser):
    """Test deleting user as regular user (should fail)."""
    response = authorized_client.delete(f"/api/v1/users/{test_superuser.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_delete_user_not_found(superuser_client):
    """Test deleting non-existent user."""
    response = superuser_client.delete("/api/v1/users/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND