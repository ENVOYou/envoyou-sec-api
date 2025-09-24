from __future__ import annotations

from sqlalchemy import Column, String, DateTime, func, Text
from app.models.user import Base

class CompanyFacilityMap(Base):
    __tablename__ = "company_facility_map"

    company = Column(String, primary_key=True, index=True)  # key by company name/CIK
    facility_id = Column(String, nullable=False)
    facility_name = Column(String, nullable=True)
    state = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
