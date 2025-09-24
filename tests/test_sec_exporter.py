from app.services.sec_exporter import cevs_to_sec_json, audit_trails_to_csv

def test_cevs_to_sec_json():
    sample = {
        "company": "Test Co",
        "country": "US",
        "score": 72.5,
        "components": {"base": 50, "iso_bonus": 20, "epa_penalty": -5.0},
        "sources": {"epa_matches": 2},
    }
    out = cevs_to_sec_json(sample)
    assert out["summary"]["score"] == 72.5
    assert out["company"] == "Test Co"


def test_audit_trails_to_csv():
    entries = [
        {
            "id": "1",
            "timestamp": "2025-09-24T00:00:00Z",
            "company_cik": "000000001",
            "source_file": "calc.py",
            "calculation_version": "0.1",
            "s3_path": None,
            "gcs_path": None,
            "notes": "ok",
        }
    ]
    csv_out = audit_trails_to_csv(entries)
    assert "company_cik" in csv_out
    assert "000000001" in csv_out
