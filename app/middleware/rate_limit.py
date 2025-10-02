"""
Rate Limiting Middleware
Uses Redis for distributed rate limiting across all API endpoints
"""

import time
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.redis_service import redis_service


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis"""

    def __init__(self, app, exclude_paths=None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(self, request: Request, call_next):
        """Process each request through rate limiting"""

        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Get client identifier (IP address or user ID if authenticated)
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id_from_request(request)

        # Use user ID if available, otherwise IP address
        identifier = user_id if user_id else client_ip

        # Define rate limits based on endpoint and authentication
        rate_limit_config = self._get_rate_limit_config(request, bool(user_id))

        # Check rate limit
        allowed, remaining = redis_service.check_rate_limit(
            key=f"ratelimit:{identifier}:{request.url.path}",
            limit=rate_limit_config["limit"],
            window_seconds=rate_limit_config["window"]
        )

        # Add rate limit headers to response
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(rate_limit_config["limit"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + rate_limit_config["window"])

        if not allowed:
            # Rate limit exceeded
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Try again in {rate_limit_config['window']} seconds.",
                    "retry_after": rate_limit_config["window"]
                },
                headers={
                    "Retry-After": str(rate_limit_config["window"])
                }
            )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers first (for proxies/load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in case of multiple
            return forwarded_for.split(",")[0].strip()

        # Check other proxy headers
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        client_host = getattr(request.client, 'host', None) if request.client else None
        return client_host or "unknown"

    def _get_user_id_from_request(self, request: Request) -> str:
        """Extract user ID from JWT token if available"""
        try:
            # Try to get from Authorization header
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]  # Remove "Bearer " prefix

                # Import here to avoid circular imports
                from app.utils.jwt import verify_token
                payload = verify_token(token)
                if payload and "sub" in payload:
                    return payload["sub"]
        except Exception:
            # If token verification fails, treat as unauthenticated
            pass

        return None

    def _get_rate_limit_config(self, request: Request, is_authenticated: bool) -> dict:
        """Get rate limit configuration based on endpoint and auth status"""

        path = request.url.path
        method = request.method

        # Default rate limits
        if is_authenticated:
            # Authenticated users get higher limits
            default_limit = 100  # requests per window
            default_window = 60  # seconds
        else:
            # Unauthenticated users get lower limits
            default_limit = 20   # requests per window
            default_window = 60  # seconds

        # Special rate limits for specific endpoints
        endpoint_limits = {
            # Authentication endpoints - more restrictive
            "/v1/auth/login": {"limit": 5, "window": 300},  # 5 attempts per 5 minutes
            "/v1/auth/register": {"limit": 3, "window": 3600},  # 3 registrations per hour
            "/v1/auth/forgot-password": {"limit": 3, "window": 3600},  # 3 resets per hour
            "/v1/auth/verify-email": {"limit": 10, "window": 3600},  # 10 verifications per hour

            # API key endpoints - separate limits for read vs write
            "/v1/user/api-keys": {
                "GET": {"limit": 60, "window": 60},  # 60 reads per minute
                "POST": {"limit": 5, "window": 300},  # 5 creates per 5 minutes
                "DELETE": {"limit": 10, "window": 300},  # 10 deletes per 5 minutes
            },

            # File upload endpoints
            "/v1/user/avatar": {"limit": 5, "window": 3600},  # 5 uploads per hour

            # Health check - no limit
            "/v1/health": {"limit": 1000, "window": 60},

            # Documentation - higher limit
            "/docs": {"limit": 100, "window": 60},
            "/redoc": {"limit": 100, "window": 60},
            "/openapi.json": {"limit": 100, "window": 60},
        }

        # Check if path matches any special endpoint
        for endpoint_path, limits in endpoint_limits.items():
            if path.startswith(endpoint_path):
                # Check if limits are method-specific (nested dict with HTTP methods)
                if isinstance(limits, dict) and method in limits and isinstance(limits[method], dict):
                    return limits[method]
                # Check if limits are simple dict with limit/window
                elif isinstance(limits, dict) and "limit" in limits and "window" in limits:
                    return limits
                # If nested dict but method not found, use default
                break

        # Return default limits
        return {
            "limit": default_limit,
            "window": default_window
        }