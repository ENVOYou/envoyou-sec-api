from typing import List
from fastapi import Depends, HTTPException, status, Request
from app.utils.rbac import Role, check_role_permission

def require_roles(required_roles: List[str]):
    """Dependency to require specific roles."""
    def role_checker(request: Request):
        user_roles = getattr(request.state, 'user_roles', [])
        
        if not user_roles:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        if not check_role_permission(required_roles, user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {required_roles}"
            )
        
        return user_roles
    
    return role_checker

def require_admin():
    """Dependency to require admin role."""
    return require_roles([Role.ADMIN])

def require_inspector():
    """Dependency to require inspector or admin role."""
    return require_roles([Role.INSPECTOR, Role.ADMIN])

def require_user():
    """Dependency to require any authenticated user."""
    return require_roles([Role.USER, Role.INSPECTOR, Role.ADMIN])