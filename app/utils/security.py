import os
import hashlib
import hmac
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Set
import time

from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

# Import Redis utilities
from .redis_utils import redis_rate_limit

# API Keys
VALID_API_KEYS: Dict[str, Dict[str, Any]] = {
    "demo_key_basic_2025": {
        "name": "Demo Client Basic",
        "tier": "basic",
        "created": datetime.now(),
        "requests_per_minute": 30,
    },
    "demo_key_premium_2025": {
        "name": "Demo Client Premium",
        "tier": "premium",
        "created": datetime.now(),
        "requests_per_minute": 100,
    },
}

def load_api_keys_from_env():
    env_keys = os.getenv("API_KEYS", "")
    if env_keys:
        try:
            for key_config in env_keys.split(","):
                parts = key_config.strip().split(":")
                if len(parts) >= 3:
                    key, name, tier = parts[0], parts[1], parts[2]
                    rpm = 30 if tier == "basic" else 100
                    VALID_API_KEYS[key] = {
                        "name": name,
                        "tier": tier,
                        "created": datetime.now(),
                        "requests_per_minute": rpm,
                    }
        except Exception as e:
            logger.error(f"Error loading API keys from environment: {e}")

load_api_keys_from_env()

def validate_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    if not api_key:
        return None
    if api_key in VALID_API_KEYS:
        return VALID_API_KEYS[api_key]
    env_master_key = os.getenv("MASTER_API_KEY")
    if env_master_key and hmac.compare_digest(api_key, env_master_key):
        return {
            "name": "Master Client",
            "tier": "premium",
            "created": datetime.now(),
            "requests_per_minute": 200,
        }
    return None

async def require_api_key(request: Request):
    api_key = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        api_key = auth_header[7:]
    if not api_key:
        api_key = request.headers.get("X-API-Key")
    if not api_key:
        api_key = request.query_params.get("api_key")
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail=(
                "API key required. Include it in Authorization header "
                "(Bearer token), X-API-Key header, or api_key parameter."
            ),
        )
    client_info = validate_api_key(api_key)
    if not client_info:
        raise HTTPException(status_code=401, detail="Invalid API key")
    request.state.client_info = client_info
    request.state.api_key = api_key

def get_rate_limit_for_key(request: Request) -> str:
    client_info = getattr(request.state, "client_info", None)
    if client_info:
        rpm = client_info.get("requests_per_minute", 30)
        return f"{rpm} per minute"
    return "30 per minute"

def rate_limit_dependency_factory():
    async def check_rate_limit(request: Request):
        # This dependency should be applied to protected routes, so we can expect client_info.
        client_info = getattr(request.state, "client_info", None)
        # Fallback to IP-based limiting if API key is not processed yet (e.g., public but limited endpoints)
        api_key_or_ip = getattr(request.state, "api_key", request.client.host)
        
        # Use the tier-based limit if available, otherwise a default.
        limit = client_info.get("requests_per_minute", 30) if client_info else 15

        if not redis_rate_limit(api_key_or_ip, limit, 60):
            raise HTTPException(
                status_code=429,
                detail={
                    "status": "error",
                    "message": f"Rate limit exceeded: {limit} requests per minute",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": 60,
                },
            )

    return check_rate_limit

def generate_api_key(client_name: str, tier: str = "basic") -> str:
    timestamp = datetime.now().isoformat()
    raw_key = f"{client_name}_{tier}_{timestamp}"
    api_key = hashlib.sha256(raw_key.encode()).hexdigest()[:32]
    VALID_API_KEYS[api_key] = {
        "name": client_name,
        "tier": tier,
        "created": datetime.now(),
        "requests_per_minute": 30 if tier == "basic" else 100,
    }
    return api_key

def list_api_keys() -> Dict[str, Dict[str, Any]]:
    safe_keys = {}
    for key, info in VALID_API_KEYS.items():
        safe_keys[key[:8] + "..."] = {
            "name": info["name"],
            "tier": info["tier"],
            "created": info["created"].isoformat()
            if isinstance(info["created"], datetime)
            else info["created"],
            "requests_per_minute": info.get("requests_per_minute", 30),
        }
    return safe_keys

PUBLIC_ENDPOINTS: Set[str] = {
    "/health",
    "/",
    "/api/docs",
    "/docs",
}

def is_public_endpoint(endpoint: str) -> bool:
    return endpoint in PUBLIC_ENDPOINTS or endpoint.startswith("/static")

# Dependency helper to extract a validated API key for routes
async def get_api_key(request: Request) -> str:
    # Reuse existing validation logic and attach state
    await require_api_key(request)
    return request.state.api_key