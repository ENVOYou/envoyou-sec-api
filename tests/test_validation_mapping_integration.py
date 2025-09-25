import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from app.services.validation_service import cross_validate_epa
from app.models.company_map import CompanyFacilityMap
from app.repositories.company_map_repository import upsert_mapping


def test_validation_with_mapping_integration(test_db: Session):
    """Test validation service with company mapping integration."""
    # Create mapping
    mapping = upsert_mapping(
        test_db,
        company="Test Company",
        facility_id="12345",
        facility_name="Test Facility",
        state="TX",
        notes="Test mapping"
    )
    
    payload = {
        "company": "Test Company",
        "scope1": {
            "fuel_type": "natural_gas",
            "amount": 1000.0,
            "unit": "mmbtu"
        },
        "scope2": {
            "kwh": 500.0,
            "grid_region": "US"
        }
    }
    
    with patch('app.services.validation_service.EPAClient') as mock_epa:
        mock_epa.return_value.get_emissions_data.return_value = []
        mock_epa.return_value.format_emission_data.return_value = []
        
        with patch('app.services.validation_service.CAMDClient') as mock_campd:
            mock_campd.return_value.get_emissions_data.return_value = [
                {"co2_mass_tons": 50.0}  # Expected ~53 tonnes from natural gas
            ]
            
            result = cross_validate_epa(payload, db=test_db)
            
            # Check mapping is included
            assert "mapping" in result
            assert result["mapping"]["facility_id"] == "12345"
            assert result["mapping"]["facility_name"] == "Test Facility"
            
            # Check quantitative deviation
            assert "quantitative_deviation" in result
            deviation = result["quantitative_deviation"]
            assert deviation["facility_id"] == "12345"
            assert len(deviation["deviations"]) == 1
            
            co2_dev = deviation["deviations"][0]
            assert co2_dev["pollutant"] == "CO2"
            assert co2_dev["source"] == "CAMPD"
            assert co2_dev["reference"] == 50.0


def test_validation_without_mapping(test_db: Session):
    """Test validation service without mapping falls back to EPA search."""
    payload = {
        "company": "Unknown Company",
        "scope1": {
            "fuel_type": "natural_gas",
            "amount": 1000.0,
            "unit": "mmbtu"
        }
    }
    
    with patch('app.services.validation_service.EPAClient') as mock_epa:
        mock_epa.return_value.get_emissions_data.return_value = []
        mock_epa.return_value.format_emission_data.return_value = []
        
        result = cross_validate_epa(payload, db=test_db)
        
        # No mapping should be present
        assert "mapping" not in result
        assert "quantitative_deviation" not in result
        
        # Should have EPA search results
        assert "epa" in result
        assert result["epa"]["matches_count"] == 0


def test_quantitative_deviation_thresholds(test_db: Session):
    """Test quantitative deviation severity levels."""
    mapping = upsert_mapping(
        test_db,
        company="High Deviation Co",
        facility_id="99999",
        facility_name="High Deviation Facility"
    )
    
    payload = {
        "company": "High Deviation Co",
        "scope1": {
            "fuel_type": "natural_gas",
            "amount": 2000.0,
            "unit": "mmbtu"
        }
    }
    
    with patch('app.services.validation_service.EPAClient') as mock_epa:
        mock_epa.return_value.get_emissions_data.return_value = []
        mock_epa.return_value.format_emission_data.return_value = []
        
        with patch('app.services.validation_service.CAMDClient') as mock_campd:
            # 50% deviation (2000 vs 1000) should trigger critical
            mock_campd.return_value.get_emissions_data.return_value = [
                {"co2_mass_tons": 1000.0}
            ]
            
            result = cross_validate_epa(payload, db=test_db)
            
            # Should have critical deviation flag
            deviation_flags = [f for f in result["flags"] if f["code"] == "quantitative_deviation"]
            assert len(deviation_flags) == 1
            assert deviation_flags[0]["severity"] == "critical"
            # Check that deviation percentage is in the message
            assert "CO2:" in deviation_flags[0]["message"]
            assert "%" in deviation_flags[0]["message"]


def test_campd_fallback_to_eia(test_db: Session):
    """Test fallback from CAMPD to EIA when CAMPD fails."""
    mapping = upsert_mapping(
        test_db,
        company="EIA Fallback Co",
        facility_id="88888",
        facility_name="EIA Fallback Facility"
    )
    
    payload = {
        "company": "EIA Fallback Co",
        "scope1": {
            "fuel_type": "natural_gas",
            "amount": 1200.0,
            "unit": "mmbtu"
        }
    }
    
    with patch('app.services.validation_service.EPAClient') as mock_epa:
        mock_epa.return_value.get_emissions_data.return_value = []
        mock_epa.return_value.format_emission_data.return_value = []
        
        with patch('app.services.validation_service.CAMDClient') as mock_campd:
            # CAMPD fails
            mock_campd.return_value.get_emissions_data.side_effect = Exception("CAMPD error")
            
            result = cross_validate_epa(payload, db=test_db)
            
            # Should not have quantitative deviation since EIA fallback is disabled
            assert "quantitative_deviation" not in result or not result["quantitative_deviation"]