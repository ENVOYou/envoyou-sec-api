from __future__ import annotations

import csv
import io
from typing import Any, Dict, List


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
    # Determine columns
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
