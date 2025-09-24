import os
from dotenv import load_dotenv
load_dotenv()

from fastapi.testclient import TestClient
from app.api_server import app

client = TestClient(app)
headers = {"X-API-Key": "demo_key_premium_2025"}


def test_export_package_local():
    payload = {
        "company": "DemoCo",
        "scope1": {"fuel_type": "diesel", "amount": 5, "unit": "gallon"},
        "scope2": {"kwh": 500, "grid_region": "US_default"},
        "state": "TX"
    }
    r = client.post("/v1/export/sec/package", json=payload, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert data["filename"].endswith('.zip')
    # Local provider returns file path by default
    assert os.path.exists(data["url"]) or data["url"].startswith("s3://") or data["url"].startswith("gs://")
