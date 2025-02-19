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
    assert response.status_code == status.HTTP_200_OK"""Test cases for authentication endpoints."""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User

def test_successful_registration(test_client: TestClient, db_session: Session):
    """Test successful user registration."""
    user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "testpass123"
    }
    response = test_client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "id" in data
    assert data["is_active"] is True

def test_duplicate_username_registration(test_client: TestClient, normal_user: User):
    """Test registration with duplicate username."""
    user_data = {
        "username": "testuser",  # Same as normal_user fixture
        "email": "another@example.com",
        "password": "testpass123"
    }
    response = test_client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Username already registered" in response.json()["detail"]

def test_duplicate_email_registration(test_client: TestClient, normal_user: User):
    """Test registration with duplicate email."""
    user_data = {
        "username": "anotheruser",
        "email": "test@example.com",  # Same as normal_user fixture
        "password": "testpass123"
    }
    response = test_client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email already registered" in response.json()["detail"]

def test_invalid_email_format(test_client: TestClient):
    """Test registration with invalid email format."""
    user_data = {
        "username": "newuser",
        "email": "invalid-email",
        "password": "testpass123"
    }
    response = test_client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_missing_required_fields(test_client: TestClient):
    """Test registration with missing required fields."""
    user_data = {
        "username": "newuser"
        # Missing email and password
    }
    response = test_client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_successful_login(test_client: TestClient, normal_user: User):
    """Test successful user login."""
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    response = test_client.post(
        "/api/v1/auth/login",
        data=login_data,  # Use data instead of json for form data
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_invalid_credentials_login(test_client: TestClient):
    """Test login with invalid credentials."""
    login_data = {
        "username": "testuser",
        "password": "wrongpassword"
    }
    response = test_client.post(
        "/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect username or password" in response.json()["detail"]

def test_nonexistent_user_login(test_client: TestClient):
    """Test login with non-existent user."""
    login_data = {
        "username": "nonexistent",
        "password": "testpass123"
    }
    response = test_client.post(
        "/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect username or password" in response.json()["detail"]

def test_successful_token_refresh(test_client: TestClient, normal_user_auth_headers: dict):
    """Test successful token refresh."""
    response = test_client.post(
        "/api/v1/auth/refresh-token",
        headers=normal_user_auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_invalid_token_refresh(test_client: TestClient):
    """Test token refresh with invalid token."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = test_client.post("/api/v1/auth/refresh-token", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in response.json()["detail"]

def test_expired_token_refresh(test_client: TestClient):
    """Test token refresh with expired token."""
    # Note: This test might need additional setup to create an expired token
    expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTUxNjIzOTAyMn0.4Auv2aMfz2dHZ7-bshEAj3hp_HlcQOWLDN8EuNMTcqY"
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = test_client.post("/api/v1/auth/refresh-token", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in response.json()["detail"]

def test_missing_token_refresh(test_client: TestClient):
    """Test token refresh without token."""
    response = test_client.post("/api/v1/auth/refresh-token")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Not authenticated" in response.json()["detail"]
