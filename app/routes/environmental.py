from fastapi import APIRouter, Depends, HTTPException
from typing import Any, List, Optional
import json
from datetime import datetime, timezone
import uuid
from pathlib import Path
from pydantic import BaseModel, Field
import os
from app.utils.security import list_api_keys

from app.services.fallback_sources import fetch_facility_info_with_fallback
from app.utils.security import get_api_key

router = APIRouter()


class ActivityItem(BaseModel):
    """Represents an activity data input for emissions calculation."""
    type: str = Field(..., description="activity type: 'electricity' or 'fuel' or 'refrigerant'")
    amount: float = Field(..., description="activity amount (kWh, liters, etc.)")
    unit: str = Field(..., description="unit for the amount, e.g. 'kWh', 'liter'")
    fuel: Optional[str] = Field(None, description="fuel type when type='fuel' (e.g., 'diesel', 'gasoline', 'natural_gas')")
    notes: Optional[str] = Field(None, description="optional free-form notes for audit trail")
    source_ref: Optional[str] = Field(None, description="optional source reference or file identifier")


class EmissionsCalcRequest(BaseModel):
    """Input payload for emissions calculation using simple static factors."""
    scope: str = Field(..., description="Scope category: 'scope1' or 'scope2'")
    activities: List[ActivityItem]

    @classmethod
    def validate(cls, value):  # type: ignore
        obj = super().validate(value)
        if obj.scope not in ("scope1", "scope2"):
            raise ValueError("scope must be 'scope1' or 'scope2'")
        # Basic unit sanity checks
        for act in obj.activities:
            if act.type == "electricity" and act.unit.lower() not in ("kwh", "mwh"):
                raise ValueError("electricity unit must be 'kWh' or 'MWh'")
            if act.type == "fuel" and act.unit.lower() not in ("liter", "l", "gallon", "kg", "m3"):
                raise ValueError("fuel unit must be one of: liter, L, gallon, kg, m3")
        return obj


class EmissionsCalcResponse(BaseModel):
    """Output payload containing per-activity and total CO2e emissions."""
    factors_version: str
    results: List[dict]
    total_co2e_kg: float


def _load_factors() -> dict:
    """Load static emission factors from JSON file."""
    try:
        with open("app/data/emission_factors.json", "r") as f:
            return json.load(f)
    except Exception:
        return {}


FACTORS_CACHE = _load_factors()


def _static_emission_factor(activity: ActivityItem) -> float:
    """Return CO2e factor in kg per unit based on simple static mapping.

    Note: These are placeholder factors for demo purposes only.
    """
    if activity.type == "electricity":
        # Lookup by unit with fallback to kWh
        elec = FACTORS_CACHE.get("electricity", {})
        unit_key = (activity.unit or "").lower()
        return float(elec.get(unit_key, elec.get("kwh", 0.45)))
    if activity.type == "fuel":
        fuel = (activity.fuel or "").lower().replace(" ", "_")
        fuel_map = FACTORS_CACHE.get("fuel", {})
        if fuel in ("lng", "natural_gas", "natural", "cng", "natural gas"):
            fuel = "natural_gas"
        unit_key = (activity.unit or "").lower()
        # Default fallbacks if mapping missing
        defaults = {"diesel": 2.68, "gasoline": 2.31, "natural_gas": 1.93}
        if isinstance(fuel_map.get(fuel), dict):
            return float(fuel_map[fuel].get(unit_key, defaults.get(fuel, 2.50)))
        return float(defaults.get(fuel, 2.50))  # default fallback
    if activity.type == "refrigerant":
        # Simplified: assume amount already in kg CO2e equivalent for demo
        return 1.0
    return 0.0


@router.post(
    "/emissions/calc",
    tags=["Environmental Data"],
    summary="Calculate basic Scope 1/2 CO2e using static factors",
    response_model=EmissionsCalcResponse,
)
async def calc_emissions(payload: EmissionsCalcRequest, api_key: str = Depends(get_api_key)):
    """
    Calculate simple CO2e totals for provided activities using static demo factors.
    """
    if payload.scope not in ("scope1", "scope2"):
        raise HTTPException(status_code=400, detail="scope must be 'scope1' or 'scope2'")

    # Validate unit-fuel consistency with friendly errors
    for item in payload.activities:
        t = (item.type or "").lower()
        unit = (item.unit or "").lower()
        if t == "electricity" and unit not in ("kwh", "mwh"):
            raise HTTPException(status_code=422, detail="For electricity, unit must be 'kWh' or 'MWh'")
        if t == "fuel":
            fuel = (item.fuel or "").lower().replace(" ", "_")
            if fuel in ("diesel",):
                if unit not in ("liter", "gallon"):
                    raise HTTPException(status_code=422, detail="For diesel, unit must be 'liter' or 'gallon'")
            elif fuel in ("gasoline", "petrol"):
                if unit not in ("liter", "gallon"):
                    raise HTTPException(status_code=422, detail="For gasoline, unit must be 'liter' or 'gallon'")
            elif fuel in ("natural_gas", "natural", "lng", "cng", "natural gas"):
                if unit not in ("m3", "kg"):
                    raise HTTPException(status_code=422, detail="For natural_gas, unit must be 'm3' or 'kg'")

    results: List[dict] = []
    total = 0.0
    for item in payload.activities:
        factor = _static_emission_factor(item)
        co2e = factor * float(item.amount)
        total += co2e
        results.append({
            "type": item.type,
            "amount": item.amount,
            "unit": item.unit,
            "fuel": item.fuel,
            "factor_kg_per_unit": factor,
            "co2e_kg": round(co2e, 4),
            "notes": getattr(item, "notes", None),
            "source_ref": getattr(item, "source_ref", None),
        })

    transaction_id = str(uuid.uuid4())
    response = EmissionsCalcResponse(
        factors_version="demo-static-v1",
        results=results,
        total_co2e_kg=round(total, 4),
    )

    # Lightweight audit trail: only when notes/source_ref provided
    try:
        if any(getattr(a, "notes", None) or getattr(a, "source_ref", None) for a in payload.activities):
            audit_dir = Path("app/data")
            audit_dir.mkdir(parents=True, exist_ok=True)
            audit_file = audit_dir / "emissions_audit.jsonl"
            entry = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "tx_id": transaction_id,
                "version": response.factors_version,
                "scope": payload.scope,
                "total_co2e_kg": response.total_co2e_kg,
                "activities": [
                    {
                        "type": it.type,
                        "unit": it.unit,
                        "amount": it.amount,
                        "fuel": it.fuel,
                        "notes": getattr(it, "notes", None),
                        "source_ref": getattr(it, "source_ref", None),
                    }
                    for it in payload.activities
                ],
            }
            with open(audit_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
    except Exception:
        # Do not fail request on audit write error
        pass

    data = response.dict()
    data["transaction_id"] = transaction_id
    return data


@router.get(
    "/debug/keys",
    tags=["Environmental Data"],
    summary="List masked API keys (development only)",
)
async def debug_list_keys():
    """Return masked API keys to verify loader in non-production only."""
    if (os.getenv("ENVIRONMENT") or "development").lower() == "production":
        raise HTTPException(status_code=403, detail="Forbidden in production")
    return {"keys": list_api_keys()}


@router.get(
    "/factors/latest",
    tags=["Environmental Data"],
    summary="Return latest emission factors with version metadata",
)
async def get_latest_factors(api_key: str = Depends(get_api_key)):
    """Expose the current static emission factors for transparency/testing."""
    data = FACTORS_CACHE or {}
    version = data.get("version", "unknown")
    sources = data.get("sources", [])
    return {
        "version": version,
        "sources": sources,
        "data": data,
    }


@router.get(
    "/emissions/audits",
    tags=["Environmental Data"],
    summary="List recent emissions calculation audit entries",
)
async def list_emissions_audits(
    limit: int = 50,
    start_ts: Optional[str] = None,
    end_ts: Optional[str] = None,
    scope: Optional[str] = None,
    api_key: str = Depends(get_api_key),
):
    """Return the most recent audit entries (dev-only transparency)."""
    if (os.getenv("ENVIRONMENT") or "development").lower() == "production":
        raise HTTPException(status_code=403, detail="Forbidden in production")
    if limit < 1:
        limit = 1
    if limit > 500:
        limit = 500
    path = Path("app/data/emissions_audit.jsonl")
    if not path.exists():
        return {"items": []}
    try:
        # Read last N lines efficiently
        lines: List[str] = []
        with open(path, "rb") as f:
            f.seek(0, 2)
            buf = b""
            pointer = f.tell()
            while pointer > 0 and len(lines) < limit:
                step = min(4096, pointer)
                pointer -= step
                f.seek(pointer)
                buf = f.read(step) + buf
                parts = buf.split(b"\n")
                # Keep last partial in buf, add complete lines
                buf = parts[0]
                lines_chunk = parts[1:]
                for ln in reversed(lines_chunk):
                    if ln.strip():
                        lines.append(ln.decode("utf-8", errors="ignore"))
                        if len(lines) >= limit:
                            break
        items = []
        for ln in lines:
            try:
                obj = json.loads(ln)
                # Filters
                if scope and obj.get("scope") != scope:
                    continue
                if start_ts:
                    try:
                        if obj.get("ts") and obj["ts"] < start_ts:
                            continue
                    except Exception:
                        pass
                if end_ts:
                    try:
                        if obj.get("ts") and obj["ts"] > end_ts:
                            continue
                    except Exception:
                        pass
                items.append(obj)
            except Exception:
                continue
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read audits: {e}")


@router.get(
    "/emissions/{transaction_id}",
    tags=["Environmental Data"],
    summary="Get a single emissions calculation by transaction id",
)
async def get_emission_by_tx(transaction_id: str, api_key: str = Depends(get_api_key)):
    """Lookup a single calculation result from the audit file by tx_id."""
    if (os.getenv("ENVIRONMENT") or "development").lower() == "production":
        raise HTTPException(status_code=403, detail="Forbidden in production")
    path = Path("app/data/emissions_audit.jsonl")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get("tx_id") == transaction_id:
                    return obj
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read audits: {e}")
    raise HTTPException(status_code=404, detail="Not found")

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
