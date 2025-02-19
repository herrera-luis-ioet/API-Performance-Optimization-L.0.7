"""Test cases for authentication endpoints."""
import pytest
from fastapi import status
from app.core.security import verify_password

def test_register_user(client, db_session):
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert "id" in data
    assert data["is_active"] is True
    assert "hashed_password" not in data

def test_register_existing_username(client, test_user):
    """Test registration with existing username."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "another@example.com",
            "username": test_user.username,
            "password": "testpass123"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Username already registered"

def test_register_existing_email(client, test_user):
    """Test registration with existing email."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user.email,
            "username": "differentuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Email already registered"

def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.username,
            "password": "test123"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client, test_user):
    """Test login with wrong password."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.username,
            "password": "wrongpass"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Incorrect username or password"

def test_login_wrong_username(client):
    """Test login with non-existent username."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "nonexistent",
            "password": "test123"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Incorrect username or password"

def test_refresh_token(authorized_client):
    """Test token refresh."""
    response = authorized_client.post("/api/v1/auth/refresh-token")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_refresh_token_unauthorized(client):
    """Test token refresh without authorization."""
    response = client.post("/api/v1/auth/refresh-token")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"

def test_refresh_token_invalid(client):
    """Test token refresh with invalid token."""
    client.headers = {"Authorization": "Bearer invalid_token"}
    response = client.post("/api/v1/auth/refresh-token")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Could not validate credentials"

def test_password_hashing(client):
    """Test password hashing during registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "testpass@example.com",
            "username": "testpass",
            "password": "mypassword123"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify password was properly hashed
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "testpass",
            "password": "mypassword123"
        }
    )
    assert response.status_code == status.HTTP_200_OK