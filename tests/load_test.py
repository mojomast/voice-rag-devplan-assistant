import asyncio
import aiohttp
import time
import json
import statistics
import tempfile
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import argparse

class LoadTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def health_check(self) -> bool:
        """Check if the API is responding"""
        try:
            async with self.session.get(f"{self.base_url}/") as response:
                return response.status == 200
        except Exception:
            return False

    async def single_request(self, endpoint: str, method: str = "GET",
                           data: Dict = None, files: Dict = None) -> Dict[str, Any]:
        """Make a single request and measure response time"""
        start_time = time.time()
        request_id = f"{method}_{endpoint}_{int(time.time()*1000)}"

        try:
            if method == "GET":
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    response_text = await response.text()
                    status_code = response.status
            elif method == "POST":
                if files:
                    # Handle file upload
                    form_data = aiohttp.FormData()
                    for key, (filename, content, content_type) in files.items():
                        form_data.add_field(key, content, filename=filename, content_type=content_type)

                    async with self.session.post(f"{self.base_url}{endpoint}", data=form_data) as response:
                        response_text = await response.text()
                        status_code = response.status
                else:
                    async with self.session.post(f"{self.base_url}{endpoint}", json=data) as response:
                        response_text = await response.text()
                        status_code = response.status

            end_time = time.time()
            response_time = end_time - start_time

            # Try to parse JSON response
            try:
                response_data = json.loads(response_text)
            except:
                response_data = {"raw_response": response_text}

            return {
                "request_id": request_id,
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "response_time": response_time,
                "success": 200 <= status_code < 300,
                "response_size": len(response_text),
                "timestamp": datetime.now().isoformat(),
                "response_data": response_data
            }

        except Exception as e:
            end_time = time.time()
            return {
                "request_id": request_id,
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "response_time": end_time - start_time,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def load_test_endpoint(self, endpoint: str, concurrent_users: int = 10,
                               requests_per_user: int = 5, **kwargs) -> List[Dict]:
        """Load test a specific endpoint"""
        print(f"🔥 Load testing {endpoint} with {concurrent_users} users, {requests_per_user} requests each...")

        tasks = []
        for user in range(concurrent_users):
            for request in range(requests_per_user):
                if endpoint == "/query/text":
                    data = {"query": f"Test query from user {user} request {request}: What is AI?"}
                    task = self.single_request(endpoint, "POST", data=data)
                elif endpoint == "/documents/upload":
                    # Create test document for upload
                    test_content = f"Test document from user {user} request {request}. This is sample content for load testing."
                    files = {
                        "file": (f"test_doc_u{user}_r{request}.txt", test_content.encode(), "text/plain")
                    }
                    task = self.single_request(endpoint, "POST", files=files)
                else:
                    task = self.single_request(endpoint, "GET")

                tasks.append(task)

        # Execute all requests concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        # Filter out exceptions and convert to proper results
        valid_results = []
        for result in results:
            if isinstance(result, dict):
                valid_results.append(result)
            else:
                # Handle exceptions
                valid_results.append({
                    "endpoint": endpoint,
                    "success": False,
                    "error": str(result),
                    "response_time": 0,
                    "timestamp": datetime.now().isoformat()
                })

        print(f"   Completed {len(valid_results)} requests in {total_time:.2f}s")
        return valid_results

    async def stress_test(self, duration_seconds: int = 60,
                         concurrent_users: int = 20) -> Dict[str, Any]:
        """Run stress test for specified duration"""
        print(f"💪 Running stress test for {duration_seconds}s with {concurrent_users} concurrent users...")

        endpoints = [
            "/",
            "/documents/stats",
            "/query/text",
            "/voice/voices"
        ]

        start_time = time.time()
        end_time = start_time + duration_seconds
        all_results = []

        async def stress_worker(worker_id: int):
            """Individual stress test worker"""
            worker_results = []
            while time.time() < end_time:
                # Choose random endpoint
                endpoint = endpoints[worker_id % len(endpoints)]

                if endpoint == "/query/text":
                    data = {"query": f"Stress test query from worker {worker_id}"}
                    result = await self.single_request(endpoint, "POST", data=data)
                else:
                    result = await self.single_request(endpoint, "GET")

                worker_results.append(result)

                # Small delay to avoid overwhelming
                await asyncio.sleep(0.1)

            return worker_results

        # Start all workers
        workers = [stress_worker(i) for i in range(concurrent_users)]
        worker_results = await asyncio.gather(*workers)

        # Flatten results
        for worker_result in worker_results:
            all_results.extend(worker_result)

        actual_duration = time.time() - start_time

        return {
            "duration": actual_duration,
            "total_requests": len(all_results),
            "requests_per_second": len(all_results) / actual_duration,
            "results": all_results
        }

    async def comprehensive_load_test(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run comprehensive load test on all endpoints"""
        if config is None:
            config = {
                "concurrent_users": 5,
                "requests_per_user": 3,
                "include_uploads": True,
                "include_queries": True
            }

        print("🚀 Starting comprehensive load test...")

        # Check API health first
        if not await self.health_check():
            print("❌ API health check failed!")
            return {"error": "API not responding"}

        endpoints_to_test = [
            ("/", "GET"),
            ("/documents/stats", "GET"),
            ("/usage/stats", "GET"),
            ("/voice/voices", "GET")
        ]

        if config.get("include_queries", True):
            endpoints_to_test.append(("/query/text", "POST"))

        if config.get("include_uploads", True):
            endpoints_to_test.append(("/documents/upload", "POST"))

        all_results = {}
        overall_stats = {
            "total_requests": 0,
            "total_successes": 0,
            "total_failures": 0,
            "start_time": datetime.now().isoformat()
        }

        for endpoint, method in endpoints_to_test:
            print(f"\n📊 Testing {method} {endpoint}...")

            try:
                results = await self.load_test_endpoint(
                    endpoint,
                    concurrent_users=config["concurrent_users"],
                    requests_per_user=config["requests_per_user"]
                )

                # Calculate statistics
                if results:
                    response_times = [r["response_time"] for r in results if "response_time" in r]
                    success_count = sum(1 for r in results if r.get("success", False))

                    stats = {
                        "total_requests": len(results),
                        "successful_requests": success_count,
                        "failed_requests": len(results) - success_count,
                        "success_rate": (success_count / len(results)) * 100 if results else 0,
                        "avg_response_time": statistics.mean(response_times) if response_times else 0,
                        "min_response_time": min(response_times) if response_times else 0,
                        "max_response_time": max(response_times) if response_times else 0,
                        "std_dev_response_time": statistics.stdev(response_times) if len(response_times) > 1 else 0,
                        "results": results
                    }

                    all_results[endpoint] = stats
                    overall_stats["total_requests"] += len(results)
                    overall_stats["total_successes"] += success_count
                    overall_stats["total_failures"] += len(results) - success_count

                    print(f"   ✅ Success rate: {stats['success_rate']:.1f}%")
                    print(f"   ⏱️  Avg response time: {stats['avg_response_time']:.3f}s")

            except Exception as e:
                print(f"   ❌ Error testing {endpoint}: {e}")
                all_results[endpoint] = {"error": str(e)}

        overall_stats["end_time"] = datetime.now().isoformat()
        overall_stats["overall_success_rate"] = (
            (overall_stats["total_successes"] / overall_stats["total_requests"]) * 100
            if overall_stats["total_requests"] > 0 else 0
        )

        return {
            "config": config,
            "overall_stats": overall_stats,
            "endpoint_results": all_results
        }

    def generate_load_test_report(self, results: Dict[str, Any]):
        """Generate a comprehensive load test report"""
        print("\n" + "="*80)
        print("🎯 LOAD TEST REPORT")
        print("="*80)

        overall = results.get("overall_stats", {})
        print(f"📊 Overall Statistics:")
        print(f"   Total Requests: {overall.get('total_requests', 0):,}")
        print(f"   Successful: {overall.get('total_successes', 0):,}")
        print(f"   Failed: {overall.get('total_failures', 0):,}")
        print(f"   Success Rate: {overall.get('overall_success_rate', 0):.1f}%")

        print(f"\n📈 Endpoint Performance:")
        endpoint_results = results.get("endpoint_results", {})

        for endpoint, stats in endpoint_results.items():
            if "error" in stats:
                print(f"   {endpoint}: ❌ {stats['error']}")
                continue

            print(f"   {endpoint}:")
            print(f"      Success Rate: {stats.get('success_rate', 0):.1f}%")
            print(f"      Avg Response: {stats.get('avg_response_time', 0):.3f}s")
            print(f"      Min Response: {stats.get('min_response_time', 0):.3f}s")
            print(f"      Max Response: {stats.get('max_response_time', 0):.3f}s")
            print(f"      Requests: {stats.get('total_requests', 0)}")

        print("\n" + "="*80)

    def save_load_test_results(self, results: Dict[str, Any], filename: str = None):
        """Save load test results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"load_test_results_{timestamp}.json"

        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"💾 Load test results saved to: {filename}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")

async def main():
    """Main load testing function"""
    parser = argparse.ArgumentParser(description="Load test the Voice RAG API")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--users", type=int, default=5, help="Concurrent users")
    parser.add_argument("--requests", type=int, default=3, help="Requests per user")
    parser.add_argument("--stress", action="store_true", help="Run stress test")
    parser.add_argument("--duration", type=int, default=60, help="Stress test duration (seconds)")

    args = parser.parse_args()

    async with LoadTester(args.url) as tester:
        if args.stress:
            print(f"🔥 Running stress test on {args.url}...")
            stress_results = await tester.stress_test(
                duration_seconds=args.duration,
                concurrent_users=args.users
            )
            print(f"\n📊 Stress Test Results:")
            print(f"   Duration: {stress_results['duration']:.1f}s")
            print(f"   Total Requests: {stress_results['total_requests']:,}")
            print(f"   Requests/Second: {stress_results['requests_per_second']:.2f}")

        else:
            config = {
                "concurrent_users": args.users,
                "requests_per_user": args.requests,
                "include_uploads": True,
                "include_queries": True
            }

            results = await tester.comprehensive_load_test(config)
            tester.generate_load_test_report(results)
            tester.save_load_test_results(results)

if __name__ == "__main__":
    asyncio.run(main())