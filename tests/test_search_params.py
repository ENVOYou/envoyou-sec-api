from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_search_by_name():
    response = client.get("/permits/search", params={"nama": "Contoh"})
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_search_by_jenis():
    response = client.get("/permits/search", params={"jenis": "Lingkungan"})
    assert response.status_code == 200
    assert any("Lingkungan" in permit["permit_type"] for permit in response.json())

def test_search_by_status():
    response = client.get("/permits/search", params={"status": "Aktif"})
    assert response.status_code == 200
    json_data = response.json()
    assert all('aktif' in permit["status"].strip().lower() for permit in json_data)

def test_search_no_params():
    response = client.get("/permits/search")
    assert response.status_code == 400
    assert response.json()["detail"] == "At least one search parameter required"

