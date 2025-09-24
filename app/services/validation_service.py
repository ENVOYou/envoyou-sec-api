from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.clients.global_client import EPAClient
from app.services.emissions_calculator import calculate_emissions
from app.config import settings


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

    min_matches = int(getattr(settings, "VALIDATION_MIN_MATCHES", 1) or 1)
    low_density = int(getattr(settings, "VALIDATION_LOW_DENSITY_THRESHOLD", 3) or 3)
    require_state = bool(getattr(settings, "VALIDATION_REQUIRE_STATE_MATCH", False))

    flags: List[Dict[str, Any]] = []

    # Match thresholds
    if len(matches) < min_matches:
        flags.append({
            "code": "no_epa_match",
            "severity": "high",
            "message": "Tidak ditemukan fasilitas yang cocok di EPA untuk nama perusahaan ini.",
            "details": {"matches_count": len(matches), "min_required": min_matches}
        })
    elif len(matches) < low_density:
        flags.append({
            "code": "low_match_density",
            "severity": "medium",
            "message": "Jumlah kecocokan EPA rendah dibanding ekspektasi.",
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
                "message": "Tidak ada match EPA dalam state yang ditentukan.",
                "details": {"requested_state": state, "matches_count": len(matches)}
            })
        elif require_state and len(same_state) == 0:
            flags.append({
                "code": "state_required_no_match",
                "severity": "high",
                "message": "Validasi mewajibkan kecocokan state namun tidak ditemukan.",
                "details": {"requested_state": state}
            })

    # Suggestions minimal
    suggestions: List[str] = []
    if any(f["code"] == "no_epa_match" for f in flags):
        suggestions.append("Periksa ejaan nama perusahaan atau gunakan alias legal name.")
    if state and state_mismatch:
        suggestions.append("Periksa state operasional pada input atau gunakan state lain untuk validasi.")

    return {
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
        "notes": "EPA TRI tidak memuat angka emisi; heuristik ini memeriksa keberadaan & kepadatan kecocokan.",
        "suggestions": suggestions,
    }
