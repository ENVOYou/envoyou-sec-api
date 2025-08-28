from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_search_permits_by_name():
    response = client.get("/permits/search", params={"nama": "Contoh"})
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    data = response_data["data"]
    assert isinstance(data, list)
    assert len(data) > 0
