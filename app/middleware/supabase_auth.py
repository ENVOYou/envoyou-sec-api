# Supabase JWT Authentication Middleware
import os
import jwt
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from pydantic import BaseModel
from ..config import settings

class SupabaseUser(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    email_verified: bool = False

class SupabaseAuthMiddleware:
    def __init__(self):
        if not settings.SUPABASE_JWT_SECRET:
            raise ValueError("SUPABASE_JWT_SECRET environment variable is required")

    def verify_token(self, token: str) -> SupabaseUser:
        """Verify Supabase JWT token and extract user information"""
        try:
            # Decode JWT token
            # Log minimal token shape
            try:
                header_segment = token.split('.')[0]
                import base64, json
                header_json = json.loads(base64.urlsafe_b64decode(header_segment + '===').decode())
                print(f"[SUPABASE VERIFY] Header alg={header_json.get('alg')} kid={header_json.get('kid')}")
            except Exception as e:  # pragma: no cover
                print(f"[SUPABASE VERIFY] Failed to parse header: {e}")

            # Disable audience verification because Supabase sets aud to authenticated/ or project ref
            # We only care about signature validity here.
            payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"], options={"verify_aud": False})
            aud = payload.get('aud')
            print(f"[SUPABASE VERIFY] Payload keys: {list(payload.keys())[:10]} aud={aud}")

            # Extract user information from token
            user_id = payload.get("sub")
            # Some Supabase tokens may nest email only in user_metadata
            email = payload.get("email") or payload.get("user_metadata", {}).get("email")
            name = payload.get("user_metadata", {}).get("name") or payload.get("user_metadata", {}).get("full_name")
            avatar_url = payload.get("user_metadata", {}).get("avatar_url")
            email_verified = payload.get("email_confirmed_at") is not None

            if not user_id or not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user information"
                )

            return SupabaseUser(
                id=user_id,
                email=email,
                name=name,
                avatar_url=avatar_url,
                email_verified=email_verified
            )

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            # Attempt fallback: maybe this is an internal app JWT, not a Supabase token
            try:
                internal_payload = jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=["HS256"],
                    options={"verify_aud": False}
                )
                print("[SUPABASE VERIFY] Fallback internal JWT accepted")
                user_id = internal_payload.get("sub")
                email = internal_payload.get("email")
                if not user_id or not email:
                    raise ValueError("Missing sub/email in internal token")
                return SupabaseUser(
                    id=user_id,
                    email=email,
                    name=None,
                    avatar_url=None,
                    email_verified=True
                )
            except Exception as ie:
                print(f"[SUPABASE VERIFY] Invalid token error (supabase + internal fallback failed): {e} / {ie}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
        except Exception as e:
            print(f"[SUPABASE VERIFY] Generic verification failure: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(e)}"
            )

    def get_current_user(self, request: Request) -> SupabaseUser:
        """Extract and verify user from Authorization header"""
        authorization = request.headers.get("Authorization")

        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing"
            )

        try:
            scheme, token = authorization.split(" ", 1)
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authorization scheme"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )

        return self.verify_token(token)

# Global middleware instance
supabase_auth = SupabaseAuthMiddleware()

# Dependency for FastAPI routes
def get_current_user(request: Request) -> SupabaseUser:
    """FastAPI dependency to get current authenticated user"""
    return supabase_auth.get_current_user(request)
