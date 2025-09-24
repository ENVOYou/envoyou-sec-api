from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Optional
from app.utils.security import require_api_key
from app.services.cevs_aggregator import compute_cevs_for_company
from app.services.sec_exporter import cevs_to_sec_json, audit_trails_to_csv, build_and_upload_sec_package
from app.models.database import get_db, create_tables
from sqlalchemy.orm import Session
from app.repositories.audit_trail_repository import list_audit_entries
from pydantic import BaseModel
from app.services.audit_service import record_audit

router = APIRouter()

class Scope1Schema(BaseModel):
    fuel_type: str
    amount: float
    unit: str

class Scope2Schema(BaseModel):
    kwh: float
    grid_region: Optional[str] = None

class ExportPayload(BaseModel):
    company: str
    scope1: Optional[Scope1Schema] = None
    scope2: Optional[Scope2Schema] = None
    state: Optional[str] = None

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

@router.post("/sec/package")
async def export_sec_package(payload: ExportPayload, db: Session = Depends(get_db), api_key: str = Depends(require_api_key)):
    try:
        create_tables()
        result = build_and_upload_sec_package(company=payload.company, payload=payload.model_dump(), db=db)
        # record in audit trail (store url in notes)
        notes = {"action": "export_package", "url": result.get("url"), "file": result.get("filename")}
        record_audit(db, source_file="sec_exporter", calculation_version="v0.1.0", company_cik=payload.company, notes=str(notes))
        return {"status": "success", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
