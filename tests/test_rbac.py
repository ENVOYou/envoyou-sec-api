import pytest
from unittest.mock import patch
from app.utils.rbac import extract_roles_from_jwt, check_role_permission, Role

def test_extract_roles_from_jwt():
    """Test extracting roles from JWT token."""
    
    # Mock JWT payload with roles
    mock_payload = {
        "sub": "user123",
        "roles": ["admin", "inspector"],
        "exp": 1234567890
    }
    
    with patch('app.utils.rbac.decode_jwt_token', return_value=mock_payload):
        roles = extract_roles_from_jwt("mock_token")
        assert roles == ["admin", "inspector"]

def test_extract_roles_supabase_format():
    """Test extracting roles from Supabase JWT format."""
    
    mock_payload = {
        "sub": "user123",
        "user_metadata": {
            "roles": ["inspector"]
        },
        "exp": 1234567890
    }
    
    with patch('app.utils.rbac.decode_jwt_token', return_value=mock_payload):
        roles = extract_roles_from_jwt("mock_token")
        assert roles == ["inspector"]

def test_extract_single_role():
    """Test extracting single role claim."""
    
    mock_payload = {
        "sub": "user123",
        "role": "admin",
        "exp": 1234567890
    }
    
    with patch('app.utils.rbac.decode_jwt_token', return_value=mock_payload):
        roles = extract_roles_from_jwt("mock_token")
        assert roles == ["admin"]

def test_extract_roles_invalid_token():
    """Test handling invalid JWT token."""
    
    with patch('app.utils.rbac.decode_jwt_token', return_value=None):
        roles = extract_roles_from_jwt("invalid_token")
        assert roles == []

def test_check_role_permission():
    """Test role permission checking."""
    
    # User has required role
    assert check_role_permission([Role.ADMIN], [Role.ADMIN, Role.USER]) == True
    
    # User has one of multiple required roles
    assert check_role_permission([Role.ADMIN, Role.INSPECTOR], [Role.INSPECTOR]) == True
    
    # User doesn't have required role
    assert check_role_permission([Role.ADMIN], [Role.USER]) == False
    
    # Empty roles
    assert check_role_permission([Role.ADMIN], []) == False
    assert check_role_permission([], [Role.USER]) == True  # No roles required