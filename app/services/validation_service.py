from __future__ import annotations

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.clients.global_client import EPAClient
from app.clients.campd_client import CAMDClient
# from app.clients.eia_client import EIAClient  # Skip EIA for now
from app.services.emissions_calculator import calculate_emissions
from app.repositories.company_map_repository import get_mapping
from app.config import settings


def _search_matches(company: str, epa_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    term = company.lower()
    out: List[Dict[str, Any]] = []
    for rec in epa_data:
        name = str(rec.get("facility_name") or "").lower()
        if term in name:
            out.append(rec)
    return out


def _check_quantitative_deviation(payload: Dict[str, Any], mapping, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Check quantitative deviation using CAMPD/EIA data for mapped facility."""
    facility_id = mapping.facility_id
    if not facility_id:
        return None
    
    # Get thresholds from settings
    co2_threshold = float(getattr(settings, "VALIDATION_CO2_DEVIATION_THRESHOLD", 15.0))
    nox_threshold = float(getattr(settings, "VALIDATION_NOX_DEVIATION_THRESHOLD", 20.0))
    so2_threshold = float(getattr(settings, "VALIDATION_SO2_DEVIATION_THRESHOLD", 25.0))
    
    deviations = []
    
    try:
        # Try CAMPD for power plants
        campd = CAMDClient()
        campd_data = campd.get_emissions_data(facility_id=facility_id, year=year or 2023)
        
        if campd_data:
            # Check CO2 deviation
            reported_co2 = _extract_co2_from_payload(payload)
            campd_co2 = _extract_co2_from_campd(campd_data)
            
            if reported_co2 and campd_co2:
                deviation_pct = abs(reported_co2 - campd_co2) / campd_co2 * 100
                severity = "critical" if deviation_pct > co2_threshold * 2 else "high" if deviation_pct > co2_threshold else "medium"
                
                deviations.append({
                    "pollutant": "CO2",
                    "reported": reported_co2,
                    "reference": campd_co2,
                    "deviation_pct": deviation_pct,
                    "threshold": co2_threshold,
                    "severity": severity,
                    "source": "CAMPD"
                })
    
    except Exception:
        # EIA fallback temporarily disabled (async client needs refactoring)
        pass
    
    if not deviations:
        return None
    
    return {
        "facility_id": facility_id,
        "year": year or 2023,
        "deviations": deviations,
        "thresholds": {
            "co2": co2_threshold,
            "nox": nox_threshold,
            "so2": so2_threshold
        }
    }


def _extract_co2_from_payload(payload: Dict[str, Any]) -> Optional[float]:
    """Extract CO2 emissions from calculated emissions result."""
    try:
        calc = calculate_emissions(payload)
        total_kg = calc.get("totals", {}).get("emissions_kg", 0.0)
        # Convert kg to tonnes for comparison with external data
        return total_kg / 1000.0 if total_kg > 0 else None
    except Exception:
        return None


def _extract_co2_from_campd(campd_data: List[Dict[str, Any]]) -> Optional[float]:
    """Extract CO2 from CAMPD data."""
    total = 0.0
    for record in campd_data:
        co2 = record.get("co2_mass_tons") or record.get("co2_emissions")
        if co2:
            total += float(co2)
    return total if total > 0 else None


def _extract_co2_from_eia(eia_data: List[Dict[str, Any]]) -> Optional[float]:
    """Extract CO2 from EIA data."""
    total = 0.0
    for record in eia_data:
        co2 = record.get("co2_emissions") or record.get("carbon_dioxide")
        if co2:
            total += float(co2)
    return total if total > 0 else None


def cross_validate_epa(payload: Dict[str, Any], *, db: Optional[Session] = None, state: Optional[str] = None, year: Optional[int] = None, sample_limit: int = 5) -> Dict[str, Any]:
    """Cross-validate calculated emissions against EPA Envirofacts presence.

    Thresholds (configurable via env):
      - VALIDATION_MIN_MATCHES (default 1)
      - VALIDATION_LOW_DENSITY_THRESHOLD (default 3)
      - VALIDATION_REQUIRE_STATE_MATCH (default False)

    Returns detailed flags with code/severity/message/details for actionable insights.
    """
    company = (payload.get("company") or "").strip()
    if not company:
        raise ValueError("company is required")

    calc = calculate_emissions(payload)

    client = EPAClient()
    raw = client.get_emissions_data(region=state, year=year, limit=500)
    norm = client.format_emission_data(raw)

    matches = _search_matches(company, norm)
    
    # Check for manual mapping
    mapping = None
    quantitative_deviation = None
    if db:
        mapping = get_mapping(db, company)
        if mapping:
            quantitative_deviation = _check_quantitative_deviation(payload, mapping, year)

    min_matches = int(getattr(settings, "VALIDATION_MIN_MATCHES", 1) or 1)
    low_density = int(getattr(settings, "VALIDATION_LOW_DENSITY_THRESHOLD", 3) or 3)
    require_state = bool(getattr(settings, "VALIDATION_REQUIRE_STATE_MATCH", False))

    flags: List[Dict[str, Any]] = []

    # Match thresholds
    if len(matches) < min_matches:
        flags.append({
            "code": "no_epa_match",
            "severity": "high",
            "message": "No matching facilities found in EPA for this company name.",
            "details": {"matches_count": len(matches), "min_required": min_matches}
        })
    elif len(matches) < low_density:
        flags.append({
            "code": "low_match_density",
            "severity": "medium",
            "message": "Low EPA match density compared to expectations.",
            "details": {"matches_count": len(matches), "threshold": low_density}
        })

    # State consistency check
    state_mismatch = None
    if state:
        same_state = [m for m in matches if str(m.get("state") or "").upper() == state.upper()]
        if len(matches) > 0 and len(same_state) == 0:
            state_mismatch = True
            flags.append({
                "code": "state_mismatch",
                "severity": "medium" if not require_state else "high",
                "message": "No EPA matches found in the specified state.",
                "details": {"requested_state": state, "matches_count": len(matches)}
            })
        elif require_state and len(same_state) == 0:
            flags.append({
                "code": "state_required_no_match",
                "severity": "high",
                "message": "State match required for validation but none found.",
                "details": {"requested_state": state}
            })

    # Suggestions minimal
    suggestions: List[str] = []
    if any(f["code"] == "no_epa_match" for f in flags):
        suggestions.append("Check company name spelling or use legal name alias.")
    if state and state_mismatch:
        suggestions.append("Check operational state in input or use different state for validation.")

    result = {
        "company": company,
        "inputs": {
            "scope1": payload.get("scope1"),
            "scope2": payload.get("scope2"),
        },
        "calc": calc,
        "epa": {
            "state": state,
            "matches_count": len(matches),
            "sample": matches[:sample_limit],
        },
        "flags": flags,
        "metrics": {
            "min_matches": min_matches,
            "low_density_threshold": low_density,
            "require_state_match": require_state,
        },
        "notes": "EPA TRI does not contain emission numbers; this heuristic checks facility presence and match density.",
        "suggestions": suggestions,
    }
    
    # Add mapping and quantitative data if available
    if mapping:
        result["mapping"] = {
            "facility_id": mapping.facility_id,
            "facility_name": mapping.facility_name,
            "state": mapping.state,
            "notes": mapping.notes
        }
    
    if quantitative_deviation:
        result["quantitative_deviation"] = quantitative_deviation
        # Add deviation flags
        for dev in quantitative_deviation.get("deviations", []):
            if dev["severity"] in ["high", "critical"]:
                flags.append({
                    "code": "quantitative_deviation",
                    "severity": dev["severity"],
                    "message": f"Significant deviation in {dev['pollutant']}: {dev['deviation_pct']:.1f}%",
                    "details": dev
                })
    
    return result
