import os
import pytest
from fastapi.testclient import TestClient
from app.api_server import app
from unittest.mock import patch

client = TestClient(app)


@pytest.fixture
def auth_headers():
    api_key = os.getenv('TEST_API_KEY')
    if not api_key:
        pytest.skip("TEST_API_KEY environment variable not set. Please set it in CI.")
    return {'X-API-KEY': api_key}


def test_global_emissions_basic_response(auth_headers):
    resp = client.get("/global/emissions?limit=5", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "data" in data
    assert "pagination" in data
    assert isinstance(data["data"], list)


def test_global_emissions_with_filters(auth_headers):
    resp = client.get("/global/emissions?state=TX&year=2023&limit=3", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["filters"]["state"] == "TX"
    assert data["filters"]["year"] == 2023


def test_global_emissions_stats(auth_headers):
    resp = client.get("/global/emissions/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "statistics" in data
    stats = data["statistics"]
    assert "by_state" in stats
    assert "by_pollutant" in stats
    assert "by_year" in stats
    assert "total_records" in stats


def test_global_iso_basic_response(auth_headers):
    resp = client.get("/global/iso?limit=10", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "data" in data
    assert isinstance(data["data"], list)


def test_global_iso_with_country_filter(auth_headers):
    resp = client.get("/global/iso?country=Germany&limit=5", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["filters"]["country"] == "Germany"


def test_global_eea_basic_response(auth_headers):
    resp = client.get("/global/eea?limit=10", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "data" in data
    assert isinstance(data["data"], list)


def test_global_eea_with_filters(auth_headers):
    resp = client.get("/global/eea?country=Sweden&indicator=GHG&year=2023&limit=5", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    filters = data["filters"]
    assert filters["country"] == "Sweden"
    assert filters["indicator"] == "GHG"
    assert filters["year"] == 2023


def test_global_cevs_basic_company(auth_headers):
    resp = client.get("/global/cevs/Green%20Energy%20Corp", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "score" in data
    assert "components" in data
    assert "sources" in data
    assert "details" in data
    assert 0 <= data["score"] <= 100
    components = data["components"]
    expected_components = [
        "base", "iso_bonus", "epa_penalty", "renewables_bonus",
        "pollution_penalty", "policy_bonus"
    ]
    for comp in expected_components:
        assert comp in components


def test_global_cevs_with_country(auth_headers):
    resp = client.get("/global/cevs/Swedish%20Wind%20Power?country=Sweden", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["country"] == "Sweden"
    details = data["details"]
    assert "renewables" in details
    if details["renewables"]["country_row"]:
        assert details["renewables"]["country_row"]["country"].lower() == "sweden"


def test_global_edgar_basic_response(auth_headers):
    resp = client.get("/global/edgar?country=United%20States&pollutant=PM2.5", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "country" in data
    assert "pollutant" in data
    assert "series" in data
    assert "trend" in data
    assert data["country"] == "United States"
    assert data["pollutant"] == "PM2.5"


def test_global_edgar_missing_country(auth_headers):
    resp = client.get("/global/edgar?pollutant=NOx", headers=auth_headers)
    assert resp.status_code == 400
    data = resp.json()
    assert data["status"] == "error"
    assert "country is required" in data["message"]


def test_global_edgar_with_window_parameter(auth_headers):
    resp = client.get("/global/edgar?country=Germany&pollutant=NOx&window=5", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    trend = data["trend"]
    assert "pollutant" in trend
    assert trend["pollutant"] == "NOx"


@patch('app.routes.global_data.CAMDClient')
def test_global_campd_success(MockCAMDClient, auth_headers):
    mock_instance = MockCAMDClient.return_value
    mock_instance.get_emissions_data.return_value = [{"year": 2023, "co2Mass": 5000}]
    mock_instance.get_compliance_data.return_value = [{"year": 2023, "compliantIndicator": 1}]
    resp = client.get("/global/campd?facility_id=123", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "emissions" in data
    assert "compliance" in data
    assert data["emissions"][0]["co2Mass"] == 5000
    assert data["compliance"][0]["compliantIndicator"] == 1


def test_global_campd_missing_param(auth_headers):
    resp = client.get("/global/campd", headers=auth_headers)
    assert resp.status_code == 400
    data = resp.json()
    assert data["status"] == "error"
    assert "facility_id parameter is required" in data["message"]


def test_global_campd_invalid_param(auth_headers):
    resp = client.get("/global/campd?facility_id=abc", headers=auth_headers)
    assert resp.status_code == 400
    data = resp.json()
    assert data["status"] == "error"
    assert "A valid facility_id parameter is required" in data["message"]