from __future__ import annotations

from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.company_map import CompanyFacilityMap


def upsert_mapping(db: Session, *, company: str, facility_id: str, facility_name: Optional[str] = None, state: Optional[str] = None, notes: Optional[str] = None) -> CompanyFacilityMap:
    company_key = company.strip()
    m = db.get(CompanyFacilityMap, company_key)
    if m is None:
        m = CompanyFacilityMap(company=company_key, facility_id=facility_id)
        db.add(m)
    else:
        m.facility_id = facility_id
    m.facility_name = facility_name
    m.state = state
    m.notes = notes
    db.commit()
    db.refresh(m)
    return m


def get_mapping(db: Session, company: str) -> Optional[CompanyFacilityMap]:
    return db.get(CompanyFacilityMap, company.strip())


def list_mappings(db: Session, limit: int = 100, offset: int = 0) -> List[CompanyFacilityMap]:
    return db.query(CompanyFacilityMap).order_by(CompanyFacilityMap.company.asc()).offset(offset).limit(limit).all()
