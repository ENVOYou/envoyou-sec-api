"""
Redis utilities for rate limiting, session management, and caching.
This module provides Redis-based implementations for various application features.
"""

from typing import Any, Dict, Optional, List
import os
import time
import json
import logging
from urllib.parse import urlparse

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL")
REDIS_CACHE_PREFIX = os.getenv("REDIS_CACHE_PREFIX", "envoyou:cache")
REDIS_RATE_LIMIT_PREFIX = os.getenv("RATE_LIMIT_REDIS_PREFIX", "envoyou:ratelimit")
REDIS_SESSION_PREFIX = os.getenv("SESSION_REDIS_PREFIX", "envoyou:sessions")
REDIS_CACHE_TTL = int(os.getenv("REDIS_CACHE_TTL", "3600"))

# Redis client
_redis_client: Optional[Any] = None


def _get_redis_client():
    """Get or create Redis client."""
    global _redis_client
    if not REDIS_AVAILABLE or not REDIS_URL:
        return None

    if _redis_client is None:
        try:
            parsed = urlparse(REDIS_URL)
            if parsed.scheme == 'rediss':
                # SSL connection for Upstash
                _redis_client = redis.Redis(
                    host=parsed.hostname,
                    port=parsed.port or 6379,
                    password=parsed.password,
                    username=parsed.username,
                    ssl=True,
                    ssl_cert_reqs=None,
                    decode_responses=True
                )
            else:
                # Regular Redis connection
                _redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

            # Test connection
            _redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            _redis_client = None

    return _redis_client


def _redis_get(key: str) -> Optional[Any]:
    """Get value from Redis."""
    client = _get_redis_client()
    if not client:
        return None

    try:
        data = client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.error(f"Redis get error: {e}")

    return None


def _redis_set(key: str, value: Any, ttl: int = None) -> bool:
    """Set value in Redis with TTL."""
    client = _get_redis_client()
    if not client:
        return False

    try:
        ttl_value = ttl or REDIS_CACHE_TTL
        serialized = json.dumps(value)
        return client.setex(key, ttl_value, serialized)
    except Exception as e:
        logger.error(f"Redis set error: {e}")
        return False


def _redis_delete(key: str) -> bool:
    """Delete key from Redis."""
    client = _get_redis_client()
    if not client:
        return False

    try:
        return client.delete(key) > 0
    except Exception as e:
        logger.error(f"Redis delete error: {e}")
        return False


def _redis_exists(key: str) -> bool:
    """Check if key exists in Redis."""
    client = _get_redis_client()
    if not client:
        return False

    try:
        return client.exists(key) > 0
    except Exception as e:
        logger.error(f"Redis exists error: {e}")
        return False


def _redis_incr(key: str, amount: int = 1) -> Optional[int]:
    """Increment value in Redis."""
    client = _get_redis_client()
    if not client:
        return None

    try:
        return client.incr(key, amount)
    except Exception as e:
        logger.error(f"Redis incr error: {e}")
        return None


def _redis_expire(key: str, ttl: int) -> bool:
    """Set expiration on Redis key."""
    client = _get_redis_client()
    if not client:
        return False

    try:
        return client.expire(key, ttl)
    except Exception as e:
        logger.error(f"Redis expire error: {e}")
        return False


# Rate Limiting Functions
def redis_rate_limit(key: str, limit: int, window: int = 60) -> bool:
    """
    Check if request is within rate limit using Redis.
    Returns True if request is allowed, False if rate limited.
    """
    client = _get_redis_client()
    if not client:
        # Fallback to simple in-memory rate limiting
        return _fallback_rate_limit(key, limit, window)

    try:
        now = int(time.time())
        window_start = now - window

        # Use Redis sorted set to track requests
        rate_key = f"{REDIS_RATE_LIMIT_PREFIX}:{key}"

        # Remove old entries outside the window
        client.zremrangebyscore(rate_key, '-inf', window_start)

        # Count current requests in window
        current_count = client.zcard(rate_key)

        if current_count >= limit:
            return False

        # Add current request
        client.zadd(rate_key, {str(now): now})

        # Set expiration on the key (window + 1 second buffer)
        client.expire(rate_key, window + 1)

        return True

    except Exception as e:
        logger.error(f"Redis rate limit error: {e}")
        # Fallback to in-memory
        return _fallback_rate_limit(key, limit, window)


# Fallback in-memory rate limiting
_rate_limit_storage = {}
def _fallback_rate_limit(key: str, limit: int, window: int = 60) -> bool:
    """Fallback in-memory rate limiting."""
    now = time.time()
    _rate_limit_storage[key] = [
        ts for ts in _rate_limit_storage.get(key, []) if now - ts < window
    ]
    current_count = len(_rate_limit_storage[key])
    if current_count >= limit:
        return False
    _rate_limit_storage.setdefault(key, []).append(now)
    return True


# Session Management Functions
def redis_store_session(session_id: str, session_data: Dict[str, Any], ttl: int = 86400) -> bool:
    """
    Store session data in Redis.
    ttl: Time to live in seconds (default 24 hours)
    """
    client = _get_redis_client()
    if not client:
        return False

    try:
        session_key = f"{REDIS_SESSION_PREFIX}:{session_id}"
        return _redis_set(session_key, session_data, ttl)
    except Exception as e:
        logger.error(f"Redis session store error: {e}")
        return False


def redis_get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve session data from Redis."""
    client = _get_redis_client()
    if not client:
        return None

    try:
        session_key = f"{REDIS_SESSION_PREFIX}:{session_id}"
        return _redis_get(session_key)
    except Exception as e:
        logger.error(f"Redis session get error: {e}")
        return None


def redis_delete_session(session_id: str) -> bool:
    """Delete session from Redis."""
    client = _get_redis_client()
    if not client:
        return False

    try:
        session_key = f"{REDIS_SESSION_PREFIX}:{session_id}"
        return _redis_delete(session_key)
    except Exception as e:
        logger.error(f"Redis session delete error: {e}")
        return False


def redis_update_session_activity(session_id: str, ttl: int = 86400) -> bool:
    """Update session last activity and extend TTL."""
    client = _get_redis_client()
    if not client:
        return False

    try:
        session_key = f"{REDIS_SESSION_PREFIX}:{session_id}"
        if client.exists(session_key):
            return client.expire(session_key, ttl)
        return False
    except Exception as e:
        logger.error(f"Redis session update error: {e}")
        return False


# API Response Caching Functions
def redis_cache_response(cache_key: str, response_data: Any, ttl: int = None) -> bool:
    """Cache API response in Redis."""
    client = _get_redis_client()
    if not client:
        return False

    try:
        full_key = f"{REDIS_CACHE_PREFIX}:response:{cache_key}"
        ttl_value = ttl or REDIS_CACHE_TTL
        return _redis_set(full_key, response_data, ttl_value)
    except Exception as e:
        logger.error(f"Redis response cache error: {e}")
        return False


def redis_get_cached_response(cache_key: str) -> Optional[Any]:
    """Get cached API response from Redis."""
    client = _get_redis_client()
    if not client:
        return None

    try:
        full_key = f"{REDIS_CACHE_PREFIX}:response:{cache_key}"
        return _redis_get(full_key)
    except Exception as e:
        logger.error(f"Redis response cache get error: {e}")
        return None


def redis_clear_response_cache(cache_key: str) -> bool:
    """Clear specific cached response."""
    client = _get_redis_client()
    if not client:
        return False

    try:
        full_key = f"{REDIS_CACHE_PREFIX}:response:{cache_key}"
        return _redis_delete(full_key)
    except Exception as e:
        logger.error(f"Redis response cache clear error: {e}")
        return False


def redis_clear_all_response_cache() -> bool:
    """Clear all cached responses."""
    client = _get_redis_client()
    if not client:
        return False

    try:
        pattern = f"{REDIS_CACHE_PREFIX}:response:*"
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys) > 0
        return True
    except Exception as e:
        logger.error(f"Redis clear all response cache error: {e}")
        return False


# Health check function
def redis_health_check() -> Dict[str, Any]:
    """Check Redis connectivity and return status."""
    client = _get_redis_client()
    if not client:
        return {
            "status": "unavailable",
            "message": "Redis client not available",
            "available": False
        }

    try:
        client.ping()
        return {
            "status": "healthy",
            "message": "Redis connection successful",
            "available": True
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Redis connection failed: {str(e)}",
            "available": False
        }
