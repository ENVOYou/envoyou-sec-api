"""
Redis Service for caching and performance optimization
Uses Upstash Redis for cloud-based Redis service
"""

import json
import logging
from typing import Any, Optional, Union

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None  # type: ignore
    REDIS_AVAILABLE = False

from app.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Redis service for caching, rate limiting, and pub/sub operations"""

    def __init__(self):
        self.redis_client = None
        self._connect()

    def _connect(self):
        """Connect to Redis using environment configuration"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis package not available, Redis service disabled")
            return

        try:
            redis_url = settings.redis_url

            if not redis_url:
                logger.warning("Redis URL not configured, Redis service disabled")
                return

            # Connect to Upstash Redis (uses TLS)
            self.redis_client = redis.from_url(redis_url, decode_responses=True)

            # Test connection
            self.redis_client.ping()
            logger.info("✅ Redis connection established successfully")

        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.redis_client = None

    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        return self.redis_client is not None

    def ping(self) -> bool:
        """Ping Redis server to test connection"""
        if not self.is_connected():
            return False
        
        try:
            return self.redis_client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    def get_info(self) -> dict:
        """Get Redis server information"""
        if not self.is_connected():
            return {}
        
        try:
            return self.redis_client.info()
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {}

    # Caching Methods
    def set_cache(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Set cache value with TTL"""
        if not self.is_connected():
            return False

        try:
            # Serialize value to JSON if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)

            return self.redis_client.setex(key, ttl_seconds, value)
        except Exception as e:
            logger.error(f"Error setting cache for key {key}: {e}")
            return False

    def get_cache(self, key: str) -> Optional[Any]:
        """Get cache value"""
        if not self.is_connected():
            return None

        try:
            value = self.redis_client.get(key)
            if value is None:
                return None

            # Try to parse as JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Error getting cache for key {key}: {e}")
            return None

    def delete_cache(self, key: str) -> bool:
        """Delete cache key"""
        if not self.is_connected():
            return False

        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting cache for key {key}: {e}")
            return False

    def exists_cache(self, key: str) -> bool:
        """Check if cache key exists"""
        if not self.is_connected():
            return False

        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Error checking cache existence for key {key}: {e}")
            return False

    # Rate Limiting Methods
    def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """
        Check rate limit for a key
        Returns: (is_allowed, remaining_requests)
        """
        if not self.is_connected():
            return True, limit  # Allow if Redis is down

        try:
            # Use Redis sorted set for sliding window rate limiting
            now = int(__import__('time').time())
            window_start = now - window_seconds

            # Remove old entries
            self.redis_client.zremrangebyscore(key, '-inf', window_start)

            # Count current requests in window
            current_count = self.redis_client.zcard(key)

            if current_count >= limit:
                remaining = 0
                allowed = False
            else:
                # Add current request
                self.redis_client.zadd(key, {str(now): now})
                # Set expiration on the key
                self.redis_client.expire(key, window_seconds)
                remaining = limit - (current_count + 1)
                allowed = True

            return allowed, max(0, remaining)

        except Exception as e:
            logger.error(f"Error checking rate limit for key {key}: {e}")
            return True, limit  # Allow on error

    # User Profile Caching
    def cache_user_profile(self, user_id: str, profile_data: dict, ttl_seconds: int = 600) -> bool:
        """Cache user profile data"""
        cache_key = f"user:profile:{user_id}"
        return self.set_cache(cache_key, profile_data, ttl_seconds)

    def get_cached_user_profile(self, user_id: str) -> Optional[dict]:
        """Get cached user profile"""
        cache_key = f"user:profile:{user_id}"
        return self.get_cache(cache_key)

    def invalidate_user_profile_cache(self, user_id: str) -> bool:
        """Invalidate user profile cache"""
        cache_key = f"user:profile:{user_id}"
        return self.delete_cache(cache_key)

    # Notification Caching
    def cache_user_notifications(self, user_id: str, notifications: list, ttl_seconds: int = 300) -> bool:
        """Cache user notifications"""
        cache_key = f"user:notifications:{user_id}"
        return self.set_cache(cache_key, notifications, ttl_seconds)

    def get_cached_user_notifications(self, user_id: str) -> Optional[list]:
        """Get cached user notifications"""
        cache_key = f"user:notifications:{user_id}"
        return self.get_cache(cache_key)

    def invalidate_user_notifications_cache(self, user_id: str) -> bool:
        """Invalidate user notifications cache"""
        cache_key = f"user:notifications:{user_id}"
        return self.delete_cache(cache_key)

    # Generic key-value operations
    def set(self, key: str, value: Any) -> bool:
        """Set key-value without TTL"""
        if not self.is_connected():
            return False

        try:
            if not isinstance(value, str):
                value = json.dumps(value)
            return self.redis_client.set(key, value)
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        if not self.is_connected():
            return None

        try:
            value = self.redis_client.get(key)
            if value is None:
                return None

            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete key"""
        return self.delete_cache(key)

    def expire(self, key: str, ttl_seconds: int) -> bool:
        """Set expiration on key"""
        if not self.is_connected():
            return False

        try:
            return bool(self.redis_client.expire(key, ttl_seconds))
        except Exception as e:
            logger.error(f"Error setting expiration for key {key}: {e}")
            return False

    # Pub/Sub (Queue) Methods
    def publish_message(self, channel: str, message: Any) -> bool:
        """Publish message to Redis channel"""
        if not self.is_connected():
            return False

        try:
            if not isinstance(message, str):
                message = json.dumps(message)
            return bool(self.redis_client.publish(channel, message))
        except Exception as e:
            logger.error(f"Error publishing message to channel {channel}: {e}")
            return False

    def subscribe_to_channel(self, channel: str):
        """Subscribe to Redis channel (blocking operation)"""
        if not self.is_connected():
            return None

        try:
            pubsub = self.redis_client.pubsub()
            pubsub.subscribe(channel)
            return pubsub
        except Exception as e:
            logger.error(f"Error subscribing to channel {channel}: {e}")
            return None

    # Background Task Queue Methods
    def queue_task(self, queue_name: str, task_data: dict) -> bool:
        """Add task to Redis queue"""
        if not self.is_connected():
            return False

        try:
            # Use Redis list as queue (LPUSH for enqueue, RPOP for dequeue)
            task_json = json.dumps(task_data)
            return bool(self.redis_client.lpush(queue_name, task_json))
        except Exception as e:
            logger.error(f"Error queuing task to {queue_name}: {e}")
            return False

    def dequeue_task(self, queue_name: str) -> Optional[dict]:
        """Get task from Redis queue"""
        if not self.is_connected():
            return None

        try:
            # RPOP returns the last element (FIFO queue)
            task_json = self.redis_client.rpop(queue_name)
            if task_json:
                return json.loads(task_json)
            return None
        except Exception as e:
            logger.error(f"Error dequeuing task from {queue_name}: {e}")
            return None

    def get_queue_length(self, queue_name: str) -> int:
        """Get number of tasks in queue"""
        if not self.is_connected():
            return 0

        try:
            return self.redis_client.llen(queue_name)
        except Exception as e:
            logger.error(f"Error getting queue length for {queue_name}: {e}")
            return 0

    # Email Task Methods
    def queue_email_task(self, to_email: str, subject: str, body: str, template_data: dict = None) -> bool:
        """Queue email sending task"""
        task_data = {
            "type": "send_email",
            "to_email": to_email,
            "subject": subject,
            "body": body,
            "template_data": template_data or {},
            "timestamp": int(__import__('time').time())
        }
        return self.queue_task("email_queue", task_data)

    def queue_notification_email_task(self, user_id: str, template_key: str, template_data: dict = None) -> bool:
        """Queue notification email task"""
        task_data = {
            "type": "send_notification_email",
            "user_id": user_id,
            "template_key": template_key,
            "template_data": template_data or {},
            "timestamp": int(__import__('time').time())
        }
        return self.queue_task("email_queue", task_data)

    # Paddle Payment Task Methods
    def queue_paddle_webhook_task(self, webhook_data: dict) -> bool:
        """Queue Paddle webhook processing task"""
        task_data = {
            "type": "process_paddle_webhook",
            "webhook_data": webhook_data,
            "timestamp": int(__import__('time').time())
        }
        return self.queue_task("paddle_queue", task_data)


# Global Redis service instance
redis_service = RedisService()