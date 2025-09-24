from typing import Optional, List
from sqlalchemy.orm import Session
from app.repositories.audit_trail_repository import create_audit_entry, list_audit_entries
from app.models.audit_trail import AuditTrail


def record_audit(db: Session, source_file: str, calculation_version: str, company_cik: str, s3_path: Optional[str] = None, gcs_path: Optional[str] = None, notes: Optional[str] = None) -> AuditTrail:
    return create_audit_entry(db, source_file=source_file, calculation_version=calculation_version, company_cik=company_cik, s3_path=s3_path, gcs_path=gcs_path, notes=notes)


def get_audits(db: Session, company_cik: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[AuditTrail]:
    return list_audit_entries(db, company_cik=company_cik, limit=limit, offset=offset)
