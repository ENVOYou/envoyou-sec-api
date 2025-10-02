from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func, Text
from sqlalchemy.orm import declarative_base, relationship
import uuid
import secrets
import hashlib
from datetime import datetime, UTC

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
        
        # Store hash of the raw key (not the full key with prefix)
        self.key_hash = key_hash
        
        # Return the actual key (only shown once during creation)
        return f"{self.prefix}_{raw_key}"
    
    def verify_key(self, provided_key: str) -> bool:
        """Verify if provided key matches this API key"""
        try:
            # Check if key starts with our prefix
            if not provided_key.startswith(self.prefix + "_"):
                return False
            
            # Extract the raw key part after prefix_
            raw_key = provided_key[len(self.prefix) + 1:]
            
            # Hash the raw key and compare with stored hash
            provided_hash = hashlib.sha256(raw_key.encode()).hexdigest()
            return provided_hash == self.key_hash
        except:
            return False
    
    def update_usage(self):
        """Update last used timestamp and increment usage count"""
        from datetime import datetime
        self.last_used = datetime.now(UTC)
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
