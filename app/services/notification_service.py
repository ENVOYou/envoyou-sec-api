"""
Notification Service
Centralized notification system for Envoyou API

Features:
- Email notifications via Mailgun
- In-app notifications (dashboard)
- Push notifications (mobile app placeholder)
- Event-based notifications
- Standardized English messaging
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session

from app.utils.email import email_service
from app.repositories.notification_repository import NotificationRepository
from app.models.notification import (
    NotificationType as DBNotificationType,
    NotificationPriority as DBNotificationPriority,
    NotificationCategory as DBNotificationCategory
)


class NotificationType(Enum):
    """Types of notifications"""
    EMAIL = "email"
    IN_APP = "in_app"
    PUSH = "push"
    SMS = "sms"  # Future use


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationCategory(Enum):
    """Notification categories"""
    ACCOUNT = "account"
    SECURITY = "security"
    BILLING = "billing"
    SYSTEM = "system"
    MARKETING = "marketing"
    SUPPORT = "support"


@dataclass
class NotificationTemplate:
    """Template for notifications"""
    type: NotificationType
    category: NotificationCategory
    priority: NotificationPriority
    subject: str
    message: str
    html_template: Optional[str] = None
    data_fields: Optional[List[str]] = None


@dataclass
class NotificationData:
    """Data structure for notification content"""
    user_id: str
    user_email: str
    subject: str
    message: str
    user_name: Optional[str] = None
    html_content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    priority: NotificationPriority = NotificationPriority.MEDIUM
    category: NotificationCategory = NotificationCategory.SYSTEM


class NotificationService:
    """Centralized notification service"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = NotificationRepository(db)
        self.templates = self._load_templates()
        self.notification_history = []  # Keep for backward compatibility, but prefer database

    def _load_templates(self) -> Dict[str, NotificationTemplate]:
        """Load notification templates"""
        return {
            # Account notifications
            "welcome": NotificationTemplate(
                type=NotificationType.EMAIL,
                category=NotificationCategory.ACCOUNT,
                priority=NotificationPriority.HIGH,
                subject="Welcome to Envoyou! 🎉",
                message="Welcome to Envoyou! Your account has been created successfully.",
                data_fields=["user_name", "login_url"]
            ),

            "email_verification": NotificationTemplate(
                type=NotificationType.EMAIL,
                category=NotificationCategory.SECURITY,
                priority=NotificationPriority.URGENT,
                subject="Verify Your Email - Envoyou",
                message="Please verify your email address to complete your registration.",
                data_fields=["verification_url", "user_name"]
            ),

            "password_reset": NotificationTemplate(
                type=NotificationType.EMAIL,
                category=NotificationCategory.SECURITY,
                priority=NotificationPriority.HIGH,
                subject="Reset Your Password - Envoyou",
                message="You requested a password reset. Click the link below to reset your password.",
                data_fields=["reset_url", "user_name"]
            ),

            "password_changed": NotificationTemplate(
                type=NotificationType.EMAIL,
                category=NotificationCategory.SECURITY,
                priority=NotificationPriority.MEDIUM,
                subject="Password Changed - Envoyou",
                message="Your password has been successfully changed.",
                data_fields=["user_name", "change_time"]
            ),

            # Billing notifications
            "payment_success": NotificationTemplate(
                type=NotificationType.EMAIL,
                category=NotificationCategory.BILLING,
                priority=NotificationPriority.MEDIUM,
                subject="Payment Successful - Envoyou",
                message="Your payment has been processed successfully.",
                data_fields=["amount", "plan_name", "user_name"]
            ),

            "payment_failed": NotificationTemplate(
                type=NotificationType.EMAIL,
                category=NotificationCategory.BILLING,
                priority=NotificationPriority.URGENT,
                subject="Payment Failed - Envoyou",
                message="Your payment could not be processed. Please update your payment method.",
                data_fields=["amount", "failure_reason", "user_name"]
            ),

            "subscription_expiring": NotificationTemplate(
                type=NotificationType.EMAIL,
                category=NotificationCategory.BILLING,
                priority=NotificationPriority.HIGH,
                subject="Subscription Expiring Soon - Envoyou",
                message="Your subscription will expire soon. Please renew to continue using our services.",
                data_fields=["expiry_date", "plan_name", "user_name"]
            ),

            # System notifications
            "new_feature": NotificationTemplate(
                type=NotificationType.IN_APP,
                category=NotificationCategory.SYSTEM,
                priority=NotificationPriority.MEDIUM,
                subject="New Feature Available",
                message="We've added a new feature to improve your experience.",
                data_fields=["feature_name", "feature_description"]
            ),

            "maintenance": NotificationTemplate(
                type=NotificationType.IN_APP,
                category=NotificationCategory.SYSTEM,
                priority=NotificationPriority.MEDIUM,
                subject="Scheduled Maintenance",
                message="We will be performing maintenance on our systems.",
                data_fields=["maintenance_time", "expected_downtime"]
            ),

            # Security notifications
            "login_alert": NotificationTemplate(
                type=NotificationType.EMAIL,
                category=NotificationCategory.SECURITY,
                priority=NotificationPriority.MEDIUM,
                subject="New Login Detected - Envoyou",
                message="We detected a new login to your account.",
                data_fields=["login_time", "login_location", "device_info"]
            ),

            "inactive_account": NotificationTemplate(
                type=NotificationType.EMAIL,
                category=NotificationCategory.SECURITY,
                priority=NotificationPriority.MEDIUM,
                subject="Account Inactive - Envoyou",
                message="We noticed you haven't logged in for a while. Your account security is important to us.",
                data_fields=["last_login", "days_inactive", "user_name"]
            ),

            # Support notifications
            "ticket_created": NotificationTemplate(
                type=NotificationType.IN_APP,
                category=NotificationCategory.SUPPORT,
                priority=NotificationPriority.MEDIUM,
                subject="Support Ticket Created",
                message="Your support ticket has been created and is being processed.",
                data_fields=["ticket_id", "ticket_subject"]
            ),

            "ticket_resolved": NotificationTemplate(
                type=NotificationType.IN_APP,
                category=NotificationCategory.SUPPORT,
                priority=NotificationPriority.MEDIUM,
                subject="Support Ticket Resolved",
                message="Your support ticket has been resolved.",
                data_fields=["ticket_id", "resolution_summary"]
            )
        }

    def send_notification(self, template_key: str, notification_data: NotificationData) -> bool:
        """
        Send notification using specified template

        Args:
            template_key: Key of the template to use
            notification_data: Data for the notification

        Returns:
            bool: True if notification sent successfully
        """
        if template_key not in self.templates:
            print(f"Template '{template_key}' not found")
            return False

        template = self.templates[template_key]

        # Merge template with data
        final_data = self._merge_template_data(template, notification_data)

        # Send based on notification type
        success = False

        if template.type == NotificationType.EMAIL:
            success = self._send_email_notification(final_data)
        elif template.type == NotificationType.IN_APP:
            success = self._send_in_app_notification(final_data)
        elif template.type == NotificationType.PUSH:
            success = self._send_push_notification(final_data)

        # Log notification
        self._log_notification(template_key, final_data, success)

        return success

    def _merge_template_data(self, template: NotificationTemplate, data: NotificationData) -> NotificationData:
        """Merge template data with notification data"""
        # This would typically use a templating engine like Jinja2
        # For now, we'll do simple string replacement

        merged_data = NotificationData(
            user_id=data.user_id,
            user_email=data.user_email,
            user_name=data.user_name,
            subject=template.subject,
            message=template.message,
            priority=template.priority,
            category=template.category,
            metadata=data.metadata or {}
        )

        # Replace placeholders in subject and message
        if data.user_name:
            merged_data.subject = merged_data.subject.replace("{user_name}", data.user_name)
            merged_data.message = merged_data.message.replace("{user_name}", data.user_name)

        # Add any additional data from metadata
        if data.metadata:
            for key, value in data.metadata.items():
                placeholder = f"{{{key}}}"
                merged_data.subject = merged_data.subject.replace(placeholder, str(value))
                merged_data.message = merged_data.message.replace(placeholder, str(value))

        return merged_data

    def _send_email_notification(self, data: NotificationData) -> bool:
        """Send email notification via Mailgun"""
        try:
            # Use existing email service
            html_content = self._generate_html_content(data)

            # Determine which email method to use based on content type
            if "verification" in data.subject.lower():
                return email_service.send_verification_email(data.user_email, "verification-token")
            elif "password" in data.subject.lower() and "reset" in data.subject.lower():
                return email_service.send_password_reset_email(data.user_email, "reset-token")
            elif "welcome" in data.subject.lower():
                return email_service.send_welcome_email(data.user_email, data.user_name or "User")
            else:
                # Generic email sending
                return self._send_generic_email(data.user_email, data.subject, html_content)

        except Exception as e:
            print(f"Email notification failed: {e}")
            return False

    def _send_generic_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send generic email using Mailgun API directly"""
        try:
            import requests
            import os

            api_key = os.getenv("MAILGUN_API_KEY")
            domain = os.getenv("MAILGUN_DOMAIN", "envoyou.com")
            from_email = os.getenv("FROM_EMAIL", "noreply@envoyou.com")

            if not api_key:
                print("Mailgun API key not configured")
                return False

            url = f"https://api.mailgun.net/v3/{domain}/messages"

            response = requests.post(
                url,
                auth=("api", api_key),
                data={
                    "from": f"Envoyou <{from_email}>",
                    "to": to_email,
                    "subject": subject,
                    "html": html_content
                },
                timeout=30
            )

            return response.status_code == 200

        except Exception as e:
            print(f"Generic email sending failed: {e}")
            return False

    def _send_in_app_notification(self, data: NotificationData) -> bool:
        """Send in-app notification (dashboard)"""
        try:
            # Save to database using repository
            notification_data = {
                "user_id": data.user_id,
                "type": DBNotificationType.IN_APP,
                "category": DBNotificationCategory(data.category.value),
                "priority": DBNotificationPriority(data.priority.value),
                "title": data.subject,
                "message": data.message,
                "html_content": data.html_content,
                "metadata": data.metadata
            }

            db_notification = self.repository.create_notification(notification_data)

            # Also keep in memory history for backward compatibility
            notification_record = {
                "id": db_notification.id,
                "user_id": data.user_id,
                "type": "in_app",
                "title": data.subject,
                "message": data.message,
                "priority": data.priority.value,
                "category": data.category.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "read": False,
                "metadata": data.metadata
            }

            self.notification_history.append(notification_record)

            print(f"In-app notification saved for user {data.user_id}: {data.subject}")
            return True

        except Exception as e:
            print(f"In-app notification failed: {e}")
            return False

    def _send_push_notification(self, data: NotificationData) -> bool:
        """Send push notification (mobile app)"""
        try:
            # Placeholder for push notification service (FCM, APNs, etc.)
            # In production, integrate with Firebase Cloud Messaging, Apple Push Notification Service, etc.

            push_data = {
                "user_id": data.user_id,
                "title": data.subject,
                "body": data.message,
                "priority": data.priority.value,
                "category": data.category.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": data.metadata
            }

            print(f"Push notification queued for user {data.user_id}: {data.subject}")
            print("(Push notification service not yet implemented - placeholder)")

            return True

        except Exception as e:
            print(f"Push notification failed: {e}")
            return False

    def _generate_html_content(self, data: NotificationData) -> str:
        """Generate HTML content for email notifications"""
        html_template = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">{data.subject}</h1>
            </div>
            <div style="background: white; padding: 40px 30px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <p style="color: #666; line-height: 1.6; font-size: 16px;">
                    {data.message}
                </p>

                {f'<div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;"><p style="margin: 0; color: #666;">Hello {data.user_name},</p></div>' if data.user_name else ''}

                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://api.envoyou.com/docs" style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">Visit Dashboard</a>
                </div>

                <p style="color: #999; font-size: 14px; text-align: center; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                    Need help? Contact our support team at <a href="mailto:support@envoyou.com" style="color: #667eea;">support@envoyou.com</a>
                </p>
            </div>
        </body>
        </html>
        """

        return html_template

    def _log_notification(self, template_key: str, data: NotificationData, success: bool):
        """Log notification for monitoring and debugging"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "template": template_key,
            "user_id": data.user_id,
            "user_email": data.user_email,
            "type": data.priority.value,
            "category": data.category.value,
            "success": success,
            "subject": data.subject
        }

        print(f"Notification logged: {json.dumps(log_entry, indent=2)}")

    # Event-based notification methods
    def notify_welcome(self, user_id: str, user_email: str, user_name: str) -> bool:
        """Send welcome notification to new user"""
        data = NotificationData(
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            metadata={"login_url": "https://api.envoyou.com/login"}
        )
        return self.send_notification("welcome", data)

    def notify_email_verification(self, user_id: str, user_email: str, user_name: str, verification_token: str) -> bool:
        """Send email verification notification"""
        data = NotificationData(
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            metadata={"verification_url": f"https://api.envoyou.com/auth/verify-email?token={verification_token}"}
        )
        return self.send_notification("email_verification", data)

    def notify_password_reset(self, user_id: str, user_email: str, user_name: str, reset_token: str) -> bool:
        """Send password reset notification"""
        data = NotificationData(
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            metadata={"reset_url": f"https://api.envoyou.com/auth/reset-password?token={reset_token}"}
        )
        return self.send_notification("password_reset", data)

    def notify_inactive_account(self, user_id: str, user_email: str, user_name: str, last_login: str, days_inactive: int) -> bool:
        """Send notification for inactive account"""
        data = NotificationData(
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            metadata={"last_login": last_login, "days_inactive": days_inactive}
        )
        return self.send_notification("inactive_account", data)

    def notify_new_feature(self, user_id: str, user_email: str, feature_name: str, feature_description: str) -> bool:
        """Send notification about new feature"""
        data = NotificationData(
            user_id=user_id,
            user_email=user_email,
            metadata={"feature_name": feature_name, "feature_description": feature_description}
        )
        return self.send_notification("new_feature", data)

    def notify_payment_success(self, user_id: str, user_email: str, user_name: str, amount: str, plan_name: str) -> bool:
        """Send payment success notification"""
        data = NotificationData(
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            metadata={"amount": amount, "plan_name": plan_name}
        )
        return self.send_notification("payment_success", data)

    def notify_login_alert(self, user_id: str, user_email: str, user_name: str, login_time: str, login_location: str, device_info: str) -> bool:
        """Send login alert notification"""
        data = NotificationData(
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            metadata={"login_time": login_time, "login_location": login_location, "device_info": device_info}
        )
        return self.send_notification("login_alert", data)

    # Event-based notification methods with background tasks support
    async def send_template_notification(
        self,
        template_key: str,
        user_id: str,
        data: Dict[str, Any],
        background_tasks: Any = None
    ) -> bool:
        """Send notification using template with background tasks support"""
        try:
            # Get user email from data or database (placeholder)
            user_email = data.get("user_email", f"user_{user_id}@envoyou.com")
            user_name = data.get("user_name")

            notification_data = NotificationData(
                user_id=user_id,
                user_email=user_email,
                user_name=user_name,
                subject="",  # Will be filled by template
                message="",  # Will be filled by template
                metadata=data
            )

            if background_tasks:
                background_tasks.add_task(self.send_notification, template_key, notification_data)
                return True
            else:
                return self.send_notification(template_key, notification_data)

        except Exception as e:
            print(f"Template notification failed: {e}")
            return False

    async def send_welcome_notification(self, user_id: str, background_tasks: Any = None):
        """Send welcome notification to new user"""
        data = {
            "user_email": f"user_{user_id}@envoyou.com",  # In production, get from user database
            "user_name": "New User",
            "login_url": "https://api.envoyou.com/login"
        }
        await self.send_template_notification("welcome", user_id, data, background_tasks)

    async def send_verification_notification(self, user_id: str, verification_code: str, background_tasks: Any = None):
        """Send email verification notification"""
        data = {
            "user_email": f"user_{user_id}@envoyou.com",  # In production, get from user database
            "user_name": "User",
            "verification_url": f"https://api.envoyou.com/auth/verify-email?code={verification_code}"
        }
        await self.send_template_notification("email_verification", user_id, data, background_tasks)

    async def send_password_reset_notification(self, user_id: str, reset_token: str, background_tasks: Any = None):
        """Send password reset notification"""
        data = {
            "user_email": f"user_{user_id}@envoyou.com",  # In production, get from user database
            "user_name": "User",
            "reset_url": f"https://api.envoyou.com/auth/reset-password?token={reset_token}"
        }
        await self.send_template_notification("password_reset", user_id, data, background_tasks)

    async def send_security_alert_notification(self, user_id: str, alert_type: str, details: str = None, background_tasks: Any = None):
        """Send security alert notification"""
        data = {
            "user_email": f"user_{user_id}@envoyou.com",  # In production, get from user database
            "user_name": "User",
            "alert_type": alert_type,
            "details": details or "",
            "alert_time": datetime.now(timezone.utc).isoformat()
        }
        await self.send_template_notification("login_alert", user_id, data, background_tasks)

    async def send_billing_notification(self, user_id: str, billing_type: str, amount: float = None, background_tasks: Any = None):
        """Send billing notification"""
        template_key = "payment_success" if billing_type == "success" else "payment_failed"

        data = {
            "user_email": f"user_{user_id}@envoyou.com",  # In production, get from user database
            "user_name": "User",
            "billing_type": billing_type,
            "amount": f"${amount:.2f}" if amount else "N/A",
            "transaction_time": datetime.now(timezone.utc).isoformat()
        }

        if billing_type == "failed":
            data["failure_reason"] = "Payment method declined"

        await self.send_template_notification(template_key, user_id, data, background_tasks)

    # Direct notification methods (for backward compatibility)
    def send_email_notification(self, user_id: str, subject: str, message: str, category: str = "system"):
        """Send email notification directly"""
        try:
            user_email = f"user_{user_id}@envoyou.com"  # In production, get from user database

            data = NotificationData(
                user_id=user_id,
                user_email=user_email,
                subject=subject,
                message=message,
                category=NotificationCategory(category)
            )

            return self._send_email_notification(data)
        except Exception as e:
            print(f"Direct email notification failed: {e}")
            return False

    def send_push_notification(self, user_id: str, title: str, message: str, category: str = "system"):
        """Send push notification directly"""
        try:
            user_email = f"user_{user_id}@envoyou.com"  # In production, get from user database

            data = NotificationData(
                user_id=user_id,
                user_email=user_email,
                subject=title,
                message=message,
                category=NotificationCategory(category)
            )

            return self._send_push_notification(data)
        except Exception as e:
            print(f"Direct push notification failed: {e}")
            return False

    # Utility methods
    def get_user_notifications(self, user_id: str, limit: int = 50, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get user notifications from database"""
        try:
            notifications = self.repository.get_user_notifications(
                user_id=user_id,
                limit=limit,
                unread_only=unread_only
            )
            return [notification.to_dict() for notification in notifications]
        except Exception as e:
            print(f"Failed to get user notifications: {e}")
            return []

    def mark_notification_read(self, notification_id: int) -> bool:
        """Mark notification as read"""
        try:
            return self.repository.mark_notification_as_read(notification_id)
        except Exception as e:
            print(f"Failed to mark notification as read: {e}")
            return False

    def get_notification_count(self, user_id: str, unread_only: bool = False) -> int:
        """Get notification count for user"""
        try:
            return self.repository.get_notification_count(user_id=user_id, unread_only=unread_only)
        except Exception as e:
            print(f"Failed to get notification count: {e}")
            return 0


# Global notification service instance (deprecated - use dependency injection instead)
# notification_service = NotificationService()
