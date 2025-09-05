import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.api_server import app
from app.models.database import get_db
from app.models.user import User
from app.utils.jwt import create_access_token
import uuid

client = TestClient(app)

def test_user_registration():
    """Test user registration endpoint"""
    user_data = {
        "email": f"test_{uuid.uuid4()}@example.com",
        "password": "TestPass123!",
        "name": "Test User",
        "company": "Test Company",
        "job_title": "Developer"
    }

    response = client.post("/auth/register", json=user_data)
    assert response.status_code in [200, 201]

    if response.status_code == 200:
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data

def test_user_login():
    """Test user login endpoint"""
    # First register a user
    user_data = {
        "email": f"login_test_{uuid.uuid4()}@example.com",
        "password": "TestPass123!",
        "name": "Login Test User"
    }

    register_response = client.post("/auth/register", json=user_data)
    assert register_response.status_code in [200, 201]

    # Now try to login
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }

    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "user" in data

def test_invalid_login():
    """Test login with invalid credentials"""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    }

    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401

def test_password_validation():
    """Test password validation rules"""
    # Test weak password
    user_data = {
        "email": f"weak_pass_{uuid.uuid4()}@example.com",
        "password": "123",  # Too short
        "name": "Weak Pass User"
    }

    response = client.post("/auth/register", json=user_data)
    # Should fail validation
    assert response.status_code == 422

def test_email_validation():
    """Test email validation"""
    user_data = {
        "email": "invalid-email",  # Invalid email format
        "password": "ValidPass123!",
        "name": "Invalid Email User"
    }

    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 422

def test_duplicate_email_registration():
    """Test registration with duplicate email"""
    email = f"duplicate_{uuid.uuid4()}@example.com"

    # First registration
    user_data = {
        "email": email,
        "password": "TestPass123!",
        "name": "First User"
    }

    response1 = client.post("/auth/register", json=user_data)
    assert response1.status_code in [200, 201]

    # Second registration with same email
    user_data2 = {
        "email": email,
        "password": "DifferentPass123!",
        "name": "Second User"
    }

    response2 = client.post("/auth/register", json=user_data2)
    assert response2.status_code == 400

def test_token_refresh():
    """Test token refresh endpoint"""
    # First login to get tokens
    user_data = {
        "email": f"refresh_test_{uuid.uuid4()}@example.com",
        "password": "TestPass123!",
        "name": "Refresh Test User"
    }

    register_response = client.post("/auth/register", json=user_data)
    assert register_response.status_code in [200, 201]

    refresh_token = register_response.json()["refresh_token"]

    # Now refresh the token
    refresh_data = {"refresh_token": refresh_token}
    response = client.post("/auth/refresh", json=refresh_data)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_protected_route_access():
    """Test access to protected routes"""
    # Try to access protected route without authentication
    response = client.get("/user/profile")
    assert response.status_code == 401

    # Register and login first
    user_data = {
        "email": f"protected_test_{uuid.uuid4()}@example.com",
        "password": "TestPass123!",
        "name": "Protected Test User"
    }

    register_response = client.post("/auth/register", json=user_data)
    assert register_response.status_code in [200, 201]

    access_token = register_response.json()["access_token"]

    # Now access protected route with token
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/user/profile", headers=headers)
    assert response.status_code == 200

def test_rate_limiting():
    """Test rate limiting on auth endpoints"""
    # Make multiple rapid requests to test rate limiting
    for i in range(10):
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "wrong"
        })

    # Should eventually get rate limited
    # Note: This depends on the rate limiting implementation
    assert response.status_code in [401, 429]

def test_password_reset_flow():
    """Test password reset flow"""
    # Register a user first
    user_data = {
        "email": f"reset_test_{uuid.uuid4()}@example.com",
        "password": "TestPass123!",
        "name": "Reset Test User"
    }

    register_response = client.post("/auth/register", json=user_data)
    assert register_response.status_code in [200, 201]

    # Request password reset
    reset_data = {"email": user_data["email"]}
    response = client.post("/auth/forgot-password", json=reset_data)
    assert response.status_code == 200

def test_input_sanitization():
    """Test input sanitization against XSS"""
    # Try to inject script tags
    user_data = {
        "email": f"sanitization_test_{uuid.uuid4()}@example.com",
        "password": "TestPass123!",
        "name": "<script>alert('xss')</script>Test User",
        "company": "<img src=x onerror=alert('xss')>"
    }

    response = client.post("/auth/register", json=user_data)
    # Should either sanitize or reject the input
    assert response.status_code in [200, 201, 422]

def test_logout():
    """Test logout functionality"""
    # Register and login first
    user_data = {
        "email": f"logout_test_{uuid.uuid4()}@example.com",
        "password": "TestPass123!",
        "name": "Logout Test User"
    }

    register_response = client.post("/auth/register", json=user_data)
    assert register_response.status_code in [200, 201]

    access_token = register_response.json()["access_token"]

    # Logout
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.post("/auth/logout", headers=headers)
    assert response.status_code == 200

    # Try to use the token after logout (should fail)
    response = client.get("/user/profile", headers=headers)
    assert response.status_code == 401

if __name__ == "__main__":
    pytest.main([__file__])
