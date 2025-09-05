from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
import secrets
import hashlib

# Use the same Base as User model
from .user import Base

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    key_hash = Column(String, nullable=False, unique=True)
    prefix = Column(String, nullable=False, unique=True)
    permissions = Column(Text, nullable=False, default="read")  # JSON string of permissions
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True))
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="api_keys")
    
    def __init__(self, user_id: str, name: str, permissions: list = None):
        self.user_id = user_id
        self.name = name
        self.permissions = str(permissions or ["read"])
        self._generate_key()
    
    def _generate_key(self):
        """Generate a secure API key with prefix"""
        # Generate random key
        raw_key = secrets.token_urlsafe(32)
        
        # Create prefix (first 8 chars of hash)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        self.prefix = f"env_{key_hash[:8]}"
        
        # Store hash of the full key
        self.key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Return the actual key (only shown once during creation)
        return f"{self.prefix}_{raw_key}"
    
    def verify_key(self, provided_key: str) -> bool:
        """Verify if provided key matches this API key"""
        try:
            # Extract the actual key part (after prefix_)
            if "_" not in provided_key:
                return False
            
            prefix, key_part = provided_key.split("_", 1)
            if prefix != self.prefix:
                return False
            
            # Hash the provided key and compare
            provided_hash = hashlib.sha256(key_part.encode()).hexdigest()
            return provided_hash == self.key_hash
        except:
            return False
    
    def update_usage(self):
        """Update last used timestamp and increment usage count"""
        from datetime import datetime
        self.last_used = datetime.utcnow()
        self.usage_count += 1
    
    def to_dict(self):
        """Convert to dictionary (without sensitive data)"""
        return {
            "id": self.id,
            "name": self.name,
            "prefix": self.prefix,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "usage_count": self.usage_count,
            "permissions": eval(self.permissions) if self.permissions else ["read"]
        }
