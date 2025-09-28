"""
Data Validator Tool

Comprehensive data validation for emissions data.
"""

from typing import Dict, Any, List, Optional
import re
from datetime import datetime


class DataValidator:
    """Comprehensive data validation for emissions calculations."""
    
    def __init__(self):
        self.version = "1.0.0"
        self.supported_fuel_types = ["gasoline", "diesel", "natural_gas"]
        self.supported_units = {
            "gasoline": ["gallon", "liter"],
            "diesel": ["gallon", "liter"], 
            "natural_gas": ["m3", "therm", "mmbtu"]
        }
        self.supported_grid_regions = ["US_default", "RFC", "WECC", "SERC"]
    
    async def validate_emissions_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive validation of emissions data."""
        
        validation_result = {
            "valid": True,
            "score": 100,
            "issues": [],
            "warnings": [],
            "field_validation": {},
            "completeness_score": 0,
            "validity_score": 0,
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0,
            "low_issues": 0
        }
        
        # Required field validation
        required_validation = self._validate_required_fields(data)
        validation_result["field_validation"]["required"] = required_validation
        
        # Company validation
        company_validation = self._validate_company_field(data.get("company"))
        validation_result["field_validation"]["company"] = company_validation
        
        # Scope 1 validation
        if "scope1" in data:
            scope1_validation = self._validate_scope1_data(data["scope1"])
            validation_result["field_validation"]["scope1"] = scope1_validation
        
        # Scope 2 validation
        if "scope2" in data:
            scope2_validation = self._validate_scope2_data(data["scope2"])
            validation_result["field_validation"]["scope2"] = scope2_validation
        
        # Optional field validation
        optional_validation = self._validate_optional_fields(data)
        validation_result["field_validation"]["optional"] = optional_validation
        
        # Compile results
        self._compile_validation_results(validation_result)
        
        return validation_result
    
    def _validate_required_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate required fields presence."""
        required_fields = ["company"]
        
        validation = {
            "valid": True,
            "missing_fields": [],
            "present_fields": []
        }
        
        for field in required_fields:
            if field not in data or not data[field]:
                validation["missing_fields"].append(field)
                validation["valid"] = False
            else:
                validation["present_fields"].append(field)
        
        return validation
    
    def _validate_company_field(self, company: Any) -> Dict[str, Any]:
        """Validate company field."""
        validation = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        if not company:
            validation["valid"] = False
            validation["issues"].append("Company name is required")
            return validation
        
        if not isinstance(company, str):
            validation["valid"] = False
            validation["issues"].append("Company name must be a string")
            return validation
        
        company_str = company.strip()
        
        # Length validation
        if len(company_str) < 2:
            validation["valid"] = False
            validation["issues"].append("Company name too short (minimum 2 characters)")
        
        if len(company_str) > 200:
            validation["warnings"].append("Company name very long (over 200 characters)")
        
        # Character validation
        if not re.match(r'^[a-zA-Z0-9\s\.\-&,()]+$', company_str):
            validation["warnings"].append("Company name contains unusual characters")
        
        # Common format checks
        if company_str.lower() in ["test", "demo", "example", "sample"]:
            validation["warnings"].append("Company name appears to be a test value")
        
        return validation
    
    def _validate_scope1_data(self, scope1_data: Any) -> Dict[str, Any]:
        """Validate Scope 1 emissions data."""
        validation = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "completeness": 0
        }
        
        if not isinstance(scope1_data, dict):
            validation["valid"] = False
            validation["issues"].append("Scope 1 data must be a dictionary")
            return validation
        
        required_fields = ["fuel_type", "amount", "unit"]
        present_fields = 0
        
        # Fuel type validation
        fuel_type = scope1_data.get("fuel_type")
        if not fuel_type:
            validation["issues"].append("Fuel type is required for Scope 1")
            validation["valid"] = False
        elif fuel_type not in self.supported_fuel_types:
            validation["issues"].append(f"Unsupported fuel type: {fuel_type}")
            validation["valid"] = False
        else:
            present_fields += 1
        
        # Amount validation
        amount = scope1_data.get("amount")
        if amount is None:
            validation["issues"].append("Amount is required for Scope 1")
            validation["valid"] = False
        elif not isinstance(amount, (int, float)):
            validation["issues"].append("Amount must be a number")
            validation["valid"] = False
        elif amount < 0:
            validation["issues"].append("Amount cannot be negative")
            validation["valid"] = False
        elif amount == 0:
            validation["warnings"].append("Amount is zero - verify if correct")
        else:
            present_fields += 1
            
            # Range validation
            if amount > 1000000:
                validation["warnings"].append("Very large amount - verify if correct")
        
        # Unit validation
        unit = scope1_data.get("unit")
        if not unit:
            validation["issues"].append("Unit is required for Scope 1")
            validation["valid"] = False
        elif fuel_type and fuel_type in self.supported_units:
            if unit not in self.supported_units[fuel_type]:
                validation["issues"].append(f"Unsupported unit '{unit}' for fuel type '{fuel_type}'")
                validation["valid"] = False
            else:
                present_fields += 1
        
        validation["completeness"] = (present_fields / len(required_fields)) * 100
        
        return validation
    
    def _validate_scope2_data(self, scope2_data: Any) -> Dict[str, Any]:
        """Validate Scope 2 emissions data."""
        validation = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "completeness": 0
        }
        
        if not isinstance(scope2_data, dict):
            validation["valid"] = False
            validation["issues"].append("Scope 2 data must be a dictionary")
            return validation
        
        required_fields = ["kwh"]
        optional_fields = ["grid_region"]
        present_fields = 0
        
        # kWh validation
        kwh = scope2_data.get("kwh")
        if kwh is None:
            validation["issues"].append("kWh is required for Scope 2")
            validation["valid"] = False
        elif not isinstance(kwh, (int, float)):
            validation["issues"].append("kWh must be a number")
            validation["valid"] = False
        elif kwh < 0:
            validation["issues"].append("kWh cannot be negative")
            validation["valid"] = False
        elif kwh == 0:
            validation["warnings"].append("kWh is zero - verify if correct")
        else:
            present_fields += 1
            
            # Range validation
            if kwh > 100000000:  # 100 million kWh
                validation["warnings"].append("Very large kWh value - verify if correct")
        
        # Grid region validation (optional)
        grid_region = scope2_data.get("grid_region")
        if grid_region:
            if grid_region not in self.supported_grid_regions:
                validation["warnings"].append(f"Unsupported grid region: {grid_region}")
            else:
                present_fields += 0.5  # Partial credit for optional field
        
        validation["completeness"] = (present_fields / len(required_fields)) * 100
        
        return validation
    
    def _validate_optional_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate optional fields."""
        validation = {
            "present_fields": [],
            "issues": [],
            "warnings": []
        }
        
        optional_fields = [
            "reporting_period", "facility_info", "methodology", 
            "emission_factors_source", "calculation_version"
        ]
        
        for field in optional_fields:
            if field in data and data[field]:
                validation["present_fields"].append(field)
                
                # Specific validations for optional fields
                if field == "reporting_period":
                    self._validate_reporting_period(data[field], validation)
                elif field == "calculation_version":
                    self._validate_calculation_version(data[field], validation)
        
        return validation
    
    def _validate_reporting_period(self, reporting_period: Any, validation: Dict[str, Any]):
        """Validate reporting period format."""
        if not isinstance(reporting_period, str):
            validation["warnings"].append("Reporting period should be a string")
            return
        
        # Check for common date formats
        date_patterns = [
            r'^\d{4}$',  # Year only
            r'^\d{4}-\d{2}$',  # Year-Month
            r'^\d{4}-\d{2}-\d{2}$',  # Full date
            r'^\d{4} Q[1-4]$'  # Quarterly
        ]
        
        if not any(re.match(pattern, reporting_period) for pattern in date_patterns):
            validation["warnings"].append("Reporting period format not recognized")
    
    def _validate_calculation_version(self, calc_version: Any, validation: Dict[str, Any]):
        """Validate calculation version."""
        if not isinstance(calc_version, str):
            validation["warnings"].append("Calculation version should be a string")
    
    def _compile_validation_results(self, validation_result: Dict[str, Any]):
        """Compile validation results and calculate scores."""
        all_issues = []
        all_warnings = []
        
        # Collect all issues and warnings
        for field_name, field_validation in validation_result["field_validation"].items():
            if isinstance(field_validation, dict):
                all_issues.extend(field_validation.get("issues", []))
                all_warnings.extend(field_validation.get("warnings", []))
        
        validation_result["issues"] = all_issues
        validation_result["warnings"] = all_warnings
        
        # Categorize issues by severity
        for issue in all_issues:
            if any(keyword in issue.lower() for keyword in ["required", "must be"]):
                validation_result["critical_issues"] += 1
            elif any(keyword in issue.lower() for keyword in ["unsupported", "cannot be"]):
                validation_result["high_issues"] += 1
            else:
                validation_result["medium_issues"] += 1
        
        validation_result["low_issues"] = len(all_warnings)
        
        # Calculate overall validity
        validation_result["valid"] = validation_result["critical_issues"] == 0
        
        # Calculate completeness score
        field_validations = validation_result["field_validation"]
        completeness_scores = []
        
        if "scope1" in field_validations:
            completeness_scores.append(field_validations["scope1"].get("completeness", 0))
        
        if "scope2" in field_validations:
            completeness_scores.append(field_validations["scope2"].get("completeness", 0))
        
        if completeness_scores:
            validation_result["completeness_score"] = sum(completeness_scores) / len(completeness_scores)
        
        # Calculate validity score
        total_issues = (validation_result["critical_issues"] * 4 + 
                       validation_result["high_issues"] * 3 + 
                       validation_result["medium_issues"] * 2 + 
                       validation_result["low_issues"] * 1)
        
        validation_result["validity_score"] = max(0, 100 - total_issues * 5)
        
        # Calculate overall score
        validation_result["score"] = (
            validation_result["completeness_score"] * 0.6 + 
            validation_result["validity_score"] * 0.4
        )