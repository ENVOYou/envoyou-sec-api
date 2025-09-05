#!/usr/bin/env python3
"""
Simple test for free API key endpoint
"""
import subprocess
import time
import requests
import sys
import os

def test_endpoint():
    """Test the endpoint"""
    try:
        # Test the endpoint
        url = "http://localhost:10000/auth/request-free-api-key"
        data = {
            "email": "test@example.com",
            "name": "Test User",
            "company": "Test Company"
        }
        
        print("Testing endpoint...")
        response = requests.post(url, json=data, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Start server in background
    print("Starting server...")
    env = os.environ.copy()
    env['PATH'] = "/home/husni/project-permit-api/venv/bin:" + env.get('PATH', '')
    
    server = subprocess.Popen(
        ["uvicorn", "app.api_server:app", "--host", "0.0.0.0", "--port", "10000"],
        cwd="/home/husni/project-permit-api",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(5)
    
    # Test endpoint
    success = test_endpoint()
    
    # Stop server
    server.terminate()
    server.wait()
    
    if success:
        print("✅ Test successful!")
    else:
        print("❌ Test failed!")
    
    sys.exit(0 if success else 1)
