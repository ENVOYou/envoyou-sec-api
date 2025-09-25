from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.audit_service import record_audit, get_audits
from app.middleware.supabase_auth import get_current_user, SupabaseUser
from app.utils.auth_dependencies import require_inspector
import os

router = APIRouter()

def _is_authorized(user: SupabaseUser) -> bool:
    admins = [e.strip().lower() for e in (os.getenv("ADMIN_EMAILS") or "").split(",") if e.strip()]
    inspectors = [e.strip().lower() for e in (os.getenv("INSPECTOR_EMAILS") or "").split(",") if e.strip()]
    email = (user.email or "").lower()
    return email in admins or email in inspectors

class AuditCreateSchema(BaseModel):
    source_file: str
    calculation_version: str
    company_cik: str
    s3_path: Optional[str] = None
    gcs_path: Optional[str] = None
    notes: Optional[str] = None

class AuditResponseSchema(BaseModel):
    id: str
    source_file: str
    calculation_version: str
    timestamp: Optional[str]
    company_cik: str
    s3_path: Optional[str]
    gcs_path: Optional[str]
    notes: Optional[str]


@router.post("/", response_model=AuditResponseSchema)
def create_audit(payload: AuditCreateSchema, db: Session = Depends(get_db), user: SupabaseUser = Depends(get_current_user), roles = Depends(require_inspector())):
    # RBAC handled by dependency
    try:
        entry = record_audit(db, source_file=payload.source_file, calculation_version=payload.calculation_version, company_cik=payload.company_cik, s3_path=payload.s3_path, gcs_path=payload.gcs_path, notes=payload.notes)
        return entry.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[AuditResponseSchema])
def list_audit(company_cik: Optional[str] = None, limit: int = 100, offset: int = 0, db: Session = Depends(get_db), user: SupabaseUser = Depends(get_current_user), roles = Depends(require_inspector())):
    # RBAC handled by dependency
    entries = get_audits(db, company_cik=company_cik, limit=limit, offset=offset)
    return [e.to_dict() for e in entries]
