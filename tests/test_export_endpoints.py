import os
from dotenv import load_dotenv
load_dotenv()

from fastapi.testclient import TestClient
from app.api_server import app

# ensure API key exists
os.environ.setdefault("API_KEYS", "test_key:Test Client:basic")

client = TestClient(app)
headers = {"X-API-Key": "test_key"}

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
