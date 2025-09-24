from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Optional
from app.utils.security import require_api_key
from app.services.cevs_aggregator import compute_cevs_for_company
from app.services.sec_exporter import cevs_to_sec_json, audit_trails_to_csv
from app.models.database import get_db, create_tables
from sqlalchemy.orm import Session
from app.repositories.audit_trail_repository import list_audit_entries

router = APIRouter()

@router.get("/sec/cevs/{company_name}")
async def export_cevs(company_name: str, company_country: Optional[str] = None, format: str = Query("json", pattern="^(json|csv)$"), api_key: str = Depends(require_api_key)):
    try:
        result = compute_cevs_for_company(company_name, company_country=company_country)
        if format == "json":
            return JSONResponse(content=cevs_to_sec_json(result))
        else:
            # Simple CSV: key-value pairs flattened
            data = cevs_to_sec_json(result)
            lines = ["key,value"]
            def flatten(prefix, obj):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        flatten(f"{prefix}{k}.", v)
                else:
                    lines.append(f"{prefix[:-1]},{str(obj).replace(',', ';')}")
            flatten("", data)
            return PlainTextResponse("\n".join(lines), media_type="text/csv")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sec/audit")
async def export_audit(company_cik: Optional[str] = None, limit: int = 100, offset: int = 0, db: Session = Depends(get_db), api_key: str = Depends(require_api_key)):
    # Ensure schema exists (helpful in CI/TestClient)
    try:
        create_tables()
    except Exception:
        pass
    entries = list_audit_entries(db, company_cik=company_cik, limit=limit, offset=offset)
    csv_text = audit_trails_to_csv([e.to_dict() for e in entries])
    return PlainTextResponse(csv_text, media_type="text/csv")
