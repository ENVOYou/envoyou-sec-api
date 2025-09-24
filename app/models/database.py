from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os

# Database URL - use SQLite for development, can be changed to PostgreSQL for production
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for debugging
    )
else:
    engine = create_engine(DATABASE_URL, echo=False)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    from .user import Base
    from .api_key import Base as APIKeyBase
    from .session import Base as SessionBase
    from .notification import Base as NotificationBase
    # Import models to ensure they are registered with Base metadata
    from .audit_trail import AuditTrail  # noqa: F401
    from .company_map import CompanyFacilityMap  # noqa: F401
    # Create all tables using the same metadata
    Base.metadata.create_all(bind=engine)
