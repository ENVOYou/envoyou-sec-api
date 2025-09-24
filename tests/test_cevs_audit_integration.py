import os
import importlib


def test_compute_cevs_records_audit(tmp_path, monkeypatch):
    # set a dedicated sqlite DB for this test before importing modules
    db_path = tmp_path / "test_cevs.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    # Import modules after env is set
    from app.models import Base
    from app.models.database import engine, SessionLocal

    # create tables
    Base.metadata.create_all(bind=engine)

    # Now import compute_cevs
    from app.services.cevs_aggregator import compute_cevs_for_company
    from app.models.audit_trail import AuditTrail
    from sqlalchemy.orm import Session

    # run calculation
    result = compute_cevs_for_company("Audit Co", company_country="US")
    assert "score" in result

    # verify audit entry exists
    with SessionLocal() as db:
        rows = db.query(AuditTrail).filter_by(company_cik="Audit Co").all()
        assert len(rows) >= 1
