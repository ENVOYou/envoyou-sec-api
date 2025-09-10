"""
API Response Caching utilities using Redis.
This module provides caching for API responses to improve performance.
"""

from typing import Any, Dict, Optional, Callable
import hashlib
import json
import logging
from functools import wraps
from fastapi import Request, Response

from .redis_utils import redis_cache_response, redis_get_cached_response, redis_clear_response_cache, redis_clear_all_response_cache

logger = logging.getLogger(__name__)


def generate_cache_key(request: Request, additional_data: Dict[str, Any] = None) -> str:
    """
    Generate a cache key from request data.

    Args:
        request: FastAPI request object
        additional_data: Additional data to include in cache key

    Returns:
        Cache key string
    """
    # Get request components
    method = request.method
    url = str(request.url)
    query_params = dict(request.query_params)
    headers = dict(request.headers)

    # Remove headers that shouldn't affect caching
    exclude_headers = {
        'authorization', 'cookie', 'x-api-key', 'user-agent',
        'accept-encoding', 'cache-control', 'pragma'
    }

    filtered_headers = {
        k: v for k, v in headers.items()
        if k.lower() not in exclude_headers
    }

    # Create cache key data
    cache_data = {
        "method": method,
        "url": url,
        "query_params": query_params,
        "headers": filtered_headers
    }

    if additional_data:
        cache_data.update(additional_data)

    # Generate hash of the cache data
    cache_string = json.dumps(cache_data, sort_keys=True)
    cache_key = hashlib.sha256(cache_string.encode()).hexdigest()

    return cache_key


def cache_response(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator to cache API responses using Redis.

    Args:
        ttl: Time to live in seconds (default 1 hour)
        key_prefix: Prefix for cache keys

    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                # If no request found, call function normally
                return await func(*args, **kwargs)

            # Generate cache key
            additional_data = {"function": func.__name__, "prefix": key_prefix}
            cache_key = generate_cache_key(request, additional_data)

            if key_prefix:
                cache_key = f"{key_prefix}:{cache_key}"

            # Try to get cached response
            cached_response = redis_get_cached_response(cache_key)
            if cached_response:
                logger.info(f"Cache hit for {cache_key}")
                # Return cached response
                return cached_response

            # Call the original function
            logger.info(f"Cache miss for {cache_key}")
            response = await func(*args, **kwargs)

            # Cache the response
            if response is not None:
                try:
                    success = redis_cache_response(cache_key, response, ttl)
                    if success:
                        logger.info(f"Response cached for {cache_key}")
                    else:
                        logger.warning(f"Failed to cache response for {cache_key}")
                except Exception as e:
                    logger.error(f"Error caching response: {e}")

            return response

        return wrapper
    return decorator


class ResponseCache:
    """Class-based API response caching."""

    def __init__(self, ttl: int = 3600, key_prefix: str = "api"):
        self.ttl = ttl
        self.key_prefix = key_prefix

    def get(self, request: Request, additional_data: Dict[str, Any] = None) -> Optional[Any]:
        """
        Get cached response for a request.

        Args:
            request: FastAPI request object
            additional_data: Additional data for cache key

        Returns:
            Cached response or None
        """
        cache_key = self._generate_key(request, additional_data)
        return redis_get_cached_response(cache_key)

    def set(self, request: Request, response_data: Any,
            additional_data: Dict[str, Any] = None) -> bool:
        """
        Cache response data.

        Args:
            request: FastAPI request object
            response_data: Data to cache
            additional_data: Additional data for cache key

        Returns:
            True if successful, False otherwise
        """
        cache_key = self._generate_key(request, additional_data)
        return redis_cache_response(cache_key, response_data, self.ttl)

    def delete(self, request: Request, additional_data: Dict[str, Any] = None) -> bool:
        """
        Delete cached response.

        Args:
            request: FastAPI request object
            additional_data: Additional data for cache key

        Returns:
            True if successful, False otherwise
        """
        cache_key = self._generate_key(request, additional_data)
        return redis_clear_response_cache(cache_key)

    def _generate_key(self, request: Request, additional_data: Dict[str, Any] = None) -> str:
        """Generate cache key for request."""
        cache_key = generate_cache_key(request, additional_data)
        if self.key_prefix:
            cache_key = f"{self.key_prefix}:{cache_key}"
        return cache_key

    @staticmethod
    def clear_all() -> bool:
        """
        Clear all cached responses.

        Returns:
            True if successful, False otherwise
        """
        return redis_clear_all_response_cache()

    @staticmethod
    def clear_by_pattern(pattern: str) -> bool:
        """
        Clear cached responses matching a pattern.
        Note: This is a simplified implementation.

        Args:
            pattern: Pattern to match

        Returns:
            True if successful, False otherwise
        """
        # This would require more complex Redis operations
        # For now, we'll clear all responses
        logger.warning("Pattern-based clearing not fully implemented")
        return redis_clear_all_response_cache()


# Global response cache instance
response_cache = ResponseCache()


def get_cached_response(request: Request, additional_data: Dict[str, Any] = None) -> Optional[Any]:
    """
    Convenience function to get cached response.

    Args:
        request: FastAPI request object
        additional_data: Additional data for cache key

    Returns:
        Cached response or None
    """
    return response_cache.get(request, additional_data)


def set_cached_response(request: Request, response_data: Any,
                       additional_data: Dict[str, Any] = None) -> bool:
    """
    Convenience function to cache response.

    Args:
        request: FastAPI request object
        response_data: Data to cache
        additional_data: Additional data for cache key

    Returns:
        True if successful, False otherwise
    """
    return response_cache.set(request, response_data, additional_data)


def clear_cached_response(request: Request, additional_data: Dict[str, Any] = None) -> bool:
    """
    Convenience function to clear cached response.

    Args:
        request: FastAPI request object
        additional_data: Additional data for cache key

    Returns:
        True if successful, False otherwise
    """
    return response_cache.delete(request, additional_data)
