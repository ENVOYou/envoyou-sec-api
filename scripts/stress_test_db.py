#!/usr/bin/env python3
"""
Stress testing script for database connections and API endpoints
Tests database connection pooling, concurrent API calls, and resource usage
"""

import asyncio
import aiohttp
import time
import psutil
import os
import statistics
from typing import List, Dict
import json
from datetime import datetime
import gc

class DatabaseStressTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_tokens = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def get_memory_usage(self):
        """Get current memory usage"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # MB

    def get_cpu_usage(self):
        """Get current CPU usage"""
        return psutil.cpu_percent(interval=1)

    async def create_test_users(self, num_users: int = 20):
        """Create test users for stress testing"""
        print(f"👥 Creating {num_users} test users...")

        for i in range(num_users):
            user_data = {
                "email": f"stress_test_{int(time.time())}_{i}@example.com",
                "password": "TestPass123!",
                "name": f"Stress Test User {i}"
            }

            try:
                async with self.session.post(
                    f"{self.base_url}/auth/register",
                    json=user_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        if "access_token" in data:
                            self.test_tokens.append(data["access_token"])
                    else:
                        print(f"❌ Failed to create user {i}: {response.status}")
            except Exception as e:
                print(f"❌ Error creating user {i}: {e}")

        print(f"✅ Created {len(self.test_tokens)} test users with tokens")

    async def test_concurrent_api_calls(self, num_requests: int = 100, concurrent: int = 20):
        """Test concurrent API calls with authenticated requests"""
        print(f"🔄 Testing {num_requests} concurrent API calls ({concurrent} at a time)")

        if not self.test_tokens:
            print("❌ No test tokens available. Run create_test_users first.")
            return None

        async def single_api_call(token_index: int):
            headers = {"Authorization": f"Bearer {self.test_tokens[token_index % len(self.test_tokens)]}"}

            start_time = time.time()
            try:
                # Test different endpoints
                endpoints = [
                    "/api/permits/search",
                    "/api/global/search",
                    "/user/profile"
                ]
                endpoint = endpoints[token_index % len(endpoints)]

                async with self.session.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    end_time = time.time()
                    content_length = len(await response.text())
                    return {
                        "status": response.status,
                        "response_time": end_time - start_time,
                        "content_length": content_length,
                        "endpoint": endpoint,
                        "success": response.status == 200
                    }
            except Exception as e:
                end_time = time.time()
                return {
                    "status": 0,
                    "response_time": end_time - start_time,
                    "content_length": 0,
                    "endpoint": "error",
                    "success": False,
                    "error": str(e)
                }

        # Monitor system resources
        initial_memory = self.get_memory_usage()
        initial_cpu = self.get_cpu_usage()

        start_time = time.time()
        tasks = [single_api_call(i) for i in range(num_requests)]
        results = []

        # Process in batches to control concurrency
        for i in range(0, len(tasks), concurrent):
            batch = tasks[i:i+concurrent]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            results.extend(batch_results)

            # Force garbage collection between batches
            gc.collect()

        total_time = time.time() - start_time

        # Final resource usage
        final_memory = self.get_memory_usage()
        final_cpu = self.get_cpu_usage()

        # Analyze results
        successful_requests = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_requests = [r for r in results if isinstance(r, dict) and not r.get("success")]
        response_times = [r["response_time"] for r in results if isinstance(r, dict)]

        print("📊 Concurrent API Calls Test Results:")
        print(f"   Total Requests: {len(results)}")
        print(f"   Successful: {len(successful_requests)}")
        print(f"   Failed: {len(failed_requests)}")
        print(f"   Total Time: {total_time:.2f}s")
        print(f"   Requests/sec: {len(results)/total_time:.2f}")
        print(f"   Avg Response Time: {statistics.mean(response_times):.3f}s")
        print(f"   Memory Usage: {initial_memory:.1f}MB → {final_memory:.1f}MB (+{final_memory-initial_memory:.1f}MB)")
        print(f"   CPU Usage: {final_cpu:.1f}%")

        return {
            "total_requests": len(results),
            "successful": len(successful_requests),
            "failed": len(failed_requests),
            "total_time": total_time,
            "requests_per_sec": len(results)/total_time,
            "avg_response_time": statistics.mean(response_times),
            "memory_delta": final_memory - initial_memory,
            "final_cpu": final_cpu
        }

    async def test_database_connection_pooling(self, num_connections: int = 50, duration: int = 60):
        """Test database connection pooling under sustained load"""
        print(f"🗄️  Testing database connection pooling with {num_connections} connections for {duration}s")

        if not self.test_tokens:
            print("❌ No test tokens available. Run create_test_users first.")
            return None

        async def sustained_connection(token: str, connection_id: int):
            headers = {"Authorization": f"Bearer {token}"}
            end_time = time.time() + duration

            request_count = 0
            while time.time() < end_time:
                try:
                    async with self.session.get(
                        f"{self.base_url}/user/profile",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            request_count += 1
                        await asyncio.sleep(0.1)  # Small delay between requests
                except Exception as e:
                    print(f"Connection {connection_id} error: {e}")
                    break

            return {"connection_id": connection_id, "requests": request_count}

        # Distribute tokens among connections
        tasks = []
        for i in range(num_connections):
            token = self.test_tokens[i % len(self.test_tokens)]
            tasks.append(sustained_connection(token, i))

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        # Analyze results
        successful_connections = [r for r in results if isinstance(r, dict)]
        total_requests = sum(r["requests"] for r in successful_connections)

        print("📊 Database Connection Pooling Test Results:")
        print(f"   Total Connections: {len(results)}")
        print(f"   Successful Connections: {len(successful_connections)}")
        print(f"   Total Requests: {total_requests}")
        print(f"   Requests/sec: {total_requests/total_time:.2f}")
        print(f"   Avg Requests per Connection: {total_requests/len(successful_connections):.1f}")
        print(f"   Test Duration: {total_time:.2f}s")

        return {
            "total_connections": len(results),
            "successful_connections": len(successful_connections),
            "total_requests": total_requests,
            "requests_per_sec": total_requests/total_time,
            "avg_requests_per_connection": total_requests/len(successful_connections),
            "test_duration": total_time
        }

    async def test_memory_leaks(self, num_iterations: int = 10, requests_per_iteration: int = 50):
        """Test for memory leaks during sustained API usage"""
        print(f"💧 Testing for memory leaks over {num_iterations} iterations")

        if not self.test_tokens:
            print("❌ No test tokens available. Run create_test_users first.")
            return None

        memory_usage_over_time = []

        for iteration in range(num_iterations):
            print(f"   Iteration {iteration + 1}/{num_iterations}")

            # Perform batch of requests
            tasks = []
            for i in range(requests_per_iteration):
                token = self.test_tokens[i % len(self.test_tokens)]
                headers = {"Authorization": f"Bearer {token}"}
                tasks.append(self.session.get(
                    f"{self.base_url}/user/profile",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ))

            # Execute requests
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Clean up responses
            for result in results:
                if hasattr(result, 'close'):
                    result.close()

            # Force garbage collection
            gc.collect()

            # Record memory usage
            memory_usage = self.get_memory_usage()
            memory_usage_over_time.append(memory_usage)
            print(f"     Memory Usage: {memory_usage:.1f}MB")

            await asyncio.sleep(0.5)  # Brief pause between iterations

        # Analyze memory usage trend
        initial_memory = memory_usage_over_time[0]
        final_memory = memory_usage_over_time[-1]
        memory_delta = final_memory - initial_memory
        max_memory = max(memory_usage_over_time)
        min_memory = min(memory_usage_over_time)

        print("📊 Memory Leak Test Results:")
        print(f"   Initial Memory: {initial_memory:.1f}MB")
        print(f"   Final Memory: {final_memory:.1f}MB")
        print(f"   Memory Delta: {memory_delta:.1f}MB")
        print(f"   Max Memory: {max_memory:.1f}MB")
        print(f"   Min Memory: {min_memory:.1f}MB")
        print(f"   Memory Growth: {'⚠️  Potential leak detected' if memory_delta > 10 else '✅ Stable'}")

        return {
            "initial_memory": initial_memory,
            "final_memory": final_memory,
            "memory_delta": memory_delta,
            "max_memory": max_memory,
            "min_memory": min_memory,
            "memory_stable": abs(memory_delta) <= 10,
            "memory_usage_over_time": memory_usage_over_time
        }

async def main():
    """Run all stress tests"""
    print("🔥 Starting Database & API Stress Tests")
    print("=" * 50)

    async with DatabaseStressTester() as tester:
        # Create test users
        print("\n" + "="*50)
        await tester.create_test_users(20)

        # Test concurrent API calls
        print("\n" + "="*50)
        await tester.test_concurrent_api_calls(num_requests=100, concurrent=10)

        # Test database connection pooling
        print("\n" + "="*50)
        await tester.test_database_connection_pooling(num_connections=20, duration=30)

        # Test for memory leaks
        print("\n" + "="*50)
        await tester.test_memory_leaks(num_iterations=5, requests_per_iteration=20)

    print("\n" + "="*50)
    print("✅ Stress tests completed!")

if __name__ == "__main__":
    import statistics  # Import here to avoid import error in function
    asyncio.run(main())
