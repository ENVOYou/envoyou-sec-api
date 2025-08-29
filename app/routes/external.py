"""
API routes for fetching data from external sources via the new service layer.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from app.models.external_data import AirQualityData
from app.services.external_api import get_api_client
from app.utils.security import get_api_key

router = APIRouter()

@router.get(
    "/air_quality/{zip_code}",
    response_model=List[AirQualityData],
    tags=["External Data"],
    summary="Get Air Quality Index (AQI) for a US zip code."
)
async def get_air_quality_for_zip(
    zip_code: str,
    use_mock: bool = False, # Query param to switch between real and mock clients
    api_key: str = Depends(get_api_key)
):
    """
    Fetches the current Air Quality Index (AQI) for a given US zip code.

    This endpoint uses a modular, resilient service layer with caching and retries.

    - **zip_code**: The 5-digit US zip code.
    - **use_mock**: Set to `true` to use the mock client for testing.
    """
    try:
        # Use the factory to get the desired client (real or mock)
        client = get_api_client("epa", use_mock=use_mock)
        
        # Fetch data using the client
        air_quality_data = await client.get_air_quality(zip_code)
        
        if not air_quality_data:
            raise HTTPException(
                status_code=404,
                detail=f"No air quality data found for zip code: {zip_code}"
            )
            
        return air_quality_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch-all for other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
