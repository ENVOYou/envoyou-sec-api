# Redis Integration Guide

## Overview
Backend sekarang terintegrasi dengan Upstash Redis untuk caching, rate limiting, dan background task processing.

## Features Implemented

### 1. Rate Limiting Middleware
- **Location**: `app/middleware/rate_limit.py`
- **Function**: Membatasi request per user/IP
- **Configuration**:
  - Authenticated users: 100 requests/minute
  - Unauthenticated users: 20 requests/minute
  - Special limits untuk auth endpoints (login: 5/hour, register: 3/hour)

### 2. Caching System
- **User Profile Caching**: `GET /v1/user/profile` (10 minutes TTL)
- **Notification Caching**: `GET /api/notifications/` (5 minutes TTL)
- **Auto-invalidation**: Cache dihapus saat data berubah

### 3. Background Task Queue
- **Email Queue**: Menggunakan Mailgun API
- **Paddle Webhook Queue**: Untuk payment processing
- **Processor**: `run_task_processor.py`

### 4. Email Service
- **Provider**: Mailgun
- **Features**: Template emails, bulk sending
- **Configuration**: Via environment variables

## Environment Variables

```bash
# Redis (Upstash)
REDIS_URL=rediss://default:...@host:6379

# Mailgun
MAILGUN_API_KEY=your_api_key
MAILGUN_DOMAIN=your_domain.mailgun.org
EMAIL_FROM=noreply@envoyou.com
EMAIL_FROM_NAME=Envoyou

# Paddle (Sandbox)
PADDLE_API_KEY=sandbox_api_key
PADDLE_ENVIRONMENT=sandbox
PADDLE_WEBHOOK_SECRET=webhook_secret
```

## Usage Examples

### Rate Limiting Headers
```http
GET /v1/user/profile
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1640995200
```

### Queue Email Task
```python
from app.services.redis_service import redis_service

redis_service.queue_email_task(
    to_email="user@example.com",
    subject="Welcome!",
    body="Welcome to Envoyou",
    template_data={"user_name": "John"}
)
```

### Cache User Profile
```python
redis_service.cache_user_profile(user_id, profile_data, ttl_seconds=600)
profile = redis_service.get_cached_user_profile(user_id)
```

## Running Background Tasks

```bash
# Terminal 1: Run API server
python start.py

# Terminal 2: Run task processor
python run_task_processor.py
```

## Monitoring

- Redis connection status logged saat startup
- Queue lengths dapat dicek via Redis CLI
- Rate limit violations logged dengan IP/user info
- Email sending success/failure logged

## Performance Benefits

1. **Database Load Reduction**: 90%+ profile queries dari cache
2. **API Protection**: Rate limiting mencegah abuse
3. **Scalability**: Background tasks tidak block API responses
4. **Reliability**: Graceful fallback jika Redis down