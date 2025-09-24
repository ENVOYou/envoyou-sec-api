from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy import func
from app.models.user import Base

class AuditTrail(Base):
    __tablename__ = "audit_trail"

    id = Column(String, primary_key=True, default=lambda: __import__('uuid').uuid4().hex)
    source_file = Column(String, nullable=False)
    calculation_version = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    company_cik = Column(String, nullable=False, index=True)
    s3_path = Column(String, nullable=True)
    gcs_path = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    def to_dict(self):
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
