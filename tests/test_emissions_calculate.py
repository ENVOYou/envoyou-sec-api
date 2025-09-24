import os
from dotenv import load_dotenv
load_dotenv()

from fastapi.testclient import TestClient
from app.api_server import app

client = TestClient(app)
headers = {"X-API-Key": "demo_key_premium_2025"}


def test_emissions_calculate_scope1_scope2():
    payload = {
        "company": "DemoCo",
        "scope1": {"fuel_type": "diesel", "amount": 10, "unit": "gallon"},
        "scope2": {"kwh": 1000, "grid_region": "US_default"}
    }
    r = client.post("/v1/emissions/calculate", json=payload, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["totals"]["emissions_kg"] > 0
