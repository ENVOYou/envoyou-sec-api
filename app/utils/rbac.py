from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from app.utils.jwt import decode_jwt_token

class Role:
    ADMIN = "admin"
    INSPECTOR = "inspector"
    USER = "user"

def extract_roles_from_jwt(token: str) -> List[str]:
    """Extract roles from JWT token claims."""
    try:
        payload = decode_jwt_token(token)
        if not payload:
            return []
        
        # Check for roles in different claim formats
        roles = []
        
        # Standard 'roles' claim
        if 'roles' in payload:
            roles.extend(payload['roles'])
        
        # Supabase 'user_metadata' format
        if 'user_metadata' in payload and 'roles' in payload['user_metadata']:
            roles.extend(payload['user_metadata']['roles'])
        
        # Custom 'role' claim (single role)
        if 'role' in payload:
            roles.append(payload['role'])
            
        return roles
    except Exception:
        return []

def check_role_permission(required_roles: List[str], user_roles: List[str]) -> bool:
    """Check if user has any of the required roles."""
    if not required_roles:  # No roles required
        return True
    return any(role in user_roles for role in required_roles)

def require_roles(required_roles: List[str]):
    """Decorator to require specific roles for endpoint access."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract JWT token from request context
            # This would be set by middleware
            token = getattr(wrapper, '_jwt_token', None)
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_roles = extract_roles_from_jwt(token)
            if not check_role_permission(required_roles, user_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required roles: {required_roles}"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator