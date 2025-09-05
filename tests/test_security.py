import pytest
from fastapi.testclient import TestClient
from app.api_server import app
import uuid

client = TestClient(app)

def test_security_headers():
    """Test that security headers are present in responses"""
    response = client.get("/health")

    # Check for security headers
    assert "X-XSS-Protection" in response.headers
    assert "X-Frame-Options" in response.headers
    assert "X-Content-Type-Options" in response.headers
    assert "Strict-Transport-Security" in response.headers
    assert "Referrer-Policy" in response.headers

def test_cors_headers():
    """Test CORS configuration"""
    response = client.options("/health", headers={
        "Origin": "https://api.envoyou.com",
        "Access-Control-Request-Method": "GET"
    })

    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers

def test_xss_protection():
    """Test XSS protection in input sanitization"""
    # Test script tag injection
    xss_payload = "<script>alert('xss')</script>"

    user_data = {
        "email": f"xss_test_{uuid.uuid4()}@example.com",
        "password": "TestPass123!",
        "name": xss_payload,
        "company": "<img src=x onerror=alert('xss')>"
    }

    response = client.post("/auth/register", json=user_data)

    # Should either sanitize or reject
    assert response.status_code in [200, 201, 422]

    if response.status_code == 200:
        # If registration succeeded, check that XSS was sanitized
        data = response.json()
        assert "<script>" not in str(data).lower()
        assert "onerror" not in str(data).lower()

def test_sql_injection_protection():
    """Test SQL injection protection"""
    # Test common SQL injection payloads
    sql_payloads = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "admin'--",
        "' UNION SELECT * FROM users--"
    ]

    for payload in sql_payloads:
        login_data = {
            "email": payload,
            "password": "password"
        }

        response = client.post("/auth/login", json=login_data)
        # Should not succeed with SQL injection
        assert response.status_code != 200

def test_csrf_protection():
    """Test CSRF protection"""
    # Test POST request without CSRF token
    user_data = {
        "email": f"csrf_test_{uuid.uuid4()}@example.com",
        "password": "TestPass123!",
        "name": "CSRF Test User"
    }

    response = client.post("/auth/register", json=user_data)
    # Should work without CSRF for API endpoints
    assert response.status_code in [200, 201]

def test_rate_limit_protection():
    """Test rate limiting protection"""
    # Make multiple requests rapidly
    responses = []
    for i in range(15):
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "wrong"
        })
        responses.append(response.status_code)

    # Should have some rate limited responses
    assert 429 in responses

def test_input_validation():
    """Test input validation"""
    # Test invalid email
    invalid_emails = [
        "invalid-email",
        "@example.com",
        "user@",
        "user.example.com",
        ""
    ]

    for email in invalid_emails:
        user_data = {
            "email": email,
            "password": "ValidPass123!",
            "name": "Test User"
        }

        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 422

def test_password_complexity():
    """Test password complexity requirements"""
    weak_passwords = [
        "123",  # Too short
        "password",  # Too common
        "12345678",  # Only numbers
        "abcdefgh",  # Only lowercase
        "ABCDEFGH",  # Only uppercase
    ]

    for password in weak_passwords:
        user_data = {
            "email": f"weak_{uuid.uuid4()}@example.com",
            "password": password,
            "name": "Weak Password User"
        }

        response = client.post("/auth/register", json=user_data)
        # Should fail validation
        assert response.status_code == 422

def test_jwt_token_security():
    """Test JWT token security"""
    # Register a user
    user_data = {
        "email": f"jwt_test_{uuid.uuid4()}@example.com",
        "password": "TestPass123!",
        "name": "JWT Test User"
    }

    register_response = client.post("/auth/register", json=user_data)
    assert register_response.status_code in [200, 201]

    access_token = register_response.json()["access_token"]

    # Test valid token
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/user/profile", headers=headers)
    assert response.status_code == 200

    # Test invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/user/profile", headers=headers)
    assert response.status_code == 401

    # Test malformed token
    headers = {"Authorization": "InvalidFormat"}
    response = client.get("/user/profile", headers=headers)
    assert response.status_code == 401

def test_api_key_security():
    """Test API key security"""
    # Test with invalid API key
    headers = {"X-API-Key": "invalid_key"}
    response = client.get("/global/emissions", headers=headers)
    assert response.status_code == 401

    # Test with valid demo key
    headers = {"X-API-Key": "demo_key_basic_2025"}
    response = client.get("/global/emissions", headers=headers)
    assert response.status_code == 200

def test_session_security():
    """Test session security features"""
    # Register and login
    user_data = {
        "email": f"session_test_{uuid.uuid4()}@example.com",
        "password": "TestPass123!",
        "name": "Session Test User"
    }

    register_response = client.post("/auth/register", json=user_data)
    assert register_response.status_code in [200, 201]

    access_token = register_response.json()["access_token"]

    # Get sessions
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/user/sessions", headers=headers)
    assert response.status_code == 200

def test_error_handling():
    """Test proper error handling"""
    # Test 404
    response = client.get("/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert "message" in data

    # Test 500 (if we can trigger it)
    # This might be hard to test without breaking the app

def test_content_security_policy():
    """Test Content Security Policy headers"""
    response = client.get("/health")

    # Check for CSP header
    csp_header = response.headers.get("X-Content-Security-Policy")
    assert csp_header is not None
    assert "default-src 'self'" in csp_header

if __name__ == "__main__":
    pytest.main([__file__])
