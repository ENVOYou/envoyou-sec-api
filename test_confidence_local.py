#!/usr/bin/env python3
"""Test confidence scoring implementation locally."""

import sys
sys.path.append('.')

from app.services.validation_service import _calculate_confidence_score
from app.routes.emissions import _assess_calculation_confidence

def test_confidence_algorithms():
    """Test confidence scoring algorithms."""
    print("🧪 Testing Confidence Scoring Algorithms\n")
    
    # Test EPA validation confidence
    print("1. EPA Validation Confidence Scoring:")
    
    # High confidence scenario
    flags_high = []
    confidence_high = _calculate_confidence_score(matches_count=5, flags=flags_high)
    print(f"   High Confidence: Score={confidence_high['score']}, Level={confidence_high['level']}")
    
    # Medium confidence scenario  
    flags_medium = [{'severity': 'medium', 'code': 'low_match_density'}]
    confidence_medium = _calculate_confidence_score(matches_count=2, flags=flags_medium)
    print(f"   Medium Confidence: Score={confidence_medium['score']}, Level={confidence_medium['level']}")
    
    # Low confidence scenario
    flags_low = [
        {'severity': 'high', 'code': 'no_epa_match'},
        {'severity': 'medium', 'code': 'state_mismatch'}
    ]
    confidence_low = _calculate_confidence_score(matches_count=0, flags=flags_low)
    print(f"   Low Confidence: Score={confidence_low['score']}, Level={confidence_low['level']}")
    
    # Test emissions calculation confidence
    print("\n2. Emissions Calculation Confidence Scoring:")
    
    # Complete data scenario
    payload_complete = {
        "company": "Demo Corp",
        "scope1": {"fuel_type": "natural_gas", "amount": 1000, "unit": "mmbtu"},
        "scope2": {"kwh": 500000, "grid_region": "RFC"}
    }
    result_complete = {
        "totals": {"emissions_kg": 303520.0}
    }
    confidence_complete = _assess_calculation_confidence(payload_complete, result_complete)
    print(f"   Complete Data: Score={confidence_complete['score']}, Level={confidence_complete['level']}")
    
    # Partial data scenario
    payload_partial = {
        "company": "Demo Corp", 
        "scope1": {"fuel_type": "natural_gas", "amount": 1000, "unit": "mmbtu"}
    }
    result_partial = {
        "totals": {"emissions_kg": 53020.0}
    }
    confidence_partial = _assess_calculation_confidence(payload_partial, result_partial)
    print(f"   Partial Data: Score={confidence_partial['score']}, Level={confidence_partial['level']}")
    
    # No data scenario
    payload_empty = {"company": "Demo Corp"}
    result_empty = {"totals": {"emissions_kg": 0.0}}
    confidence_empty = _assess_calculation_confidence(payload_empty, result_empty)
    print(f"   No Data: Score={confidence_empty['score']}, Level={confidence_empty['level']}")

def test_business_scenarios():
    """Test confidence scoring for real business scenarios."""
    print("\n🏢 Business Scenario Testing:\n")
    
    # Scenario 1: Fortune 500 company with complete data
    print("Scenario 1: Fortune 500 Company (Complete Data)")
    flags_f500 = []
    confidence_f500 = _calculate_confidence_score(matches_count=8, flags=flags_f500)
    print(f"   Result: {confidence_f500['recommendation']}")
    print(f"   Score: {confidence_f500['score']} ({confidence_f500['level']})")
    
    # Scenario 2: Mid-cap company with some EPA matches
    print("\nScenario 2: Mid-Cap Company (Some EPA Matches)")
    flags_midcap = [{'severity': 'medium', 'code': 'low_match_density'}]
    confidence_midcap = _calculate_confidence_score(matches_count=2, flags=flags_midcap)
    print(f"   Result: {confidence_midcap['recommendation']}")
    print(f"   Score: {confidence_midcap['score']} ({confidence_midcap['level']})")
    
    # Scenario 3: Small company with no EPA presence
    print("\nScenario 3: Small Company (No EPA Presence)")
    flags_small = [
        {'severity': 'high', 'code': 'no_epa_match'},
        {'severity': 'low', 'code': 'small_emissions'}
    ]
    confidence_small = _calculate_confidence_score(matches_count=0, flags=flags_small)
    print(f"   Result: {confidence_small['recommendation']}")
    print(f"   Score: {confidence_small['score']} ({confidence_small['level']})")

if __name__ == "__main__":
    test_confidence_algorithms()
    test_business_scenarios()
    print("\n✅ Confidence scoring tests completed!")
    print("\n📊 Summary:")
    print("   - High confidence (80-100): Ready for SEC filing")
    print("   - Medium confidence (60-79): Review recommended") 
    print("   - Low confidence (0-59): Manual verification required")