import httpx
import logging
import os
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Updated base URL - use dev environment for development
AMDALNET_API_BASE_URL = os.getenv("AMDALNET_API_URL", "https://amdalnet-dev.kemenlh.go.id")

class AmdalnetClient:
    """
    A client for interacting with the KLHK Amdalnet API
    to fetch environmental approval data (SK Final).

    API Documentation: https://amdalnet-dev.kemenlh.go.id/docs
    Authentication: Uses 'token' header with API key
    """
    def __init__(self, api_key: str = None, timeout: int = 30):
        self.base_url = AMDALNET_API_BASE_URL
        self.api_key = api_key or os.getenv("AMDALNET_API_KEY") # Changed env var name
        self.timeout = timeout
        self.headers = {
            "User-Agent": "ENVOYOU-CEVS-Aggregator/1.0",
            "Accept": "application/json"
        }
        # Use correct header format: token instead of Authorization Bearer
        if self.api_key:
            self.headers["token"] = self.api_key

    def sso_login(self, username: str, password: str) -> Optional[str]:
        """
        Perform SSO login to get authentication token.

        Args:
            username (str): SSO username
            password (str): SSO password

        Returns:
            Optional[str]: Authentication token if login successful
        """
        endpoint = "/services/api/sso/login"
        payload = {
            "username": username,
            "password": password
        }

        try:
            with httpx.Client(headers=self.headers, timeout=self.timeout) as client:
                response = client.post(f"{self.base_url}{endpoint}", json=payload)
                response.raise_for_status()

                data = response.json()
                if data.get("success"):
                    token = data.get("token")
                    if token:
                        self.api_key = token
                        self.headers["token"] = token
                        logger.info("SSO login successful")
                        return token
                else:
                    logger.error(f"SSO login failed: {data.get('message', 'Unknown error')}")

        except Exception as e:
            logger.error(f"SSO login error: {e}")

        return None

    def get_sk_final(self, page: int = 1, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetches a paginated list of final decrees (SK Final) from the Amdalnet API.

        Args:
            page (int, optional): The page number to retrieve. Defaults to 1.
            limit (int, optional): The number of items per page. Defaults to 100.

        Returns:
            List[Dict[str, Any]]: A list of SK Final data dictionaries.
        """
        endpoint = "/api/client/sk-final"
        params = {"page": page, "limit": limit}

        try:
            with httpx.Client(headers=self.headers, timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}{endpoint}", params=params)
                response.raise_for_status()

                data = response.json()

                # Handle different response formats
                if isinstance(data, dict):
                    if data.get("success") and "data" in data:
                        result = data["data"]
                    elif "data" in data:
                        result = data["data"]
                    else:
                        # If it's a dict but no data key, return empty list
                        logger.warning(f"Unexpected response format: {data}")
                        result = []
                elif isinstance(data, list):
                    result = data
                else:
                    result = []

                logger.info(f"Successfully fetched {len(result)} SK Final records from Amdalnet API.")
                return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Authentication failed. Please check your API token.")
            else:
                logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []