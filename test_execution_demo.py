#!/usr/bin/env python3
"""
Test Execution Demo

Demonstrates the real API testing and assisted testing framework execution.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add the tests directory to the path
sys.path.append(str(Path(__file__).parent / "tests"))

try:
    from api_key_manager import APIKeyManager
    from assisted_testing.core import AssistedTestFramework
except ImportError as e:
    print(f"❌ Error: Could not import required modules: {e}")
    print("Make sure you're running this from the voice-rag-system directory")
    sys.exit(1)


class TestExecutionDemo:
    """
    Demo class for executing real API tests and assisted testing.
    """
    
    def __init__(self):
        self.output_dir = Path("./tests/results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.api_manager = APIKeyManager()
        self.assisted_framework = AssistedTestFramework(str(self.output_dir))
        
        # Session info
        self.session_id = f"demo_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.results = []
        
        print(f"🚀 Test Execution Demo Initialized - Session: {self.session_id}")
    
    def check_api_keys(self) -> Dict[str, bool]:
        """Check which API keys are configured"""
        print("\n🔑 Checking API Key Configuration...")
        
        configs = self.api_manager.list_configs()
        key_status = {}
        
        for name, config in configs.items():
            is_configured = config["is_configured"]
            key_status[name] = is_configured
            status = "✅" if is_configured else "❌"
            print(f"{status} {name}: {config['service']}")
        
        return key_status
    
    async def run_assisted_test_demo(self) -> Dict[str, Any]:
        """Run a demo assisted test"""
        print("\n🎯 Running Assisted Test Demo...")
        
        # Create a simple demo scenario
        from assisted_testing.core import TestScenario, TestStep, TestStepType
        
        demo_scenario = TestScenario(
            id="demo_execution",
            name="Demo: Test Execution Framework",
            description="Demonstrates the assisted testing framework execution",
            category="demo",
            steps=[
                TestStep(
                    id="setup_check",
                    name="Setup Check",
                    description="Verify demo setup",
                    step_type=TestStepType.USER_INPUT,
                    instructions="This is a demo step to show the framework execution.",
                    user_prompt="Is the demo setup working? (yes/no)",
                    choices=["yes", "no"],
                    required=True
                ),
                TestStep(
                    id="framework_test",
                    name="Framework Test",
                    description="Test framework functionality",
                    step_type=TestStepType.USER_INPUT,
                    instructions="Testing the framework's ability to collect user input and validate responses.",
                    user_prompt="How would you rate this demo? (excellent/good/fair/poor)",
                    choices=["excellent", "good", "fair", "poor"],
                    required=True
                ),
                TestStep(
                    id="completion_check",
                    name="Completion Check",
                    description="Verify demo completion",
                    step_type=TestStepStepType.MANUAL_VALIDATION,
                    instructions="Final validation step to confirm demo completion.",
                    user_prompt="Did the demo complete successfully? (yes/no)",
                    choices=["yes", "no"],
                    required=True
                )
            ],
            estimated_duration_minutes=2,
            difficulty_level="easy"
        )
        
        # Add scenario to framework
        self.assisted_framework.add_scenario(demo_scenario)
        
        # Run the scenario
        try:
            result = await self.assisted_framework.run_scenario("demo_execution", "Demo User")
            
            return {
                "scenario_id": result.scenario_id,
                "status": result.status,
                "duration_seconds": result.total_execution_time_seconds,
                "step_count": len(result.step_results),
                "passed_steps": sum(1 for r in result.step_results if r.status == "passed"),
                "feedback": result.overall_feedback
            }
        
        except Exception as e:
            print(f"❌ Assisted test demo failed: {e}")
            return {
                "scenario_id": "demo_execution",
                "status": "error",
                "error": str(e)
            }
    
    def simulate_api_test(self, test_name: str) -> Dict[str, Any]:
        """Simulate an API test (since we don't have real API keys in this demo)"""
        print(f"\n🌐 Simulating API Test: {test_name}")
        
        # Simulate different test outcomes
        import random
        
        # 70% chance of success, 20% failure, 10% error
        outcome = random.choices(["passed", "failed", "error"], weights=[0.7, 0.2, 0.1])[0]
        
        # Simulate test duration
        duration = random.uniform(1.0, 5.0)
        
        result = {
            "test_name": test_name,
            "status": outcome,
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat()
        }
        
        if outcome == "failed":
            result["error"] = "Simulated API failure - invalid response format"
        elif outcome == "error":
            result["error"] = "Simulated network error - connection timeout"
        
        status_symbol = {"passed": "✅", "failed": "❌", "error": "💥"}[outcome]
        print(f"{status_symbol} {test_name}: {outcome} ({duration:.1f}s)")
        
        return result
    
    async def run_demo_test_suite(self) -> Dict[str, Any]:
        """Run a complete demo test suite"""
        print("\n🎬 Running Demo Test Suite...")
        print("=" * 60)
        
        # Check API keys
        key_status = self.check_api_keys()
        
        # Simulate API tests
        api_tests = [
            "test_openai_chat_real",
            "test_openai_embeddings_real",
            "test_voice_tts_real",
            "test_requesty_router_real"
        ]
        
        api_results = []
        for test_name in api_tests:
            result = self.simulate_api_test(test_name)
            api_results.append(result)
            await asyncio.sleep(0.5)  # Small delay between tests
        
        # Run assisted test demo
        assisted_result = await self.run_assisted_test_demo()
        
        # Calculate summary
        total_tests = len(api_results) + 1  # +1 for assisted test
        passed_tests = sum(1 for r in api_results if r["status"] == "passed")
        if assisted_result["status"] == "passed":
            passed_tests += 1
        
        failed_tests = sum(1 for r in api_results if r["status"] == "failed")
        if assisted_result["status"] == "failed":
            failed_tests += 1
        
        error_tests = sum(1 for r in api_results if r["status"] == "error")
        if assisted_result["status"] == "error":
            error_tests += 1
        
        # Create summary
        summary = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "error_tests": error_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "api_key_status": key_status,
            "api_test_results": api_results,
            "assisted_test_result": assisted_result
        }
        
        # Save results
        self.save_results(summary)
        
        return summary
    
    def save_results(self, results: Dict[str, Any]):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"demo_test_results_{timestamp}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📁 Results saved to: {filepath}")
    
    def print_summary(self, results: Dict[str, Any]):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 DEMO TEST EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Session ID: {results['session_id']}")
        print(f"Timestamp: {results['timestamp']}")
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed_tests']}")
        print(f"Failed: {results['failed_tests']}")
        print(f"Errors: {results['error_tests']}")
        print(f"Success Rate: {results['success_rate'] * 100:.1f}%")
        print()
        
        print("API Key Configuration:")
        for key, configured in results['api_key_status'].items():
            status = "✅" if configured else "❌"
            print(f"  {status} {key}")
        print()
        
        print("API Test Results:")
        for result in results['api_test_results']:
            status_symbol = {"passed": "✅", "failed": "❌", "error": "💥"}[result["status"]]
            print(f"  {status_symbol} {result['test_name']}: {result['status']}")
        print()
        
        print("Assisted Test Result:")
        assisted = results['assisted_test_result']
        status_symbol = {"passed": "✅", "failed": "❌", "error": "💥"}[assisted["status"]]
        print(f"  {status_symbol} {assisted['scenario_id']}: {assisted['status']}")
        if 'feedback' in assisted:
            print(f"  Feedback: {assisted['feedback']}")
        
        print("\n" + "=" * 60)


async def main():
    """Main demo function"""
    print("🎯 Real API Testing & Assisted Testing Framework Demo")
    print("=" * 70)
    print("This demo shows how the comprehensive testing framework works.")
    print("It simulates API tests and runs a real assisted test scenario.")
    print()
    
    demo = TestExecutionDemo()
    
    try:
        # Run demo test suite
        results = await demo.run_demo_test_suite()
        
        # Print summary
        demo.print_summary(results)
        
        print("\n✅ Demo completed successfully!")
        print("📝 Check the results file for detailed information.")
        
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())