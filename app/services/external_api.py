"""
Service layer for interacting with external APIs.

This module provides a structured, modular, and resilient way to fetch data from third-party APIs.

Features:
- A factory to get real or mock API clients.
- Async-aware caching using cachetools.
- An async retry decorator for handling transient network errors.
- A base protocol for consistent client implementation.
"""

import asyncio
import functools
import logging
from typing import Any, Dict, List, Protocol

import httpx
from cachetools import TTLCache

import os

logger = logging.getLogger(__name__)

# --- Configuration ---
# Assumes API keys are stored in environment variables
AIRNOW_API_KEY = os.getenv("AIRNOW_API_KEY", "YOUR_AIRNOW_API_KEY_HERE")

# --- 1. Async-aware Caching ---
class AsyncCache:
    """A simple async-safe wrapper around cachetools.TTLCache."""
    def __init__(self, maxsize: int = 128, ttl: int = 3600):
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            return self._cache.get(key)

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._cache[key] = value

cache = AsyncCache()

# --- 2. Retry Decorator ---
def async_retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """A decorator for retrying an async function on specific HTTP errors."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except httpx.RequestError as e:
                    logger.warning("Retry %d/%d: Request error for %s: %s", attempt + 1, max_retries, e.request.url, e)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in [500, 502, 503, 504]:
                        logger.warning("Retry %d/%d: Server error (%d) for %s", attempt + 1, max_retries, e.response.status_code, e.request.url)
                    else:
                        raise # Do not retry on 4xx client errors
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
                else:
                    logger.error("All retries failed for %s", args, exc_info=True)
                    raise # Re-raise the last exception after all retries fail
        return wrapper
    return decorator

# --- 3. Client Protocol ---
class BaseAPIClient(Protocol):
    """Defines the common interface for all external API clients."""
    async def get_air_quality(self, zip_code: str) -> List[Dict[str, Any]]:
        ...

    async def get_water_quality(self, location: str) -> Dict[str, Any]:
        ...

# --- 4. Client Implementations ---
class RealEPAClient(BaseAPIClient):
    """The actual implementation for EPA APIs (starting with AirNow)."""

    @async_retry()
    async def _fetch_airnow_data(self, zip_code: str) -> List[Dict[str, Any]]:
        """Private method to perform the actual API call with retry logic."""
        if AIRNOW_API_KEY == "YOUR_AIRNOW_API_KEY_HERE":
            logger.warning("AIRNOW_API_KEY is not set. Using mock data for get_air_quality.")
            return [{"Category": {"Name": "Good"}, "AQI": 42, "ReportingArea": "Placeholder"}]

        url = "https://www.airnowapi.org/aq/observation/zipCode/current/"
        params = {
            "format": "application/json",
            "zipCode": zip_code,
            "API_KEY": AIRNOW_API_KEY,
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=15.0)
            response.raise_for_status()
            return response.json()

    import httpx
from cachetools import TTLCache

from app.models.external_data import AirQualityData

logger = logging.getLogger(__name__)

# --- Configuration ---
# Assumes API keys are stored in environment variables
AIRNOW_API_KEY = os.getenv("AIRNOW_API_KEY", "YOUR_AIRNOW_API_KEY_HERE")

# --- 1. Async-aware Caching ---
class AsyncCache:
    """A simple async-safe wrapper around cachetools.TTLCache."""
    def __init__(self, maxsize: int = 128, ttl: int = 3600):
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            return self._cache.get(key)

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._cache[key] = value

cache = AsyncCache()

# --- 2. Retry Decorator ---
def async_retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """A decorator for retrying an async function on specific HTTP errors."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except httpx.RequestError as e:
                    logger.warning("Retry %d/%d: Request error for %s: %s", attempt + 1, max_retries, e.request.url, e)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in [500, 502, 503, 504]:
                        logger.warning("Retry %d/%d: Server error (%d) for %s", attempt + 1, max_retries, e.response.status_code, e.request.url)
                    else:
                        raise # Do not retry on 4xx client errors
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
                else:
                    logger.error("All retries failed for %s", args, exc_info=True)
                    raise # Re-raise the last exception after all retries fail
        return wrapper
    return decorator

# --- 3. Client Protocol ---
class BaseAPIClient(Protocol):
    """Defines the common interface for all external API clients."""
    async def get_air_quality(self, zip_code: str) -> List[AirQualityData]:
        ...

    async def get_water_quality(self, location: str) -> Dict[str, Any]:
        ...

# --- 4. Client Implementations ---
class RealEPAClient(BaseAPIClient):
    """The actual implementation for EPA APIs (starting with AirNow)."""

    @async_retry()
    async def _fetch_airnow_data(self, zip_code: str) -> List[AirQualityData]:
        """Private method to perform the actual API call with retry logic."""
        if AIRNOW_API_KEY == "YOUR_AIRNOW_API_KEY_HERE":
            logger.warning("AIRNOW_API_KEY is not set. Using mock data for get_air_quality.")
            return [AirQualityData(ReportingArea="Placeholder", AQI=42, Category={"Name": "Good"})]

        url = "https://www.airnowapi.org/aq/observation/zipCode/current/"
        params = {
            "format": "application/json",
            "zipCode": zip_code,
            "API_KEY": AIRNOW_API_KEY,
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=15.0)
            response.raise_for_status()
            # Parse and validate the JSON response using the Pydantic model
            return [AirQualityData.model_validate(item) for item in response.json()]

    async def get_air_quality(self, zip_code: str) -> List[AirQualityData]:
        """Fetches air quality data from AirNow, with caching."""
        cache_key = f"air_quality_{zip_code}"
        cached_data = await cache.get(cache_key)
        if cached_data:
            logger.info("Returning cached air quality data for zip code: %s", zip_code)
            return cached_data

        logger.info("Fetching new air quality data for zip code: %s", zip_code)
        fresh_data = await self._fetch_airnow_data(zip_code)
        
        await cache.set(cache_key, fresh_data)
        return fresh_data

    async def get_water_quality(self, location: str) -> Dict[str, Any]:
        # This would follow a similar pattern: cache check, then call a
        # private, retry-decorated method for a specific water API.
        return {"location": location, "turbidity": 1.5, "source": "real_epa_placeholder"}

class MockEPAClient(BaseAPIClient):
    """A mock client for testing and development."""
    async def get_air_quality(self, zip_code: str) -> List[AirQualityData]:
        logger.info("Using MockEPAClient to get air quality for %s", zip_code)
        # Return a Pydantic model instance instead of a raw dict
        return [AirQualityData(ReportingArea="Mockville", AQI=42, Category={"Name": "Good"})]

    async def get_water_quality(self, location: str) -> Dict[str, Any]:
        logger.info("Using MockEPAClient to get water quality for %s", location)
        return {"location": location, "turbidity": 1.0, "source": "mock"}

    async def get_water_quality(self, location: str) -> Dict[str, Any]:
        # This would follow a similar pattern: cache check, then call a
        # private, retry-decorated method for a specific water API.
        return {"location": location, "turbidity": 1.5, "source": "real_epa_placeholder"}

class MockEPAClient(BaseAPIClient):
    """A mock client for testing and development."""
    async def get_air_quality(self, zip_code: str) -> List[Dict[str, Any]]:
        logger.info("Using MockEPAClient to get air quality for %s", zip_code)
        return [{"Category": {"Name": "Good"}, "AQI": 42, "ReportingArea": "Mockville"}]

    async def get_water_quality(self, location: str) -> Dict[str, Any]:
        logger.info("Using MockEPAClient to get water quality for %s", location)
        return {"location": location, "turbidity": 1.0, "source": "mock"}

# --- 5. Factory Function ---
_clients = {
    "epa": {
        "real": RealEPAClient(),
        "mock": MockEPAClient(),
    }
}

def get_api_client(api_name: str, use_mock: bool = False) -> BaseAPIClient:
    """Factory to get an instance of a real or mock API client."""
    client_map = _clients.get(api_name.lower())
    if not client_map:
        raise ValueError(f"Unknown API: {api_name}. Available: {list(_clients.keys())}")

    client_type = "mock" if use_mock else "real"
    return client_map[client_type]
