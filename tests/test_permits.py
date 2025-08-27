from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_all_permits():
    response = client.get("/permits")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for permit in data:
        assert "id" in permit
        assert "company_name" in permit


def test_get_permit_by_id():
    response = client.get("/permits/1")
    assert response.status_code == 200
    permit = response.json()
    assert permit["id"] == 1
    
    response_not_found = client.get("/permits/999")
    assert response_not_found.status_code == 404
    assert response_not_found.json()["detail"] == "Permit not found"
