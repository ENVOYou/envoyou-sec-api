"""
SQLAlchemy model for emissions calculations
"""

from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .user import Base


class EmissionsCalculation(Base):
    """Model for storing emissions calculations"""
    __tablename__ = 'emissions_calculations'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    company = Column(String(255), nullable=False)
    scope1_data = Column(JSON, nullable=True)
    scope2_data = Column(JSON, nullable=True)
    results = Column(JSON, nullable=False)
    name = Column(Text, nullable=True)  # Optional name for saved calculations
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    user = relationship("User", back_populates="emissions_calculations")

    def __repr__(self):
        return f"<EmissionsCalculation(id={self.id}, company='{self.company}', user_id={self.user_id})>"