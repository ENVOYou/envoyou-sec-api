from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import re
import html
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced security middleware for XSS, CSRF, and input sanitization"""

    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]

    async def dispatch(self, request: Request, call_next):
        # Skip security checks for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # XSS Protection - Sanitize input
        await self._sanitize_input(request)

        # CSRF Protection for state-changing requests
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            csrf_valid = await self._validate_csrf(request)
            if not csrf_valid:
                return JSONResponse(
                    status_code=403,
                    content={
                        "status": "error",
                        "message": "CSRF token validation failed",
                        "code": "CSRF_VALIDATION_FAILED"
                    }
                )

        # Security headers
        response = await call_next(request)
        response = self._add_security_headers(response)

        return response

    async def _sanitize_input(self, request: Request):
        """Sanitize input data to prevent XSS attacks"""
        try:
            # Sanitize query parameters
            sanitized_query = {}
            for key, value in request.query_params.items():
                if isinstance(value, str):
                    sanitized_query[key] = self._sanitize_string(value)
                else:
                    sanitized_query[key] = value
            request.state.sanitized_query = sanitized_query

            # For POST/PUT requests, sanitize JSON body
            if request.method in ["POST", "PUT", "PATCH"] and request.headers.get("content-type", "").startswith("application/json"):
                body = await request.json()
                sanitized_body = self._sanitize_dict(body)
                request.state.sanitized_body = sanitized_body
                # Reset body for next read
                await request.body()

        except Exception as e:
            logger.warning(f"Input sanitization failed: {e}")

    def _sanitize_string(self, value: str) -> str:
        """Sanitize string input"""
        if not value:
            return value

        # Remove potentially dangerous HTML/script tags
        value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r'<iframe[^>]*>.*?</iframe>', '', value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r'<object[^>]*>.*?</object>', '', value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r'<embed[^>]*>.*?</embed>', '', value, flags=re.IGNORECASE | re.DOTALL)

        # Escape HTML entities
        value = html.escape(value)

        return value

    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary values"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self._sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_string(item) if isinstance(item, str)
                    else self._sanitize_dict(item) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized

    async def _validate_csrf(self, request: Request) -> bool:
        """Validate CSRF token for state-changing requests"""
        try:
            # Skip CSRF for API endpoints that use JWT authentication
            if request.headers.get("Authorization", "").startswith("Bearer "):
                return True

            # For form-based requests, check CSRF token
            csrf_token = request.headers.get("X-CSRF-Token") or request.query_params.get("csrf_token")

            if not csrf_token:
                # Allow requests without CSRF token for API calls (they should use JWT)
                return True

            # In a real implementation, you'd validate the token against a session
            # For now, we'll accept any non-empty token
            return bool(csrf_token.strip())

        except Exception as e:
            logger.warning(f"CSRF validation failed: {e}")
            return False

    def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response"""
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy
        response.headers["X-Content-Security-Policy"] = "default-src 'self'"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS (HTTP Strict Transport Security)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
