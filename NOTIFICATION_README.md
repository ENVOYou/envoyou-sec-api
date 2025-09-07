# Notification System Documentation

## Overview

The Envoyou API now includes a comprehensive notification system that supports multiple channels:
- **Email notifications** via Mailgun
- **In-app notifications** stored in database
- **Push notifications** (placeholder for mobile apps)
- **Event-based notifications** triggered by user actions

## Features

### ✅ Completed Features
- Email notifications via Mailgun API
- In-app notifications with database storage
- Notification templates for standardized messaging
- Event-based notification triggers
- User notification preferences
- RESTful API endpoints for notification management
- Background task processing for notifications
- Database models and repositories
- Notification cleanup and maintenance

### 🔄 Future Enhancements
- Push notification service integration (FCM/APNs)
- Real-time notification delivery (WebSocket)
- Notification analytics and reporting
- Advanced template customization
- Mobile app notification integration

## Database Tables

The notification system creates three main tables:

### `notifications`
Stores individual notifications for users
```sql
- id: Primary key
- user_id: User identifier
- type: Notification type (email/in_app/push)
- category: Notification category (account/security/billing/system)
- priority: Notification priority (low/medium/high/urgent)
- title: Notification title
- message: Notification message
- html_content: Rich HTML content (optional)
- read: Read status
- read_at: Timestamp when read
- metadata: Additional data (JSON)
- created_at: Creation timestamp
- updated_at: Last update timestamp
- expires_at: Expiration timestamp (optional)
```

### `notification_templates`
Stores reusable notification templates
```sql
- id: Primary key
- key: Template identifier
- name: Template name
- description: Template description
- type: Notification type
- category: Notification category
- priority: Notification priority
- subject_template: Email subject template
- message_template: Message template
- html_template: HTML template (optional)
- data_fields: Required data fields (JSON)
- is_active: Template status
- created_at: Creation timestamp
- updated_at: Last update timestamp
```

### `notification_preferences`
Stores user notification preferences
```sql
- id: Primary key
- user_id: User identifier
- email_enabled: Master email toggle
- email_verification: Email verification notifications
- email_security: Security-related emails
- email_billing: Billing-related emails
- email_marketing: Marketing emails
- email_system: System emails
- in_app_enabled: Master in-app toggle
- in_app_*: Individual in-app preferences
- push_enabled: Master push toggle
- push_*: Individual push preferences
- created_at: Creation timestamp
- updated_at: Last update timestamp
```

## API Endpoints

### Notification Management

#### Create Notification
```http
POST /api/notifications/
Content-Type: application/json

{
  "user_id": "user123",
  "type": "in_app",
  "category": "system",
  "priority": "medium",
  "title": "Welcome to Envoyou!",
  "message": "Your account has been created successfully.",
  "metadata": {"login_url": "https://api.envoyou.com/login"}
}
```

#### Get User Notifications
```http
GET /api/notifications/?user_id=user123&limit=50&unread_only=false
```

#### Mark Notification as Read
```http
PUT /api/notifications/{notification_id}/read
```

#### Get Notification Count
```http
GET /api/notifications/count?user_id=user123&unread_only=true
```

### Event-Based Notifications

#### Send Welcome Notification
```http
POST /api/notifications/events/welcome?user_id=user123
```

#### Send Email Verification
```http
POST /api/notifications/events/verification?user_id=user123&verification_code=ABC123
```

#### Send Password Reset
```http
POST /api/notifications/events/password-reset?user_id=user123&reset_token=XYZ789
```

#### Send Security Alert
```http
POST /api/notifications/events/security-alert?user_id=user123&alert_type=login&details=New device login
```

#### Send Billing Notification
```http
POST /api/notifications/events/billing?user_id=user123&billing_type=success&amount=29.99
```

### Template Management

#### Get All Templates
```http
GET /api/notifications/templates
```

#### Send Template Notification
```http
POST /api/notifications/send-template?template_key=welcome&user_id=user123
```

### User Preferences

#### Get User Preferences
```http
GET /api/notifications/preferences/{user_id}
```

#### Update User Preferences
```http
PUT /api/notifications/preferences/{user_id}
Content-Type: application/json

{
  "email_enabled": true,
  "email_marketing": false,
  "in_app_enabled": true,
  "push_enabled": true
}
```

## Setup Instructions

### 1. Database Migration

Run the migration script to create notification tables:

```bash
python run_notification_migration.py
```

### 2. Environment Variables

Ensure these environment variables are set:

```bash
# Mailgun Configuration
MAILGUN_API_KEY=your_mailgun_api_key
MAILGUN_DOMAIN=envoyou.com
FROM_EMAIL=noreply@envoyou.com

# Database
DATABASE_URL=sqlite:///app.db
```

### 3. Service Integration

The notification service is automatically integrated with the FastAPI application. All notification endpoints are available at `/api/notifications/`.

## Usage Examples

### Python Service Integration

```python
from app.services.notification_service import NotificationService
from app.database import get_db

# Get database session
db = next(get_db())

# Initialize notification service
notification_service = NotificationService(db)

# Send welcome notification
await notification_service.send_welcome_notification("user123")

# Send custom notification
success = notification_service.send_email_notification(
    user_id="user123",
    subject="Custom Subject",
    message="Custom message content",
    category="system"
)

# Get user notifications
notifications = notification_service.get_user_notifications("user123", limit=10)
```

### JavaScript/React Integration

```javascript
// Get user notifications
const response = await fetch('/api/notifications/?user_id=user123&limit=20');
const notifications = await response.json();

// Mark notification as read
await fetch(`/api/notifications/${notificationId}/read`, {
  method: 'PUT'
});

// Send welcome notification
await fetch('/api/notifications/events/welcome?user_id=user123', {
  method: 'POST'
});
```

## Notification Templates

### Available Templates

| Template Key | Type | Category | Description |
|-------------|------|----------|-------------|
| `welcome` | Email | Account | Welcome new users |
| `email_verification` | Email | Security | Email verification |
| `password_reset` | Email | Security | Password reset |
| `password_changed` | Email | Security | Password change confirmation |
| `payment_success` | Email | Billing | Payment success |
| `payment_failed` | Email | Billing | Payment failure |
| `subscription_expiring` | Email | Billing | Subscription expiration warning |
| `login_alert` | Email | Security | New login detection |
| `inactive_account` | Email | Security | Inactive account reminder |
| `new_feature` | In-App | System | New feature announcement |
| `maintenance` | In-App | System | Maintenance notice |
| `ticket_created` | In-App | Support | Support ticket creation |
| `ticket_resolved` | In-App | Support | Support ticket resolution |

### Custom Templates

To add custom templates, insert into the `notification_templates` table:

```sql
INSERT INTO notification_templates (
  key, name, type, category, priority,
  subject_template, message_template, data_fields
) VALUES (
  'custom_template',
  'Custom Notification',
  'email',
  'system',
  'medium',
  'Custom Subject: {custom_field}',
  'Custom message with {custom_field}',
  '["custom_field"]'
);
```

## Monitoring and Maintenance

### Cleanup Expired Notifications

```http
POST /api/notifications/cleanup
```

This endpoint removes expired notifications from the database.

### Notification Statistics

Monitor notification delivery and user engagement through the API endpoints.

## Security Considerations

- All notification endpoints require proper authentication
- User preferences are respected for all notification types
- Sensitive information is not included in notification metadata
- Email verification tokens expire appropriately
- Database queries are optimized with proper indexing

## Troubleshooting

### Common Issues

1. **Email notifications not sending**
   - Check Mailgun API key and domain configuration
   - Verify FROM_EMAIL environment variable
   - Check Mailgun dashboard for delivery status

2. **In-app notifications not appearing**
   - Verify database connection
   - Check user_id format consistency
   - Ensure notification tables exist

3. **Template not found errors**
   - Verify template key exists in database
   - Check template is_active status
   - Ensure data fields match template requirements

### Debug Mode

Enable debug logging by setting:
```bash
DEBUG=true
```

## Future Roadmap

- [ ] Push notification service integration
- [ ] Real-time WebSocket notifications
- [ ] Notification analytics dashboard
- [ ] Advanced template editor
- [ ] Mobile app notification support
- [ ] Notification scheduling
- [ ] Bulk notification sending
- [ ] Notification delivery receipts

## Support

For issues or questions about the notification system:
- Check this documentation first
- Review API endpoint responses for error details
- Contact the development team for technical support
