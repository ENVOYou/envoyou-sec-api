import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.api_server import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_api_key_validation():
    """Mock API key validation for tests."""
    with patch('app.utils.security.validate_api_key') as mock_validate:
        mock_validate.return_value = {"app_name": "Test App", "tier": "basic"}
        yield mock_validate

def test_get_emission_factors():
    """Test getting emission factors."""
    response = client.get("/v1/emissions/factors", headers={"X-API-Key": "test_key"})
    
    assert response.status_code == 200
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert "version" in data
    assert "scope1_factors" in data
    assert "scope2_grid_factors" in data
    
    # Check some expected factors
    assert "natural_gas_mmbtu" in data["scope1_factors"]
    assert "gasoline_gallon" in data["scope1_factors"]
    assert "US_default" in data["scope2_grid_factors"]

def test_get_supported_units():
    """Test getting supported units."""
    response = client.get("/v1/emissions/units", headers={"X-API-Key": "test_key"})
    
    assert response.status_code == 200
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert "scope1_units" in data
    assert "scope2_units" in data
    
    # Check expected units
    assert "natural_gas" in data["scope1_units"]
    assert "mmbtu" in data["scope1_units"]["natural_gas"]
    assert "gasoline" in data["scope1_units"]
    assert "gallon" in data["scope1_units"]["gasoline"]
    
    assert data["scope2_units"]["electricity"] == ["kwh"]
    assert "US_default" in data["scope2_units"]["grid_regions"]

def test_factors_require_api_key():
    """Test that factors endpoints require API key."""
    response = client.get("/v1/emissions/factors")
    assert response.status_code == 401
    
    response = client.get("/v1/emissions/units")
    assert response.status_code == 401