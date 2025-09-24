from __future__ import annotations

import csv
import io
import json
import zipfile
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.services.validation_service import cross_validate_epa
from app.repositories.audit_trail_repository import list_audit_entries
from app.services.storage_service import get_storage


def cevs_to_sec_json(result: Dict[str, Any]) -> Dict[str, Any]:
    """Map compute_cevs_for_company() result into a SEC-friendly JSON shape.
    This is a minimal scaffold and can be extended to match final schema.
    """
    return {
        "company": result.get("company"),
        "country": result.get("country"),
        "summary": {
            "score": result.get("score"),
            "components": result.get("components", {}),
        },
        "data_sources": result.get("sources", {}),
        "technical_notes": {
            "methodology": "Composite score based on ISO presence, EPA matches, renewables proxy, pollution trends, and CAMPD penalties.",
            "version": "v0.1.0",
        },
    }


def audit_trails_to_csv(entries: List[Dict[str, Any]]) -> str:
    """Export list of audit trail dicts to CSV string."""
    if not entries:
        return ""
    columns = [
        "id",
        "timestamp",
        "company_cik",
        "source_file",
        "calculation_version",
        "s3_path",
        "gcs_path",
        "notes",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns)
    writer.writeheader()
    for e in entries:
        writer.writerow({k: e.get(k) for k in columns})
    return buf.getvalue()


def build_and_upload_sec_package(*, company: str, payload: Dict[str, Any], db) -> Dict[str, Any]:
    """Build a SEC export package (zip) containing:
    - cevs.json (by calling compute_cevs upstream; expected in payload consumer)
    - validation.json (cross-validation EPA)
    - audit.csv (audit entries for company)
    - readme.txt (timestamp and basic info)

    Upload using configured storage and return URL + filenames.
    """
    # Build validation
    validation = cross_validate_epa(payload, state=payload.get("state"))

    # Fetch audit entries
    audits = list_audit_entries(db, company_cik=company, limit=1000)
    audit_csv = audit_trails_to_csv([a.to_dict() for a in audits])

    # Build zip in memory
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
        # validation.json
        z.writestr("validation.json", json.dumps(validation, ensure_ascii=False, indent=2))
        # audit.csv
        z.writestr("audit.csv", audit_csv)
        # readme
        ts = datetime.now(timezone.utc).isoformat()
        readme = f"SEC Export Package\nCompany: {company}\nGenerated: {ts}\nFiles: validation.json, audit.csv\n"
        z.writestr("README.txt", readme)
    zip_bytes = zip_buf.getvalue()

    # Upload
    storage = get_storage()
    fname = f"{company.replace(' ', '_').lower()}_sec_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    url = storage.upload_bytes(fname, zip_bytes, content_type="application/zip")

    return {
        "url": url,
        "filename": fname,
        "size_bytes": len(zip_bytes),
        "files": ["validation.json", "audit.csv", "README.txt"],
    }
