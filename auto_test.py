#!/usr/bin/env python3
"""
Automated test script for free API key endpoint
"""
import subprocess
import time
import requests
import json
import sys
import os

def start_server():
    """Start the server in background"""
    print("Starting server...")
    env = os.environ.copy()
    env['PATH'] = f"/home/husni/project-permit-api/venv/bin:{env['PATH']}"

    process = subprocess.Popen(
        ["python", "start.py"],
        cwd="/home/husni/project-permit-api",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return process

def test_endpoints():
    """Test the free API key endpoints"""
    print("Testing endpoints...")

    # Test /auth endpoint
    try:
        url = "http://localhost:10000/auth/request-free-api-key"
        data = {
            "email": "test@example.com",
            "name": "Test User",
            "company": "Test Company"
        }
        response = requests.post(url, json=data, timeout=5)
        print(f"✅ /auth endpoint: Status {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Response: {result}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ /auth endpoint failed: {e}")

    # Test /api/v1 endpoint
    try:
        url = "http://localhost:10000/api/v1/request-free-api-key"
        data = {
            "email": "test2@example.com",
            "name": "Test User 2",
            "company": "Test Company 2"
        }
        response = requests.post(url, json=data, timeout=5)
        print(f"✅ /api/v1 endpoint: Status {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Response: {result}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ /api/v1 endpoint failed: {e}")

def main():
    # Start server
    server_process = start_server()

    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(5)

    # Test endpoints
    test_endpoints()

    # Stop server
    print("Stopping server...")
    server_process.terminate()
    server_process.wait()

    print("Test completed!")

if __name__ == "__main__":
    main()
