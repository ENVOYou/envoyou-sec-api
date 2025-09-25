from fastapi import APIRouter, Depends
from typing import Any, Dict, List

from app.utils.security import require_api_key
from app.services.emissions_calculator import SCOPE1_FACTORS, SCOPE2_GRID_FACTORS, FACTORS_VERSION

router = APIRouter()

@router.get("/factors")
async def get_emission_factors(api_key: Any = Depends(require_api_key)):
    """Get current emission factors with version info."""
    return {
        "status": "success",
        "version": FACTORS_VERSION,
        "scope1_factors": {
            f"{fuel}_{unit}": factor 
            for (fuel, unit), factor in SCOPE1_FACTORS.items()
        },
        "scope2_grid_factors": SCOPE2_GRID_FACTORS
    }

@router.get("/units")
async def get_supported_units(api_key: Any = Depends(require_api_key)):
    """Get supported units for each fuel type."""
    scope1_units = {}
    for (fuel, unit), _ in SCOPE1_FACTORS.items():
        if fuel not in scope1_units:
            scope1_units[fuel] = []
        scope1_units[fuel].append(unit)
    
    return {
        "status": "success",
        "scope1_units": scope1_units,
        "scope2_units": {
            "electricity": ["kwh"],
            "grid_regions": list(SCOPE2_GRID_FACTORS.keys())
        }
    }