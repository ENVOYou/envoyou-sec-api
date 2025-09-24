import json
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _headers():
    return {"Content-Type": "application/json", "X-API-Key": "demo_key"}


def test_electricity_mwh_vs_kwh_equivalence():
    # 1 MWh should equal 1000 kWh; factors file encodes per-unit factors accordingly
    payload_mwh = {
        "scope": "scope2",
        "activities": [{"type": "electricity", "amount": 1, "unit": "MWh"}],
    }
    r1 = client.post("/v1/environmental/emissions/calc", headers=_headers(), data=json.dumps(payload_mwh))
    assert r1.status_code == 200, r1.text
    total_mwh = r1.json()["total_co2e_kg"]

    payload_kwh = {
        "scope": "scope2",
        "activities": [{"type": "electricity", "amount": 1000, "unit": "kWh"}],
    }
    r2 = client.post("/v1/environmental/emissions/calc", headers=_headers(), data=json.dumps(payload_kwh))
    assert r2.status_code == 200, r2.text
    total_kwh = r2.json()["total_co2e_kg"]

    assert abs(total_mwh - total_kwh) < 1e-6


def test_diesel_liter_calculation():
    payload = {
        "scope": "scope1",
        "activities": [{"type": "fuel", "amount": 200, "unit": "liter", "fuel": "diesel"}],
    }
    r = client.post("/v1/environmental/emissions/calc", headers=_headers(), data=json.dumps(payload))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total_co2e_kg"] == 200 * 2.68

