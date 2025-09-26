from fastapi.testclient import TestClient
from app.api_server import app

client = TestClient(app)

def test_search_by_name():
    response = client.get("/permits/search", params={"nama": "Contoh"})
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert len(response_data["data"]) > 0

def test_search_by_jenis():
    response = client.get("/permits/search", params={"jenis": "Lingkungan"})
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert any("Lingkungan" in permit["permit_type"] for permit in response_data["data"])

def test_search_by_status():
    response = client.get("/permits/search", params={"status": "Aktif"})
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert all('aktif' in permit["status"].strip().lower() for permit in response_data["data"])

def test_search_no_params():
    response = client.get("/permits/search")
    assert response.status_code == 400
    assert response.json()["detail"] == "At least one search parameter required (nama, jenis, or status)"

