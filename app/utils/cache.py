"""
Redis-backed cache utilities with in-memory fallback.
This module provides caching functionality using Redis (Upstash) with fallback to in-memory cache.
"""

from typing import Any, Callable, Optional
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

# Global in-memory cache state (fallback)
_data_cache: Any = None
_cache_timestamp: Optional[float] = None

# Default TTL (seconds)
CACHE_DURATION: int = int(os.getenv("CACHE_DURATION", "3600"))

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL")
REDIS_CACHE_PREFIX = os.getenv("REDIS_CACHE_PREFIX", "envoyou:cache")
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


def is_cache_valid(now: Optional[float] = None, ttl: Optional[int] = None) -> bool:
    """Return True if cache exists and is within TTL."""
    # Try Redis first
    client = _get_redis_client()
    if client:
        try:
            cache_key = f"{REDIS_CACHE_PREFIX}:timestamp"
            timestamp_data = _redis_get(cache_key)
            if timestamp_data:
                now_ts = now if now is not None else time.time()
                dur = ttl if ttl is not None else CACHE_DURATION
                return (now_ts - timestamp_data) < dur
        except Exception as e:
            logger.error(f"Redis cache validation error: {e}")

    # Fallback to in-memory
    global _cache_timestamp
    if _cache_timestamp is None:
        return False
    now_ts = now if now is not None else time.time()
    dur = ttl if ttl is not None else CACHE_DURATION
    return (now_ts - _cache_timestamp) < dur


def get_or_set(fetcher: Callable[[], Any], *, ttl: Optional[int] = None) -> Any:
    """
    Return cached value if valid, else fetch using fetcher(), cache it, and return it.
    """
    cache_key = f"{REDIS_CACHE_PREFIX}:data"
    timestamp_key = f"{REDIS_CACHE_PREFIX}:timestamp"

    # Try Redis first
    client = _get_redis_client()
    if client:
        try:
            now_ts = time.time()
            timestamp_data = _redis_get(timestamp_key)

            if timestamp_data:
                dur = ttl if ttl is not None else CACHE_DURATION
                if (now_ts - timestamp_data) < dur:
                    # Cache is valid, return cached data
                    cached_data = _redis_get(cache_key)
                    if cached_data is not None:
                        return cached_data

            # Cache is invalid or missing, fetch new data
            data = fetcher()

            # Cache the new data
            ttl_value = ttl or CACHE_DURATION
            _redis_set(cache_key, data, ttl_value)
            _redis_set(timestamp_key, now_ts, ttl_value)

            return data

        except Exception as e:
            logger.error(f"Redis cache operation error: {e}")
            # Fall through to in-memory cache

    # Fallback to in-memory cache
    global _data_cache, _cache_timestamp
    now_ts = time.time()
    if is_cache_valid(now_ts, ttl):
        return _data_cache

    data = fetcher()
    _data_cache = data
    _cache_timestamp = now_ts
    return data


def clear_cache() -> None:
    """Clear the cache and timestamp."""
    # Clear Redis cache
    client = _get_redis_client()
    if client:
        try:
            cache_key = f"{REDIS_CACHE_PREFIX}:data"
            timestamp_key = f"{REDIS_CACHE_PREFIX}:timestamp"
            _redis_delete(cache_key)
            _redis_delete(timestamp_key)
        except Exception as e:
            logger.error(f"Redis cache clear error: {e}")

    # Clear in-memory cache
    global _data_cache, _cache_timestamp
    _data_cache = None
    _cache_timestamp = None


def get_cache_timestamp() -> Optional[float]:
    """Get the last cache update timestamp (epoch seconds)."""
    # Try Redis first
    client = _get_redis_client()
    if client:
        try:
            timestamp_key = f"{REDIS_CACHE_PREFIX}:timestamp"
            timestamp_data = _redis_get(timestamp_key)
            if timestamp_data:
                return timestamp_data
        except Exception as e:
            logger.error(f"Redis timestamp retrieval error: {e}")

    # Fallback to in-memory
    return _cache_timestamp


def set_cache_duration(seconds: int) -> None:
    """Override default cache TTL (global)."""
    global CACHE_DURATION
    if isinstance(seconds, int) and seconds > 0:
        CACHE_DURATION = seconds
