from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import time
import json
from app.services.redis_service import redis_service


class LiveRequestsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        try:
            # Only publish for API routes (v1) to reduce noise
            if request.url.path.startswith('/v1') and redis_service.is_connected():
                # Prefer using the api_key attached to request.state (set by require_api_key)
                api_key = getattr(request.state, 'api_key', None)
                key_prefix = None
                if api_key and isinstance(api_key, str):
                    key_prefix = api_key[:8]

                payload = {
                    'ts': int(time.time() * 1000),
                    'path': request.url.path,
                    'method': request.method,
                    'key_prefix': key_prefix,
                }
                # Best-effort publish; ignore result
                try:
                    redis_service.publish_message('live:requests', payload)
                except Exception:
                    pass
        except Exception:
            pass
        return response
