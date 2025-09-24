from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.utils.security import require_api_key
from app.models.database import get_db, create_tables
from app.repositories.company_map_repository import upsert_mapping, get_mapping, list_mappings

router = APIRouter()

class MappingPayload(BaseModel):
    company: str
    facility_id: str
    facility_name: Optional[str] = None
    state: Optional[str] = None
    notes: Optional[str] = None


def _require_admin(request: Request):
    client_info = getattr(request.state, "client_info", {})
    if client_info.get("tier") != "premium":
        raise HTTPException(status_code=403, detail="Admin privileges required")


@router.post("/mappings", dependencies=[Depends(require_api_key)])
async def upsert_company_mapping(payload: MappingPayload, request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    create_tables()
    m = upsert_mapping(db, company=payload.company, facility_id=payload.facility_id, facility_name=payload.facility_name, state=payload.state, notes=payload.notes)
    return {"status": "success", "data": {
        "company": m.company,
        "facility_id": m.facility_id,
        "facility_name": m.facility_name,
        "state": m.state,
        "notes": m.notes,
    }}


@router.get("/mappings/{company}", dependencies=[Depends(require_api_key)])
async def get_company_mapping(company: str, request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    create_tables()
    m = get_mapping(db, company)
    if not m:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return {"status": "success", "data": {
        "company": m.company,
        "facility_id": m.facility_id,
        "facility_name": m.facility_name,
        "state": m.state,
        "notes": m.notes,
    }}


@router.get("/mappings", dependencies=[Depends(require_api_key)])
async def list_company_mappings(request: Request, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    _require_admin(request)
    create_tables()
    rows = list_mappings(db, limit=limit, offset=offset)
    return {"status": "success", "data": [
        {
            "company": r.company,
            "facility_id": r.facility_id,
            "facility_name": r.facility_name,
            "state": r.state,
            "notes": r.notes,
        } for r in rows
    ], "count": len(rows)}
