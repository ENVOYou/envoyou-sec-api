from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
import os

from app.clients.global_client import KLHKClient
from app.utils import cache as cache_util
from app.clients.iso_client import ISOClient
from app.clients.eea_client import EEAClient
from app.clients.edgar_client import EDGARClient
from app.clients.campd_client import CAMDClient
from app.services.cevs_aggregator import compute_cevs_for_company
from app.utils.security import require_api_key

router = APIRouter()
logger = logging.getLogger(__name__)


def _fetch_and_normalize() -> List[Dict[str, Any]]:
    """Fetch fresh EPA emissions data and normalize to our schema."""
    logger.info("Fetching fresh EPA emissions data (global route)")
    client = KLHKClient()
    try:
        raw = client.get_status_sk(plain=False)
        data = raw if (raw and isinstance(raw, list)) else client.create_sample_data()
    except Exception as e:
        logger.error(f"Error fetching EPA data: {e}")
        data = client.create_sample_data()

    normalized = client.format_permit_data(data)
    return normalized


def _get_cached_data() -> List[Dict[str, Any]]:
    data = cache_util.get_or_set(_fetch_and_normalize)
    ts = cache_util.get_cache_timestamp()
    return data


def _matches_filters(item: Dict[str, Any], *, state: Optional[str], year: Optional[int], pollutant: Optional[str]) -> bool:
    if state:
        extras = item.get("extras", {})
        raw = extras.get("raw", {})
        st = str(extras.get("state") or raw.get("state") or raw.get("state_name") or "")
        if st.lower() != state.lower():
            return False

    if year is not None:
        y = item.get("tanggal_berlaku")
        if str(y) != str(year):
            return False

    if pollutant:
        pol = str(item.get("judul_kegiatan") or "")
        if pollutant.lower() not in pol.lower():
            return False

    return True


@router.get("/emissions", dependencies=[Depends(require_api_key)])
async def global_emissions(
    state: Optional[str] = None,
    year: Optional[int] = Query(None, alias="year"),
    pollutant: Optional[str] = None,
    page: int = 1,
    limit: int = 50
):
    """EPA power plant emissions with optional filters and pagination."""
    try:
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 50

        if state or year is not None or pollutant:
            client = KLHKClient()
            end_idx = max(0, (page - 1) * limit + limit)
            raw = client.get_emissions_power_plants(state=state, limit=end_idx)
            data = client.format_permit_data(raw)
            filtered = [d for d in data if _matches_filters(d, state=state, year=year, pollutant=pollutant)]
        else:
            data = _get_cached_data()
            filtered = [d for d in data if _matches_filters(d, state=state, year=year, pollutant=pollutant)]

        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated = filtered[start_idx:end_idx]

        return JSONResponse(content={
            "status": "success",
            "data": paginated,
            "filters": {"state": state, "year": year, "pollutant": pollutant},
            "pagination": {
                "page": page,
                "limit": limit,
                "total_records": len(filtered),
                "total_pages": (len(filtered) + limit - 1) // limit,
                "has_next": end_idx < len(filtered),
                "has_prev": page > 1,
            },
            "retrieved_at": datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"Error in /global/emissions: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@router.get("/emissions/stats", dependencies=[Depends(require_api_key)])
async def global_emissions_stats():
    """Basic stats aggregated by state, pollutant, and year."""
    try:
        data = _get_cached_data()

        by_state: Dict[str, int] = {}
        by_pollutant: Dict[str, int] = {}
        by_year: Dict[str, int] = {}

        for item in data:
            raw = (item.get("extras") or {}).get("raw", {})
            state = str(raw.get("state") or raw.get("state_name") or "Unknown")
            pol = str(item.get("judul_kegiatan") or "Unknown")
            year = str(item.get("tanggal_berlaku") or "Unknown")

            by_state[state] = by_state.get(state, 0) + 1
            by_pollutant[pol] = by_pollutant.get(pol, 0) + 1
            by_year[year] = by_year.get(year, 0) + 1

        return JSONResponse(content={
            "status": "success",
            "statistics": {
                "by_state": by_state,
                "by_pollutant": by_pollutant,
                "by_year": by_year,
                "total_records": len(data),
            },
            "retrieved_at": datetime.now().isoformat(),
        })

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
