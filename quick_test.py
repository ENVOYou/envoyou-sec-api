#!/usr/bin/env python3
"""
Quick test for API endpoints
"""
import requests
import time
import subprocess
import sys
import os

def test_endpoints():
    """Test all endpoints"""
    base_url = "http://localhost:10000"

    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Health: {response.status_code}")
    except Exception as e:
        print(f"❌ Health failed: {e}")
        return False

    # Test free API key endpoint
    try:
        data = {
            "email": "test@example.com",
            "name": "Test User",
            "company": "Test Company"
        }
        response = requests.post(
            f"{base_url}/api/v1/request-free-api-key",
            json=data,
            timeout=10
        )
        print(f"✅ Free API Key: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Response: {result.get('message', 'Success')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Free API Key failed: {e}")

    # Test auth endpoint
    try:
        data = {
            "email": "test@example.com",
            "name": "Test User",
            "company": "Test Company"
        }
        response = requests.post(
            f"{base_url}/auth/request-free-api-key",
            json=data,
            timeout=10
        )
        print(f"✅ Auth Free API Key: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Response: {result.get('message', 'Success')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Auth Free API Key failed: {e}")

    return True

def main():
    # Start server
    print("🚀 Starting server...")
    env = os.environ.copy()
    env['PATH'] = "/home/husni/project-permit-api/venv/bin:" + env.get('PATH', '')

    server = subprocess.Popen(
        ["python", "start.py"],
        cwd="/home/husni/project-permit-api",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for server
    print("⏳ Waiting for server to start...")
    time.sleep(5)

    # Test endpoints
    print("🧪 Testing endpoints...")
    success = test_endpoints()

    # Stop server
    print("🛑 Stopping server...")
    server.terminate()
    server.wait()

    print("✅ Test completed!")
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
