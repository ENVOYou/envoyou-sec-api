from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_search_permits_by_name():
    response = client.get("/permits/search", params={"nama": "Contoh"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_search_permits_by_type():
    response = client.get("/permits/search", params={"jenis": "Lingkungan"})
    assert response.status_code == 200
    data = response.json()
    assert any("Lingkungan" in permit["permit_type"] for permit in data)


def test_search_permits_by_status():
    response = client.get("/permits/search", params={"status": "Aktif"})
    assert response.status_code == 200
    data = response.json()
    assert all(permit["status"] == "Aktif" for permit in data)


def test_search_permits_missing_params():
    response = client.get("/permits/search")
    assert response.status_code == 400
    assert response.json()["detail"] == "At least one search parameter required (nama, jenis, or status)"
