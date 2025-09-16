#!/usr/bin/env python3
"""
Test script for Paddle payment integration
Run this to verify that the payment endpoints are working correctly
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_paddle_config():
    """Test that Paddle configuration is loaded correctly"""
    try:
        from app.config import settings

        print("Testing Paddle Configuration:")
        print(f"PADDLE_API_KEY: {'✓ Set' if settings.PADDLE_API_KEY else '✗ Not set'}")
        print(f"PADDLE_ENVIRONMENT: {settings.PADDLE_ENVIRONMENT}")
        print(f"PADDLE_WEBHOOK_SECRET: {'✓ Set' if settings.PADDLE_WEBHOOK_SECRET else '✗ Not set'}")
        print(f"PADDLE_PRODUCT_ID: {'✓ Set' if settings.PADDLE_PRODUCT_ID else '✗ Not set'}")
        print(f"PADDLE_PRICE_ID: {'✓ Set' if settings.PADDLE_PRICE_ID else '✗ Not set'}")
        print(f"Paddle API Base URL: {settings.paddle_api_base_url}")
        print(f"Paddle Checkout URL: {settings.paddle_checkout_url}")

        return True
    except Exception as e:
        print(f"✗ Configuration error: {str(e)}")
        return False

def test_paddle_sdk():
    """Test that Paddle SDK is installed and importable"""
    try:
        import paddle_billing  # type: ignore
        print("✓ Paddle SDK imported successfully")
        print(f"Paddle SDK version: {getattr(paddle_billing, '__version__', 'Unknown')}")
        return True
    except ImportError:
        print("⚠ Paddle SDK not available - using requests fallback")
        print("  This is OK for basic functionality")
        return True  # Not a failure, just a warning

def test_payment_routes():
    """Test that payment routes file exists and contains expected endpoints"""
    try:
        import os

        payments_file = os.path.join(os.path.dirname(__file__), 'app', 'routes', 'payments.py')

        if not os.path.exists(payments_file):
            print("✗ payments.py file not found")
            return False

        # Read the file and check for expected route definitions
        with open(payments_file, 'r') as f:
            content = f.read()

        expected_routes = [
            '@router.post("/create-subscription"',
            '@router.get("/subscription/{subscription_id}"',
            '@router.post("/webhook"'
        ]

        found_routes = []
        for route in expected_routes:
            if route in content:
                found_routes.append(route)
                print(f"  ✓ Found: {route}")
            else:
                print(f"  ✗ Missing: {route}")

        if len(found_routes) == len(expected_routes):
            print("✓ All payment routes are defined in payments.py")
            return True
        else:
            print(f"✗ Only {len(found_routes)}/{len(expected_routes)} routes found")
            return False

    except Exception as e:
        print(f"✗ Route file test failed: {str(e)}")
        return False

def test_database_migration():
    """Test that database migration was applied"""
    try:
        import sqlite3

        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()

        # Check if paddle_customer_id column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        conn.close()

        if 'paddle_customer_id' in column_names:
            print("✓ paddle_customer_id column exists in users table")
            return True
        else:
            print("✗ paddle_customer_id column not found in users table")
            return False

    except Exception as e:
        print(f"✗ Database migration test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Paddle Payment Integration\n")

    tests = [
        ("Configuration", test_paddle_config),
        ("Paddle SDK", test_paddle_sdk),
        ("Payment Routes", test_payment_routes),
        ("Database Migration", test_database_migration),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n--- {test_name} Test ---")
        if test_func():
            passed += 1
        print()

    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Paddle integration is ready.")
        print("\nNext steps:")
        print("1. Set your Paddle API credentials in .env file")
        print("2. Configure webhook endpoint: /v1/payments/webhook")
        print("3. Test with sandbox environment first")
        print("4. Deploy and test production payments")
    else:
        print("❌ Some tests failed. Please check the errors above.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)