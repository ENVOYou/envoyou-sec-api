from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from passlib.context import CryptContext
import uuid

Base = declarative_base()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    company = Column(String)
    job_title = Column(String)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def set_password(self, password: str):
        """Hash and set the user's password"""
        self.password_hash = pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash"""
        return pwd_context.verify(password, self.password_hash)
    
    def to_dict(self):
        """Convert user object to dictionary (without password)"""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "company": self.company,
            "job_title": self.job_title,
            "email_verified": self.email_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
