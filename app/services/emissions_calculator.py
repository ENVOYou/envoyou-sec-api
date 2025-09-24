from __future__ import annotations

from typing import Dict, Any, Optional, Tuple

FACTORS_VERSION = "0.1"

# Simple emission factors (v0.1) — rough defaults for MVP
# scope1 fuel factors in kg CO2 per unit
SCOPE1_FACTORS = {
    # per gallon (US)
    ("gasoline", "gallon"): 8.887,
    ("diesel", "gallon"): 10.21,
    # per liter (converted via gallon)
    ("gasoline", "liter"): 8.887 / 3.78541,
    ("diesel", "liter"): 10.21 / 3.78541,
    # natural gas approximations
    ("natural_gas", "m3"): 1.9,            # kg CO2 per cubic meter (approx)
    ("natural_gas", "therm"): 5.3,         # kg CO2 per therm (approx)
    ("natural_gas", "mmbtu"): 53.06,       # kg CO2 per MMBtu
}

# scope2 grid factors in kg CO2 per kWh (v0.1)
SCOPE2_GRID_FACTORS = {
    "US_default": 0.4,
    "RFC": 0.45,
    "WECC": 0.35,
    "SERC": 0.5,
}


def grid_factor(region: Optional[str]) -> Tuple[str, float]:
    if not region:
        return ("US_default", SCOPE2_GRID_FACTORS["US_default"])
    region_key = region.upper()
    if region_key in SCOPE2_GRID_FACTORS:
        return (region_key, SCOPE2_GRID_FACTORS[region_key])
    return ("US_default", SCOPE2_GRID_FACTORS["US_default"])  # fallback


def calc_scope1(fuel_type: str, amount: float, unit: str) -> Dict[str, Any]:
    key = (fuel_type.lower(), unit.lower())
    if key not in SCOPE1_FACTORS:
        raise ValueError(f"Unsupported fuel/unit: {fuel_type}/{unit}")
    factor = SCOPE1_FACTORS[key]
    co2 = amount * factor
    return {
        "fuel_type": fuel_type,
        "unit": unit,
        "amount": amount,
        "factor": factor,
        "emissions_kg": round(co2, 6),
    }


def calc_scope2(kwh: float, region: Optional[str]) -> Dict[str, Any]:
    region_used, factor = grid_factor(region)
    co2 = kwh * factor
    return {
        "region": region_used,
        "kwh": kwh,
        "factor": factor,
        "emissions_kg": round(co2, 6),
    }


def calculate_emissions(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate Scope 1 & 2 emissions using v0.1 factors.
    Expected payload shape:
    {
      "company": "...",  # required for audit
      "scope1": {"fuel_type": "diesel|gasoline|natural_gas", "amount": 100, "unit": "gallon|liter|m3|therm|mmbtu"},
      "scope2": {"kwh": 5000, "grid_region": "US_default|RFC|WECC|SERC"}
    }
    """
    company = (payload.get("company") or "").strip()
    if not company:
        raise ValueError("company is required")

    out: Dict[str, Any] = {
        "version": FACTORS_VERSION,
        "company": company,
        "components": {},
        "totals": {},
    }

    scope1_res = None
    s1 = payload.get("scope1") or {}
    if s1:
        scope1_res = calc_scope1(str(s1.get("fuel_type")), float(s1.get("amount", 0.0)), str(s1.get("unit")))
        out["components"]["scope1"] = scope1_res

    scope2_res = None
    s2 = payload.get("scope2") or {}
    if s2:
        scope2_res = calc_scope2(float(s2.get("kwh", 0.0)), s2.get("grid_region"))
        out["components"]["scope2"] = scope2_res

    total_kg = 0.0
    if scope1_res:
        total_kg += scope1_res["emissions_kg"]
    if scope2_res:
        total_kg += scope2_res["emissions_kg"]

    out["totals"] = {
        "emissions_kg": round(total_kg, 6),
        "emissions_tonnes": round(total_kg / 1000.0, 6),
    }
    return out
