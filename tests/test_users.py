"""Test cases for user CRUD operations."""
import pytest
from fastapi import status
from typing import Dict

# Test data
VALID_USER_DATA = {
    "username": "testuser123",
    "email": "test123@example.com",
    "password": "securepass123",
    "full_name": "Test User",
    "is_active": True,
    "is_superuser": False
}

INVALID_USER_DATA = {
    "username": "te",  # Too short
    "email": "invalid-email",
    "password": "short",
    "full_name": "",
    "is_active": True,
    "is_superuser": False
}

@pytest.fixture
def user_data() -> Dict:
    """Fixture to provide valid user data."""
    return VALID_USER_DATA.copy()

# List Users Tests
def test_list_users_superuser(superuser_client, test_user):
    """Test listing users as superuser."""
    response = superuser_client.get("/api/v1/users/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(user["email"] == test_user.email for user in data)

def test_list_users_pagination(superuser_client, test_user):
    """Test users listing with pagination."""
    # Test skip parameter
    response = superuser_client.get("/api/v1/users/?skip=1")
    assert response.status_code == status.HTTP_200_OK
    skip_data = response.json()
    
    # Test limit parameter
    response = superuser_client.get("/api/v1/users/?limit=1")
    assert response.status_code == status.HTTP_200_OK
    limit_data = response.json()
    assert len(limit_data) <= 1

def test_list_users_invalid_pagination(superuser_client):
    """Test users listing with invalid pagination parameters."""
    response = superuser_client.get("/api/v1/users/?skip=-1")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    response = superuser_client.get("/api/v1/users/?limit=0")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_list_users_regular_user(authorized_client):
    """Test listing users as regular user (should fail)."""
    response = authorized_client.get("/api/v1/users/")
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_list_users_unauthorized(client):
    """Test listing users without authorization."""
    response = client.get("/api/v1/users/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# Create User Tests
def test_create_user_success(client, user_data):
    """Test successful user creation with valid data."""
    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "id" in data
    assert "hashed_password" not in data

def test_create_user_validation(client):
    """Test user creation with invalid data."""
    response = client.post("/api/v1/users/", json=INVALID_USER_DATA)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    errors = response.json()["detail"]
    assert any("username" in error["loc"] for error in errors)
    assert any("email" in error["loc"] for error in errors)
    assert any("password" in error["loc"] for error in errors)

def test_create_user_existing_email(client, test_user):
    """Test user creation with existing email."""
    user_data = VALID_USER_DATA.copy()
    user_data["email"] = test_user.email
    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "exists" in response.json()["detail"].lower()

def test_create_user_missing_fields(client):
    """Test user creation with missing required fields."""
    incomplete_data = {"email": "test@example.com"}
    response = client.post("/api/v1/users/", json=incomplete_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# Get User Tests
def test_get_user_by_id_own_profile(authorized_client, test_user):
    """Test getting own user profile."""
    response = authorized_client.get(f"/api/v1/users/{test_user.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == test_user.id
    assert "hashed_password" not in data

def test_get_user_not_found(authorized_client):
    """Test getting non-existent user."""
    response = authorized_client.get("/api/v1/users/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_user_invalid_id(authorized_client):
    """Test getting user with invalid ID format."""
    response = authorized_client.get("/api/v1/users/invalid")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

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

def test_get_user_unauthorized(client, test_user):
    """Test getting user data without authorization."""
    response = client.get(f"/api/v1/users/{test_user.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# Update User Tests
def test_update_user_success(authorized_client, test_user):
    """Test successful user update with valid data."""
    update_data = {
        "full_name": "Updated Name",
        "password": "newpassword123",
        "email": "updated@example.com"
    }
    response = authorized_client.put(
        f"/api/v1/users/{test_user.id}",
        json=update_data
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == update_data["full_name"]
    assert data["email"] == update_data["email"]
    assert "password" not in data
    assert "hashed_password" not in data

def test_update_user_validation(authorized_client, test_user):
    """Test user update with invalid data."""
    invalid_data = {
        "username": "a",  # Too short
        "email": "invalid-email",
        "password": "short"
    }
    response = authorized_client.put(
        f"/api/v1/users/{test_user.id}",
        json=invalid_data
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_update_user_partial(authorized_client, test_user):
    """Test partial user update."""
    update_data = {"full_name": "New Name Only"}
    response = authorized_client.put(
        f"/api/v1/users/{test_user.id}",
        json=update_data
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == update_data["full_name"]
    assert data["email"] == test_user.email  # Unchanged

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

def test_update_user_superuser(superuser_client, test_user):
    """Test updating user as superuser."""
    update_data = {"full_name": "Admin Updated"}
    response = superuser_client.put(
        f"/api/v1/users/{test_user.id}",
        json=update_data
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == update_data["full_name"]

# Delete User Tests
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

def test_delete_user_invalid_id(superuser_client):
    """Test deleting user with invalid ID format."""
    response = superuser_client.delete("/api/v1/users/invalid")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_delete_user_unauthorized(client, test_user):
    """Test deleting user without authorization."""
    response = client.delete(f"/api/v1/users/{test_user.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_delete_own_account_regular_user(authorized_client, test_user):
    """Test user trying to delete their own account (should fail)."""
    response = authorized_client.delete(f"/api/v1/users/{test_user.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN

# Permission Tests
def test_superuser_operations(superuser_client, test_user, user_data):
    """Test comprehensive superuser permissions."""
    # List users
    response = superuser_client.get("/api/v1/users/")
    assert response.status_code == status.HTTP_200_OK
    
    # Create user
    response = superuser_client.post("/api/v1/users/", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    
    # Get other user
    response = superuser_client.get(f"/api/v1/users/{test_user.id}")
    assert response.status_code == status.HTTP_200_OK
    
    # Update other user
    response = superuser_client.put(
        f"/api/v1/users/{test_user.id}",
        json={"full_name": "Updated by Admin"}
    )
    assert response.status_code == status.HTTP_200_OK
    
    # Delete user
    response = superuser_client.delete(f"/api/v1/users/{test_user.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

def test_regular_user_permissions(authorized_client, test_superuser, user_data):
    """Test regular user permission restrictions."""
    # Try to list users
    response = authorized_client.get("/api/v1/users/")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Try to get superuser details
    response = authorized_client.get(f"/api/v1/users/{test_superuser.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Try to update superuser
    response = authorized_client.put(
        f"/api/v1/users/{test_superuser.id}",
        json={"full_name": "Hacked Admin"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Try to delete superuser
    response = authorized_client.delete(f"/api/v1/users/{test_superuser.id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN
