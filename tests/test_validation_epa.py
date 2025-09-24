import os
from dotenv import load_dotenv
load_dotenv()

from fastapi.testclient import TestClient
from app.api_server import app

client = TestClient(app)
headers = {"X-API-Key": "demo_key_premium_2025"}


def test_validation_epa_presence():
    payload = {
        "company": "Sample",
        "scope1": {"fuel_type": "diesel", "amount": 5, "unit": "gallon"},
        "scope2": {"kwh": 500, "grid_region": "US_default"}
    }
    r = client.post("/v1/validation/epa?state=TX", json=payload, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert "flags" in data
