#!/usr/bin/env python3
"""
Test script for free API key endpoint
"""
import requests
import json

def test_free_api_key():
    url = "http://localhost:10000/auth/request-free-api-key"
    data = {
        "email": "test@example.com",
        "name": "Test User",
        "company": "Test Company"
    }

    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_free_api_key()
