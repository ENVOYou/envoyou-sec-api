from fastapi.testclient import TestClient
from app.api_server import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_get_all_permits():
    response = client.get("/permits")
    assert response.status_code == 200
    assert "data" in response.json()


def test_get_permits_with_pagination():
    response = client.get("/permits", params={"page": 1, "limit": 5})
    assert response.status_code == 200
    assert "data" in response.json()


def test_search_permits_by_company_name():
    response = client.get("/permits/search", params={"nama": "PT"})
    assert response.status_code == 200
    assert "data" in response.json()


def test_search_permits_by_permit_type():
    response = client.get("/permits/search", params={"jenis": "Izin Lingkungan"})
    assert response.status_code == 200
    assert "data" in response.json()


def test_search_permits_by_status():
    response = client.get("/permits/search", params={"status": "Aktif"})
    assert response.status_code == 200
    assert "data" in response.json()


def test_get_active_permits():
    response = client.get("/permits/active")
    assert response.status_code == 200
    assert "data" in response.json()


def test_get_permits_by_company():
    response = client.get("/permits/company/PT.%20Contoh%20Satu")
    assert response.status_code == 200
    assert "data" in response.json()


def test_get_permits_by_type():
    response = client.get("/permits/type/Izin%20Lingkungan")
    assert response.status_code == 200
    assert "data" in response.json()


def test_get_permits_stats():
    response = client.get("/permits/stats")
    assert response.status_code == 200
    assert "total_permits" in response.json()["data"]


def test_invalid_endpoint():
    response = client.get("/invalid_endpoint")
    assert response.status_code == 404


def test_search_without_parameters():
    response = client.get("/permits/search")
    # Assuming it returns 400 on missing params
    assert response.status_code in (400, 422)


def test_company_not_found():
    response = client.get("/permits/company/NonExistentCompany")
    assert response.status_code == 404
    assert response.json()["detail"] == "Company not found"

