from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.rbac import extract_roles_from_jwt

class RBACMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and validate JWT roles."""
    
    async def dispatch(self, request: Request, call_next):
        # Extract JWT token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            
            # Extract roles and add to request state
            roles = extract_roles_from_jwt(token)
            request.state.user_roles = roles
            request.state.jwt_token = token
        else:
            request.state.user_roles = []
            request.state.jwt_token = None
        
        response = await call_next(request)
        return response