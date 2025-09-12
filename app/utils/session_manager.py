"""
Redis-based session management utilities.
This module provides se        if session_data:
            # Check if session is expired
            expires_at = datetime.fromisoformat(session_data.get("expires_at", ""))
            if datetime.now(UTC) > expires_at:
                # Session expired, delete it
                self.delete_session(session_id)
                return None

            # Update last active time
            session_data["last_active"] = datetime.now(UTC).isoformat()
            redis_store_session(session_id, session_data, self.session_ttl)

            return session_dataent using Redis as the primary storage.
"""

from typing import Dict, Any, Optional
import uuid
import hashlib
import json
from datetime import datetime, timedelta, UTC
import logging

from .redis_utils import redis_store_session, redis_get_session, redis_delete_session, redis_update_session_activity

logger = logging.getLogger(__name__)


class RedisSessionManager:
    """Redis-based session manager."""

    def __init__(self, session_ttl: int = 86400):  # 24 hours default
        self.session_ttl = session_ttl

    def create_session(self, user_id: str, user_data: Dict[str, Any],
                      device_info: Dict[str, Any] = None,
                      ip_address: str = None) -> str:
        """
        Create a new session and store it in Redis.

        Args:
            user_id: User ID
            user_data: User data dictionary
            device_info: Device information
            ip_address: Client IP address

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())

        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "user_data": user_data,
            "device_info": device_info or {},
            "ip_address": ip_address,
            "created_at": datetime.now(UTC).isoformat(),
            "last_active": datetime.now(UTC).isoformat(),
            "expires_at": (datetime.now(UTC) + timedelta(seconds=self.session_ttl)).isoformat()
        }

        if redis_store_session(session_id, session_data, self.session_ttl):
            logger.info(f"Session created for user {user_id}: {session_id}")
            return session_id
        else:
            logger.error(f"Failed to create session for user {user_id}")
            return None

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data from Redis.

        Args:
            session_id: Session ID

        Returns:
            Session data or None if not found/expired
        """
        session_data = redis_get_session(session_id)
        if session_data:
            # Check if session is expired
            expires_at = datetime.fromisoformat(session_data.get("expires_at", ""))
            if datetime.utcnow() > expires_at:
                # Session expired, delete it
                self.delete_session(session_id)
                return None

            # Update last active time
            session_data["last_active"] = datetime.utcnow().isoformat()
            redis_store_session(session_id, session_data, self.session_ttl)

            return session_data

        return None

    def update_session_activity(self, session_id: str) -> bool:
        """
        Update session last activity timestamp.

        Args:
            session_id: Session ID

        Returns:
            True if successful, False otherwise
        """
        return redis_update_session_activity(session_id, self.session_ttl)

    def delete_session(self, session_id: str) -> bool:
        """
        Delete session from Redis.

        Args:
            session_id: Session ID

        Returns:
            True if successful, False otherwise
        """
        success = redis_delete_session(session_id)
        if success:
            logger.info(f"Session deleted: {session_id}")
        else:
            logger.error(f"Failed to delete session: {session_id}")
        return success

    def validate_session(self, session_id: str, user_id: str = None) -> bool:
        """
        Validate if session exists and optionally matches user_id.

        Args:
            session_id: Session ID
            user_id: Optional user ID to validate against

        Returns:
            True if valid, False otherwise
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return False

        if user_id and session_data.get("user_id") != user_id:
            return False

        return True

    def get_user_sessions(self, user_id: str) -> list:
        """
        Get all active sessions for a user.
        Note: This is a simplified implementation. In production,
        you might want to maintain a separate index of user sessions.

        Args:
            user_id: User ID

        Returns:
            List of session data (simplified - only returns session IDs)
        """
        # This is a placeholder - in a real implementation,
        # you'd maintain an index of user sessions in Redis
        logger.warning("get_user_sessions is not fully implemented - requires session index")
        return []


# Global session manager instance
session_manager = RedisSessionManager()


def create_user_session(user_id: str, user_data: Dict[str, Any],
                       device_info: Dict[str, Any] = None,
                       ip_address: str = None) -> Optional[str]:
    """
    Convenience function to create a user session.

    Args:
        user_id: User ID
        user_data: User data
        device_info: Device information
        ip_address: Client IP address

    Returns:
        Session ID or None
    """
    return session_manager.create_session(user_id, user_data, device_info, ip_address)


def get_user_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get session data.

    Args:
        session_id: Session ID

    Returns:
        Session data or None
    """
    return session_manager.get_session(session_id)


def validate_user_session(session_id: str, user_id: str = None) -> bool:
    """
    Convenience function to validate session.

    Args:
        session_id: Session ID
        user_id: Optional user ID

    Returns:
        True if valid, False otherwise
    """
    return session_manager.validate_session(session_id, user_id)


def delete_user_session(session_id: str) -> bool:
    """
    Convenience function to delete session.

    Args:
        session_id: Session ID

    Returns:
        True if successful, False otherwise
    """
    return session_manager.delete_session(session_id)
