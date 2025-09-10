# Redis Implementation for Envoyou API

This document describes the Redis implementation for rate limiting, session management, and API response caching in the Envoyou API.

## Overview

The Envoyou API now uses Redis (Upstash) for:
- **Rate Limiting**: Per-user/API key rate limiting with sliding window
- **Session Management**: Redis-based session storage with fallback to database
- **API Response Caching**: Intelligent caching of API responses
- **General Caching**: Enhanced caching system with Redis backend

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Redis Configuration (Production - Upstash)
REDIS_URL="rediss://default:your-redis-password@your-upstash-host:6379"

# Redis Settings
REDIS_CACHE_PREFIX="envoyou:cache"
REDIS_RATE_LIMIT_PREFIX="envoyou:ratelimit"
REDIS_SESSION_PREFIX="envoyou:sessions"
REDIS_CACHE_TTL="3600"

# Optional: Enable Redis Sessions
USE_REDIS_SESSIONS="true"
```

### Dependencies

Add to `requirements.txt`:
```txt
redis==6.4.0
```

## Features

### 1. Rate Limiting with Redis

**Location**: `app/utils/security.py`

**Features**:
- Sliding window rate limiting using Redis sorted sets
- Per-user/API key limiting
- Automatic cleanup of expired entries
- Fallback to in-memory limiting if Redis unavailable

**Usage**:
```python
from app.utils.redis_utils import redis_rate_limit

# Check if request is allowed (30 requests per minute)
allowed = redis_rate_limit("user_123", 30, 60)
if not allowed:
    raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

### 2. Session Management with Redis

**Location**: `app/utils/session_manager.py`

**Features**:
- Redis-based session storage
- Automatic expiration handling
- Session validation and activity tracking
- Fallback to database sessions

**Usage**:
```python
from app.utils.session_manager import create_user_session, get_user_session

# Create session
session_id = create_user_session(
    user_id="user_123",
    user_data={"email": "user@example.com", "name": "User"},
    device_info={"browser": "Chrome"},
    ip_address="192.168.1.1"
)

# Get session
session_data = get_user_session(session_id)
```

**API Endpoints**:
- `GET /auth/sessions/redis/{session_id}` - Get session info
- `DELETE /auth/sessions/redis/{session_id}` - Delete session

### 3. API Response Caching

**Location**: `app/utils/response_cache.py`

**Features**:
- Intelligent cache key generation
- Automatic cache invalidation
- Response compression support
- Configurable TTL per endpoint

**Usage**:
```python
from app.utils.response_cache import response_cache

# In your route handler
@router.get("/api/data")
async def get_data(request: Request):
    # Try cache first
    cached = response_cache.get(request)
    if cached:
        return JSONResponse(content=cached)

    # Generate fresh data
    data = generate_fresh_data()

    # Cache response (30 minutes)
    response_cache.set(request, data, ttl=1800)

    return JSONResponse(content=data)
```

### 4. Enhanced Health Check

**Location**: `app/routes/health.py`

The health check now includes Redis status:

```json
{
  "system": {
    "redis": {
      "status": "healthy",
      "available": true
    }
  },
  "services": {
    "rate_limiting": "redis",
    "session_storage": "redis"
  }
}
```

## Implementation Details

### Redis Utilities (`app/utils/redis_utils.py`)

Core Redis operations:
- Connection management with SSL support
- Rate limiting with sorted sets
- Session CRUD operations
- Response caching
- Health monitoring

### Cache Enhancement (`app/utils/cache.py`)

Enhanced the existing cache system:
- Redis as primary backend
- In-memory fallback
- Automatic failover
- Better error handling

### Security Integration (`app/utils/security.py`)

Updated rate limiting:
- Redis-based rate limiting
- Backward compatibility
- Graceful degradation

## Testing

Run the comprehensive test suite:

```bash
cd /home/husni/api-envoyou
python3 test_redis_implementation.py
```

Test results should show:
- ✅ Redis Connection: PASSED
- ✅ Rate Limiting: PASSED
- ✅ Session Management: PASSED
- ✅ Response Caching: PASSED

## Performance Benefits

### Before Redis:
- Rate limiting: In-memory (lost on restart)
- Sessions: Database queries
- Caching: In-memory only
- No persistence across server restarts

### After Redis:
- Rate limiting: Persistent, distributed
- Sessions: Fast Redis lookups
- Caching: Persistent, shared across instances
- High availability with Upstash

## Monitoring

### Health Check Endpoint
```
GET /health
```

Returns Redis status and availability.

### Logging
All Redis operations are logged with appropriate levels:
- Connection status
- Cache hits/misses
- Rate limit violations
- Session operations

## Best Practices

1. **Connection Pooling**: Redis client handles connection pooling automatically
2. **Error Handling**: All operations have try/catch with fallbacks
3. **TTL Management**: Appropriate TTL values for different data types
4. **Key Naming**: Consistent prefixing for different data types
5. **Monitoring**: Regular health checks and monitoring

## Troubleshooting

### Redis Connection Issues
- Check `REDIS_URL` in environment
- Verify Upstash credentials
- Check network connectivity

### Rate Limiting Not Working
- Verify Redis connection
- Check rate limit prefixes
- Monitor Redis memory usage

### Session Issues
- Enable `USE_REDIS_SESSIONS=true`
- Check session TTL settings
- Verify session key format

## Migration Notes

- Existing in-memory cache continues to work
- Database sessions remain functional
- Gradual rollout possible with feature flags
- Backward compatibility maintained

## Future Enhancements

- Redis clustering support
- Advanced caching strategies (LRU, LFU)
- Session replication across regions
- Real-time rate limit monitoring
- Cache warming strategies
