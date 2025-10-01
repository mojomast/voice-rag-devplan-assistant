"""
Monitoring module for Real API Test Framework

Provides cost tracking, usage monitoring, and rate limiting for API tests.
"""

import time
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from pathlib import Path
from loguru import logger
import threading


@dataclass
class APICostInfo:
    """Cost information for API calls"""
    provider: str
    model: str
    operation: str  # chat, transcription, tts, embedding
    input_tokens: int = 0
    output_tokens: int = 0
    cost_per_input_token: float = 0.0
    cost_per_output_token: float = 0.0
    base_cost: float = 0.0
    total_cost: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class UsageRecord:
    """Record of API usage"""
    timestamp: datetime
    provider: str
    operation: str
    model: str
    tokens_used: int = 0
    duration_ms: int = 0
    success: bool = True
    error_type: Optional[str] = None


class CostMonitor:
    """
    Monitors and tracks API costs across different providers and models.
    """
    
    # Cost per 1K tokens (USD) - approximate rates
    COST_RATES = {
        "openai": {
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
            "text-embedding-3-large": {"input": 0.00013, "output": 0.0},
            "whisper-1": {"base": 0.006},  # per minute
            "tts-1": {"base": 0.015},  # per 1K characters
            "tts-1-hd": {"base": 0.030}  # per 1K characters
        },
        "requesty": {
            "zai/glm-4.5": {"input": 0.00005, "output": 0.00015},
            "requesty/embedding-001": {"input": 0.00001, "output": 0.0},
            "openai/gpt-4o-mini": {"input": 0.00015, "output": 0.0006}
        }
    }
    
    def __init__(self, config):
        self.config = config
        self.session_costs: List[APICostInfo] = []
        self.test_costs: Dict[str, List[APICostInfo]] = defaultdict(list)
        self.current_test_tracker: Optional[CostTracker] = None
        self.total_session_cost = 0.0
        self.cost_warnings_sent = 0
        self._lock = threading.Lock()
    
    def initialize(self):
        """Initialize the cost monitor"""
        logger.info("Cost monitor initialized")
    
    def start_test_tracking(self, test_name: str) -> 'CostTracker':
        """Start tracking costs for a specific test"""
        tracker = CostTracker(self, test_name)
        self.current_test_tracker = tracker
        return tracker
    
    def record_cost(self, cost_info: APICostInfo):
        """Record a cost entry"""
        with self._lock:
            self.session_costs.append(cost_info)
            self.total_session_cost += cost_info.total_cost
            
            if self.current_test_tracker:
                test_name = self.current_test_tracker.test_name
                self.test_costs[test_name].append(cost_info)
            
            # Check cost warning threshold
            if self.total_session_cost > self.config.max_cost_per_session * self.config.cost_warning_threshold:
                if self.cost_warnings_sent < 3:  # Limit warnings
                    logger.warning(f"Session cost warning: ${self.total_session_cost:.4f} (threshold: ${self.config.max_cost_per_session * self.config.cost_warning_threshold:.4f})")
                    self.cost_warnings_sent += 1
    
    def calculate_test_cost(self, test_name: str, api_response: Dict) -> float:
        """Calculate cost for a test based on API response"""
        cost = 0.0
        
        # Extract cost information from response
        if "usage" in api_response:
            usage = api_response["usage"]
            provider = api_response.get("provider", "openai")
            model = api_response.get("model", "unknown")
            operation = api_response.get("operation", "chat")
            
            cost_info = self._calculate_cost_from_usage(
                provider, model, operation, usage
            )
            cost = cost_info.total_cost
            self.record_cost(cost_info)
        
        elif "cost" in api_response:
            # Direct cost provided
            cost = float(api_response["cost"])
            cost_info = APICostInfo(
                provider=api_response.get("provider", "unknown"),
                model=api_response.get("model", "unknown"),
                operation=api_response.get("operation", "unknown"),
                total_cost=cost
            )
            self.record_cost(cost_info)
        
        return cost
    
    def _calculate_cost_from_usage(self, provider: str, model: str, operation: str, usage: Dict) -> APICostInfo:
        """Calculate cost from usage information"""
        provider_rates = self.COST_RATES.get(provider.lower(), {})
        model_rates = provider_rates.get(model, {})
        
        input_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0))
        output_tokens = usage.get("completion_tokens", usage.get("output_tokens", 0))
        
        cost_per_input = model_rates.get("input", 0.0)
        cost_per_output = model_rates.get("output", 0.0)
        base_cost = model_rates.get("base", 0.0)
        
        # Handle special cases
        if operation == "transcription" and "duration" in usage:
            # Whisper pricing per minute
            duration_minutes = usage["duration"] / 60
            base_cost = model_rates.get("base", 0.006) * duration_minutes
        elif operation == "tts" and "character_count" in usage:
            # TTS pricing per 1K characters
            char_count = usage["character_count"]
            base_cost = model_rates.get("base", 0.015) * (char_count / 1000)
        
        input_cost = (input_tokens / 1000) * cost_per_input
        output_cost = (output_tokens / 1000) * cost_per_output
        total_cost = input_cost + output_cost + base_cost
        
        return APICostInfo(
            provider=provider,
            model=model,
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_per_input_token=cost_per_input,
            cost_per_output_token=cost_per_output,
            base_cost=base_cost,
            total_cost=total_cost
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get cost monitoring summary"""
        with self._lock:
            # Provider breakdown
            provider_costs = defaultdict(float)
            model_costs = defaultdict(float)
            operation_costs = defaultdict(float)
            
            for cost_info in self.session_costs:
                provider_costs[cost_info.provider] += cost_info.total_cost
                model_costs[f"{cost_info.provider}/{cost_info.model}"] += cost_info.total_cost
                operation_costs[cost_info.operation] += cost_info.total_cost
            
            # Test breakdown
            test_breakdown = {}
            for test_name, costs in self.test_costs.items():
                test_breakdown[test_name] = sum(c.total_cost for c in costs)
            
            return {
                "total_session_cost": self.total_session_cost,
                "total_api_calls": len(self.session_costs),
                "provider_breakdown": dict(provider_costs),
                "model_breakdown": dict(model_costs),
                "operation_breakdown": dict(operation_costs),
                "test_breakdown": test_breakdown,
                "cost_warnings_sent": self.cost_warnings_sent,
                "budget_utilization": self.total_session_cost / self.config.max_cost_per_session
            }
    
    def cleanup(self):
        """Cleanup cost monitor resources"""
        logger.info(f"Cost monitor cleanup - Total session cost: ${self.total_session_cost:.4f}")


class CostTracker:
    """
    Tracks costs for a specific test.
    """
    
    def __init__(self, cost_monitor: CostMonitor, test_name: str):
        self.cost_monitor = cost_monitor
        self.test_name = test_name
        self.start_time = datetime.now()
        self.costs: List[APICostInfo] = []
        self.total_cost = 0.0
    
    def record_cost(self, cost: float):
        """Record cost for the current test"""
        self.total_cost += cost
    
    def end_tracking(self):
        """End tracking for the current test"""
        duration = (datetime.now() - self.start_time).total_seconds()
        logger.debug(f"Test {self.test_name} cost tracking ended - Cost: ${self.total_cost:.4f}, Duration: {duration:.2f}s")


class UsageTracker:
    """
    Tracks API usage patterns and statistics.
    """
    
    def __init__(self, config):
        self.config = config
        self.usage_records: List[UsageRecord] = []
        self.provider_stats: Dict[str, Dict] = defaultdict(lambda: {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_duration_ms": 0,
            "average_duration_ms": 0.0,
            "error_types": defaultdict(int)
        })
        self._lock = threading.Lock()
    
    def initialize(self):
        """Initialize the usage tracker"""
        logger.info("Usage tracker initialized")
    
    def record_test_usage(self, test_name: str, category: str, result: Dict):
        """Record usage for a test"""
        if "api_calls" not in result:
            return
        
        for api_call in result["api_calls"]:
            record = UsageRecord(
                timestamp=datetime.now(),
                provider=api_call.get("provider", "unknown"),
                operation=api_call.get("operation", "unknown"),
                model=api_call.get("model", "unknown"),
                tokens_used=api_call.get("tokens_used", 0),
                duration_ms=api_call.get("duration_ms", 0),
                success=api_call.get("success", True),
                error_type=api_call.get("error_type") if not api_call.get("success", True) else None
            )
            
            self._add_usage_record(record)
    
    def _add_usage_record(self, record: UsageRecord):
        """Add a usage record and update statistics"""
        with self._lock:
            self.usage_records.append(record)
            
            # Update provider statistics
            stats = self.provider_stats[record.provider]
            stats["total_requests"] += 1
            
            if record.success:
                stats["successful_requests"] += 1
            else:
                stats["failed_requests"] += 1
                if record.error_type:
                    stats["error_types"][record.error_type] += 1
            
            stats["total_tokens"] += record.tokens_used
            stats["total_duration_ms"] += record.duration_ms
            
            # Calculate average duration
            if stats["total_requests"] > 0:
                stats["average_duration_ms"] = stats["total_duration_ms"] / stats["total_requests"]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get usage tracking summary"""
        with self._lock:
            # Calculate success rates
            for provider, stats in self.provider_stats.items():
                total = stats["total_requests"]
                if total > 0:
                    stats["success_rate"] = stats["successful_requests"] / total
                else:
                    stats["success_rate"] = 0.0
            
            # Time-based statistics
            now = datetime.now()
            last_hour = now - timedelta(hours=1)
            last_day = now - timedelta(days=1)
            
            recent_records = [r for r in self.usage_records if r.timestamp >= last_hour]
            day_records = [r for r in self.usage_records if r.timestamp >= last_day]
            
            return {
                "total_requests": len(self.usage_records),
                "requests_last_hour": len(recent_records),
                "requests_last_day": len(day_records),
                "provider_stats": dict(self.provider_stats),
                "most_used_provider": max(self.provider_stats.keys(), key=lambda p: self.provider_stats[p]["total_requests"]) if self.provider_stats else None,
                "average_tokens_per_request": sum(r.tokens_used for r in self.usage_records) / len(self.usage_records) if self.usage_records else 0
            }
    
    def cleanup(self):
        """Cleanup usage tracker resources"""
        logger.info("Usage tracker cleanup completed")


class RateLimitMonitor:
    """
    Monitors and enforces API rate limits.
    """
    
    def __init__(self, config):
        self.config = config
        self.request_times: deque = deque(maxlen=1000)
        self.minute_requests: deque = deque()
        self.hour_requests: deque = deque()
        self.rate_limit_warnings = 0
        self._lock = threading.Lock()
    
    def initialize(self):
        """Initialize the rate limit monitor"""
        logger.info(f"Rate limit monitor initialized - {self.config.requests_per_minute} req/min, {self.config.requests_per_hour} req/hour")
    
    def can_make_request(self) -> bool:
        """Check if a request can be made without exceeding rate limits"""
        with self._lock:
            now = time.time()
            
            # Clean old requests
            self._cleanup_old_requests(now)
            
            # Check minute limit
            minute_cutoff = now - 60
            recent_minute = [t for t in self.minute_requests if t >= minute_cutoff]
            
            if len(recent_minute) >= self.config.requests_per_minute:
                if self.rate_limit_warnings < 5:  # Limit warnings
                    logger.warning(f"Rate limit exceeded: {len(recent_minute)} requests in last minute (limit: {self.config.requests_per_minute})")
                    self.rate_limit_warnings += 1
                return False
            
            # Check hour limit
            hour_cutoff = now - 3600
            recent_hour = [t for t in self.hour_requests if t >= hour_cutoff]
            
            if len(recent_hour) >= self.config.requests_per_hour:
                if self.rate_limit_warnings < 5:
                    logger.warning(f"Rate limit exceeded: {len(recent_hour)} requests in last hour (limit: {self.config.requests_per_hour})")
                    self.rate_limit_warnings += 1
                return False
            
            return True
    
    def record_request_start(self):
        """Record the start of a request"""
        with self._lock:
            now = time.time()
            self.request_times.append(now)
            self.minute_requests.append(now)
            self.hour_requests.append(now)
    
    def record_request_end(self):
        """Record the end of a request"""
        # This could be used for tracking request duration
        pass
    
    def _cleanup_old_requests(self, now: float):
        """Clean up old request timestamps"""
        minute_cutoff = now - 60
        hour_cutoff = now - 3600
        
        # Clean minute requests
        while self.minute_requests and self.minute_requests[0] < minute_cutoff:
            self.minute_requests.popleft()
        
        # Clean hour requests
        while self.hour_requests and self.hour_requests[0] < hour_cutoff:
            self.hour_requests.popleft()
    
    def get_wait_time(self) -> float:
        """Get the time to wait before making the next request"""
        if self.can_make_request():
            return 0.0
        
        with self._lock:
            now = time.time()
            
            # Calculate wait time based on minute limit
            if self.minute_requests:
                oldest_request = min(self.minute_requests)
                wait_until = oldest_request + 60
                minute_wait = max(0, wait_until - now)
            else:
                minute_wait = 0.0
            
            # Calculate wait time based on hour limit
            if self.hour_requests:
                oldest_request = min(self.hour_requests)
                wait_until = oldest_request + 3600
                hour_wait = max(0, wait_until - now)
            else:
                hour_wait = 0.0
            
            return max(minute_wait, hour_wait)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get rate limiting summary"""
        with self._lock:
            now = time.time()
            minute_cutoff = now - 60
            hour_cutoff = now - 3600
            
            recent_minute = len([t for t in self.minute_requests if t >= minute_cutoff])
            recent_hour = len([t for t in self.hour_requests if t >= hour_cutoff])
            
            return {
                "requests_last_minute": recent_minute,
                "requests_last_hour": recent_hour,
                "minute_limit": self.config.requests_per_minute,
                "hour_limit": self.config.requests_per_hour,
                "minute_utilization": recent_minute / self.config.requests_per_minute,
                "hour_utilization": recent_hour / self.config.requests_per_hour,
                "rate_limit_warnings": self.rate_limit_warnings,
                "wait_time_seconds": self.get_wait_time()
            }
    
    def cleanup(self):
        """Cleanup rate limit monitor resources"""
        logger.info("Rate limit monitor cleanup completed")