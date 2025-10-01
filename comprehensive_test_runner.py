#!/usr/bin/env python3
"""
Comprehensive Test Runner

Integrates real API tests and assisted testing framework for complete testing coverage.
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from loguru import logger

# Add the tests directory to the path
sys.path.append(str(Path(__file__).parent / "tests"))

try:
    from api_key_manager import APIKeyManager
    from assisted_testing.runner import AssistedTestRunner
    from assisted_testing.voice_scenarios import VoiceAssistedTestFramework
except ImportError as e:
    print(f"❌ Error: Could not import required modules: {e}")
    print("Make sure you're running this from the voice-rag-system directory")
    sys.exit(1)


@dataclass
class TestSuite:
    """Test suite configuration"""
    name: str
    description: str
    test_type: str  # "api", "assisted", "hybrid"
    tests: List[str]
    required_keys: List[str]
    estimated_duration_minutes: int
    category: str = "general"


@dataclass
class TestResult:
    """Result of a test execution"""
    suite_name: str
    test_name: str
    test_type: str
    status: str  # "passed", "failed", "skipped", "error"
    duration_seconds: float
    error_message: Optional[str] = None
    details: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class TestSuiteResult:
    """Result of a test suite execution"""
    suite_name: str
    suite_type: str
    status: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    duration_seconds: float
    test_results: List[TestResult]
    start_time: datetime
    end_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.end_time is None:
            self.end_time = datetime.now()


class ComprehensiveTestRunner:
    """
    Comprehensive test runner that integrates real API tests and assisted testing.
    """
    
    def __init__(self, config_dir: Optional[str] = None, output_dir: Optional[str] = None):
        self.config_dir = Path(config_dir or "./tests/config")
        self.output_dir = Path(output_dir or "./tests/results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.api_manager = APIKeyManager(str(self.config_dir))
        self.assisted_runner = AssistedTestRunner(str(self.output_dir))
        self.voice_framework = VoiceAssistedTestFramework(str(self.output_dir))
        
        # Test suites
        self.test_suites = self._create_test_suites()
        
        # Session info
        self.session_id = f"comprehensive_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session_results: List[TestSuiteResult] = []
        
        logger.info(f"Comprehensive Test Runner initialized - Session: {self.session_id}")
    
    def _create_test_suites(self) -> Dict[str, TestSuite]:
        """Create test suite configurations"""
        suites = {}
        
        # API Test Suites
        suites["openai_essential"] = TestSuite(
            name="openai_essential",
            description="Essential OpenAI API tests",
            test_type="api",
            tests=[
                "test_openai_chat_real",
                "test_openai_embeddings_real",
                "test_openai_models_real"
            ],
            required_keys=["openai"],
            estimated_duration_minutes=5,
            category="api"
        )
        
        suites["voice_api_essential"] = TestSuite(
            name="voice_api_essential",
            description="Essential voice API tests",
            test_type="api",
            tests=[
                "test_voice_tts_real",
                "test_voice_stt_real"
            ],
            required_keys=["openai"],
            estimated_duration_minutes=8,
            category="voice"
        )
        
        suites["requesty_voice"] = TestSuite(
            name="requesty_voice",
            description="Requesty.ai enhanced voice tests",
            test_type="api",
            tests=[
                "test_requesty_router_real",
                "test_requesty_embeddings_real",
                "test_enhanced_voice_real"
            ],
            required_keys=["requesty"],
            estimated_duration_minutes=10,
            category="voice"
        )
        
        suites["multi_provider_voice"] = TestSuite(
            name="multi_provider_voice",
            description="Multi-provider voice service tests",
            test_type="api",
            tests=[
                "test_elevenlabs_tts_real",
                "test_azure_stt_real",
                "test_google_stt_real",
                "test_aws_polly_real"
            ],
            required_keys=["elevenlabs", "azure_speech", "google_speech", "aws_polly"],
            estimated_duration_minutes=15,
            category="voice"
        )
        
        # Assisted Test Suites
        suites["voice_input_assisted"] = TestSuite(
            name="voice_input_assisted",
            description="Assisted voice input testing",
            test_type="assisted",
            tests=["voice_input_comprehensive"],
            required_keys=[],
            estimated_duration_minutes=10,
            category="voice"
        )
        
        suites["voice_output_assisted"] = TestSuite(
            name="voice_output_assisted",
            description="Assisted voice output testing",
            test_type="assisted",
            tests=["voice_output_comprehensive"],
            required_keys=[],
            estimated_duration_minutes=12,
            category="voice"
        )
        
        suites["voice_workflow_assisted"] = TestSuite(
            name="voice_workflow_assisted",
            description="Assisted complete voice workflow testing",
            test_type="assisted",
            tests=["voice_workflow_complete"],
            required_keys=[],
            estimated_duration_minutes=15,
            category="voice"
        )
        
        suites["voice_ui_assisted"] = TestSuite(
            name="voice_ui_assisted",
            description="Assisted voice UI integration testing",
            test_type="assisted",
            tests=["voice_ui_integration"],
            required_keys=[],
            estimated_duration_minutes=10,
            category="ui"
        )
        
        suites["voice_error_assisted"] = TestSuite(
            name="voice_error_assisted",
            description="Assisted voice error handling testing",
            test_type="assisted",
            tests=["voice_error_handling"],
            required_keys=[],
            estimated_duration_minutes=12,
            category="voice"
        )
        
        # Hybrid Test Suites
        suites["voice_complete"] = TestSuite(
            name="voice_complete",
            description="Complete voice testing (API + Assisted)",
            test_type="hybrid",
            tests=[
                "test_voice_tts_real",
                "test_voice_stt_real",
                "voice_input_comprehensive",
                "voice_output_comprehensive",
                "voice_workflow_complete"
            ],
            required_keys=["openai"],
            estimated_duration_minutes=45,
            category="voice"
        )
        
        suites["full_system"] = TestSuite(
            name="full_system",
            description="Complete system testing",
            test_type="hybrid",
            tests=[
                "test_openai_chat_real",
                "test_openai_embeddings_real",
                "test_requesty_router_real",
                "test_voice_tts_real",
                "test_voice_stt_real",
                "voice_input_comprehensive",
                "voice_output_comprehensive",
                "voice_workflow_complete",
                "voice_ui_integration",
                "voice_error_handling"
            ],
            required_keys=["openai", "requesty"],
            estimated_duration_minutes=90,
            category="system"
        )
        
        return suites
    
    def list_suites(self, category: Optional[str] = None, test_type: Optional[str] = None) -> List[TestSuite]:
        """List available test suites"""
        suites = list(self.test_suites.values())
        
        if category:
            suites = [s for s in suites if s.category == category]
        
        if test_type:
            suites = [s for s in suites if s.test_type == test_type]
        
        return suites
    
    def check_suite_requirements(self, suite_name: str) -> Tuple[bool, List[str]]:
        """Check if all required API keys are configured for a suite"""
        if suite_name not in self.test_suites:
            return False, [f"Unknown test suite: {suite_name}"]
        
        suite = self.test_suites[suite_name]
        missing_keys = []
        
        for key_name in suite.required_keys:
            if not self.api_manager.api_configs[key_name].is_configured:
                missing_keys.append(key_name)
        
        return len(missing_keys) == 0, missing_keys
    
    async def run_api_test(self, test_name: str) -> TestResult:
        """Run a single API test"""
        logger.info(f"Running API test: {test_name}")
        start_time = datetime.now()
        
        try:
            # Import and run the test
            test_module = __import__(f"tests.real_api.{test_name}", fromlist=[test_name])
            test_function = getattr(test_module, f"test_{test_name}")
            
            # Execute test
            result = await test_function()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return TestResult(
                suite_name="api",
                test_name=test_name,
                test_type="api",
                status="passed" if result else "failed",
                duration_seconds=duration,
                details={"result": result}
            )
        
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"API test {test_name} failed: {e}")
            
            return TestResult(
                suite_name="api",
                test_name=test_name,
                test_type="api",
                status="error",
                duration_seconds=duration,
                error_message=str(e)
            )
    
    async def run_assisted_test(self, test_name: str, tester_name: Optional[str] = None) -> TestResult:
        """Run a single assisted test"""
        logger.info(f"Running assisted test: {test_name}")
        start_time = datetime.now()
        
        try:
            # Run assisted test scenario
            result = await self.assisted_runner.run_scenario(test_name, tester_name)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return TestResult(
                suite_name="assisted",
                test_name=test_name,
                test_type="assisted",
                status=result["status"],
                duration_seconds=duration,
                details=result
            )
        
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Assisted test {test_name} failed: {e}")
            
            return TestResult(
                suite_name="assisted",
                test_name=test_name,
                test_type="assisted",
                status="error",
                duration_seconds=duration,
                error_message=str(e)
            )
    
    async def run_test_suite(self, suite_name: str, tester_name: Optional[str] = None) -> TestSuiteResult:
        """Run a complete test suite"""
        if suite_name not in self.test_suites:
            raise ValueError(f"Unknown test suite: {suite_name}")
        
        suite = self.test_suites[suite_name]
        logger.info(f"Running test suite: {suite.name}")
        
        # Check requirements
        can_run, missing_keys = self.check_suite_requirements(suite_name)
        if not can_run:
            logger.warning(f"Cannot run suite {suite_name}: missing keys {missing_keys}")
            return TestSuiteResult(
                suite_name=suite_name,
                suite_type=suite.test_type,
                status="skipped",
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                error_tests=0,
                duration_seconds=0,
                test_results=[],
                start_time=datetime.now()
            )
        
        start_time = datetime.now()
        test_results = []
        
        # Run tests based on type
        for test_name in suite.tests:
            if suite.test_type == "api":
                result = await self.run_api_test(test_name)
            elif suite.test_type == "assisted":
                result = await self.run_assisted_test(test_name, tester_name)
            elif suite.test_type == "hybrid":
                # Determine test type by name
                if test_name.startswith("test_"):
                    result = await self.run_api_test(test_name)
                else:
                    result = await self.run_assisted_test(test_name, tester_name)
            else:
                result = TestResult(
                    suite_name=suite_name,
                    test_name=test_name,
                    test_type="unknown",
                    status="error",
                    duration_seconds=0,
                    error_message=f"Unknown test type: {suite.test_type}"
                )
            
            test_results.append(result)
        
        # Calculate suite results
        total_tests = len(test_results)
        passed_tests = sum(1 for r in test_results if r.status == "passed")
        failed_tests = sum(1 for r in test_results if r.status == "failed")
        skipped_tests = sum(1 for r in test_results if r.status == "skipped")
        error_tests = sum(1 for r in test_results if r.status == "error")
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Determine suite status
        if error_tests > 0:
            status = "error"
        elif failed_tests > 0:
            status = "failed"
        elif skipped_tests > 0 and passed_tests == 0:
            status = "skipped"
        else:
            status = "passed"
        
        suite_result = TestSuiteResult(
            suite_name=suite_name,
            suite_type=suite.test_type,
            status=status,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            error_tests=error_tests,
            duration_seconds=duration,
            test_results=test_results,
            start_time=start_time,
            end_time=datetime.now()
        )
        
        self.session_results.append(suite_result)
        return suite_result
    
    def generate_report(self, format: str = "text") -> str:
        """Generate comprehensive test report"""
        if not self.session_results:
            return "No test results available"
        
        # Calculate overall statistics
        total_suites = len(self.session_results)
        total_tests = sum(r.total_tests for r in self.session_results)
        total_passed = sum(r.passed_tests for r in self.session_results)
        total_failed = sum(r.failed_tests for r in self.session_results)
        total_skipped = sum(r.skipped_tests for r in self.session_results)
        total_errors = sum(r.error_tests for r in self.session_results)
        total_duration = sum(r.duration_seconds for r in self.session_results)
        
        # Category breakdown
        categories = {}
        for suite_result in self.session_results:
            suite = self.test_suites.get(suite_result.suite_name)
            if suite:
                category = suite.category
                if category not in categories:
                    categories[category] = {
                        "suites": 0, "passed": 0, "failed": 0, "tests": 0
                    }
                categories[category]["suites"] += 1
                categories[category]["tests"] += suite_result.total_tests
                if suite_result.status == "passed":
                    categories[category]["passed"] += 1
                elif suite_result.status == "failed":
                    categories[category]["failed"] += 1
        
        if format == "json":
            return json.dumps({
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_suites": total_suites,
                    "total_tests": total_tests,
                    "passed": total_passed,
                    "failed": total_failed,
                    "skipped": total_skipped,
                    "errors": total_errors,
                    "success_rate": total_passed / total_tests if total_tests > 0 else 0,
                    "total_duration_seconds": total_duration
                },
                "category_breakdown": categories,
                "suite_results": [
                    {
                        "suite_name": r.suite_name,
                        "status": r.status,
                        "total_tests": r.total_tests,
                        "passed": r.passed_tests,
                        "failed": r.failed_tests,
                        "skipped": r.skipped_tests,
                        "errors": r.error_tests,
                        "duration_seconds": r.duration_seconds,
                        "test_results": [
                            {
                                "test_name": tr.test_name,
                                "status": tr.status,
                                "duration_seconds": tr.duration_seconds,
                                "error_message": tr.error_message
                            }
                            for tr in r.test_results
                        ]
                    }
                    for r in self.session_results
                ]
            }, indent=2, default=str)
        
        else:  # text format
            report = []
            report.append("=" * 80)
            report.append("COMPREHENSIVE TEST REPORT")
            report.append("=" * 80)
            report.append(f"Session ID: {self.session_id}")
            report.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append("")
            
            report.append("OVERALL SUMMARY")
            report.append("-" * 30)
            report.append(f"Total Test Suites: {total_suites}")
            report.append(f"Total Tests: {total_tests}")
            report.append(f"Passed: {total_passed}")
            report.append(f"Failed: {total_failed}")
            report.append(f"Skipped: {total_skipped}")
            report.append(f"Errors: {total_errors}")
            report.append(f"Success Rate: {total_passed / total_tests * 100:.1f}%" if total_tests > 0 else "Success Rate: N/A")
            report.append(f"Total Duration: {total_duration / 60:.1f} minutes")
            report.append("")
            
            report.append("CATEGORY BREAKDOWN")
            report.append("-" * 30)
            for category, stats in categories.items():
                report.append(f"{category}: {stats['passed']}/{stats['suites']} suites passed, {stats['tests']} tests")
            report.append("")
            
            report.append("SUITE RESULTS")
            report.append("-" * 30)
            for suite_result in self.session_results:
                suite = self.test_suites.get(suite_result.suite_name)
                report.append(f"Suite: {suite_result.suite_name}")
                if suite:
                    report.append(f"  Description: {suite.description}")
                    report.append(f"  Type: {suite.test_type}")
                    report.append(f"  Category: {suite.category}")
                report.append(f"  Status: {suite_result.status}")
                report.append(f"  Tests: {suite_result.passed_tests}/{suite_result.total_tests} passed")
                report.append(f"  Duration: {suite_result.duration_seconds / 60:.1f} minutes")
                
                if suite_result.test_results:
                    report.append("  Test Results:")
                    for test_result in suite_result.test_results:
                        status_symbol = {
                            "passed": "✅",
                            "failed": "❌",
                            "skipped": "⏭️",
                            "error": "💥"
                        }.get(test_result.status, "❓")
                        report.append(f"    {status_symbol} {test_result.test_name}: {test_result.status}")
                        if test_result.error_message:
                            report.append(f"      Error: {test_result.error_message}")
                
                report.append("")
            
            return "\n".join(report)
    
    def save_results(self):
        """Save test results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON report
        json_report = self.generate_report("json")
        json_file = self.output_dir / f"comprehensive_test_{self.session_id}.json"
        with open(json_file, 'w') as f:
            f.write(json_report)
        
        # Save text report
        text_report = self.generate_report("text")
        text_file = self.output_dir / f"comprehensive_test_{self.session_id}.txt"
        with open(text_file, 'w') as f:
            f.write(text_report)
        
        logger.info(f"Test results saved to {json_file} and {text_file}")


async def main():
    """Main command-line interface"""
    parser = argparse.ArgumentParser(description="Comprehensive Test Runner")
    parser.add_argument("--list-suites", action="store_true", help="List available test suites")
    parser.add_argument("--category", help="Filter suites by category")
    parser.add_argument("--type", choices=["api", "assisted", "hybrid"], help="Filter suites by type")
    parser.add_argument("--suite", help="Run a specific test suite")
    parser.add_argument("--tester", help="Name of the tester (for assisted tests)")
    parser.add_argument("--check-requirements", action="store_true", help="Check suite requirements")
    parser.add_argument("--output-dir", help="Output directory for results")
    parser.add_argument("--report", choices=["text", "json"], default="text", help="Report format")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    # Initialize runner
    runner = ComprehensiveTestRunner(output_dir=args.output_dir)
    
    try:
        if args.list_suites:
            suites = runner.list_suites(args.category, args.type)
            
            if not suites:
                print("No test suites found")
                return
            
            print(f"Available Test Suites ({len(suites)}):")
            print("=" * 80)
            
            for suite in suites:
                print(f"ID: {suite.name}")
                print(f"Name: {suite.description}")
                print(f"Type: {suite.test_type}")
                print(f"Category: {suite.category}")
                print(f"Duration: ~{suite.estimated_duration_minutes} minutes")
                print(f"Required keys: {', '.join(suite.required_keys)}")
                print(f"Tests: {len(suite.tests)}")
                print("-" * 80)
        
        elif args.check_requirements:
            if args.suite:
                can_run, missing = runner.check_suite_requirements(args.suite)
                if can_run:
                    print(f"✅ Suite '{args.suite}' requirements met")
                else:
                    print(f"❌ Suite '{args.suite}' missing keys: {', '.join(missing)}")
            else:
                print("Checking all suite requirements...")
                for suite_name, suite in runner.test_suites.items():
                    can_run, missing = runner.check_suite_requirements(suite_name)
                    status = "✅" if can_run else "❌"
                    print(f"{status} {suite_name}: {len(missing)} missing keys")
        
        elif args.suite:
            print(f"Running test suite: {args.suite}")
            result = await runner.run_test_suite(args.suite, args.tester)
            
            print(f"\nSuite Result: {result.status}")
            print(f"Tests: {result.passed_tests}/{result.total_tests} passed")
            print(f"Duration: {result.duration_seconds / 60:.1f} minutes")
            
            # Save results
            runner.save_results()
            
            # Generate report
            print("\n" + runner.generate_report(args.report))
        
        else:
            # Interactive mode
            print("Comprehensive Test Runner - Interactive Mode")
            print("=" * 60)
            
            # Show available suites
            suites = runner.list_suites()
            
            if not suites:
                print("No test suites available")
                return
            
            print("Available Test Suites:")
            for i, suite in enumerate(suites, 1):
                can_run, missing = runner.check_suite_requirements(suite.name)
                status = "✅" if can_run else "❌"
                print(f"{i}. {suite.description} ({suite.test_type}) {status}")
                print(f"   Duration: ~{suite.estimated_duration_minutes} min")
                if not can_run:
                    print(f"   Missing: {', '.join(missing)}")
            
            # Get user choice
            try:
                choice = int(input("\nSelect a suite (number): ")) - 1
                if 0 <= choice < len(suites):
                    selected_suite = suites[choice]
                    print(f"\nRunning: {selected_suite.description}")
                    
                    # Check requirements
                    can_run, missing = runner.check_suite_requirements(selected_suite.name)
                    if not can_run:
                        print(f"❌ Cannot run suite: missing keys {', '.join(missing)}")
                        print("Please configure API keys first using: python setup_api_keys.py")
                        return
                    
                    result = await runner.run_test_suite(selected_suite.name, args.tester)
                    
                    print(f"\nSuite Result: {result.status}")
                    print(f"Tests: {result.passed_tests}/{result.total_tests} passed")
                    print(f"Duration: {result.duration_seconds / 60:.1f} minutes")
                    
                    # Save results
                    runner.save_results()
                    
                    # Generate report
                    print("\n" + runner.generate_report(args.report))
                else:
                    print("Invalid selection")
            except ValueError:
                print("Invalid input")
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())