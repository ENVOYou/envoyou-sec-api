from fastapi.testclient import TestClient
from app.main import app
import os
import pytest

client = TestClient(app)


def test_global_edgar_endpoint_smoke(monkeypatch):
    api_keys_str = os.getenv('API_KEYS')
    api_key = os.getenv('TEST_API_KEY')
    if not api_keys_str or not api_key:
        pytest.skip("API_KEYS or TEST_API_KEY environment variables not set in CI.")

    monkeypatch.setenv('API_KEYS', api_keys_str)
    headers = {'X-API-KEY': api_key}

    resp = client.get("/global/edgar?country=United%20States&pollutant=PM2.5&window=3", headers=headers)
    
    assert resp.status_code in (200, 400)
    data = resp.json()
    assert isinstance(data, dict)
    if resp.status_code == 200:
        assert data.get("status") == "success"
        assert "series" in data and isinstance(data["series"], list)
        assert "trend" in data and isinstance(data["trend"], dict)


def test_api_endpoints():
    base_path = ""
    endpoints = [
        "/",
        "/health",
        "/permits",
        "/permits/search?nama=PT",
        "/permits/company/PT%20Semen%20Indonesia",
        "/permits/stats",
    ]

    print("🧪 Quick API Test")
    print("=" * 50)

    for endpoint in endpoints:
        response = client.get(endpoint)
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success - {endpoint}")
            if "data" in data and isinstance(data["data"], list):
                print(f" Records: {len(data['data'])}")
            elif "statistics" in data:
                stats = data["statistics"]
                print(f" Total permits: {stats.get('total_permits', 'N/A')}")
            elif "status" in data:
                print(f" API Status: {data['status']}")
        else:
            print(f"\n❌ Failed - {endpoint} (Status {response.status_code})")

    print("\n" + "=" * 50)
    print("Test complete!")


if __name__ == "__main__":
    test_api_endpoints()