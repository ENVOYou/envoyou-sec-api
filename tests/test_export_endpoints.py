from fastapi.testclient import TestClient
from app.api_server import app

client = TestClient(app)
# Use built-in demo key from security module defaults
headers = {"X-API-Key": "demo_key_premium_2025"}


def test_export_cevs_json():
    r = client.get("/v1/export/sec/cevs/Test Company", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "summary" in data


def test_export_audit_csv():
    r = client.get("/v1/export/sec/audit?company_cik=Test Company", headers=headers)
    # OK even if empty
    assert r.status_code == 200
    assert "company_cik" in r.text or r.text == ""
