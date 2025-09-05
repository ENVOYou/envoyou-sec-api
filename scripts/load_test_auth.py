#!/usr/bin/env python3
"""
Load testing script for authentication endpoints
Tests rate limiting, concurrent users, and performance under load
"""

import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict
import json
from datetime import datetime

class AuthLoadTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_registration_load(self, num_requests: int = 100, concurrent: int = 10):
        """Test registration endpoint under load"""
        print(f"🧪 Testing registration with {num_requests} requests ({concurrent} concurrent)")

        async def single_registration():
            user_data = {
                "email": f"loadtest_{int(time.time()*1000000)}_{asyncio.current_task().get_name()}@example.com",
                "password": "TestPass123!",
                "name": "Load Test User"
            }

            start_time = time.time()
            try:
                async with self.session.post(
                    f"{self.base_url}/auth/register",
                    json=user_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    end_time = time.time()
                    return {
                        "status": response.status,
                        "response_time": end_time - start_time,
                        "success": response.status in [200, 201]
                    }
            except Exception as e:
                end_time = time.time()
                return {
                    "status": 0,
                    "response_time": end_time - start_time,
                    "success": False,
                    "error": str(e)
                }

        # Run concurrent requests
        start_time = time.time()
        tasks = [single_registration() for _ in range(num_requests)]
        results = []

        # Process in batches to control concurrency
        for i in range(0, len(tasks), concurrent):
            batch = tasks[i:i+concurrent]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            results.extend(batch_results)

        total_time = time.time() - start_time

        # Analyze results
        successful_requests = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_requests = [r for r in results if isinstance(r, dict) and not r.get("success")]
        response_times = [r["response_time"] for r in results if isinstance(r, dict)]

        print("📊 Registration Load Test Results:")
        print(f"   Total Requests: {len(results)}")
        print(f"   Successful: {len(successful_requests)}")
        print(f"   Failed: {len(failed_requests)}")
        print(f"   Total Time: {total_time:.2f}s")
        print(f"   Requests/sec: {len(results)/total_time:.2f}")
        print(f"   Avg Response Time: {statistics.mean(response_times):.3f}s")
        print(f"   Median Response Time: {statistics.median(response_times):.3f}s")
        print(f"   95th Percentile: {statistics.quantiles(response_times, n=20)[18]:.3f}s")

        return {
            "total_requests": len(results),
            "successful": len(successful_requests),
            "failed": len(failed_requests),
            "total_time": total_time,
            "requests_per_sec": len(results)/total_time,
            "avg_response_time": statistics.mean(response_times),
            "median_response_time": statistics.median(response_times),
            "p95_response_time": statistics.quantiles(response_times, n=20)[18]
        }

    async def test_login_load(self, num_requests: int = 100, concurrent: int = 10):
        """Test login endpoint under load"""
        print(f"🔐 Testing login with {num_requests} requests ({concurrent} concurrent)")

        # First create a test user
        user_data = {
            "email": f"login_loadtest_{int(time.time())}@example.com",
            "password": "TestPass123!",
            "name": "Login Load Test User"
        }

        async with self.session.post(
            f"{self.base_url}/auth/register",
            json=user_data
        ) as response:
            if response.status not in [200, 201]:
                print("❌ Failed to create test user for login load test")
                return None

        async def single_login():
            login_data = {
                "email": user_data["email"],
                "password": user_data["password"]
            }

            start_time = time.time()
            try:
                async with self.session.post(
                    f"{self.base_url}/auth/login",
                    json=login_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    end_time = time.time()
                    return {
                        "status": response.status,
                        "response_time": end_time - start_time,
                        "success": response.status == 200
                    }
            except Exception as e:
                end_time = time.time()
                return {
                    "status": 0,
                    "response_time": end_time - start_time,
                    "success": False,
                    "error": str(e)
                }

        # Run concurrent requests
        start_time = time.time()
        tasks = [single_login() for _ in range(num_requests)]
        results = []

        # Process in batches to control concurrency
        for i in range(0, len(tasks), concurrent):
            batch = tasks[i:i+concurrent]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            results.extend(batch_results)

        total_time = time.time() - start_time

        # Analyze results
        successful_requests = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_requests = [r for r in results if isinstance(r, dict) and not r.get("success")]
        response_times = [r["response_time"] for r in results if isinstance(r, dict)]

        print("📊 Login Load Test Results:")
        print(f"   Total Requests: {len(results)}")
        print(f"   Successful: {len(successful_requests)}")
        print(f"   Failed: {len(failed_requests)}")
        print(f"   Total Time: {total_time:.2f}s")
        print(f"   Requests/sec: {len(results)/total_time:.2f}")
        print(f"   Avg Response Time: {statistics.mean(response_times):.3f}s")
        print(f"   Median Response Time: {statistics.median(response_times):.3f}s")
        if len(response_times) > 1:
            print(f"   95th Percentile: {statistics.quantiles(response_times, n=20)[18]:.3f}s")

        return {
            "total_requests": len(results),
            "successful": len(successful_requests),
            "failed": len(failed_requests),
            "total_time": total_time,
            "requests_per_sec": len(results)/total_time,
            "avg_response_time": statistics.mean(response_times),
            "median_response_time": statistics.median(response_times),
            "p95_response_time": statistics.quantiles(response_times, n=20)[18] if len(response_times) > 1 else 0
        }

    async def test_rate_limiting(self, num_requests: int = 50, delay: float = 0.1):
        """Test rate limiting by making rapid requests"""
        print(f"🛡️  Testing rate limiting with {num_requests} rapid requests")

        results = []
        for i in range(num_requests):
            start_time = time.time()
            try:
                async with self.session.post(
                    f"{self.base_url}/auth/login",
                    json={"email": "test@example.com", "password": "wrong"},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    end_time = time.time()
                    results.append({
                        "request": i+1,
                        "status": response.status,
                        "response_time": end_time - start_time,
                        "rate_limited": response.status == 429
                    })
            except Exception as e:
                end_time = time.time()
                results.append({
                    "request": i+1,
                    "status": 0,
                    "response_time": end_time - start_time,
                    "error": str(e)
                })

            if delay > 0:
                await asyncio.sleep(delay)

        rate_limited_count = sum(1 for r in results if r.get("rate_limited"))
        print("📊 Rate Limiting Test Results:")
        print(f"   Total Requests: {len(results)}")
        print(f"   Rate Limited: {rate_limited_count}")
        print(f"   Rate Limit Percentage: {(rate_limited_count/len(results))*100:.1f}%")

        return results

async def main():
    """Run all load tests"""
    print("🚀 Starting Authentication Load Tests")
    print("=" * 50)

    async with AuthLoadTester() as tester:
        # Test registration load
        print("\n" + "="*50)
        await tester.test_registration_load(num_requests=50, concurrent=5)

        # Test login load
        print("\n" + "="*50)
        await tester.test_login_load(num_requests=50, concurrent=5)

        # Test rate limiting
        print("\n" + "="*50)
        await tester.test_rate_limiting(num_requests=30, delay=0.05)

    print("\n" + "="*50)
    print("✅ Load tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
