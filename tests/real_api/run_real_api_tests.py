"""
Real API Test Runner

Comprehensive test runner for executing real API tests and comparing with mock test results.
"""

import os
import sys
import json
import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pytest
import subprocess
from loguru import logger

# Add the framework to path
sys.path.append(str(Path(__file__).parent))

from real_api_framework.core import RealAPITestFramework, APITestConfig, TestMode
from real_api_framework.security import APIKeyManager, SecureCredentialsStore


class RealAPITestRunner:
    """
    Comprehensive test runner for real API testing with comparison capabilities.
    """
    
    def __init__(self, config: Optional[APITestConfig] = None):
        self.config = config or self._create_default_config()
        self.framework = None
        self.results = {
            "session_info": {},
            "test_results": [],
            "comparison_with_mocks": {},
            "cost_analysis": {},
            "performance_metrics": {},
            "recommendations": []
        }
        
    def _create_default_config(self) -> APITestConfig:
        """Create default configuration for real API testing"""
        return APITestConfig(
            mode=TestMode.REAL_API,
            max_cost_per_test=0.5,
            max_cost_per_session=10.0,
            cost_warning_threshold=0.7,
            requests_per_minute=30,
            requests_per_hour=500,
            retry_attempts=2,
            request_timeout=30.0,
            test_timeout=120.0,
            cache_responses=True,
            cache_duration=1800,
            save_test_data=True,
            require_api_keys=True,
            validate_keys=True,
            encrypt_credentials=True,
            enable_cost_tracking=True,
            enable_usage_tracking=True,
            enable_rate_limiting=True,
            log_level="INFO",
            log_requests=True,
            log_responses=False,
            enabled_providers=["openai", "requesty"],
            enabled_categories=[
                "voice_transcription", "text_to_speech", "chat_completion",
                "embeddings", "planning", "rag_queries"
            ]
        )
    
    async def setup_framework(self):
        """Initialize the real API framework"""
        try:
            self.framework = RealAPITestFramework(self.config)
            self.results["session_info"] = {
                "session_id": self.framework.session_id,
                "start_time": datetime.now().isoformat(),
                "config": self.config.__dict__
            }
            logger.info(f"Real API Test Framework initialized - Session: {self.framework.session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize framework: {e}")
            return False
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """Validate API keys for all enabled providers"""
        validation_results = {}
        
        try:
            store = SecureCredentialsStore()
            manager = APIKeyManager(store)
            
            for provider in self.config.enabled_providers:
                validation = manager.validate_key(provider)
                validation_results[provider] = validation["valid"]
                
                if validation["valid"]:
                    logger.info(f"✓ {provider} API key validated")
                else:
                    logger.warning(f"✗ {provider} API key validation failed: {validation.get('error', 'Unknown error')}")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return {provider: False for provider in self.config.enabled_providers}
    
    async def run_real_api_tests(self, test_modules: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run real API tests"""
        if not self.framework:
            raise RuntimeError("Framework not initialized. Call setup_framework() first.")
        
        # Default test modules if not specified
        if test_modules is None:
            test_modules = [
                "test_voice_service_real.py",
                "test_requesty_client_real.py", 
                "test_rag_handler_real.py"
            ]
        
        logger.info(f"Running real API tests for modules: {test_modules}")
        
        # Run pytest with real API tests
        test_results = {}
        
        for module in test_modules:
            module_path = Path(__file__).parent / module
            if not module_path.exists():
                logger.warning(f"Test module not found: {module}")
                continue
            
            logger.info(f"Running tests in {module}")
            
            try:
                # Run pytest for the module
                result = subprocess.run([
                    sys.executable, "-m", "pytest", 
                    str(module_path),
                    "-v",
                    "--tb=short",
                    "--json-report",
                    "--json-report-file",
                    str(Path(__file__).parent / "reports" / f"{module.replace('.py', '_report.json')}")
                ], 
                capture_output=True, 
                text=True,
                cwd=Path(__file__).parent
                )
                
                test_results[module] = {
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "success": result.returncode == 0
                }
                
                if result.returncode == 0:
                    logger.info(f"✓ {module} tests passed")
                else:
                    logger.error(f"✗ {module} tests failed")
                    
            except Exception as e:
                logger.error(f"Failed to run tests for {module}: {e}")
                test_results[module] = {
                    "error": str(e),
                    "success": False
                }
        
        self.results["test_results"] = test_results
        return test_results
    
    async def run_mock_tests_for_comparison(self, test_modules: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run mock tests for comparison"""
        if test_modules is None:
            test_modules = [
                "test_voice_service.py",
                "test_requesty_client.py",
                "test_rag_handler.py"
            ]
        
        logger.info("Running mock tests for comparison...")
        
        mock_results = {}
        
        for module in test_modules:
            mock_module_path = Path(__file__).parent.parent / "unit" / module
            if not mock_module_path.exists():
                logger.warning(f"Mock test module not found: {module}")
                continue
            
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pytest",
                    str(mock_module_path),
                    "-v",
                    "--tb=short",
                    "--json-report",
                    "--json-report-file",
                    str(Path(__file__).parent / "reports" / f"mock_{module.replace('.py', '_report.json')}")
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
                )
                
                mock_results[module] = {
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "success": result.returncode == 0
                }
                
                logger.info(f"Mock tests for {module}: {'PASSED' if result.returncode == 0 else 'FAILED'}")
                
            except Exception as e:
                logger.error(f"Failed to run mock tests for {module}: {e}")
                mock_results[module] = {
                    "error": str(e),
                    "success": False
                }
        
        return mock_results
    
    def compare_results(self, real_results: Dict[str, Any], mock_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compare real API results with mock test results"""
        comparison = {
            "summary": {},
            "differences": [],
            "recommendations": []
        }
        
        # Compare success rates
        real_success_count = sum(1 for r in real_results.values() if r.get("success", False))
        mock_success_count = sum(1 for r in mock_results.values() if r.get("success", False))
        
        comparison["summary"] = {
            "real_api_tests": {
                "total": len(real_results),
                "passed": real_success_count,
                "success_rate": real_success_count / len(real_results) if real_results else 0
            },
            "mock_tests": {
                "total": len(mock_results),
                "passed": mock_success_count,
                "success_rate": mock_success_count / len(mock_results) if mock_results else 0
            }
        }
        
        # Analyze differences
        if real_success_count < mock_success_count:
            comparison["differences"].append("Real API tests have lower success rate than mock tests")
            comparison["recommendations"].append("Investigate API connectivity and authentication issues")
        
        if real_success_count == mock_success_count:
            comparison["recommendations"].append("Real API tests match mock test success rates - good consistency")
        
        # Cost analysis
        if self.framework:
            session_summary = self.framework.get_session_summary()
            comparison["cost_analysis"] = {
                "total_cost": session_summary["total_cost"],
                "cost_per_test": session_summary["total_cost"] / len(real_results) if real_results else 0,
                "provider_breakdown": session_summary.get("cost_monitor", {}).get("provider_breakdown", {})
            }
        
        self.results["comparison_with_mocks"] = comparison
        return comparison
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if not self.framework:
            recommendations.append("Framework initialization failed - check configuration")
            return recommendations
        
        session_summary = self.framework.get_session_summary()
        
        # Cost recommendations
        if session_summary["total_cost"] > self.config.max_cost_per_session * 0.8:
            recommendations.append("High cost detected - consider reducing test scope or using cheaper models")
        
        # Success rate recommendations
        if session_summary["successful_tests"] / session_summary["total_tests"] < 0.8:
            recommendations.append("Low success rate - investigate API connectivity and error handling")
        
        # Performance recommendations
        if session_summary.get("rate_limiter", {}).get("wait_time_seconds", 0) > 5:
            recommendations.append("High rate limiting detected - consider increasing test intervals or reducing concurrent tests")
        
        # API key recommendations
        validation_results = self.validate_api_keys()
        failed_validations = [p for p, v in validation_results.items() if not v]
        if failed_validations:
            recommendations.append(f"API key validation failed for: {', '.join(failed_validations)}")
        
        # Usage recommendations
        if session_summary.get("usage_tracker", {}).get("most_used_provider"):
            most_used = session_summary["usage_tracker"]["most_used_provider"]
            recommendations.append(f"Most used provider: {most_used} - monitor usage and costs")
        
        self.results["recommendations"] = recommendations
        return recommendations
    
    def save_comprehensive_report(self, output_path: Optional[str] = None) -> str:
        """Save comprehensive test report"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(__file__).parent / "reports" / f"real_api_test_report_{timestamp}.json"
        
        # Ensure reports directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Add final session summary if framework is available
        if self.framework:
            self.results["final_session_summary"] = self.framework.get_session_summary()
        
        # Add generation metadata
        self.results["report_metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "generated_by": "RealAPITestRunner",
            "version": "1.0.0"
        }
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Comprehensive report saved to: {output_path}")
        return str(output_path)
    
    async def run_complete_test_suite(self, 
                                   include_mock_comparison: bool = True,
                                   test_modules: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run complete test suite with optional mock comparison"""
        
        logger.info("Starting complete real API test suite...")
        
        # Setup framework
        if not await self.setup_framework():
            raise RuntimeError("Failed to setup framework")
        
        # Validate API keys
        validation_results = self.validate_api_keys()
        if not any(validation_results.values()):
            logger.error("No valid API keys found - cannot proceed with real API testing")
            return {"error": "No valid API keys", "validation_results": validation_results}
        
        # Run real API tests
        real_results = await self.run_real_api_tests(test_modules)
        
        # Run mock tests for comparison if requested
        mock_results = {}
        if include_mock_comparison:
            mock_results = await self.run_mock_tests_for_comparison(test_modules)
            self.compare_results(real_results, mock_results)
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Save report
        report_path = self.save_comprehensive_report()
        
        # Cleanup framework
        if self.framework:
            self.framework.cleanup()
        
        logger.info("Complete test suite finished")
        
        return {
            "real_results": real_results,
            "mock_results": mock_results if include_mock_comparison else None,
            "report_path": report_path,
            "validation_results": validation_results,
            "recommendations": self.results["recommendations"]
        }


async def main():
    """Main function for running real API tests"""
    parser = argparse.ArgumentParser(description="Real API Test Runner")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--modules", nargs="+", help="Test modules to run")
    parser.add_argument("--no-mock-comparison", action="store_true", help="Skip mock test comparison")
    parser.add_argument("--max-cost", type=float, help="Maximum cost per session")
    parser.add_argument("--max-cost-per-test", type=float, help="Maximum cost per test")
    parser.add_argument("--output", help="Output report path")
    
    args = parser.parse_args()
    
    # Create configuration
    config = None
    if args.config:
        # Load configuration from file (implementation needed)
        pass
    else:
        config = APITestConfig()
        if args.max_cost:
            config.max_cost_per_session = args.max_cost
        if args.max_cost_per_test:
            config.max_cost_per_test = args.max_cost_per_test
    
    # Create and run test suite
    runner = RealAPITestRunner(config)
    
    try:
        results = await runner.run_complete_test_suite(
            include_mock_comparison=not args.no_mock_comparison,
            test_modules=args.modules
        )
        
        print("\n" + "="*60)
        print("REAL API TEST SUITE RESULTS")
        print("="*60)
        
        if "error" in results:
            print(f"ERROR: {results['error']}")
            return 1
        
        real_results = results["real_results"]
        real_passed = sum(1 for r in real_results.values() if r.get("success", False))
        real_total = len(real_results)
        
        print(f"Real API Tests: {real_passed}/{real_total} passed")
        
        if results.get("mock_results"):
            mock_results = results["mock_results"]
            mock_passed = sum(1 for r in mock_results.values() if r.get("success", False))
            mock_total = len(mock_results)
            print(f"Mock Tests: {mock_passed}/{mock_total} passed")
        
        if results.get("report_path"):
            print(f"Report saved to: {results['report_path']}")
        
        print("\nRecommendations:")
        for rec in results.get("recommendations", []):
            print(f"  • {rec}")
        
        print("="*60)
        
        return 0 if real_passed == real_total else 1
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)