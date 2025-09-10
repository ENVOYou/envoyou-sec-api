#!/usr/bin/env python3
"""
Test script for Supabase JWT Authentication
Run this script to test the Supabase authentication integration.
"""

import os
import sys
import requests
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_supabase_auth():
    """Test Supabase authentication endpoints"""

    base_url = "http://localhost:8000"

    print("🧪 Testing Supabase Authentication Integration")
    print("=" * 50)

    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server is not responding properly")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the server is running on port 8000")
        return

    # Test 2: Check if Supabase endpoints are available
    try:
        response = requests.get(f"{base_url}/auth/supabase/me")
        # Should return 401 Unauthorized without token
        if response.status_code == 401:
            print("✅ Supabase auth endpoints are properly protected")
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing Supabase endpoints: {e}")

    # Test 3: Check configuration
    from app.config import settings

    required_vars = [
        "SUPABASE_JWT_SECRET",
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY"
    ]

    print("\n🔧 Configuration Check:")
    for var in required_vars:
        value = getattr(settings, var, None)
        if value:
            print(f"✅ {var}: Configured")
        else:
            print(f"❌ {var}: Not configured")

    if not settings.SUPABASE_JWT_SECRET:
        print("\n⚠️  SUPABASE_JWT_SECRET is required for JWT verification")
        print("   Add it to your .env file or environment variables")

    print("\n📝 Next Steps:")
    print("1. Configure Supabase environment variables")
    print("2. Test with a real Supabase JWT token")
    print("3. Update frontend to use Supabase Auth SDK")
    print("4. Remove old manual OAuth endpoints if desired")

    print("\n📖 See SUPABASE_AUTH_INTEGRATION.md for detailed documentation")

if __name__ == "__main__":
    test_supabase_auth()
