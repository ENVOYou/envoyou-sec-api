from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.clients.global_client import EPAClient
from app.services.emissions_calculator import calculate_emissions


def _search_matches(company: str, epa_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    term = company.lower()
    out: List[Dict[str, Any]] = []
    for rec in epa_data:
        name = str(rec.get("facility_name") or "").lower()
        if term in name:
            out.append(rec)
    return out


def cross_validate_epa(payload: Dict[str, Any], *, state: Optional[str] = None, year: Optional[int] = None, sample_limit: int = 5) -> Dict[str, Any]:
    """Cross-validate calculated emissions against EPA Envirofacts presence.

    MVP heuristics:
    - Recalculate totals via calculate_emissions(payload)
    - Fetch EPA facilities (optionally filtered by state)
    - Find name matches by substring
    - Flags:
      - no_epa_match: if no facility matched
      - low_match_density: if < 3 matches (heuristic)
    """
    company = (payload.get("company") or "").strip()
    if not company:
        raise ValueError("company is required")

    calc = calculate_emissions(payload)

    client = EPAClient()
    raw = client.get_emissions_data(region=state, year=year, limit=500)
    # normalize using client's formatter if available
    norm = client.format_emission_data(raw)

    matches = _search_matches(company, norm)

    flags: List[str] = []
    if len(matches) == 0:
        flags.append("no_epa_match")
    elif len(matches) < 3:
        flags.append("low_match_density")

    return {
        "company": company,
        "input_totals": calc.get("totals", {}),
        "epa": {
            "state": state,
            "matches_count": len(matches),
            "sample": matches[:sample_limit],
        },
        "flags": flags,
        "notes": "EPA TRIF dataset lacks numeric emission totals; this MVP checks presence/density as sanity checks.",
    }
