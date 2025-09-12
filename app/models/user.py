from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import declarative_base, relationship
from passlib.context import CryptContext
import uuid
from datetime import datetime, timedelta, UTC

Base = declarative_base()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)  # Allow null for OAuth users
    name = Column(String, nullable=False)
    company = Column(String)
    job_title = Column(String)
    avatar_url = Column(String)
    timezone = Column(String, default="Asia/Jakarta")
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String)
    email_verification_expires = Column(DateTime(timezone=True))
    password_reset_token = Column(String)
    password_reset_expires = Column(DateTime(timezone=True))
    last_login = Column(DateTime(timezone=True))
    two_factor_secret = Column(String)
    two_factor_enabled = Column(Boolean, default=False)
    auth_provider = Column(String)  # 'google', 'github', etc.
    auth_provider_id = Column(String)  # ID from the OAuth provider
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    
    def set_password(self, password: str):
        """Hash and set the user's password"""
        self.password_hash = pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash"""
        if self.password_hash is None:
            return False  # OAuth users don't have passwords
        return pwd_context.verify(password, self.password_hash)
    
    def generate_verification_token(self):
        """Generate email verification token"""
        self.email_verification_token = str(uuid.uuid4())
        self.email_verification_expires = datetime.now(UTC) + timedelta(hours=24)
    
    def generate_reset_token(self):
        """Generate password reset token"""
        self.password_reset_token = str(uuid.uuid4())
        self.password_reset_expires = datetime.now(UTC) + timedelta(hours=1)
    
    def verify_verification_token(self, token: str) -> bool:
        """Verify email verification token"""
        if (self.email_verification_token == token and 
            self.email_verification_expires and 
            datetime.now(UTC) < self.email_verification_expires):
            self.email_verified = True
            self.email_verification_token = None
            self.email_verification_expires = None
            return True
        return False
    
    def verify_reset_token(self, token: str) -> bool:
        """Verify password reset token"""
        if (self.password_reset_token == token and 
            self.password_reset_expires and 
            datetime.now(UTC) < self.password_reset_expires):
            self.password_reset_token = None
            self.password_reset_expires = None
            return True
        return False
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.now(UTC)
    
    def setup_2fa(self, secret: str):
        """Setup 2FA with secret"""
        self.two_factor_secret = secret
        # Don't enable yet, wait for verification
    
    def enable_2fa(self):
        """Enable 2FA after verification"""
        self.two_factor_enabled = True
    
    def disable_2fa(self):
        """Disable 2FA"""
        self.two_factor_enabled = False
        self.two_factor_secret = None
    
    def verify_2fa_code(self, code: str) -> bool:
        """Verify 2FA code"""
        if not self.two_factor_secret or not self.two_factor_enabled:
            return False
        
        try:
            import pyotp
            totp = pyotp.TOTP(self.two_factor_secret)
            return totp.verify(code)
        except:
            return False
    
    def to_dict(self):
        """Convert user object to dictionary (without password)"""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "company": self.company,
            "job_title": self.job_title,
            "avatar_url": self.avatar_url,
            "timezone": self.timezone,
            "email_verified": self.email_verified,
            "two_factor_enabled": self.two_factor_enabled,
            "auth_provider": self.auth_provider,
            "has_local_password": self.password_hash is not None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
