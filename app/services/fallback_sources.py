"""
Fallback Sources Service (Async)

This module provides a fallback mechanism for fetching facility data from multiple sources.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

# Import the specific async functions from the clients
from app.clients import epa_client
from app.clients import eia_client

# Get a logger for this module
logger = logging.getLogger(__name__)


async def _fetch_from_epa(facility_name: str) -> List[Dict[str, Any]]:
    """Wrapper for fetching from EPA, adding source info and handling errors."""
    try:
        logger.info("Attempting to fetch '%s' from EPA...", facility_name)
        results = await epa_client.get_facility_information(facility_name)
        if results:
            logger.info("Successfully fetched data from EPA for '%s'.", facility_name)
            for result in results:
                result['source'] = 'EPA'
            return results
    except HTTPException as e:
        if e.status_code != 404:
            logger.warning("EPA client failed for '%s': %s", facility_name, e.detail, exc_info=True)
    except Exception as e:
        logger.error("An unexpected error occurred with EPA client for '%s'.", facility_name, exc_info=True)
    return []

async def _fetch_from_eia(facility_name: str) -> List[Dict[str, Any]]:
    """Wrapper for fetching from EIA, adding source info and handling errors."""
    try:
        logger.info("Attempting to fetch '%s' from EIA...", facility_name)
        results = await eia_client.get_facility_information(facility_name)
        if results:
            logger.info("Successfully fetched data from EIA for '%s'.", facility_name)
            return results
    except Exception as e:
        logger.error("An unexpected error occurred with EIA client for '%s'.", facility_name, exc_info=True)
    return []

async def fetch_facility_info_with_fallback(
    facility_name: str, force_source: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetches facility information from multiple sources.

    If `force_source` is provided, it will only use that source.
    Otherwise, it attempts sources in a predefined order.
    """
    # --- Handle forced source for debugging ---
    if force_source:
        source = force_source.lower()
        logger.info("Forcing data source: %s for '%s'", source, facility_name)
        if source == 'epa':
            results = await _fetch_from_epa(facility_name)
        elif source == 'eia':
            results = await _fetch_from_eia(facility_name)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid source '{force_source}'. Available sources: 'epa', 'eia'."
            )
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No facilities found for '{facility_name}' from the specified source: {source}"
            )
        return results

    # --- Default fallback logic ---
    epa_results = await _fetch_from_epa(facility_name)
    if epa_results:
        return epa_results
    
    logger.info("No results from EPA for '%s', proceeding to fallback.", facility_name)

    eia_results = await _fetch_from_eia(facility_name)
    if eia_results:
        return eia_results

    # --- If all sources fail ---
    logger.warning("All sources failed for facility '%s'.", facility_name)
    raise HTTPException(
        status_code=404,
        detail=f"No facilities found matching the name '{facility_name}' from any available source.",
    )
