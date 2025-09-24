from __future__ import annotations

from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

# Reuse the shared Base so metadata aggregates under one registry
from .user import Base  # noqa: F401


class AuditTrail(Base):
    __tablename__ = "audit_trail"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Required fields per migration rule
    source_file = Column(String, nullable=False)  # e.g., s3://bucket/key or gcs://bucket/key
    calculation_version = Column(String, nullable=False)  # e.g., ef-static-v1 or model version
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    company_cik = Column(String, nullable=False, index=True)

    # Optional pointer fields for clarity (prefer one of them)
    s3_path = Column(String, nullable=True)
    gcs_path = Column(String, nullable=True)

    # Optional context
    notes = Column(String, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_file": self.source_file,
            "calculation_version": self.calculation_version,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "company_cik": self.company_cik,
            "s3_path": self.s3_path,
            "gcs_path": self.gcs_path,
            "notes": self.notes,
        }



