from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.audit_trail import AuditTrail


def create_audit_entry(db: Session, *, source_file: str, calculation_version: str, company_cik: str, s3_path: Optional[str] = None, gcs_path: Optional[str] = None, notes: Optional[str] = None) -> AuditTrail:
    entry = AuditTrail(
        source_file=source_file,
        calculation_version=calculation_version,
        company_cik=company_cik,
        s3_path=s3_path,
        gcs_path=gcs_path,
        notes=notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_audit_entries(db: Session, company_cik: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[AuditTrail]:
    query = db.query(AuditTrail)
    if company_cik:
        query = query.filter(AuditTrail.company_cik == company_cik)
    return query.order_by(AuditTrail.timestamp.desc()).offset(offset).limit(limit).all()
