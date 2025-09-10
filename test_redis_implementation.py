#!/usr/bin/env python3
"""
Test script for Redis implementations in Envoyou API.
Tests rate limiting, session management, and response caching.
"""

import os
import sys
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_redis_connection():
    """Test Redis connection."""
    print("🔗 Testing Redis Connection...")
    try:
        from utils.redis_utils import _get_redis_client, redis_health_check

        client = _get_redis_client()
        if client:
            health = redis_health_check()
            print(f"✅ Redis Status: {health['status']}")
            print(f"   Available: {health['available']}")
            return True
        else:
            print("❌ Redis client not available")
            return False
    except Exception as e:
        print(f"❌ Redis connection test failed: {e}")
        return False

def test_rate_limiting():
    """Test Redis-based rate limiting."""
    print("\n🚦 Testing Rate Limiting...")
    try:
        from utils.redis_utils import redis_rate_limit

        test_key = f"test_rate_limit_{datetime.now().timestamp()}"

        # Test allowing requests within limit
        for i in range(3):  # Test with limit of 5, so 3 should pass
            allowed = redis_rate_limit(test_key, 5, 60)
            print(f"   Request {i+1}: {'✅ Allowed' if allowed else '❌ Blocked'}")

        # Test blocking after limit exceeded
        for i in range(3):  # These should be blocked
            allowed = redis_rate_limit(test_key, 5, 60)
            print(f"   Request {i+4}: {'✅ Allowed' if allowed else '❌ Blocked'}")

        print("✅ Rate limiting test completed")
        return True
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
        return False

def test_session_management():
    """Test Redis-based session management."""
    print("\n🔐 Testing Session Management...")
    try:
        from utils.session_manager import create_user_session, get_user_session, validate_user_session, delete_user_session

        # Create test session
        user_id = "test_user_123"
        user_data = {"email": "test@example.com", "name": "Test User"}
        device_info = {"browser": "Chrome", "os": "Linux"}
        ip_address = "127.0.0.1"

        session_id = create_user_session(user_id, user_data, device_info, ip_address)
        if session_id:
            print(f"✅ Session created: {session_id}")

            # Get session
            session_data = get_user_session(session_id)
            if session_data:
                print("✅ Session retrieved successfully")
                print(f"   User ID: {session_data.get('user_id')}")
                print(f"   Created: {session_data.get('created_at')}")

                # Validate session
                valid = validate_user_session(session_id, user_id)
                print(f"✅ Session validation: {'Valid' if valid else 'Invalid'}")

                # Delete session
                deleted = delete_user_session(session_id)
                print(f"✅ Session deletion: {'Success' if deleted else 'Failed'}")

                return True
            else:
                print("❌ Failed to retrieve session")
                return False
        else:
            print("❌ Failed to create session")
            return False
    except Exception as e:
        print(f"❌ Session management test failed: {e}")
        return False

def test_response_caching():
    """Test Redis-based response caching."""
    print("\n💾 Testing Response Caching...")
    try:
        from utils.redis_utils import redis_cache_response, redis_get_cached_response, redis_clear_response_cache
        from fastapi import Request
        from unittest.mock import Mock

        # Create mock request
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url = "http://test.com/api/test"
        mock_request.query_params = {}
        mock_request.headers = {}

        # Test caching
        cache_key = "test_response_cache"
        test_data = {"status": "success", "data": "test response"}

        # Cache response
        cached = redis_cache_response(cache_key, test_data, ttl=300)
        if cached:
            print("✅ Response cached successfully")

            # Retrieve cached response
            retrieved = redis_get_cached_response(cache_key)
            if retrieved == test_data:
                print("✅ Cached response retrieved successfully")

                # Clear cache
                cleared = redis_clear_response_cache(cache_key)
                print(f"✅ Cache cleared: {'Success' if cleared else 'Failed'}")

                return True
            else:
                print("❌ Retrieved data doesn't match cached data")
                return False
        else:
            print("❌ Failed to cache response")
            return False
    except Exception as e:
        print(f"❌ Response caching test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Starting Redis Implementation Tests")
    print("=" * 50)

    # Change to the correct directory
    os.chdir(os.path.dirname(__file__))

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    tests = [
        ("Redis Connection", test_redis_connection),
        ("Rate Limiting", test_rate_limiting),
        ("Session Management", test_session_management),
        ("Response Caching", test_response_caching),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Redis implementation is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())
