
import httpx
from fastapi import HTTPException

# Base URL for the EPA Envirofacts API
ENVIROFACTS_API_URL = "https://data.epa.gov/efservice"


async def get_facility_information(facility_name: str):
    """
    Fetches facility information from the EPA Envirofacts API.

    This is a proof-of-concept function to demonstrate API integration.
    It searches for facilities by name.
    """
    # The table we want to query
    table = "T_FRS_FACILITY_SITE"
    
    # The column we are searching in
    column = "PRIMARY_NAME"
    
    # Construct the query URL
    # Example: https://data.epa.gov/efservice/T_FRS_FACILITY_SITE/PRIMARY_NAME/CONTAINING/WATER/JSON
    query_url = f"{ENVIROFACTS_API_URL}/{table}/{column}/CONTAINING/{facility_name}/JSON"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(query_url, timeout=30.0)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error from EPA Envirofacts API: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Service Unavailable: Could not connect to EPA Envirofacts API. {e}",
            )

