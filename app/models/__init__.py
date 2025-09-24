"""
Models package initialization
Import all models in the correct order to avoid circular dependencies
"""

# Import Base first
from .user import Base

# Import all models in dependency order
from .user import User
from .api_key import APIKey
from .session import Session
from .permit import Permit
from .permit_search import PermitSearchParams
from .external_data import AirQualityData
from .notification import (
    Notification,
    NotificationTemplate,
    NotificationPreference
)
from .audit_trail import AuditTrail
from .company_map import CompanyFacilityMap

# Make all models available at package level
__all__ = [
    "Base",
    "User",
    "APIKey",
    "Session",
    "Permit",
    "PermitSearchParams",
    "AirQualityData",
    "Notification",
    "NotificationTemplate",
    "NotificationPreference",
    "AuditTrail",
    "CompanyFacilityMap",
]
