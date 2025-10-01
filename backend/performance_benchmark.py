"""
Performance Benchmarking and Monitoring Tools
Provides comprehensive performance testing and monitoring capabilities
"""

import asyncio
import time
import json
import statistics
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import psutil
import numpy as np

from loguru import logger
from .cache_manager import cache_manager
from .vector_store_optimizer import vector_store_manager
from .connection_pool import connection_manager
from .optimized_rag_handler import optimized_rag_handler
from .config import settings

@dataclass
class BenchmarkConfig:
    """Configuration for benchmark tests"""
    # Test parameters
    num_queries: int = 100
    concurrent_users: int = 10
    test_duration_seconds: int = 60
    warmup_queries: int = 10
    
    # Performance targets
    target_response_time_ms: float = 500.0
    target_throughput_qps: float = 20.0
    target_error_rate: float = 0.01  # 1%
    target_cache_hit_rate: float = 0.8  # 80%
    
    # Test data
    test_queries: List[str] = None
    
    # Reporting
    enable_detailed_logging: bool = False
    save_results: bool = True
    results_file: str = "benchmark_results.json"

@dataclass
class BenchmarkResult:
    """Single benchmark test result"""
    query: str
    response_time_ms: float
    status: str
    error: Optional[str] = None
    cache_hit: bool = False
    vector_search_time_ms: Optional[float] = None
    llm_time_ms: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class BenchmarkSummary:
    """Summary of benchmark results"""
    total_queries: int
    successful_queries: int
    failed_queries: int
    avg_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    throughput_qps: float
    error_rate: float
    cache_hit_rate: float
    total_duration_seconds: float
    targets_met: Dict[str, bool]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class PerformanceBenchmark:
    """Comprehensive performance benchmarking tool"""
    
    def __init__(self, config: Optional[BenchmarkConfig] = None):
        self.config = config or BenchmarkConfig()
        self.results: List[BenchmarkResult] = []
        self.system_metrics: List[Dict[str, Any]] = []
        self._monitoring_active = False
        self._monitoring_thread = None
        
        # Default test queries if not provided
        if not self.config.test_queries:
            self.config.test_queries = [
                "What is the authentication system architecture?",
                "How do I implement user registration?",
                "What are the database schema requirements?",
                "Explain the API endpoint structure",
                "How does the caching system work?",
                "What are the security best practices?",
                "Describe the deployment process",
                "How to handle error logging?",
                "What is the testing strategy?",
                "Explain the performance optimization approach"
            ]
        
        logger.info(f"Performance benchmark initialized with {len(self.config.test_queries)} test queries")
    
    async def run_benchmark(self) -> BenchmarkSummary:
        """Run comprehensive performance benchmark"""
        logger.info("Starting performance benchmark")
        
        try:
            # Clear caches for clean test
            await self._prepare_test_environment()
            
            # Start system monitoring
            self._start_system_monitoring()
            
            # Warmup phase
            await self._run_warmup()
            
            # Main benchmark phase
            start_time = time.time()
            await self._run_main_benchmark()
            total_duration = time.time() - start_time
            
            # Stop monitoring
            self._stop_system_monitoring()
            
            # Generate summary
            summary = self._generate_summary(total_duration)
            
            # Save results if configured
            if self.config.save_results:
                await self._save_results(summary)
            
            logger.info(f"Benchmark completed - Avg response time: {summary.avg_response_time_ms:.2f}ms, "
                       f"Throughput: {summary.throughput_qps:.2f} QPS")
            
            return summary
            
        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            raise
    
    async def _prepare_test_environment(self):
        """Prepare test environment"""
        try:
            # Clear caches
            await cache_manager.clear_namespace('query')
            await cache_manager.clear_namespace('vector')
            await cache_manager.clear_namespace('embedding')
            
            # Reset stats
            self.results.clear()
            self.system_metrics.clear()
            
            logger.info("Test environment prepared")
            
        except Exception as e:
            logger.error(f"Failed to prepare test environment: {e}")
            raise
    
    async def _run_warmup(self):
        """Run warmup queries"""
        logger.info(f"Running {self.config.warmup_queries} warmup queries")
        
        warmup_queries = self.config.test_queries[:self.config.warmup_queries]
        
        for query in warmup_queries:
            try:
                await optimized_rag_handler.ask_question(query)
                await asyncio.sleep(0.1)  # Small delay between queries
            except Exception as e:
                logger.warning(f"Warmup query failed: {e}")
        
        logger.info("Warmup completed")
    
    async def _run_main_benchmark(self):
        """Run main benchmark test"""
        logger.info(f"Running main benchmark with {self.config.num_queries} queries")
        
        if self.config.concurrent_users == 1:
            # Sequential execution
            await self._run_sequential_benchmark()
        else:
            # Concurrent execution
            await self._run_concurrent_benchmark()
    
    async def _run_sequential_benchmark(self):
        """Run benchmark sequentially"""
        for i in range(self.config.num_queries):
            query = self.config.test_queries[i % len(self.config.test_queries)]
            result = await self._execute_query(query)
            self.results.append(result)
            
            if self.config.enable_detailed_logging:
                logger.debug(f"Query {i+1}: {result.response_time_ms:.2f}ms")
    
    async def _run_concurrent_benchmark(self):
        """Run benchmark with concurrent users"""
        semaphore = asyncio.Semaphore(self.config.concurrent_users)
        
        async def execute_with_semaphore(query: str) -> BenchmarkResult:
            async with semaphore:
                return await self._execute_query(query)
        
        # Create tasks
        tasks = []
        for i in range(self.config.num_queries):
            query = self.config.test_queries[i % len(self.config.test_queries)]
            task = execute_with_semaphore(query)
            tasks.append(task)
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Concurrent query failed: {result}")
                # Create error result
                error_result = BenchmarkResult(
                    query="unknown",
                    response_time_ms=0,
                    status="error",
                    error=str(result)
                )
                self.results.append(error_result)
            else:
                self.results.append(result)
    
    async def _execute_query(self, query: str) -> BenchmarkResult:
        """Execute single query and measure performance"""
        start_time = time.time()
        
        try:
            # Execute query
            response = await optimized_rag_handler.ask_question(query)
            
            response_time = (time.time() - start_time) * 1000
            
            # Extract timing information
            vector_search_time = response.get('metadata', {}).get('vector_search_time_ms')
            llm_time = response.get('metadata', {}).get('llm_time_ms')
            cache_hit = response.get('cached', False)
            
            return BenchmarkResult(
                query=query,
                response_time_ms=response_time,
                status=response.get('status', 'unknown'),
                cache_hit=cache_hit,
                vector_search_time_ms=vector_search_time,
                llm_time_ms=llm_time
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return BenchmarkResult(
                query=query,
                response_time_ms=response_time,
                status="error",
                error=str(e)
            )
    
    def _start_system_monitoring(self):
        """Start system resource monitoring"""
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(target=self._monitor_system_resources)
        self._monitoring_thread.daemon = True
        self._monitoring_thread.start()
    
    def _stop_system_monitoring(self):
        """Stop system resource monitoring"""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
    
    def _monitor_system_resources(self):
        """Monitor system resources during benchmark"""
        while self._monitoring_active:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Collect network I/O
                net_io = psutil.net_io_counters()
                
                metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_percent': disk.percent,
                    'network_bytes_sent': net_io.bytes_sent,
                    'network_bytes_recv': net_io.bytes_recv
                }
                
                self.system_metrics.append(metrics)
                
                # Keep only last 1000 metrics
                if len(self.system_metrics) > 1000:
                    self.system_metrics.pop(0)
                
                time.sleep(1)  # Collect metrics every second
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                break
    
    def _generate_summary(self, total_duration: float) -> BenchmarkSummary:
        """Generate benchmark summary"""
        if not self.results:
            raise ValueError("No results to summarize")
        
        # Filter successful results
        successful_results = [r for r in self.results if r.status == 'success']
        failed_results = [r for r in self.results if r.status == 'error']
        
        # Calculate response time statistics
        response_times = [r.response_time_ms for r in successful_results]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p50_response_time = np.percentile(response_times, 50)
            p95_response_time = np.percentile(response_times, 95)
            p99_response_time = np.percentile(response_times, 99)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = p50_response_time = p95_response_time = p99_response_time = 0
            min_response_time = max_response_time = 0
        
        # Calculate other metrics
        total_queries = len(self.results)
        successful_queries = len(successful_results)
        failed_queries = len(failed_results)
        throughput = total_queries / total_duration if total_duration > 0 else 0
        error_rate = failed_queries / total_queries if total_queries > 0 else 0
        cache_hit_rate = sum(1 for r in successful_results if r.cache_hit) / len(successful_results) if successful_results else 0
        
        # Check targets
        targets_met = {
            'response_time': avg_response_time <= self.config.target_response_time_ms,
            'throughput': throughput >= self.config.target_throughput_qps,
            'error_rate': error_rate <= self.config.target_error_rate,
            'cache_hit_rate': cache_hit_rate >= self.config.target_cache_hit_rate
        }
        
        return BenchmarkSummary(
            total_queries=total_queries,
            successful_queries=successful_queries,
            failed_queries=failed_queries,
            avg_response_time_ms=avg_response_time,
            p50_response_time_ms=p50_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            min_response_time_ms=min_response_time,
            max_response_time_ms=max_response_time,
            throughput_qps=throughput,
            error_rate=error_rate,
            cache_hit_rate=cache_hit_rate,
            total_duration_seconds=total_duration,
            targets_met=targets_met
        )
    
    async def _save_results(self, summary: BenchmarkSummary):
        """Save benchmark results to file"""
        try:
            results_data = {
                'config': asdict(self.config),
                'summary': asdict(summary),
                'detailed_results': [asdict(r) for r in self.results],
                'system_metrics': self.system_metrics,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.config.results_file, 'w') as f:
                json.dump(results_data, f, indent=2, default=str)
            
            logger.info(f"Benchmark results saved to {self.config.results_file}")
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

class PerformanceMonitor:
    """Real-time performance monitoring"""
    
    def __init__(self):
        self.metrics_history: List[Dict[str, Any]] = []
        self.alerts: List[Dict[str, Any]] = []
        self._monitoring_active = False
        self._monitoring_task = None
        
        # Performance thresholds
        self.thresholds = {
            'response_time_ms': 1000.0,
            'error_rate': 0.05,
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'cache_hit_rate': 0.5
        }
    
    async def start_monitoring(self, interval_seconds: int = 30):
        """Start real-time monitoring"""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop(interval_seconds))
        logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop real-time monitoring"""
        self._monitoring_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self, interval_seconds: int):
        """Main monitoring loop"""
        while self._monitoring_active:
            try:
                # Collect metrics
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last 1000 entries
                if len(self.metrics_history) > 1000:
                    self.metrics_history.pop(0)
                
                # Check for alerts
                await self._check_alerts(metrics)
                
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(interval_seconds)
    
    async def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current performance metrics"""
        try:
            # Get RAG handler stats
            rag_stats = optimized_rag_handler.get_stats()
            
            # Get cache stats
            cache_stats = cache_manager.get_stats()
            
            # Get vector store stats
            vector_stats = vector_store_manager.get_all_stats()
            
            # Get connection pool stats
            pool_stats = connection_manager.get_all_stats()
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'rag_handler': rag_stats,
                'cache': cache_stats,
                'vector_stores': vector_stats,
                'connection_pools': pool_stats,
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def _check_alerts(self, metrics: Dict[str, Any]):
        """Check for performance alerts"""
        try:
            alerts = []
            
            # Check response time
            rag_stats = metrics.get('rag_handler', {})
            avg_response_time = rag_stats.get('avg_response_time_ms', 0)
            if avg_response_time > self.thresholds['response_time_ms']:
                alerts.append({
                    'type': 'high_response_time',
                    'severity': 'warning',
                    'message': f"Average response time {avg_response_time:.2f}ms exceeds threshold {self.thresholds['response_time_ms']}ms",
                    'timestamp': datetime.now().isoformat()
                })
            
            # Check cache hit rate
            cache_stats = metrics.get('cache', {})
            hit_rate = cache_stats.get('hit_rate', 0)
            if hit_rate < self.thresholds['cache_hit_rate']:
                alerts.append({
                    'type': 'low_cache_hit_rate',
                    'severity': 'warning',
                    'message': f"Cache hit rate {hit_rate:.2%} below threshold {self.thresholds['cache_hit_rate']:.0%}",
                    'timestamp': datetime.now().isoformat()
                })
            
            # Check system resources
            system_stats = metrics.get('system', {})
            cpu_percent = system_stats.get('cpu_percent', 0)
            memory_percent = system_stats.get('memory_percent', 0)
            
            if cpu_percent > self.thresholds['cpu_percent']:
                alerts.append({
                    'type': 'high_cpu',
                    'severity': 'critical',
                    'message': f"CPU usage {cpu_percent:.1f}% exceeds threshold {self.thresholds['cpu_percent']}%",
                    'timestamp': datetime.now().isoformat()
                })
            
            if memory_percent > self.thresholds['memory_percent']:
                alerts.append({
                    'type': 'high_memory',
                    'severity': 'critical',
                    'message': f"Memory usage {memory_percent:.1f}% exceeds threshold {self.thresholds['memory_percent']}%",
                    'timestamp': datetime.now().isoformat()
                })
            
            # Add alerts to history
            for alert in alerts:
                self.alerts.append(alert)
                logger.warning(f"Performance alert: {alert['message']}")
            
            # Keep only last 100 alerts
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
                
        except Exception as e:
            logger.error(f"Alert checking failed: {e}")
    
    def get_current_metrics(self) -> Optional[Dict[str, Any]]:
        """Get most recent metrics"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_history(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get metrics history for specified time period"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [
            m for m in self.metrics_history
            if datetime.fromisoformat(m['timestamp']) >= cutoff_time
        ]
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            a for a in self.alerts
            if datetime.fromisoformat(a['timestamp']) >= cutoff_time
        ]

# Global instances
performance_benchmark = PerformanceBenchmark()
performance_monitor = PerformanceMonitor()

# Convenience functions
async def run_performance_benchmark(config: Optional[BenchmarkConfig] = None) -> BenchmarkSummary:
    """Run performance benchmark with optional custom config"""
    if config:
        benchmark = PerformanceBenchmark(config)
    else:
        benchmark = performance_benchmark
    
    return await benchmark.run_benchmark()

async def start_performance_monitoring(interval_seconds: int = 30):
    """Start real-time performance monitoring"""
    await performance_monitor.start_monitoring(interval_seconds)

async def stop_performance_monitoring():
    """Stop performance monitoring"""
    await performance_monitor.stop_monitoring()

def get_performance_dashboard() -> Dict[str, Any]:
    """Get comprehensive performance dashboard data"""
    current_metrics = performance_monitor.get_current_metrics()
    recent_alerts = performance_monitor.get_recent_alerts()
    metrics_history = performance_monitor.get_metrics_history(60)  # Last hour
    
    return {
        'current_metrics': current_metrics,
        'recent_alerts': recent_alerts,
        'metrics_history': metrics_history,
        'alert_count': len(recent_alerts),
        'monitoring_active': performance_monitor._monitoring_active
    }