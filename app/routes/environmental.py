from fastapi import APIRouter, Depends, HTTPException
from typing import Any, List, Optional

from app.services.fallback_sources import fetch_facility_info_with_fallback
from app.utils.security import get_api_key

router = APIRouter()


@router.get(
    "/us/facilities/{facility_name}",
    tags=["Environmental Data"],
    summary="Search for US facilities from multiple sources (EPA, EIA)",
    response_model=List[Any], 
)
async def search_us_facilities(
    facility_name: str, 
    source: Optional[str] = None, # Optional query param for debugging
    api_key: str = Depends(get_api_key)
):
    """
    Search for environmental facilities in the United States using a fallback mechanism.

    The system will first query the **EPA Envirofacts** database.
    If no results are found, it will automatically fall back to the **EIA API**.

    - **facility_name**: The name of the facility to search for (can be a partial name).
    - **source**: (Optional) Force a specific data source. Accepts `epa` or `eia`. Useful for debugging.
    """
    try:
        # Pass the source parameter to the fallback service
        facilities = await fetch_facility_info_with_fallback(facility_name, force_source=source)
        return facilities
    except HTTPException as e:
        # The fallback service raises a 404 if all sources fail, which we re-raise
        raise e
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
