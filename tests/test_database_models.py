from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.models.notification import Notification
from app.models.audit_trail import AuditTrail
import os

# Prefer test DB URL, fallback to DATABASE_URL, else default to sqlite test db
database_url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL") or "sqlite:///./test.db"

# Create a test database engine
engine = create_engine(database_url)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def test_db():
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop the database tables after the test
        Base.metadata.drop_all(bind=engine)

def test_notification_model(test_db):
    session = test_db  # Use the session object directly
    notification = Notification(
        user_id="test_user",
        type="email",
        category="system",
        priority="high",
        title="Test Notification",
        message="This is a test notification."
    )
    session.add(notification)
    session.commit()

    # Verify the notification was added
    result = session.query(Notification).filter_by(user_id="test_user").first()
    assert result is not None
    assert result.title == "Test Notification"

def test_audit_trail_model(test_db):
    session = test_db  # Use the session object directly
    audit_entry = AuditTrail(
        source_file="test_file.py",
        calculation_version="1.0",
        company_cik="123456789",
        notes="Test audit trail entry."
    )
    session.add(audit_entry)
    session.commit()

    # Verify the audit trail entry was added
    result = session.query(AuditTrail).filter_by(company_cik="123456789").first()
    assert result is not None
    assert result.source_file == "test_file.py"