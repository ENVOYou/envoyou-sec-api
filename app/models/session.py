from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
import hashlib
import json
from datetime import datetime, timedelta

# Use the same Base as User model
from .user import Base

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String, nullable=False, unique=True)
    device_info = Column(Text)  # JSON string containing device information
    ip_address = Column(String)
    location = Column(String)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="sessions")
    
    def __init__(self, user_id: str, token: str, device_info: dict = None, ip_address: str = None):
        self.user_id = user_id
        self.device_info = json.dumps(device_info or {})
        self.ip_address = ip_address
        
        # Hash the token for storage
        self.token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Set expiration (30 days from now)
        self.expires_at = datetime.utcnow() + timedelta(days=30)
    
    def update_activity(self):
        """Update last active timestamp"""
        self.last_active = datetime.utcnow()
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    def verify_token(self, token: str) -> bool:
        """Verify if provided token matches this session"""
        provided_hash = hashlib.sha256(token.encode()).hexdigest()
        return provided_hash == self.token_hash
    
    def get_device_info(self) -> dict:
        """Get device information as dictionary"""
        try:
            return json.loads(self.device_info) if self.device_info else {}
        except:
            return {}
    
    def to_dict(self):
        """Convert to dictionary for API response"""
        device_info = self.get_device_info()
        
        return {
            "id": self.id,
            "device": device_info.get("device", "Unknown Device"),
            "ip": self.ip_address or "Unknown",
            "location": self.location or "Unknown",
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "current": False  # Will be set by the API
        }
