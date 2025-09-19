"""
Notification Models
Database models for storing notifications
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Enum
import enum

from app.models.user import Base


class NotificationType(str, enum.Enum):
    """Types of notifications"""
    EMAIL = "email"
    IN_APP = "in_app"
    PUSH = "push"
    SMS = "sms"


class NotificationPriority(str, enum.Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationCategory(str, enum.Enum):
    """Notification categories"""
    ACCOUNT = "account"
    SECURITY = "security"
    BILLING = "billing"
    SYSTEM = "system"
    MARKETING = "marketing"
    SUPPORT = "support"


class Notification(Base):
    """Notification model for storing user notifications"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    type = Column(Enum(NotificationType), nullable=False, default=NotificationType.IN_APP)
    category = Column(Enum(NotificationCategory), nullable=False, default=NotificationCategory.SYSTEM)
    priority = Column(Enum(NotificationPriority), nullable=False, default=NotificationPriority.MEDIUM)

    # Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    html_content = Column(Text, nullable=True)

    # Status
    read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    metadata_json = Column(JSON, nullable=True)  # Additional data like URLs, timestamps, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)  # For time-sensitive notifications

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, title={self.title}, read={self.read})>"

    def mark_as_read(self):
        """Mark notification as read"""
        self.read = True
        self.read_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type.value,
            "category": self.category.value,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "html_content": self.html_content,
            "read": self.read,
            # Backward compatible alias for frontend expecting `is_read`
            "is_read": self.read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "metadata": self.metadata_json,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class NotificationTemplate(Base):
    """Template model for storing notification templates"""
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Template configuration
    type = Column(Enum(NotificationType), nullable=False)
    category = Column(Enum(NotificationCategory), nullable=False)
    priority = Column(Enum(NotificationPriority), nullable=False, default=NotificationPriority.MEDIUM)

    # Content templates
    subject_template = Column(String(255), nullable=True)
    message_template = Column(Text, nullable=False)
    html_template = Column(Text, nullable=True)

    # Configuration
    data_fields = Column(JSON, nullable=True)  # Required fields for template
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<NotificationTemplate(id={self.id}, key={self.key}, name={self.name})>"


class NotificationPreference(Base):
    """User notification preferences"""
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, unique=True, index=True)

    # Email preferences
    email_enabled = Column(Boolean, default=True)
    email_verification = Column(Boolean, default=True)
    email_security = Column(Boolean, default=True)
    email_billing = Column(Boolean, default=True)
    email_marketing = Column(Boolean, default=False)
    email_system = Column(Boolean, default=True)

    # In-app preferences
    in_app_enabled = Column(Boolean, default=True)
    in_app_account = Column(Boolean, default=True)
    in_app_security = Column(Boolean, default=True)
    in_app_billing = Column(Boolean, default=True)
    in_app_system = Column(Boolean, default=True)
    in_app_marketing = Column(Boolean, default=False)

    # Push preferences (for future mobile app)
    push_enabled = Column(Boolean, default=True)
    push_account = Column(Boolean, default=True)
    push_security = Column(Boolean, default=True)
    push_billing = Column(Boolean, default=True)
    push_system = Column(Boolean, default=True)
    push_marketing = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<NotificationPreference(user_id={self.user_id}, email_enabled={self.email_enabled})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert preferences to dictionary"""
        return {
            "user_id": self.user_id,
            "email": {
                "enabled": self.email_enabled,
                "verification": self.email_verification,
                "security": self.email_security,
                "billing": self.email_billing,
                "marketing": self.email_marketing,
                "system": self.email_system,
            },
            "in_app": {
                "enabled": self.in_app_enabled,
                "account": self.in_app_account,
                "security": self.in_app_security,
                "billing": self.in_app_billing,
                "system": self.in_app_system,
                "marketing": self.in_app_marketing,
            },
            "push": {
                "enabled": self.push_enabled,
                "account": self.push_account,
                "security": self.push_security,
                "billing": self.push_billing,
                "system": self.push_system,
                "marketing": self.push_marketing,
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
