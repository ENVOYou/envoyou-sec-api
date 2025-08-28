from fastapi import APIRouter, Depends, HTTPException
from typing import Any, List

from app.clients import epa_client
from app.utils.security import get_api_key

router = APIRouter()


@router.get(
    "/us/facilities/{facility_name}",
    tags=["Environmental Data"],
    summary="Search for US facilities from EPA Envirofacts",
    response_model=List[Any],  # Using List[Any] as the response structure can be complex
)
async def search_us_facilities(
    facility_name: str, api_key: str = Depends(get_api_key)
):
    """
    Search for environmental facilities in the United States using the EPA Envirofacts database.

    This endpoint provides a proof-of-concept integration with a US-based data source.

    - **facility_name**: The name of the facility to search for (can be a partial name).
    """
    try:
        facilities = await epa_client.get_facility_information(facility_name)
        if not facilities:
            raise HTTPException(
                status_code=404,
                detail=f"No facilities found matching the name: {facility_name}",
            )
        return facilities
    except HTTPException as e:
        # Re-raise HTTPException to ensure FastAPI handles it
        raise e
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
