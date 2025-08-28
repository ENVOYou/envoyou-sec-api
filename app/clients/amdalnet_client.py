import httpx
import logging
import os
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Updated base URL based on API documentation
AMDALNET_API_BASE_URL = os.getenv("AMDALNET_API_URL", "https://amdalnet.kemenlh.go.id") # Using the non-dev URL as a better default

class AmdalnetClient: # Renamed class
    """
    A client for interacting with the KLHK Amdalnet API
    to fetch environmental approval data (SK Final).
    """
    def __init__(self, api_key: str = None, timeout: int = 30):
        self.base_url = AMDALNET_API_BASE_URL
        self.api_key = api_key or os.getenv("AMDALNET_API_KEY") # Changed env var name
        self.timeout = timeout
        self.headers = {
            "User-Agent": "ENVOYOU-CEVS-Aggregator/1.0",
            "Accept": "application/json"
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    def get_sk_final(self, page: int = 1, limit: int = 100) -> List[Dict[str, Any]]: # Renamed method, added params
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
                # Assuming the response is a list or a dict with a 'data' key
                data = response.json()
                if isinstance(data, dict) and "data" in data:
                    result = data["data"]
                elif isinstance(data, list):
                    result = data
                else:
                    result = []
                
                logger.info(f"Successfully fetched {len(result)} SK Final records from Amdalnet API.")
                return result
        except httpx.RequestError as e:
            logger.error(f"An error occurred while requesting data from Amdalnet API: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return []