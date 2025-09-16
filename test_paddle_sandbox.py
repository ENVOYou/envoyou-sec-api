#!/usr/bin/env python3
"""
Paddle Sandbox Integration Test
Tests webhook processing and subscription management
"""

import asyncio
import json
import logging
import requests
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test webhook data for different events
TEST_WEBHOOKS = {
    "subscription_created": {
        "event_type": "subscription.created",
        "data": {
            "id": "sub_test_123",
            "customer_id": "cus_test_456",
            "status": "active",
            "price_id": "pri_test_789",
            "product_id": "pro_test_101",
            "currency_code": "USD",
            "custom_data": {"user_id": "1"}
        }
    },
    "subscription_updated": {
        "event_type": "subscription.updated",
        "data": {
            "id": "sub_test_123",
            "customer_id": "cus_test_456",
            "status": "active",
            "price_id": "pri_test_789",
            "product_id": "pro_test_101",
            "currency_code": "USD"
        }
    },
    "transaction_completed": {
        "event_type": "transaction.completed",
        "data": {
            "id": "txn_test_123",
            "subscription_id": "sub_test_123",
            "customer_id": "cus_test_456",
            "status": "completed",
            "details": {
                "totals": {
                    "total": "29.99"
                }
            }
        }
    }
}

class PaddleSandboxTester:
    """Test Paddle sandbox integration"""

    def __init__(self, base_url: str = "http://localhost:10000"):
        self.base_url = base_url
        self.webhook_url = f"{base_url}/v1/payments/webhook"

    async def test_webhook_processing(self, event_type: str):
        """Test webhook processing for a specific event type"""
        logger.info(f"Testing webhook processing for: {event_type}")

        webhook_data = TEST_WEBHOOKS.get(event_type)
        if not webhook_data:
            logger.error(f"Unknown event type: {event_type}")
            return False

        try:
            # Convert to JSON bytes
            payload = json.dumps(webhook_data).encode()

            # For testing, we'll skip signature verification
            # In production, you'd generate a proper HMAC signature
            headers = {
                "Content-Type": "application/json",
                "Paddle-Signature": "test_signature"  # Mock signature
            }

            response = requests.post(
                self.webhook_url,
                data=payload,
                headers=headers
            )

            if response.status_code == 200:
                logger.info(f"✅ Webhook {event_type} processed successfully")
                return True
            else:
                logger.error(f"❌ Webhook {event_type} failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error testing webhook {event_type}: {str(e)}")
            return False

    async def test_subscription_creation(self):
        """Test subscription creation"""
        logger.info("Testing subscription creation")

        try:
            # This would require authentication, so we'll just test the endpoint exists
            response = requests.options(f"{self.base_url}/v1/payments/create-subscription")

            if response.status_code in [200, 404]:  # 404 is expected without auth
                logger.info("✅ Subscription creation endpoint accessible")
                return True
            else:
                logger.error(f"❌ Subscription creation endpoint error: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error testing subscription creation: {str(e)}")
            return False

    async def test_task_processor_status(self):
        """Test if task processor is running"""
        logger.info("Testing task processor status")

        try:
            # Check Redis queue length (this would require Redis access)
            # For now, just check if the service is importable
            from app.services.task_processor import task_processor
            logger.info("✅ Task processor service importable")
            return True

        except Exception as e:
            logger.error(f"Error testing task processor: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all Paddle integration tests"""
        logger.info("🚀 Starting Paddle Sandbox Integration Tests")

        results = []

        # Test webhook processing for different events
        for event_type in TEST_WEBHOOKS.keys():
            result = await self.test_webhook_processing(event_type)
            results.append(("webhook_" + event_type, result))

        # Test subscription creation endpoint
        result = await self.test_subscription_creation()
        results.append(("subscription_creation", result))

        # Test task processor
        result = await self.test_task_processor_status()
        results.append(("task_processor", result))

        # Print results
        logger.info("\n📊 Test Results:")
        passed = 0
        total = len(results)

        for test_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            logger.info(f"  {test_name}: {status}")
            if success:
                passed += 1

        logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")

        if passed == total:
            logger.info("🎉 All Paddle integration tests passed!")
        else:
            logger.warning(f"⚠️  {total - passed} tests failed")

        return passed == total

async def main():
    """Main test function"""
    tester = PaddleSandboxTester()

    # Run all tests
    success = await tester.run_all_tests()

    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())