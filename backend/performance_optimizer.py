# ===== Performance Optimization Module =====
# Voice RAG System Performance Enhancements
# Advanced caching, query optimization, and resource management

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from functools import wraps, lru_cache
from datetime import datetime, timedelta
import hashlib
import pickle
import psutil

try:
    import redis  # type: ignore
except ImportError:  # pragma: no cover - Redis is optional for local/test environments
    redis = None
from sqlalchemy.orm import Session
from sqlalchemy import text
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import defaultdict, deque
import weakref

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Advanced performance monitoring and optimization."""

    def __init__(self):
        self.metrics = defaultdict(deque)
        self.query_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.optimization_suggestions = []

    def record_metric(self, metric_name: str, value: float, timestamp: Optional[datetime] = None):
        """Record a performance metric with automatic cleanup."""
        if timestamp is None:
            timestamp = datetime.now()

        # Keep only last 1000 entries per metric
        metric_queue = self.metrics[metric_name]
        metric_queue.append((timestamp, value))

        if len(metric_queue) > 1000:
            metric_queue.popleft()

    def get_metric_stats(self, metric_name: str, time_window: timedelta = timedelta(minutes=5)) -> Dict[str, float]:
        """Get statistical analysis of a metric within time window."""
        cutoff_time = datetime.now() - time_window
        recent_values = [
            value for timestamp, value in self.metrics[metric_name]
            if timestamp >= cutoff_time
        ]

        if not recent_values:
            return {}

        return {
            "count": len(recent_values),
            "mean": np.mean(recent_values),
            "median": np.median(recent_values),
            "std": np.std(recent_values),
            "min": np.min(recent_values),
            "max": np.max(recent_values),
            "p95": np.percentile(recent_values, 95),
            "p99": np.percentile(recent_values, 99)
        }

    def analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends and generate optimization suggestions."""
        analysis = {}

        for metric_name in self.metrics:
            stats = self.get_metric_stats(metric_name)
            if stats:
                analysis[metric_name] = stats

                # Generate optimization suggestions based on metrics
                if metric_name == "query_response_time" and stats.get("p95", 0) > 2.0:
                    self.optimization_suggestions.append({
                        "type": "query_optimization",
                        "metric": metric_name,
                        "current_p95": stats["p95"],
                        "suggestion": "Consider query caching or index optimization",
                        "priority": "high" if stats["p95"] > 5.0 else "medium"
                    })

                elif metric_name == "memory_usage" and stats.get("mean", 0) > 80:
                    self.optimization_suggestions.append({
                        "type": "memory_optimization",
                        "metric": metric_name,
                        "current_mean": stats["mean"],
                        "suggestion": "Implement memory pooling or reduce cache size",
                        "priority": "high" if stats["mean"] > 90 else "medium"
                    })

        return {
            "metrics": analysis,
            "suggestions": self.optimization_suggestions[-10:],  # Last 10 suggestions
            "cache_hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
        }

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def performance_track(metric_name: str = None):
    """Decorator to track function performance."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                performance_monitor.record_metric(
                    metric_name or f"{func.__name__}_response_time",
                    execution_time
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                performance_monitor.record_metric(
                    f"{func.__name__}_error_time",
                    execution_time
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                performance_monitor.record_metric(
                    metric_name or f"{func.__name__}_response_time",
                    execution_time
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                performance_monitor.record_metric(
                    f"{func.__name__}_error_time",
                    execution_time
                )
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

class SmartCache:
    """Intelligent caching system with TTL, LRU, and size-based eviction."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600, redis_client=None):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.redis_client = redis_client
        self.local_cache = {}
        self.access_times = {}
        self.lock = threading.RLock()

    def _generate_key(self, key: str, **kwargs) -> str:
        """Generate a cache key from parameters."""
        if kwargs:
            key_data = f"{key}:{hashlib.md5(str(sorted(kwargs.items())).encode()).hexdigest()}"
        else:
            key_data = key
        return f"voice_rag:cache:{key_data}"

    def _evict_lru(self):
        """Evict least recently used items when cache is full."""
        if len(self.local_cache) >= self.max_size:
            # Remove 20% of least recently used items
            items_to_remove = int(self.max_size * 0.2)
            sorted_items = sorted(self.access_times.items(), key=lambda x: x[1])

            for key, _ in sorted_items[:items_to_remove]:
                self.local_cache.pop(key, None)
                self.access_times.pop(key, None)

    async def get(self, key: str, **kwargs) -> Optional[Any]:
        """Get item from cache with hierarchical lookup (local -> Redis)."""
        cache_key = self._generate_key(key, **kwargs)

        with self.lock:
            # Check local cache first
            if cache_key in self.local_cache:
                item, expiry = self.local_cache[cache_key]
                if datetime.now() < expiry:
                    self.access_times[cache_key] = datetime.now()
                    performance_monitor.cache_hits += 1
                    return item
                else:
                    # Expired - remove from local cache
                    del self.local_cache[cache_key]
                    self.access_times.pop(cache_key, None)

        # Check Redis cache if available
        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    item = pickle.loads(cached_data)
                    # Store in local cache for faster access
                    await self.set(key, item, **kwargs)
                    performance_monitor.cache_hits += 1
                    return item
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")

        performance_monitor.cache_misses += 1
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None, **kwargs):
        """Set item in cache with TTL."""
        cache_key = self._generate_key(key, **kwargs)
        ttl = ttl or self.default_ttl
        expiry = datetime.now() + timedelta(seconds=ttl)

        with self.lock:
            self._evict_lru()
            self.local_cache[cache_key] = (value, expiry)
            self.access_times[cache_key] = datetime.now()

        # Also store in Redis if available
        if self.redis_client:
            try:
                serialized_value = pickle.dumps(value)
                await self.redis_client.setex(cache_key, ttl, serialized_value)
            except Exception as e:
                logger.warning(f"Redis cache set error: {e}")

    async def invalidate(self, pattern: str = None):
        """Invalidate cache entries by pattern or clear all."""
        if pattern:
            keys_to_remove = [k for k in self.local_cache.keys() if pattern in k]
            with self.lock:
                for key in keys_to_remove:
                    self.local_cache.pop(key, None)
                    self.access_times.pop(key, None)

            if self.redis_client:
                try:
                    keys = await self.redis_client.keys(f"*{pattern}*")
                    if keys:
                        await self.redis_client.delete(*keys)
                except Exception as e:
                    logger.warning(f"Redis cache invalidation error: {e}")
        else:
            with self.lock:
                self.local_cache.clear()
                self.access_times.clear()

            if self.redis_client:
                try:
                    await self.redis_client.flushdb()
                except Exception as e:
                    logger.warning(f"Redis cache flush error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "local_cache_size": len(self.local_cache),
            "max_size": self.max_size,
            "cache_utilization": len(self.local_cache) / self.max_size,
            "hit_rate": performance_monitor.cache_hits / (performance_monitor.cache_hits + performance_monitor.cache_misses) if (performance_monitor.cache_hits + performance_monitor.cache_misses) > 0 else 0
        }

# Global cache instance
smart_cache = SmartCache()

class QueryOptimizer:
    """Database query optimization and analysis."""

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.query_patterns = defaultdict(list)
        self.slow_queries = deque(maxlen=100)

    @performance_track("db_query_time")
    async def execute_optimized_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute query with optimization and monitoring."""
        start_time = time.time()

        # Check cache first
        cache_key = f"query:{hashlib.md5(f'{query}:{params}'.encode()).hexdigest()}"
        cached_result = await smart_cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        try:
            # Execute query
            result = self.db_session.execute(text(query), params or {})
            rows = [dict(row._mapping) for row in result.fetchall()]

            execution_time = time.time() - start_time

            # Log slow queries for analysis
            if execution_time > 1.0:  # Queries taking more than 1 second
                self.slow_queries.append({
                    "query": query,
                    "params": params,
                    "execution_time": execution_time,
                    "timestamp": datetime.now(),
                    "row_count": len(rows)
                })

                logger.warning(f"Slow query detected: {execution_time:.2f}s - {query[:100]}...")

            # Cache result if query completed quickly and returned reasonable amount of data
            if execution_time < 0.5 and len(rows) < 1000:
                await smart_cache.set(cache_key, rows, ttl=300)  # 5-minute cache

            return rows

        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise

    def analyze_query_patterns(self) -> Dict[str, Any]:
        """Analyze query patterns for optimization opportunities."""
        analysis = {
            "slow_queries": list(self.slow_queries),
            "optimization_suggestions": []
        }

        # Analyze slow queries for patterns
        for slow_query in self.slow_queries:
            query = slow_query["query"].lower()

            suggestions = []
            if "select *" in query:
                suggestions.append("Consider selecting only needed columns instead of SELECT *")

            if "order by" in query and "limit" not in query:
                suggestions.append("Consider adding LIMIT to ORDER BY queries")

            if query.count("join") > 3:
                suggestions.append("Consider breaking complex joins into smaller queries")

            if "like '%" in query:
                suggestions.append("Consider full-text search instead of LIKE patterns starting with %")

            if suggestions:
                analysis["optimization_suggestions"].extend(suggestions)

        return analysis

class ResourceMonitor:
    """System resource monitoring and optimization."""

    def __init__(self):
        self.resource_history = defaultdict(deque)

    def collect_system_metrics(self) -> Dict[str, float]:
        """Collect current system resource metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Network I/O
            net_io = psutil.net_io_counters()

            metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
                "network_bytes_sent": net_io.bytes_sent,
                "network_bytes_recv": net_io.bytes_recv
            }

            # Record metrics
            timestamp = datetime.now()
            for metric_name, value in metrics.items():
                self.resource_history[metric_name].append((timestamp, value))

                # Keep only last 1000 entries
                if len(self.resource_history[metric_name]) > 1000:
                    self.resource_history[metric_name].popleft()

                # Record in performance monitor
                performance_monitor.record_metric(metric_name, value, timestamp)

            return metrics

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}

    def get_resource_recommendations(self) -> List[Dict[str, Any]]:
        """Generate resource optimization recommendations."""
        recommendations = []

        try:
            current_metrics = self.collect_system_metrics()

            if current_metrics.get("cpu_percent", 0) > 80:
                recommendations.append({
                    "type": "cpu_optimization",
                    "priority": "high",
                    "current_value": current_metrics["cpu_percent"],
                    "recommendation": "High CPU usage detected. Consider scaling up or optimizing CPU-intensive operations.",
                    "actions": [
                        "Enable CPU-based auto-scaling",
                        "Profile and optimize hot code paths",
                        "Consider async processing for heavy tasks"
                    ]
                })

            if current_metrics.get("memory_percent", 0) > 85:
                recommendations.append({
                    "type": "memory_optimization",
                    "priority": "high",
                    "current_value": current_metrics["memory_percent"],
                    "recommendation": "High memory usage detected. Consider memory optimization strategies.",
                    "actions": [
                        "Implement memory pooling",
                        "Reduce cache sizes",
                        "Enable memory-based auto-scaling",
                        "Profile memory usage patterns"
                    ]
                })

            if current_metrics.get("disk_percent", 0) > 90:
                recommendations.append({
                    "type": "storage_optimization",
                    "priority": "critical",
                    "current_value": current_metrics["disk_percent"],
                    "recommendation": "Critical disk usage detected. Immediate action required.",
                    "actions": [
                        "Clean up temporary files",
                        "Archive old logs",
                        "Implement log rotation",
                        "Scale storage capacity"
                    ]
                })

        except Exception as e:
            logger.error(f"Error generating resource recommendations: {e}")

        return recommendations

class ConnectionPoolOptimizer:
    """Database connection pool optimization."""

    def __init__(self, initial_pool_size: int = 5, max_pool_size: int = 20):
        self.initial_pool_size = initial_pool_size
        self.max_pool_size = max_pool_size
        self.connection_stats = defaultdict(int)
        self.pool_adjustments = []

    def monitor_connection_usage(self, active_connections: int, pool_size: int):
        """Monitor connection pool usage and suggest optimizations."""
        self.connection_stats["total_requests"] += 1

        utilization = active_connections / pool_size if pool_size > 0 else 0

        performance_monitor.record_metric("connection_pool_utilization", utilization)
        performance_monitor.record_metric("active_connections", active_connections)

        # Suggest pool size adjustments
        if utilization > 0.9 and pool_size < self.max_pool_size:
            suggestion = {
                "action": "increase_pool_size",
                "current_size": pool_size,
                "suggested_size": min(pool_size + 2, self.max_pool_size),
                "reason": f"High utilization: {utilization:.2f}",
                "timestamp": datetime.now()
            }
            self.pool_adjustments.append(suggestion)
            return suggestion

        elif utilization < 0.3 and pool_size > self.initial_pool_size:
            suggestion = {
                "action": "decrease_pool_size",
                "current_size": pool_size,
                "suggested_size": max(pool_size - 1, self.initial_pool_size),
                "reason": f"Low utilization: {utilization:.2f}",
                "timestamp": datetime.now()
            }
            self.pool_adjustments.append(suggestion)
            return suggestion

        return None

class AsyncTaskOptimizer:
    """Optimize async task execution and resource allocation."""

    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
        self.task_metrics = defaultdict(list)

    async def execute_batch_tasks(self, tasks: List[callable], batch_size: int = None) -> List[Any]:
        """Execute tasks in optimized batches."""
        batch_size = batch_size or min(len(tasks), self.max_concurrent_tasks)
        results = []

        # Execute tasks in batches to avoid overwhelming system resources
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            start_time = time.time()

            try:
                # Execute batch concurrently
                loop = asyncio.get_event_loop()
                batch_results = await asyncio.gather(
                    *[loop.run_in_executor(self.executor, task) for task in batch],
                    return_exceptions=True
                )

                # Process results and handle exceptions
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Task execution error: {result}")
                        results.append(None)
                    else:
                        results.append(result)

                execution_time = time.time() - start_time
                performance_monitor.record_metric("batch_execution_time", execution_time)

                # Add small delay between batches to prevent resource exhaustion
                if i + batch_size < len(tasks):
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Batch execution error: {e}")
                results.extend([None] * len(batch))

        return results

    def optimize_task_scheduling(self, task_priorities: Dict[str, int] = None) -> Dict[str, Any]:
        """Optimize task scheduling based on priorities and resource availability."""
        current_metrics = performance_monitor.get_metric_stats("cpu_percent")

        optimization_strategy = {
            "recommended_batch_size": self.max_concurrent_tasks,
            "priority_scheduling": False,
            "resource_throttling": False
        }

        # Adjust based on current CPU usage
        if current_metrics and current_metrics.get("mean", 0) > 70:
            optimization_strategy["recommended_batch_size"] = max(1, self.max_concurrent_tasks // 2)
            optimization_strategy["resource_throttling"] = True

        # Enable priority scheduling if priorities are provided
        if task_priorities:
            optimization_strategy["priority_scheduling"] = True
            optimization_strategy["priority_order"] = sorted(
                task_priorities.items(),
                key=lambda x: x[1],
                reverse=True
            )

        return optimization_strategy

# Global optimizers
resource_monitor = ResourceMonitor()
connection_optimizer = ConnectionPoolOptimizer()
task_optimizer = AsyncTaskOptimizer()

async def get_performance_summary() -> Dict[str, Any]:
    """Get comprehensive performance summary and recommendations."""
    try:
        # Collect current metrics
        system_metrics = resource_monitor.collect_system_metrics()
        performance_analysis = performance_monitor.analyze_performance_trends()
        cache_stats = smart_cache.get_stats()
        resource_recommendations = resource_monitor.get_resource_recommendations()

        return {
            "timestamp": datetime.now().isoformat(),
            "system_metrics": system_metrics,
            "performance_analysis": performance_analysis,
            "cache_statistics": cache_stats,
            "recommendations": resource_recommendations,
            "optimization_status": {
                "caching_enabled": True,
                "query_optimization": True,
                "resource_monitoring": True,
                "async_optimization": True
            }
        }

    except Exception as e:
        logger.error(f"Error generating performance summary: {e}")
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

# Startup optimization function
async def initialize_performance_optimizations():
    """Initialize all performance optimization components."""
    logger.info("Initializing performance optimizations...")

    try:
        # Start resource monitoring
        resource_monitor.collect_system_metrics()

        # Warm up cache
        await smart_cache.set("initialization", {"status": "complete"})

        # Initialize task optimizer
        task_optimizer.optimize_task_scheduling()

        logger.info("Performance optimizations initialized successfully")

    except Exception as e:
        logger.error(f"Error initializing performance optimizations: {e}")
        raise