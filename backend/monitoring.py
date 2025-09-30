import time
import psutil
import asyncio
from typing import Dict, Any, Optional
from loguru import logger
from functools import wraps
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json
import threading
from dataclasses import dataclass, asdict
from enum import Enum

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

@dataclass
class Metric:
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str]
    metric_type: MetricType

class PerformanceMonitor:
    def __init__(self, max_metrics_per_type: int = 10000):
        self.metrics = defaultdict(lambda: deque(maxlen=max_metrics_per_type))
        self.request_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.response_times = defaultdict(lambda: deque(maxlen=1000))
        self.system_metrics = deque(maxlen=1000)
        self.active_requests = defaultdict(int)
        self.start_time = datetime.now()
        self._lock = threading.Lock()

    def track_request_time(self, endpoint: str):
        """Decorator to track request response times"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self._track_async_request(func, endpoint, *args, **kwargs)

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return self._track_sync_request(func, endpoint, *args, **kwargs)

            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        return decorator

    async def _track_async_request(self, func, endpoint, *args, **kwargs):
        """Track async request"""
        start_time = time.time()
        request_id = f"{endpoint}_{int(time.time()*1000000)}"

        with self._lock:
            self.active_requests[endpoint] += 1

        try:
            result = await func(*args, **kwargs)
            self._record_success(endpoint, start_time, request_id)
            return result
        except Exception as e:
            self._record_error(endpoint, start_time, request_id, e)
            raise
        finally:
            with self._lock:
                self.active_requests[endpoint] -= 1

    def _track_sync_request(self, func, endpoint, *args, **kwargs):
        """Track sync request"""
        start_time = time.time()
        request_id = f"{endpoint}_{int(time.time()*1000000)}"

        with self._lock:
            self.active_requests[endpoint] += 1

        try:
            result = func(*args, **kwargs)
            self._record_success(endpoint, start_time, request_id)
            return result
        except Exception as e:
            self._record_error(endpoint, start_time, request_id, e)
            raise
        finally:
            with self._lock:
                self.active_requests[endpoint] -= 1

    def _record_success(self, endpoint: str, start_time: float, request_id: str):
        """Record successful request"""
        duration = time.time() - start_time

        with self._lock:
            self.request_counts[endpoint] += 1
            self.response_times[endpoint].append(duration)

            # Record metrics
            self.record_metric(
                f"request_duration_seconds",
                duration,
                labels={"endpoint": endpoint, "status": "success"}
            )

            self.record_metric(
                f"requests_total",
                1,
                labels={"endpoint": endpoint, "status": "success"},
                metric_type=MetricType.COUNTER
            )

        logger.info(f"Request {request_id} to {endpoint} completed in {duration:.3f}s")

    def _record_error(self, endpoint: str, start_time: float, request_id: str, error: Exception):
        """Record failed request"""
        duration = time.time() - start_time
        error_type = type(error).__name__

        with self._lock:
            self.error_counts[endpoint] += 1
            self.response_times[endpoint].append(duration)

            # Record metrics
            self.record_metric(
                f"request_duration_seconds",
                duration,
                labels={"endpoint": endpoint, "status": "error", "error_type": error_type}
            )

            self.record_metric(
                f"requests_total",
                1,
                labels={"endpoint": endpoint, "status": "error", "error_type": error_type},
                metric_type=MetricType.COUNTER
            )

        logger.error(f"Request {request_id} to {endpoint} failed after {duration:.3f}s: {error}")

    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None,
                     metric_type: MetricType = MetricType.GAUGE):
        """Record a custom metric"""
        if labels is None:
            labels = {}

        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            labels=labels,
            metric_type=metric_type
        )

        with self._lock:
            self.metrics[name].append(metric)

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        with self._lock:
            stats = {}
            current_time = datetime.now()

            for endpoint in self.request_counts.keys():
                if endpoint in self.response_times and self.response_times[endpoint]:
                    durations = list(self.response_times[endpoint])
                    total_requests = self.request_counts[endpoint]
                    total_errors = self.error_counts[endpoint]

                    # Calculate percentiles
                    sorted_durations = sorted(durations)
                    n = len(sorted_durations)

                    stats[endpoint] = {
                        "total_requests": total_requests,
                        "total_errors": total_errors,
                        "success_rate": ((total_requests - total_errors) / total_requests * 100) if total_requests > 0 else 0,
                        "avg_response_time": sum(durations) / len(durations),
                        "min_response_time": min(durations),
                        "max_response_time": max(durations),
                        "p50_response_time": sorted_durations[int(n * 0.5)] if n > 0 else 0,
                        "p90_response_time": sorted_durations[int(n * 0.9)] if n > 0 else 0,
                        "p95_response_time": sorted_durations[int(n * 0.95)] if n > 0 else 0,
                        "p99_response_time": sorted_durations[int(n * 0.99)] if n > 0 else 0,
                        "active_requests": self.active_requests[endpoint],
                        "requests_per_minute": self._calculate_rpm(endpoint),
                        "error_rate": (total_errors / total_requests * 100) if total_requests > 0 else 0
                    }

            # Overall system stats
            uptime = current_time - self.start_time
            total_requests = sum(self.request_counts.values())
            total_errors = sum(self.error_counts.values())

            stats["_overall"] = {
                "uptime_seconds": uptime.total_seconds(),
                "total_requests": total_requests,
                "total_errors": total_errors,
                "overall_success_rate": ((total_requests - total_errors) / total_requests * 100) if total_requests > 0 else 0,
                "requests_per_second": total_requests / uptime.total_seconds() if uptime.total_seconds() > 0 else 0,
                "active_requests_total": sum(self.active_requests.values())
            }

        return stats

    def _calculate_rpm(self, endpoint: str) -> float:
        """Calculate requests per minute for an endpoint"""
        cutoff_time = datetime.now() - timedelta(minutes=1)
        recent_requests = 0

        # This is a simplified calculation
        # In a real implementation, you'd track request timestamps
        if endpoint in self.request_counts:
            # Estimate based on total requests and uptime
            uptime_minutes = (datetime.now() - self.start_time).total_seconds() / 60
            if uptime_minutes > 0:
                total_requests = self.request_counts[endpoint]
                return (total_requests / uptime_minutes) if uptime_minutes >= 1 else total_requests

        return 0

    def collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Disk metrics
            disk = psutil.disk_usage('/')

            # Network metrics (if available)
            try:
                network = psutil.net_io_counters()
                network_stats = {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            except:
                network_stats = {}

            metrics = {
                "timestamp": datetime.now(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": {
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "used_gb": memory.used / (1024**3),
                    "percent": memory.percent
                },
                "swap": {
                    "total_gb": swap.total / (1024**3),
                    "used_gb": swap.used / (1024**3),
                    "percent": swap.percent
                },
                "disk": {
                    "total_gb": disk.total / (1024**3),
                    "used_gb": disk.used / (1024**3),
                    "free_gb": disk.free / (1024**3),
                    "percent": disk.percent
                },
                "network": network_stats
            }

            with self._lock:
                self.system_metrics.append(metrics)

            # Record individual metrics for Prometheus-style collection
            self.record_metric("cpu_usage_percent", cpu_percent)
            self.record_metric("memory_usage_percent", memory.percent)
            self.record_metric("disk_usage_percent", disk.percent)
            self.record_metric("memory_available_gb", memory.available / (1024**3))

            return metrics

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return None

    def get_system_metrics_history(self, minutes: int = 60) -> list:
        """Get system metrics for the last N minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        with self._lock:
            return [
                metric for metric in self.system_metrics
                if metric["timestamp"] > cutoff_time
            ]

    def get_metrics_for_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        current_time = time.time()

        with self._lock:
            # Group metrics by name
            metrics_by_name = defaultdict(list)
            for metric_name, metric_list in self.metrics.items():
                for metric in metric_list:
                    metrics_by_name[metric_name].append(metric)

            for metric_name, metric_list in metrics_by_name.items():
                # Add help and type comments
                lines.append(f"# HELP {metric_name} {metric_name}")
                lines.append(f"# TYPE {metric_name} {metric_list[0].metric_type.value}")

                for metric in metric_list:
                    labels_str = ""
                    if metric.labels:
                        label_parts = [f'{k}="{v}"' for k, v in metric.labels.items()]
                        labels_str = "{" + ",".join(label_parts) + "}"

                    timestamp_ms = int(metric.timestamp.timestamp() * 1000)
                    lines.append(f"{metric_name}{labels_str} {metric.value} {timestamp_ms}")

        return "\n".join(lines)

    async def start_monitoring(self, interval: int = 60):
        """Start background monitoring task"""
        logger.info("Starting performance monitoring...")

        while True:
            try:
                self.collect_system_metrics()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(interval)

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        try:
            system_metrics = self.collect_system_metrics()
            stats = self.get_performance_stats()

            # Determine health based on various factors
            health_score = 100

            # Check CPU usage
            if system_metrics and system_metrics["cpu"]["percent"] > 80:
                health_score -= 20

            # Check memory usage
            if system_metrics and system_metrics["memory"]["percent"] > 90:
                health_score -= 30

            # Check disk usage
            if system_metrics and system_metrics["disk"]["percent"] > 85:
                health_score -= 15

            # Check error rates
            overall_stats = stats.get("_overall", {})
            success_rate = overall_stats.get("overall_success_rate", 100)
            if success_rate < 95:
                health_score -= 25

            # Determine status
            if health_score >= 80:
                status = "healthy"
            elif health_score >= 60:
                status = "degraded"
            else:
                status = "unhealthy"

            return {
                "status": status,
                "health_score": max(0, health_score),
                "checks": {
                    "cpu_ok": system_metrics["cpu"]["percent"] < 80 if system_metrics else True,
                    "memory_ok": system_metrics["memory"]["percent"] < 90 if system_metrics else True,
                    "disk_ok": system_metrics["disk"]["percent"] < 85 if system_metrics else True,
                    "success_rate_ok": success_rate >= 95
                },
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
            }

        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                "status": "unknown",
                "health_score": 0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Global monitor instance
performance_monitor = PerformanceMonitor()

# Cost tracking functionality
class CostTracker:
    def __init__(self):
        self.api_calls = deque(maxlen=10000)
        self.cost_estimates = {
            "text-embedding-3-small": 0.00002,  # per 1K tokens
            "text-embedding-3-large": 0.00013,  # per 1K tokens
            "gpt-4o-mini": 0.00015,  # per 1K tokens (input)
            "gpt-4o": 0.005,  # per 1K tokens (input)
            "gpt-4": 0.03,  # per 1K tokens (input)
            "whisper-1": 0.006,  # per minute
            "tts-1": 0.015,  # per 1K characters
            "tts-1-hd": 0.030,  # per 1K characters
        }
        self._lock = threading.Lock()

    def track_api_call(self, model: str, tokens: int = 0, duration: float = 0,
                      characters: int = 0, call_type: str = "unknown"):
        """Track API usage for cost estimation"""
        cost = 0

        if model in self.cost_estimates:
            if tokens > 0:
                cost = (tokens / 1000) * self.cost_estimates[model]
            elif duration > 0:  # For audio models
                cost = (duration / 60) * self.cost_estimates[model]
            elif characters > 0:  # For TTS
                cost = (characters / 1000) * self.cost_estimates[model]

        call_record = {
            "model": model,
            "call_type": call_type,
            "tokens": tokens,
            "duration": duration,
            "characters": characters,
            "estimated_cost": cost,
            "timestamp": datetime.now()
        }

        with self._lock:
            self.api_calls.append(call_record)

        # Record as metrics
        performance_monitor.record_metric(
            "api_cost_usd",
            cost,
            labels={"model": model, "call_type": call_type},
            metric_type=MetricType.COUNTER
        )

        performance_monitor.record_metric(
            "api_calls_total",
            1,
            labels={"model": model, "call_type": call_type},
            metric_type=MetricType.COUNTER
        )

        logger.info(f"API call tracked: {model} - ${cost:.6f}")

    def get_cost_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get cost summary for the specified period"""
        cutoff = datetime.now() - timedelta(days=days)

        with self._lock:
            recent_calls = [call for call in self.api_calls if call["timestamp"] > cutoff]

        if not recent_calls:
            return {
                "period_days": days,
                "total_calls": 0,
                "total_estimated_cost": 0,
                "daily_average": 0,
                "cost_by_model": {},
                "cost_by_day": {}
            }

        total_cost = sum(call["estimated_cost"] for call in recent_calls)
        calls_by_model = defaultdict(list)
        calls_by_day = defaultdict(list)

        for call in recent_calls:
            calls_by_model[call["model"]].append(call)
            day_key = call["timestamp"].date().isoformat()
            calls_by_day[day_key].append(call)

        cost_by_model = {}
        for model, calls in calls_by_model.items():
            cost_by_model[model] = {
                "calls": len(calls),
                "cost": sum(call["estimated_cost"] for call in calls),
                "tokens": sum(call["tokens"] for call in calls),
                "duration": sum(call["duration"] for call in calls),
                "characters": sum(call["characters"] for call in calls)
            }

        cost_by_day = {}
        for day, calls in calls_by_day.items():
            cost_by_day[day] = {
                "calls": len(calls),
                "cost": sum(call["estimated_cost"] for call in calls)
            }

        return {
            "period_days": days,
            "total_calls": len(recent_calls),
            "total_estimated_cost": total_cost,
            "daily_average": total_cost / days if days > 0 else 0,
            "cost_by_model": cost_by_model,
            "cost_by_day": cost_by_day,
            "projection_monthly": total_cost * 30 / days if days > 0 else 0
        }

# Global cost tracker
cost_tracker = CostTracker()