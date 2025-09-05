#!/usr/bin/env python3
"""
Test script for free API key endpoint
"""
import requests
import json
import time
import subprocess
import sys

def test_free_api_key():
    # Test endpoint with /auth prefix
    url = "http://localhost:10000/auth/request-free-api-key"
    data = {
        "email": "test@example.com",
        "name": "Test User",
        "company": "Test Company"
    }

    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return False

def test_api_v1_endpoint():
    # Test endpoint with /api/v1 prefix
    url = "http://localhost:10000/api/v1/request-free-api-key"
    data = {
        "email": "test2@example.com",
        "name": "Test User 2",
        "company": "Test Company 2"
    }

    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"API v1 Status Code: {response.status_code}")
        print(f"API v1 Response: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"API v1 Request failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing free API key endpoints...")
    print("Waiting for server to be ready...")

    # Wait a bit for server to start
    time.sleep(3)

    print("\n1. Testing /auth/request-free-api-key:")
    success1 = test_free_api_key()

    print("\n2. Testing /api/v1/request-free-api-key:")
    success2 = test_api_v1_endpoint()

    if success1 or success2:
        print("\n✅ At least one endpoint test successful!")
    else:
        print("\n❌ All endpoint tests failed!")
