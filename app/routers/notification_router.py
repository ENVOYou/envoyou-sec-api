"""
Notification API Router
API endpoints for notification management
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.models.database import get_db
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_service import NotificationService
from app.models.notification import (
    NotificationType,
    NotificationPriority,
    NotificationCategory
)


router = APIRouter(prefix="/api/notifications", tags=["notifications"])


# Pydantic models for API
class NotificationCreate(BaseModel):
    user_id: str = Field(..., description="User ID to send notification to")
    type: NotificationType = Field(default=NotificationType.IN_APP, description="Notification type")
    category: NotificationCategory = Field(default=NotificationCategory.SYSTEM, description="Notification category")
    priority: NotificationPriority = Field(default=NotificationPriority.MEDIUM, description="Notification priority")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    html_content: Optional[str] = Field(None, description="HTML content for rich notifications")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class NotificationResponse(BaseModel):
    id: int
    user_id: str
    type: str
    category: str
    priority: str
    title: str
    message: str
    html_content: Optional[str]
    read: bool
    read_at: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str
    expires_at: Optional[str]


class NotificationPreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    email_verification: Optional[bool] = None
    email_security: Optional[bool] = None
    email_billing: Optional[bool] = None
    email_marketing: Optional[bool] = None
    email_system: Optional[bool] = None

    in_app_enabled: Optional[bool] = None
    in_app_account: Optional[bool] = None
    in_app_security: Optional[bool] = None
    in_app_billing: Optional[bool] = None
    in_app_system: Optional[bool] = None
    in_app_marketing: Optional[bool] = None

    push_enabled: Optional[bool] = None
    push_account: Optional[bool] = None
    push_security: Optional[bool] = None
    push_billing: Optional[bool] = None
    push_system: Optional[bool] = None
    push_marketing: Optional[bool] = None


class NotificationPreferenceResponse(BaseModel):
    user_id: str
    email: Dict[str, bool]
    in_app: Dict[str, bool]
    push: Dict[str, bool]
    created_at: str
    updated_at: str


# Dependencies
def get_notification_repository(db: Session = Depends(get_db)) -> NotificationRepository:
    return NotificationRepository(db)

def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(db)


# Notification endpoints
@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks,
    repo: NotificationRepository = Depends(get_notification_repository),
    service: NotificationService = Depends(get_notification_service)
):
    """Create a new notification"""
    try:
        # Create notification in database
        notification_data = notification.dict()
        db_notification = repo.create_notification(notification_data)

        # Send notification based on type
        if notification.type == NotificationType.EMAIL:
            background_tasks.add_task(
                service.send_email_notification,
                notification.user_id,
                notification.title,
                notification.message,
                notification.category.value
            )
        elif notification.type == NotificationType.IN_APP:
            # In-app notification is already stored
            pass
        elif notification.type == NotificationType.PUSH:
            background_tasks.add_task(
                service.send_push_notification,
                notification.user_id,
                notification.title,
                notification.message,
                notification.category.value
            )

        return db_notification.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create notification: {str(e)}")


@router.get("/", response_model=List[NotificationResponse])
async def get_user_notifications(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(50, description="Maximum number of notifications to return"),
    offset: int = Query(0, description="Number of notifications to skip"),
    unread_only: bool = Query(False, description="Return only unread notifications"),
    category: Optional[NotificationCategory] = Query(None, description="Filter by category"),
    repo: NotificationRepository = Depends(get_notification_repository)
):
    """Get notifications for a user"""
    try:
        notifications = repo.get_user_notifications(
            user_id=user_id,
            limit=limit,
            offset=offset,
            unread_only=unread_only,
            category=category
        )
        return [notification.to_dict() for notification in notifications]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notifications: {str(e)}")


@router.get("/count")
async def get_notification_count(
    user_id: str = Query(..., description="User ID"),
    unread_only: bool = Query(False, description="Count only unread notifications"),
    repo: NotificationRepository = Depends(get_notification_repository)
):
    """Get notification count for a user"""
    try:
        count = repo.get_notification_count(user_id=user_id, unread_only=unread_only)
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notification count: {str(e)}")


@router.put("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    repo: NotificationRepository = Depends(get_notification_repository)
):
    """Mark a notification as read"""
    try:
        success = repo.mark_notification_as_read(notification_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {"message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark notification as read: {str(e)}")


@router.put("/read-all")
async def mark_all_notifications_as_read(
    user_id: str = Query(..., description="User ID"),
    repo: NotificationRepository = Depends(get_notification_repository)
):
    """Mark all notifications as read for a user"""
    try:
        count = repo.mark_all_user_notifications_as_read(user_id)
        return {"message": f"Marked {count} notifications as read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark notifications as read: {str(e)}")


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    repo: NotificationRepository = Depends(get_notification_repository)
):
    """Delete a notification"""
    try:
        success = repo.delete_notification(notification_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {"message": "Notification deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete notification: {str(e)}")


# Template endpoints
@router.get("/templates")
async def get_notification_templates(
    repo: NotificationRepository = Depends(get_notification_repository)
):
    """Get all notification templates"""
    try:
        templates = repo.get_all_templates()
        return [
            {
                "id": template.id,
                "key": template.key,
                "name": template.name,
                "description": template.description,
                "type": template.type.value,
                "category": template.category.value,
                "priority": template.priority.value,
                "subject_template": template.subject_template,
                "message_template": template.message_template,
                "html_template": template.html_template,
                "data_fields": template.data_fields,
                "is_active": template.is_active,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat(),
            }
            for template in templates
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")


@router.post("/send-template")
async def send_template_notification(
    template_key: str = Query(..., description="Template key"),
    user_id: str = Query(..., description="User ID"),
    data: Optional[Dict[str, Any]] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    service: NotificationService = Depends(get_notification_service)
):
    """Send notification using a template"""
    try:
        success = await service.send_template_notification(
            template_key=template_key,
            user_id=user_id,
            data=data or {},
            background_tasks=background_tasks
        )
        if not success:
            raise HTTPException(status_code=404, detail="Template not found or inactive")
        return {"message": "Template notification sent"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send template notification: {str(e)}")


# Preference endpoints
@router.get("/preferences/{user_id}", response_model=NotificationPreferenceResponse)
async def get_user_preferences(
    user_id: str,
    repo: NotificationRepository = Depends(get_notification_repository)
):
    """Get user notification preferences"""
    try:
        preferences = repo.get_user_preferences(user_id)
        if not preferences:
            raise HTTPException(status_code=404, detail="Preferences not found")
        return preferences.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get preferences: {str(e)}")


@router.put("/preferences/{user_id}", response_model=NotificationPreferenceResponse)
async def update_user_preferences(
    user_id: str,
    preferences: NotificationPreferenceUpdate,
    repo: NotificationRepository = Depends(get_notification_repository)
):
    """Update user notification preferences"""
    try:
        updated_preferences = repo.create_or_update_preferences(
            user_id=user_id,
            preferences_data=preferences.dict(exclude_unset=True)
        )
        return updated_preferences.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update preferences: {str(e)}")


@router.delete("/preferences/{user_id}")
async def delete_user_preferences(
    user_id: str,
    repo: NotificationRepository = Depends(get_notification_repository)
):
    """Delete user notification preferences"""
    try:
        success = repo.delete_user_preferences(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Preferences not found")
        return {"message": "Preferences deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete preferences: {str(e)}")


# Event-based notification endpoints
@router.post("/events/welcome")
async def send_welcome_notification(
    user_id: str = Query(..., description="User ID"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    service: NotificationService = Depends(get_notification_service)
):
    """Send welcome notification to new user"""
    try:
        await service.send_welcome_notification(user_id, background_tasks)
        return {"message": "Welcome notification sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send welcome notification: {str(e)}")


@router.post("/events/verification")
async def send_verification_notification(
    user_id: str = Query(..., description="User ID"),
    verification_code: str = Query(..., description="Verification code"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    service: NotificationService = Depends(get_notification_service)
):
    """Send email verification notification"""
    try:
        await service.send_verification_notification(user_id, verification_code, background_tasks)
        return {"message": "Verification notification sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send verification notification: {str(e)}")


@router.post("/events/password-reset")
async def send_password_reset_notification(
    user_id: str = Query(..., description="User ID"),
    reset_token: str = Query(..., description="Reset token"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    service: NotificationService = Depends(get_notification_service)
):
    """Send password reset notification"""
    try:
        await service.send_password_reset_notification(user_id, reset_token, background_tasks)
        return {"message": "Password reset notification sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send password reset notification: {str(e)}")


@router.post("/events/security-alert")
async def send_security_alert_notification(
    user_id: str = Query(..., description="User ID"),
    alert_type: str = Query(..., description="Type of security alert"),
    details: Optional[str] = Query(None, description="Additional details"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    service: NotificationService = Depends(get_notification_service)
):
    """Send security alert notification"""
    try:
        await service.send_security_alert_notification(user_id, alert_type, details, background_tasks)
        return {"message": "Security alert notification sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send security alert notification: {str(e)}")


@router.post("/events/billing")
async def send_billing_notification(
    user_id: str = Query(..., description="User ID"),
    billing_type: str = Query(..., description="Type of billing event"),
    amount: Optional[float] = Query(None, description="Amount involved"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    service: NotificationService = Depends(get_notification_service)
):
    """Send billing notification"""
    try:
        await service.send_billing_notification(user_id, billing_type, amount, background_tasks)
        return {"message": "Billing notification sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send billing notification: {str(e)}")


# Cleanup endpoint (admin only)
@router.post("/cleanup")
async def cleanup_expired_notifications(
    repo: NotificationRepository = Depends(get_notification_repository)
):
    """Clean up expired notifications (admin endpoint)"""
    try:
        deleted_count = repo.cleanup_expired_notifications()
        return {"message": f"Cleaned up {deleted_count} expired notifications"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup notifications: {str(e)}")
