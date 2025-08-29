"""
EIA Client (Async)
Handles interactions with the U.S. Energy Information Administration (EIA) API using httpx.
"""

import os
import httpx
from fastapi import HTTPException
from typing import Any, Dict, List

# --- Configuration ---
EIA_API_KEY = os.getenv("EIA_API_KEY")
BASE_URL = os.getenv("EIA_API_URL", "https://api.eia.gov/v2/")


def _format_response(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Formats the real EIA API v2 response into a list of facility dicts.
    This ensures the structure is similar to the one from epa_client.
    """
    results = []
    # The actual data is nested under response -> data
    raw_facilities = raw_data.get("response", {}).get("data", [])

    for facility in raw_facilities:
        # Mapping from real EIA fields to our common, standardized structure
        formatted_facility = {
            "REGISTRY_ID": f"EIA-{facility.get('plantCode')}",
            "PRIMARY_NAME": facility.get("plantName", "Unknown EIA Facility"),
            "LOCATION_ADDRESS": "N/A", # Not typically provided in this EIA dataset
            "CITY_NAME": "N/A",
            "STATE_CODE": facility.get("state", "N/A"),
            "POSTAL_CODE": "N/A",
            "LATITUDE": facility.get("latitude"),
            "LONGITUDE": facility.get("longitude"),
            "source": "EIA" # Add source identifier
        }
        results.append(formatted_facility)
    return results

async def get_facility_information(facility_name: str) -> List[Dict[str, Any]]:
    """
    Fetches facility information from the EIA v2 API by name.
    """
    if not EIA_API_KEY:
        logger.warning("EIA_API_KEY not set. Skipping EIA client.")
        return []

    # The correct, real endpoint for plant operational data
    endpoint = "https://api.eia.gov/v2/electricity/power-operations/plant-data/data/"

    # API v2 uses a POST request with a JSON payload for complex queries
    payload = {
        "frequency": "annual",
        "data": [
            "plantCode",
            "plantName",
            "state",
            "latitude",
            "longitude"
        ],
        "facets": {
            "plantName": [facility_name] # Filter by the plant name
        },
        "start": "2022-01-01", # Specify a recent period for relevant data
        "end": "2023-01-01",
        "sort": [
            {"column": "plantName", "direction": "asc"}
        ],
        "offset": 0,
        "length": 500 # Limit the number of results
    }

    headers = {
        'Content-Type': 'application/json',
        'X-Api-Key': EIA_API_KEY
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(endpoint, json=payload, headers=headers, timeout=20.0)
            response.raise_for_status()
            
            json_response = response.json()
            logger.info("Successfully received response from EIA API.")
            return _format_response(json_response)

        except httpx.HTTPStatusError as e:
            logger.error(
                "Error from EIA API for '%s': %s - %s",
                facility_name,
                e.response.status_code,
                e.response.text,
                exc_info=True
            )
            # Re-raising as HTTPException so the route can handle it
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error from EIA API: {e.response.text}",
            )
        except httpx.RequestError as e:
            logger.error("Could not connect to EIA API: %s", e, exc_info=True)
            raise HTTPException(
                status_code=503,
                detail=f"Service Unavailable: Could not connect to EIA API. {e}",
            )
