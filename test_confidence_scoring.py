#!/usr/bin/env python3
"""Quick test for confidence scoring implementation."""

import requests
import json
import urllib3

# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Test data
test_payload = {
    "company": "Demo Corp",
    "scope1": {
        "fuel_type": "natural_gas",
        "amount": 1000,
        "unit": "mmbtu"
    },
    "scope2": {
        "kwh": 500000,
        "grid_region": "RFC"
    }
}

def test_local_api():
    """Test local API endpoints."""
    base_url = "http://localhost:8000"
    
    # Test emissions calculation
    print("Testing emissions calculation with confidence scoring...")
    try:
        response = requests.post(
            f"{base_url}/v1/emissions/calculate",
            json=test_payload,
            headers={"X-API-Key": "demo-key-12345"}
        )
        if response.status_code == 200:
            data = response.json()
            confidence = data.get("confidence_analysis", {})
            print(f"✅ Emissions calculation successful")
            print(f"   Confidence Score: {confidence.get('score', 'N/A')}")
            print(f"   Confidence Level: {confidence.get('level', 'N/A')}")
            print(f"   Recommendation: {confidence.get('recommendation', 'N/A')}")
        else:
            print(f"❌ Emissions calculation failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing emissions: {e}")
    
    # Test EPA validation
    print("\nTesting EPA validation with confidence scoring...")
    try:
        response = requests.post(
            f"{base_url}/v1/validation/epa",
            json=test_payload,
            headers={"X-API-Key": "demo-key-12345"}
        )
        if response.status_code == 200:
            data = response.json()
            validation = data.get("validation", {})
            print(f"✅ EPA validation successful")
            print(f"   Confidence Score: {validation.get('confidence_score', 'N/A')}")
            print(f"   Confidence Level: {validation.get('confidence_level', 'N/A')}")
            print(f"   Recommendation: {validation.get('recommendation', 'N/A')}")
            print(f"   Matches Found: {validation.get('matches_found', 'N/A')}")
        else:
            print(f"❌ EPA validation failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing validation: {e}")

def test_production_api():
    """Test production API endpoints."""
    base_url = "https://api.envoyou.com"
    
    print("\nTesting production API...")
    try:
        # Get demo API key first
        response = requests.post(
            f"{base_url}/admin/request-demo-key",
            json={"client_name": "Confidence Test"},
            verify=False
        )
        if response.status_code == 200:
            api_key = response.json()["data"]["api_key"]
            print(f"✅ Got demo API key: {api_key[:8]}...")
            
            # Test with real API key
            response = requests.post(
                f"{base_url}/v1/emissions/calculate",
                json=test_payload,
                headers={"X-API-Key": api_key},
                verify=False
            )
            if response.status_code == 200:
                data = response.json()
                confidence = data.get("confidence_analysis", {})
                print(f"✅ Production emissions calculation successful")
                print(f"   Confidence Score: {confidence.get('score', 'N/A')}")
                print(f"   Confidence Level: {confidence.get('level', 'N/A')}")
            else:
                print(f"❌ Production test failed: {response.status_code}")
        else:
            print(f"❌ Failed to get demo API key: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing production: {e}")

if __name__ == "__main__":
    print("🧪 Testing Confidence Scoring Implementation\n")
    test_local_api()
    test_production_api()
    print("\n✅ Confidence scoring tests completed!")