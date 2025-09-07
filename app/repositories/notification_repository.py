"""
Notification Repository
Database operations for notifications
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.notification import (
    Notification,
    NotificationTemplate,
    NotificationPreference,
    NotificationType,
    NotificationPriority,
    NotificationCategory
)


class NotificationRepository:
    """Repository for notification database operations"""

    def __init__(self, db: Session):
        self.db = db

    # Notification CRUD operations
    def create_notification(self, notification_data: Dict[str, Any]) -> Notification:
        """Create a new notification"""
        notification = Notification(**notification_data)
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_notification_by_id(self, notification_id: int) -> Optional[Notification]:
        """Get notification by ID"""
        return self.db.query(Notification).filter(Notification.id == notification_id).first()

    def get_user_notifications(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
        category: Optional[NotificationCategory] = None
    ) -> List[Notification]:
        """Get notifications for a user"""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)

        if unread_only:
            query = query.filter(Notification.read == False)

        if category:
            query = query.filter(Notification.category == category)

        return query.order_by(desc(Notification.created_at)).limit(limit).offset(offset).all()

    def mark_notification_as_read(self, notification_id: int) -> bool:
        """Mark a notification as read"""
        notification = self.get_notification_by_id(notification_id)
        if notification:
            notification.mark_as_read()
            self.db.commit()
            return True
        return False

    def mark_all_user_notifications_as_read(self, user_id: str) -> int:
        """Mark all user notifications as read"""
        result = self.db.query(Notification).filter(
            and_(Notification.user_id == user_id, Notification.read == False)
        ).update({"read": True, "read_at": datetime.now(timezone.utc)})
        self.db.commit()
        return result

    def delete_notification(self, notification_id: int) -> bool:
        """Delete a notification"""
        notification = self.get_notification_by_id(notification_id)
        if notification:
            self.db.delete(notification)
            self.db.commit()
            return True
        return False

    def get_notification_count(self, user_id: str, unread_only: bool = False) -> int:
        """Get notification count for a user"""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)

        if unread_only:
            query = query.filter(Notification.read == False)

        return query.count()

    def cleanup_expired_notifications(self) -> int:
        """Delete expired notifications"""
        now = datetime.now(timezone.utc)
        result = self.db.query(Notification).filter(
            and_(Notification.expires_at.isnot(None), Notification.expires_at < now)
        ).delete()
        self.db.commit()
        return result

    # Template operations
    def get_template_by_key(self, key: str) -> Optional[NotificationTemplate]:
        """Get template by key"""
        return self.db.query(NotificationTemplate).filter(
            and_(NotificationTemplate.key == key, NotificationTemplate.is_active == True)
        ).first()

    def get_all_templates(self) -> List[NotificationTemplate]:
        """Get all active templates"""
        return self.db.query(NotificationTemplate).filter(NotificationTemplate.is_active == True).all()

    def create_template(self, template_data: Dict[str, Any]) -> NotificationTemplate:
        """Create a new template"""
        template = NotificationTemplate(**template_data)
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    # Preference operations
    def get_user_preferences(self, user_id: str) -> Optional[NotificationPreference]:
        """Get user notification preferences"""
        return self.db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()

    def create_or_update_preferences(self, user_id: str, preferences_data: Dict[str, Any]) -> NotificationPreference:
        """Create or update user preferences"""
        preferences = self.get_user_preferences(user_id)

        if preferences:
            # Update existing preferences
            for key, value in preferences_data.items():
                if hasattr(preferences, key):
                    setattr(preferences, key, value)
        else:
            # Create new preferences
            preferences_data['user_id'] = user_id
            preferences = NotificationPreference(**preferences_data)
            self.db.add(preferences)

        self.db.commit()
        self.db.refresh(preferences)
        return preferences

    def delete_user_preferences(self, user_id: str) -> bool:
        """Delete user preferences"""
        preferences = self.get_user_preferences(user_id)
        if preferences:
            self.db.delete(preferences)
            self.db.commit()
            return True
        return False

    # Bulk operations
    def create_bulk_notifications(self, notifications_data: List[Dict[str, Any]]) -> List[Notification]:
        """Create multiple notifications at once"""
        notifications = [Notification(**data) for data in notifications_data]
        self.db.add_all(notifications)
        self.db.commit()
        for notification in notifications:
            self.db.refresh(notification)
        return notifications

    def get_notifications_by_category(
        self,
        category: NotificationCategory,
        limit: int = 100
    ) -> List[Notification]:
        """Get notifications by category"""
        return self.db.query(Notification).filter(
            Notification.category == category
        ).order_by(desc(Notification.created_at)).limit(limit).all()

    def get_notifications_by_priority(
        self,
        priority: NotificationPriority,
        limit: int = 100
    ) -> List[Notification]:
        """Get notifications by priority"""
        return self.db.query(Notification).filter(
            Notification.priority == priority
        ).order_by(desc(Notification.created_at)).limit(limit).all()
