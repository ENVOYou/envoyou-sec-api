from typing import Any, Dict
from datetime import datetime

def ensure_epa_emission_schema(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes raw EPA Envirofacts (e.g., tri_facility) data into a consistent
    emission-like schema.

    Args:
        data (Dict[str, Any]): Raw data record from EPA.

    Returns:
        Dict[str, Any]: Normalized record.
    """
    # Buat kamus case-insensitive untuk pencarian yang lebih mudah dan kuat
    data_lower = {str(k).lower(): v for k, v in data.items()}

    # Check for already normalized keys first to handle sample data correctly
    facility_name = data_lower.get("facility_name") or data_lower.get("primary_name") or "Unknown Facility"
    state = data_lower.get("state") or data_lower.get("state_abbr") or None
    
    normalized = {
        "facility_name": facility_name,
        "state": state,
        "county": data_lower.get("county") or data_lower.get("county_name") or None,
        # For tri_facility, year and pollutant are not directly available.
        # We'll add placeholders or infer them if possible.
        "year": data.get("year") or datetime.now().year, # Default to current year if not present
        "pollutant": data.get("pollutant") or "TRI", # Default to 'TRI' for TRI facilities
        "emissions": data.get("emissions") or data.get("EMISSIONS") or None, # Placeholder for actual emission value
        "unit": data.get("unit") or data.get("UNIT") or None, # Placeholder for emission unit
        # Add other relevant fields from raw data if needed
        "raw_data_id": data_lower.get("raw_data_id") or data_lower.get("facility_id") or data_lower.get("tri_facility_id") or None,
        "source_table": data.get("source_table") or "tri_facility" # Indicate source table
    }
    return normalized


def ensure_iso_cert_schema(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes raw ISO certification data into a consistent schema.

    Args:
        data (Dict[str, Any]): Raw data record from ISO data source.

    Returns:
        Dict[str, Any]: Normalized record.
    """
    normalized = {
        "company_name": data.get("company") or data.get("company_name") or data.get("nama_perusahaan") or "Unknown Company",
        "country": data.get("country") or None,
        "certificate": data.get("certificate") or "ISO 14001",
        "valid_until": data.get("valid_until") or None,
    }
    return normalized