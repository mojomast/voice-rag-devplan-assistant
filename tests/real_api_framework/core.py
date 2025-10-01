"""
Core Real API Test Framework

Provides the main framework class and configuration for real API testing.
"""

import os
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from pathlib import Path
from loguru import logger
import pytest
from enum import Enum

from .security import APIKeyManager, SecureCredentialsStore
from .monitors import CostMonitor, UsageTracker, RateLimitMonitor
from .utils import TestDataGenerator, APIResponseValidator


class TestMode(Enum):
    """Testing modes for the framework"""
    REAL_API = "real_api"
    SIMULATED = "simulated"
    HYBRID = "hybrid"


@dataclass
class APITestConfig:
    """Configuration for real API testing"""
    
    # Test Mode
    mode: TestMode = TestMode.REAL_API
    
    # Cost Controls
    max_cost_per_test: float = 1.0  # USD
    max_cost_per_session: float = 10.0  # USD
    cost_warning_threshold: float = 0.8  # 80% of max cost
    
    # Rate Limits
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    retry_attempts: int = 3
    retry_delay: float = 1.0  # seconds
    
    # Timeouts
    request_timeout: float = 30.0  # seconds
    test_timeout: float = 300.0  # seconds
    
    # Data Management
    cache_responses: bool = True
    cache_duration: int = 3600  # seconds
    save_test_data: bool = True
    test_data_dir: str = "./tests/real_api_data"
    
    # Security
    require_api_keys: bool = True
    validate_keys: bool = True
    encrypt_credentials: bool = True
    
    # Monitoring
    enable_cost_tracking: bool = True
    enable_usage_tracking: bool = True
    enable_rate_limiting: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_requests: bool = True
    log_responses: bool = False  # Don't log sensitive response data
    
    # API Providers
    enabled_providers: List[str] = field(default_factory=lambda: ["openai", "requesty"])
    
    # Test Categories
    enabled_categories: List[str] = field(default_factory=lambda: [
        "voice_transcription", "text_to_speech", "chat_completion", 
        "embeddings", "planning", "rag_queries"
    ])


class RealAPITestFramework:
    """
    Main framework class for real API testing with security and cost controls.
    """
    
    def __init__(self, config: Optional[APITestConfig] = None):
        self.config = config or APITestConfig()
        self.session_id = self._generate_session_id()
        
        # Initialize components
        self.credentials_store = SecureCredentialsStore()
        self.api_key_manager = APIKeyManager(self.credentials_store)
        self.cost_monitor = CostMonitor(self.config)
        self.usage_tracker = UsageTracker(self.config)
        self.rate_limiter = RateLimitMonitor(self.config)
        self.test_data_generator = TestDataGenerator()
        self.response_validator = APIResponseValidator()
        
        # Session state
        self.session_start_time = datetime.now()
        self.test_results: List[Dict] = []
        self.current_test_cost = 0.0
        self.session_cost = 0.0
        
        # Setup logging
        self._setup_logging()
        
        # Initialize framework
        self._initialize()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        import uuid
        return f"real_api_test_{uuid.uuid4().hex[:12]}_{int(time.time())}"
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path(self.config.test_data_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"real_api_test_{self.session_id}.log"
        
        logger.add(
            log_file,
            level=self.config.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            rotation="10 MB",
            retention="7 days"
        )
        
        logger.info(f"Real API Test Framework initialized - Session: {self.session_id}")
    
    def _initialize(self):
        """Initialize the framework"""
        try:
            # Create test data directory
            Path(self.config.test_data_dir).mkdir(parents=True, exist_ok=True)
            
            # Validate API keys if required
            if self.config.require_api_keys:
                self._validate_api_keys()
            
            # Initialize monitors
            if self.config.enable_cost_tracking:
                self.cost_monitor.initialize()
            
            if self.config.enable_usage_tracking:
                self.usage_tracker.initialize()
            
            if self.config.enable_rate_limiting:
                self.rate_limiter.initialize()
            
            logger.info("Framework initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Framework initialization failed: {e}")
            raise
    
    def _validate_api_keys(self):
        """Validate required API keys"""
        missing_keys = []
        
        for provider in self.config.enabled_providers:
            if not self.api_key_manager.has_valid_key(provider):
                missing_keys.append(provider)
        
        if missing_keys:
            error_msg = f"Missing or invalid API keys for providers: {missing_keys}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    async def run_test(self, 
                      test_name: str, 
                      test_func: Callable,
                      test_data: Optional[Dict] = None,
                      category: str = "general") -> Dict[str, Any]:
        """
        Run a single test with cost controls and monitoring.
        
        Args:
            test_name: Name of the test
            test_func: Async test function to execute
            test_data: Test data to pass to the function
            category: Test category for tracking
            
        Returns:
            Test result dictionary
        """
        test_start_time = datetime.now()
        
        # Check if category is enabled
        if category not in self.config.enabled_categories:
            return {
                "test_name": test_name,
                "status": "skipped",
                "reason": f"Category '{category}' not enabled",
                "session_id": self.session_id
            }
        
        # Check cost limits
        if not self._check_cost_limits():
            return {
                "test_name": test_name,
                "status": "skipped",
                "reason": "Cost limit exceeded",
                "session_id": self.session_id
            }
        
        # Check rate limits
        if not self.rate_limiter.can_make_request():
            return {
                "test_name": test_name,
                "status": "skipped", 
                "reason": "Rate limit exceeded",
                "session_id": self.session_id
            }
        
        logger.info(f"Running test: {test_name} (Category: {category})")
        
        try:
            # Execute test with timeout
            result = await asyncio.wait_for(
                self._execute_test_with_monitoring(test_name, test_func, test_data, category),
                timeout=self.config.test_timeout
            )
            
            # Calculate test duration
            test_duration = (datetime.now() - test_start_time).total_seconds()
            result["duration"] = test_duration
            
            # Record test result
            self.test_results.append(result)
            
            logger.info(f"Test completed: {test_name} - Status: {result['status']}")
            
            return result
            
        except asyncio.TimeoutError:
            error_result = {
                "test_name": test_name,
                "status": "timeout",
                "error": f"Test exceeded timeout of {self.config.test_timeout}s",
                "session_id": self.session_id,
                "duration": (datetime.now() - test_start_time).total_seconds()
            }
            self.test_results.append(error_result)
            logger.error(f"Test timeout: {test_name}")
            return error_result
            
        except Exception as e:
            error_result = {
                "test_name": test_name,
                "status": "error",
                "error": str(e),
                "session_id": self.session_id,
                "duration": (datetime.now() - test_start_time).total_seconds()
            }
            self.test_results.append(error_result)
            logger.error(f"Test error: {test_name} - {e}")
            return error_result
    
    async def _execute_test_with_monitoring(self, 
                                         test_name: str,
                                         test_func: Callable,
                                         test_data: Optional[Dict],
                                         category: str) -> Dict[str, Any]:
        """Execute test with full monitoring"""
        
        # Start monitoring
        self.rate_limiter.record_request_start()
        cost_tracker = self.cost_monitor.start_test_tracking(test_name)
        
        try:
            # Execute the test
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func(test_data or {})
            else:
                result = test_func(test_data or {})
            
            # Validate response if it's an API response
            if isinstance(result, dict) and "status" in result:
                validation_result = self.response_validator.validate(result, category)
                result["validation"] = validation_result
            
            # Calculate cost
            test_cost = self.cost_monitor.calculate_test_cost(test_name, result)
            cost_tracker.record_cost(test_cost)
            
            # Update session cost
            self.current_test_cost = test_cost
            self.session_cost += test_cost
            
            # Check cost warning threshold
            if test_cost > self.config.max_cost_per_test * self.config.cost_warning_threshold:
                logger.warning(f"High cost test: {test_name} - ${test_cost:.4f}")
            
            result.update({
                "status": "success",
                "cost": test_cost,
                "session_cost": self.session_cost,
                "session_id": self.session_id,
                "category": category
            })
            
            return result
            
        finally:
            # End monitoring
            self.rate_limiter.record_request_end()
            cost_tracker.end_tracking()
            
            # Track usage
            if self.config.enable_usage_tracking:
                self.usage_tracker.record_test_usage(test_name, category, result)
    
    def _check_cost_limits(self) -> bool:
        """Check if cost limits allow running more tests"""
        if self.current_test_cost > self.config.max_cost_per_test:
            logger.warning(f"Current test cost ${self.current_test_cost:.4f} exceeds limit ${self.config.max_cost_per_test:.4f}")
            return False
        
        if self.session_cost > self.config.max_cost_per_session:
            logger.warning(f"Session cost ${self.session_cost:.4f} exceeds limit ${self.config.max_cost_per_session:.4f}")
            return False
        
        return True
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        session_duration = (datetime.now() - self.session_start_time).total_seconds()
        
        # Calculate statistics
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r["status"] == "success"])
        failed_tests = len([r for r in self.test_results if r["status"] == "error"])
        skipped_tests = len([r for r in self.test_results if r["status"] == "skipped"])
        timeout_tests = len([r for r in self.test_results if r["status"] == "timeout"])
        
        # Category breakdown
        category_stats = {}
        for result in self.test_results:
            category = result.get("category", "general")
            if category not in category_stats:
                category_stats[category] = {"total": 0, "success": 0, "failed": 0}
            category_stats[category]["total"] += 1
            if result["status"] == "success":
                category_stats[category]["success"] += 1
            elif result["status"] == "error":
                category_stats[category]["failed"] += 1
        
        return {
            "session_id": self.session_id,
            "session_duration": session_duration,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "timeout_tests": timeout_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "total_cost": self.session_cost,
            "average_cost_per_test": self.session_cost / total_tests if total_tests > 0 else 0,
            "category_breakdown": category_stats,
            "cost_monitor": self.cost_monitor.get_summary() if self.config.enable_cost_tracking else None,
            "usage_tracker": self.usage_tracker.get_summary() if self.config.enable_usage_tracking else None,
            "rate_limiter": self.rate_limiter.get_summary() if self.config.enable_rate_limiting else None,
        }
    
    def save_session_report(self, output_path: Optional[str] = None):
        """Save detailed session report to file"""
        if output_path is None:
            output_path = Path(self.config.test_data_dir) / "reports" / f"session_{self.session_id}.json"
        
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            "session_info": {
                "session_id": self.session_id,
                "start_time": self.session_start_time.isoformat(),
                "config": self.config.__dict__
            },
            "summary": self.get_session_summary(),
            "test_results": self.test_results,
            "generated_at": datetime.now().isoformat()
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Session report saved to: {output_path}")
        return output_path
    
    def cleanup(self):
        """Cleanup framework resources"""
        try:
            # Save final session report
            self.save_session_report()
            
            # Cleanup monitors
            if self.config.enable_cost_tracking:
                self.cost_monitor.cleanup()
            
            if self.config.enable_usage_tracking:
                self.usage_tracker.cleanup()
            
            if self.config.enable_rate_limiting:
                self.rate_limiter.cleanup()
            
            logger.info("Framework cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


# Pytest fixture for framework integration
@pytest.fixture(scope="session")
def real_api_framework():
    """Pytest fixture for real API framework"""
    config = APITestConfig(
        mode=TestMode.REAL_API,
        max_cost_per_test=0.5,  # Conservative for CI
        max_cost_per_session=5.0,
        require_api_keys=True,
        enable_cost_tracking=True,
        enable_usage_tracking=True
    )
    
    framework = RealAPITestFramework(config)
    yield framework
    
    # Cleanup
    framework.cleanup()


@pytest.fixture
def real_api_test_data():
    """Pytest fixture for test data generation"""
    generator = TestDataGenerator()
    return generator.get_test_data()