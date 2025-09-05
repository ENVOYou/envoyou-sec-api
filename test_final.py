#!/usr/bin/env python3
"""
Test free API key endpoint
"""
import requests
import time
import json

def wait_for_server(url, timeout=30):
    """Wait for server to be ready"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False

def test_endpoint():
    """Test the free API key endpoint"""
    base_url = "http://localhost:10000"

    # Wait for server
    print("Waiting for server to be ready...")
    if not wait_for_server(f"{base_url}/health"):
        print("❌ Server not ready")
        return

    print("✅ Server is ready")

    # Test /auth endpoint
    print("\nTesting /auth/request-free-api-key...")
    try:
        url = f"{base_url}/auth/request-free-api-key"
        data = {
            "email": "test@example.com",
            "name": "Test User",
            "company": "Test Company"
        }
        response = requests.post(url, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")

    # Test /api/v1 endpoint
    print("\nTesting /api/v1/request-free-api-key...")
    try:
        url = f"{base_url}/api/v1/request-free-api-key"
        data = {
            "email": "test2@example.com",
            "name": "Test User 2",
            "company": "Test Company 2"
        }
        response = requests.post(url, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_endpoint()
