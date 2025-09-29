# Supabase JWT Authentication Middleware
import os
import jwt
import logging
import time
import requests
from jose import jwk, jwt as jose_jwt, JWTError
from jose.utils import base64url_decode
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
        # Simple in-memory cache for JWKS
        self._jwks_cache = {
            "keys": None,
            "fetched_at": 0
        }

    def verify_token(self, token: str) -> SupabaseUser:
        """Verify Supabase JWT token and extract user information"""
        try:
            # Decode JWT token
            # Log minimal token shape
            try:
                header_segment = token.split('.')[0]
                import base64, json
                header_json = json.loads(base64.urlsafe_b64decode(header_segment + '===').decode())
                if settings.DEBUG_SUPABASE_AUTH:
                    logging.getLogger(__name__).debug(
                        "[SUPABASE VERIFY] Header alg=%s kid=%s", header_json.get('alg'), header_json.get('kid')
                    )
            except Exception as e:  # pragma: no cover
                if settings.DEBUG_SUPABASE_AUTH:
                    logging.getLogger(__name__).debug("[SUPABASE VERIFY] Failed to parse header: %s", e)

            # Prefer JWKS-based verification if configured (handles key rotation)
            payload = None
            jwks_url = settings.SUPABASE_JWKS_URL
            # If JWKS URL is not set but SUPABASE_URL is, derive the common JWKS location
            if not jwks_url and settings.SUPABASE_URL:
                jwks_url = settings.SUPABASE_URL.rstrip('/') + '/.well-known/jwks.json'

            if jwks_url:
                try:
                    payload = self._verify_with_jwks(token, jwks_url)
                except Exception as e:
                    if settings.DEBUG_SUPABASE_AUTH:
                        logging.getLogger(__name__).debug("[SUPABASE VERIFY] JWKS verification failed: %s", e)

            # If JWKS not used or verification failed, fall back to HS256 with primary then secondary
            if payload is None:
                try:
                    payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"], options={"verify_aud": False})
                except Exception as primary_exc:
                    # Try secondary secret if configured
                    if settings.SUPABASE_JWT_SECRET_SECONDARY:
                        try:
                            payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET_SECONDARY, algorithms=["HS256"], options={"verify_aud": False})
                        except Exception:
                            raise primary_exc
                    else:
                        raise primary_exc
            aud = payload.get('aud')
            if settings.DEBUG_SUPABASE_AUTH:
                logging.getLogger(__name__).debug(
                    "[SUPABASE VERIFY] Payload keys: %s aud=%s", list(payload.keys())[:10], aud
                )

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
                if settings.DEBUG_SUPABASE_AUTH:
                    logging.getLogger(__name__).debug("[SUPABASE VERIFY] Fallback internal JWT accepted")
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
                logging.getLogger(__name__).warning(
                    "[SUPABASE VERIFY] Invalid token error (supabase + internal fallback failed): %s / %s", e, ie
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
        except Exception as e:
            logging.getLogger(__name__).warning("[SUPABASE VERIFY] Generic verification failure: %s", e)
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

    def _fetch_jwks(self, jwks_url: str) -> dict:
        """Fetch JWKS with a basic caching layer."""
        now = int(time.time())
        ttl = settings.SUPABASE_JWKS_CACHE_TTL or 0
        if self._jwks_cache["keys"] and (now - self._jwks_cache["fetched_at"] < ttl):
            return self._jwks_cache["keys"]

        resp = requests.get(jwks_url, timeout=5)
        resp.raise_for_status()
        jwks = resp.json()
        self._jwks_cache["keys"] = jwks
        self._jwks_cache["fetched_at"] = now
        return jwks

    def _verify_with_jwks(self, token: str, jwks_url: str) -> dict:
        """Verify a JWT using a JWKS endpoint and return the payload on success."""
        # Parse header to get kid
        try:
            header_b64 = token.split('.')[0]
            header_json = base64url_decode(header_b64.encode())
            import json
            header = json.loads(header_json)
            kid = header.get('kid')
        except Exception:
            raise JWTError('Invalid token header')

        jwks = self._fetch_jwks(jwks_url)
        keys = jwks.get('keys', [])
        key_obj = None
        for k in keys:
            if k.get('kid') == kid:
                key_obj = k
                break

        if key_obj is None:
            raise JWTError('No matching JWK found for kid')

        # Use python-jose to construct the public key and verify
        from jose import jwt as jose_jwt
        # jose can accept the jwk dict via 'key' argument
        try:
            # Let jose select the proper algorithm from the key (RS/ES)
            payload = jose_jwt.decode(token, key_obj, algorithms=[key_obj.get('alg')] , options={"verify_aud": False})
            return payload
        except Exception as e:
            raise

# Global middleware instance
supabase_auth = SupabaseAuthMiddleware()

# Dependency for FastAPI routes
def get_current_user(request: Request) -> SupabaseUser:
    """FastAPI dependency to get current authenticated user"""
    return supabase_auth.get_current_user(request)
