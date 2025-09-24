import os
from dotenv import load_dotenv
load_dotenv()

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.models.audit_trail import AuditTrail

# Setup test DB
DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL") or "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_create_and_list_audit(db):
    entry = AuditTrail(
        source_file="test_source.py",
        calculation_version="0.1",
        company_cik="000000000",
        notes="unit test entry"
    )
    db.add(entry)
    db.commit()

    results = db.query(AuditTrail).filter_by(company_cik="000000000").all()
    assert len(results) == 1
    assert results[0].source_file == "test_source.py"
