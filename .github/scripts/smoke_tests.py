#!/usr/bin/env python3
"""
Smoke tests for deployed environments.
Validates basic functionality after deployment.
"""

import requests
import argparse
import sys
import time
import json
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmokeTestRunner:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.results = []

    def run_test(self, test_name: str, test_func):
        """Run a single test and record results."""
        logger.info(f"Running test: {test_name}")
        start_time = time.time()

        try:
            result = test_func()
            duration = time.time() - start_time

            self.results.append({
                "test": test_name,
                "status": "PASS",
                "duration": duration,
                "message": result.get("message", "Test passed"),
                "details": result.get("details", {})
            })
            logger.info(f"✅ {test_name} - PASSED ({duration:.2f}s)")
            return True

        except Exception as e:
            duration = time.time() - start_time

            self.results.append({
                "test": test_name,
                "status": "FAIL",
                "duration": duration,
                "message": str(e),
                "details": {}
            })
            logger.error(f"❌ {test_name} - FAILED ({duration:.2f}s): {e}")
            return False

    def test_health_check(self) -> Dict[str, Any]:
        """Test basic health endpoint."""
        response = requests.get(f"{self.base_url}/", timeout=self.timeout)
        response.raise_for_status()

        health_data = response.json()

        if health_data.get("status") != "healthy":
            raise Exception(f"Health check failed: {health_data}")

        return {
            "message": "Health check passed",
            "details": health_data
        }

    def test_detailed_health(self) -> Dict[str, Any]:
        """Test detailed health endpoint."""
        response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        response.raise_for_status()

        health_data = response.json()

        # Check required health indicators
        required_checks = ["status", "vector_store_exists", "document_count"]
        for check in required_checks:
            if check not in health_data:
                raise Exception(f"Missing health check: {check}")

        return {
            "message": "Detailed health check passed",
            "details": health_data
        }

    def test_api_documentation(self) -> Dict[str, Any]:
        """Test API documentation endpoint."""
        response = requests.get(f"{self.base_url}/docs", timeout=self.timeout)
        response.raise_for_status()

        if "swagger" not in response.text.lower() and "openapi" not in response.text.lower():
            raise Exception("API documentation not properly loaded")

        return {
            "message": "API documentation accessible",
            "details": {"status_code": response.status_code}
        }

    def test_voice_capabilities(self) -> Dict[str, Any]:
        """Test voice processing capabilities endpoint."""
        response = requests.get(f"{self.base_url}/voice/capabilities", timeout=self.timeout)
        response.raise_for_status()

        capabilities = response.json()

        # Check for essential capabilities
        essential_caps = ["basic_transcription", "text_to_speech"]
        for cap in essential_caps:
            if not capabilities.get(cap, False):
                raise Exception(f"Essential voice capability missing: {cap}")

        return {
            "message": "Voice capabilities verified",
            "details": capabilities
        }

    def test_document_formats(self) -> Dict[str, Any]:
        """Test supported document formats endpoint."""
        response = requests.get(f"{self.base_url}/documents/supported-formats", timeout=self.timeout)
        response.raise_for_status()

        formats = response.json()

        if formats.get("total_supported", 0) < 5:
            raise Exception("Insufficient document format support")

        return {
            "message": "Document format support verified",
            "details": formats
        }

    def test_analytics_dashboard(self) -> Dict[str, Any]:
        """Test analytics dashboard endpoint."""
        response = requests.get(f"{self.base_url}/analytics/dashboard", timeout=self.timeout)
        response.raise_for_status()

        analytics = response.json()

        # Check for key analytics sections
        required_sections = ["system_metrics", "health_status", "usage_stats"]
        for section in required_sections:
            if section not in analytics:
                raise Exception(f"Missing analytics section: {section}")

        return {
            "message": "Analytics dashboard accessible",
            "details": {"sections": list(analytics.keys())}
        }

    def test_simple_text_query(self) -> Dict[str, Any]:
        """Test basic text query functionality."""
        # This test only works if there are documents indexed
        # We'll make it non-critical
        try:
            response = requests.post(
                f"{self.base_url}/query/text",
                json={"query": "test query", "include_sources": False},
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()

            if "answer" not in result:
                raise Exception("Query response missing answer field")

            return {
                "message": "Text query functionality working",
                "details": {"response_length": len(result.get("answer", ""))}
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # No documents indexed - this is OK for smoke test
                return {
                    "message": "Text query endpoint accessible (no documents indexed)",
                    "details": {"status": "no_documents"}
                }
            else:
                raise

    def test_metrics_endpoint(self) -> Dict[str, Any]:
        """Test metrics endpoint for monitoring."""
        response = requests.get(f"{self.base_url}/metrics", timeout=self.timeout)
        response.raise_for_status()

        metrics = response.json()

        if "metrics" not in metrics:
            raise Exception("Metrics endpoint not returning proper format")

        return {
            "message": "Metrics endpoint accessible",
            "details": {"format": metrics.get("format", "unknown")}
        }

    def test_performance_stats(self) -> Dict[str, Any]:
        """Test performance statistics endpoint."""
        response = requests.get(f"{self.base_url}/performance/stats", timeout=self.timeout)
        response.raise_for_status()

        stats = response.json()

        # Check for overall stats
        if "_overall" not in stats:
            raise Exception("Performance stats missing overall section")

        return {
            "message": "Performance stats accessible",
            "details": stats.get("_overall", {})
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all smoke tests."""
        logger.info(f"Starting smoke tests for {self.base_url}")

        # Critical tests - must pass
        critical_tests = [
            ("Health Check", self.test_health_check),
            ("Detailed Health", self.test_detailed_health),
            ("API Documentation", self.test_api_documentation),
        ]

        # Important tests - should pass but not critical
        important_tests = [
            ("Voice Capabilities", self.test_voice_capabilities),
            ("Document Formats", self.test_document_formats),
            ("Analytics Dashboard", self.test_analytics_dashboard),
            ("Metrics Endpoint", self.test_metrics_endpoint),
            ("Performance Stats", self.test_performance_stats),
        ]

        # Optional tests - nice to have
        optional_tests = [
            ("Simple Text Query", self.test_simple_text_query),
        ]

        # Run critical tests
        critical_passed = 0
        for test_name, test_func in critical_tests:
            if self.run_test(test_name, test_func):
                critical_passed += 1

        # Run important tests
        important_passed = 0
        for test_name, test_func in important_tests:
            if self.run_test(test_name, test_func):
                important_passed += 1

        # Run optional tests
        optional_passed = 0
        for test_name, test_func in optional_tests:
            if self.run_test(test_name, test_func):
                optional_passed += 1

        # Calculate summary
        total_tests = len(critical_tests) + len(important_tests) + len(optional_tests)
        total_passed = critical_passed + important_passed + optional_passed

        summary = {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "critical_tests": {
                "total": len(critical_tests),
                "passed": critical_passed
            },
            "important_tests": {
                "total": len(important_tests),
                "passed": important_passed
            },
            "optional_tests": {
                "total": len(optional_tests),
                "passed": optional_passed
            },
            "success_rate": total_passed / total_tests if total_tests > 0 else 0,
            "overall_status": "PASS" if critical_passed == len(critical_tests) else "FAIL"
        }

        return summary

    def generate_report(self, summary: Dict[str, Any]) -> str:
        """Generate a test report."""
        report = []
        report.append(f"# Smoke Test Report - {self.base_url}")
        report.append("")

        # Summary
        status_emoji = "✅" if summary["overall_status"] == "PASS" else "❌"
        report.append(f"{status_emoji} **Overall Status**: {summary['overall_status']}")
        report.append(f"📊 **Success Rate**: {summary['success_rate']*100:.1f}% ({summary['total_passed']}/{summary['total_tests']})")
        report.append("")

        # Test categories
        report.append("## Test Results by Category")
        report.append("")

        categories = [
            ("Critical Tests", summary["critical_tests"]),
            ("Important Tests", summary["important_tests"]),
            ("Optional Tests", summary["optional_tests"])
        ]

        for category, stats in categories:
            status = "✅" if stats["passed"] == stats["total"] else "⚠️"
            report.append(f"{status} **{category}**: {stats['passed']}/{stats['total']} passed")

        report.append("")

        # Individual test results
        report.append("## Individual Test Results")
        report.append("")

        for result in self.results:
            status_emoji = "✅" if result["status"] == "PASS" else "❌"
            report.append(f"{status_emoji} **{result['test']}** ({result['duration']:.2f}s)")

            if result["status"] == "FAIL":
                report.append(f"   - Error: {result['message']}")
            else:
                report.append(f"   - {result['message']}")

            report.append("")

        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description="Run smoke tests against deployed environment")
    parser.add_argument("--url", required=True, help="Base URL of the deployed application")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    parser.add_argument("--output-report", help="Path to save test report")
    parser.add_argument("--output-json", help="Path to save JSON results")

    args = parser.parse_args()

    # Run smoke tests
    runner = SmokeTestRunner(args.url, args.timeout)
    summary = runner.run_all_tests()

    # Generate and display report
    report = runner.generate_report(summary)
    print("\n" + report)

    # Save report if requested
    if args.output_report:
        with open(args.output_report, 'w') as f:
            f.write(report)
        logger.info(f"Report saved to {args.output_report}")

    # Save JSON results if requested
    if args.output_json:
        results_data = {
            "summary": summary,
            "results": runner.results,
            "url": args.url,
            "timestamp": time.time()
        }

        with open(args.output_json, 'w') as f:
            json.dump(results_data, f, indent=2)
        logger.info(f"JSON results saved to {args.output_json}")

    # Exit with appropriate code
    if summary["overall_status"] == "PASS":
        logger.info("🎉 All smoke tests passed!")
        sys.exit(0)
    else:
        logger.error("💥 Critical smoke tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()