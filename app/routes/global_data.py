from fastapi import APIRouter, HTTPException, Query, Depends, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
import os

from app.clients.global_client import EPAClient
from app.utils import cache as cache_util
from app.clients.iso_client import ISOClient
from app.clients.eea_client import EEAClient
from app.clients.edgar_client import EDGARClient
from app.clients.campd_client import CAMDClient
from app.services.cevs_aggregator import compute_cevs_for_company
from app.utils.security import require_api_key
from app.services.fallback_sources import fetch_us_emissions_data
from app.utils.response_cache import response_cache

router = APIRouter()
logger = logging.getLogger(__name__)


def _fetch_and_normalize() -> List[Dict[str, Any]]:
    """Fetch fresh EPA emissions data and normalize to our schema."""
    logger.info("Fetching fresh EPA emissions data (global route)")
    client = EPAClient()
    try:
        # Fetch a decent number of records for caching
        raw_data = client.get_emissions_data(limit=500)
    except Exception as e:
        logger.error(f"Error fetching EPA data: {e}")
        raw_data = client.create_sample_data()
    normalized = client.format_emission_data(raw_data)
    return normalized


def _get_cached_data() -> List[Dict[str, Any]]:
    data = cache_util.get_or_set(_fetch_and_normalize)
    ts = cache_util.get_cache_timestamp()
    return data


def _matches_filters(item: Dict[str, Any], *, state: Optional[str], year: Optional[int], pollutant: Optional[str]) -> bool:
    logger.debug(f"Checking item: {item.get('facility_name')}, state: {item.get('state')}, year: {item.get('year')}, pollutant: {item.get('pollutant')}")
    logger.debug(f"Filters: state={state}, year={year}, pollutant={pollutant}")

    # State filtering is primarily handled by the API call, but this is a good safeguard.
    if state and str(item.get("state") or "").lower() != state.lower():
        logger.debug(f"State mismatch: {item.get('state')} vs {state}")
        return False

    # The EPA Envirofacts API used doesn't filter by year, so we do it here.
    if year is not None:
        # The schema normalizer might set a default year.
        if item.get("year") != year:
            logger.debug(f"Year mismatch: {item.get('year')} vs {year}")
            return False

    # The EPA Envirofacts API used doesn't filter by pollutant, so we do it here.
    if pollutant:
        if pollutant.lower() not in str(item.get("pollutant") or "").lower():
            logger.debug(f"Pollutant mismatch: {item.get('pollutant')} vs {pollutant}")
            return False

    return True


@router.get("/emissions", dependencies=[Depends(require_api_key)])
async def global_emissions(
    state: Optional[str] = None,
    year: Optional[int] = Query(None, alias="year"),
    pollutant: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    source: Optional[str] = Query(None, description="Force data source (epa or eia) for debugging")
):
    """
    Provides U.S. power plant emissions data with a fallback mechanism (EPA -> EIA).
    Includes optional filters and pagination.
    """
    try:
        # Validate pagination parameters
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 50

        # Step 1: Get the base dataset using the fallback service
        # The fallback service handles caching and fetching logic internally.
        # We pass filters directly to the service.
        emissions_response = fetch_us_emissions_data(
            source=source,
            state=state,
            year=year,
            pollutant=pollutant,
            limit=1000  # Fetch a larger dataset to allow for accurate filtering and pagination
        )
        
        source_data = emissions_response.get("data", [])
        data_source_name = emissions_response.get("source", "unknown")
        
        logger.debug(f"Data received from source: {data_source_name}. Records: {len(source_data)}")

        # Step 2: Apply all filters to the dataset we have
        # Note: The new fallback service might already perform some filtering.
        # This ensures consistency.
        filtered_data = [
            d for d in source_data if _matches_filters(
                d,
                state=state,
                year=year,
                pollutant=pollutant)
        ]
        logger.debug(f"Filtered data after _matches_filters: {len(filtered_data)} records")

        # Langkah 3: Lakukan paginasi pada hasil yang sudah difilter
        total_records = len(filtered_data)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_data = filtered_data[start_idx:end_idx]

        return JSONResponse(content={
            "status": "success",
            "data": paginated_data,
            "filters": {"state": state, "year": year, "pollutant": pollutant},
            "pagination": {
                "page": page,
                "limit": limit,
                "total_records": total_records,
                "total_pages": (total_records + limit - 1) // limit if limit > 0 else 0,
                "has_next": end_idx < total_records,
                "has_prev": page > 1,
            },
            "retrieved_at": datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Error in /global/emissions: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/emissions/stats", dependencies=[Depends(require_api_key)])
async def global_emissions_stats(request: Request):
    """Basic stats aggregated by state, pollutant, and year."""
    try:
        # Try to get cached response first
        cached_response = response_cache.get(request)
        if cached_response:
            logger.info("Returning cached emissions stats")
            return JSONResponse(content=cached_response, status_code=200)

        # Cache miss - compute fresh data
        logger.info("Computing fresh emissions stats")
        data = _get_cached_data()

        by_state: Dict[str, int] = {}
        by_pollutant: Dict[str, int] = {}
        by_year: Dict[str, int] = {}

        for item in data:
            # Use fields from the normalized EPA schema
            state = str(item.get("state") or "Unknown")
            pol = str(item.get("pollutant") or "Unknown")
            year = str(item.get("year") or "Unknown")

            by_state[state] = by_state.get(state, 0) + 1
            by_pollutant[pol] = by_pollutant.get(pol, 0) + 1
            by_year[year] = by_year.get(year, 0) + 1

        response_data = {
            "status": "success",
            "statistics": {
                "by_state": by_state,
                "by_pollutant": by_pollutant,
                "by_year": by_year,
                "total_records": len(data),
            },
            "retrieved_at": datetime.now().isoformat(),
            "cached": False
        }

        # Cache the response for 30 minutes
        response_cache.set(request, response_data, ttl=1800)

        return JSONResponse(content=response_data, status_code=200)

    except Exception as e:
        logger.error(f"Error in /global/emissions/stats: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/iso", dependencies=[Depends(require_api_key)])
async def global_iso(
    country: Optional[str] = None,
    limit: int = 50
):
    try:
        client = ISOClient()
        data = client.get_iso14001_certifications(country=country, limit=limit)
        return JSONResponse(content={
            "status": "success",
            "data": data,
            "filters": {"country": country},
            "retrieved_at": datetime.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"Error in /global/iso: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/eea", dependencies=[Depends(require_api_key)])
async def global_eea(
    country: Optional[str] = None,
    indicator: str = "GHG",
    year: Optional[int] = Query(None, alias="year"),
    limit: int = 50
):
    try:
        client = EEAClient()
        data = client.get_indicator(indicator=indicator, country=country, year=year, limit=limit)
        return JSONResponse(content={
            "status": "success",
            "data": data,
            "filters": {"country": country, "indicator": indicator, "year": year},
            "retrieved_at": datetime.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"Error in /global/eea: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/edgar", dependencies=[Depends(require_api_key)])
async def global_edgar(
    country: str,
    pollutant: str = "PM2.5",
    window: int = 3
):
    """Diagnostic endpoint: return EDGAR series and trend for a country."""
    try:
        if not country:
            raise HTTPException(status_code=400, detail="country is required")
        try:
            client = EDGARClient()
            series = client.get_country_series(country, pollutant)
            trend = client.get_country_emissions_trend(country, pollutant=pollutant, window=window)
        except FileNotFoundError:
            series = []
            trend = {"pollutant": pollutant, "slope": 0.0, "increase": False, "years": []}

        return JSONResponse(content={
            "status": "success",
            "country": country,
            "pollutant": pollutant,
            "series": series,
            "trend": trend,
            "retrieved_at": datetime.now().isoformat(),
            "source": os.getenv("EDGAR_XLSX_PATH") or "local:EDGAR_emiss_on_UCDB_2024.xlsx",
        })
    except Exception as e:
        logger.error(f"Error in /global/edgar: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/cevs/{company_name}", dependencies=[Depends(require_api_key)])
async def global_cevs(
    company_name: str,
    country: Optional[str] = None
):
    try:
        result = compute_cevs_for_company(company_name, company_country=country)
        return JSONResponse(content={
            "status": "success",
            "company": company_name,
            "country": country,
            "score": result["score"],
            "components": result["components"],
            "sources": result["sources"],
            "details": result["details"],
            "retrieved_at": datetime.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"Error in /global/cevs/{company_name}: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/campd", dependencies=[Depends(require_api_key)])
async def get_campd_data(
    facility_id: int
):
    try:
        client = CAMDClient()
        emissions = client.get_emissions_data(facility_id)
        compliance = client.get_compliance_data(facility_id)
        
        return JSONResponse(content={
            "status": "success",
            "emissions": emissions,
            "compliance": compliance,
            "retrieved_at": datetime.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"Error in /global/campd: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


__all__ = ["router"]
