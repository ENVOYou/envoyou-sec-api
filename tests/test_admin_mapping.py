import os
from dotenv import load_dotenv
load_dotenv()

from fastapi.testclient import TestClient
from app.api_server import app

client = TestClient(app)
# premium tier required for admin endpoints
headers = {"X-API-Key": "demo_key_premium_2025"}


def test_admin_upsert_and_get_mapping():
    payload = {
        "company": "DemoCo",
        "facility_id": "PLT1001",
        "facility_name": "Demo Plant",
        "state": "TX",
        "notes": "manual mapping"
    }
    r = client.post("/v1/admin/mappings", json=payload, headers=headers)
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["company"] == "DemoCo"

    r2 = client.get("/v1/admin/mappings/DemoCo", headers=headers)
    assert r2.status_code == 200
    d2 = r2.json()["data"]
    assert d2["facility_id"] == "PLT1001"

    r3 = client.get("/v1/admin/mappings", headers=headers)
    assert r3.status_code == 200
    lst = r3.json()["data"]
    assert any(x["company"] == "DemoCo" for x in lst)
