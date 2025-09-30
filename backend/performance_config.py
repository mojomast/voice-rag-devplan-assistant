# ===== Performance Configuration =====
# Environment-specific performance optimization settings
# Voice RAG System Performance Tuning Parameters

import os
from typing import Dict, Any, Optional
from pydantic import BaseSettings, Field

class PerformanceSettings(BaseSettings):
    """Performance optimization configuration."""

    # ===== Cache Configuration =====
    CACHE_ENABLED: bool = Field(True, description="Enable intelligent caching")
    CACHE_MAX_SIZE: int = Field(1000, description="Maximum cache items in memory")
    CACHE_DEFAULT_TTL: int = Field(3600, description="Default cache TTL in seconds")
    CACHE_REDIS_ENABLED: bool = Field(False, description="Enable Redis for distributed caching")
    CACHE_REDIS_URL: Optional[str] = Field(None, description="Redis connection URL")

    # ===== Query Optimization =====
    QUERY_CACHE_ENABLED: bool = Field(True, description="Enable query result caching")
    QUERY_CACHE_TTL: int = Field(600, description="Query cache TTL in seconds")
    SLOW_QUERY_THRESHOLD: float = Field(1.0, description="Log queries slower than this (seconds)")
    MAX_QUERY_RESULTS: int = Field(1000, description="Maximum query results to cache")

    # ===== Resource Monitoring =====
    RESOURCE_MONITORING_ENABLED: bool = Field(True, description="Enable system resource monitoring")
    RESOURCE_COLLECTION_INTERVAL: int = Field(60, description="Resource collection interval in seconds")
    CPU_THRESHOLD_WARNING: float = Field(80.0, description="CPU usage warning threshold (%)")
    CPU_THRESHOLD_CRITICAL: float = Field(90.0, description="CPU usage critical threshold (%)")
    MEMORY_THRESHOLD_WARNING: float = Field(85.0, description="Memory usage warning threshold (%)")
    MEMORY_THRESHOLD_CRITICAL: float = Field(95.0, description="Memory usage critical threshold (%)")

    # ===== Connection Pool Optimization =====
    DB_POOL_SIZE: int = Field(5, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(10, description="Database connection pool max overflow")
    DB_POOL_TIMEOUT: int = Field(30, description="Database connection timeout in seconds")
    DB_POOL_RECYCLE: int = Field(3600, description="Database connection recycle time in seconds")

    # ===== Async Task Optimization =====
    MAX_CONCURRENT_TASKS: int = Field(10, description="Maximum concurrent async tasks")
    TASK_BATCH_SIZE: int = Field(5, description="Default batch size for task execution")
    TASK_TIMEOUT: int = Field(300, description="Task timeout in seconds")

    # ===== Performance Tracking =====
    PERFORMANCE_TRACKING_ENABLED: bool = Field(True, description="Enable performance tracking")
    METRICS_RETENTION_DAYS: int = Field(7, description="Metrics retention period in days")
    METRICS_COLLECTION_INTERVAL: int = Field(30, description="Metrics collection interval in seconds")

    # ===== Environment-specific Overrides =====
    ENV: str = Field("development", description="Environment (development, staging, production)")

    class Config:
        env_file = ".env"
        env_prefix = "PERF_"

    def get_environment_config(self) -> Dict[str, Any]:
        """Get environment-specific performance configuration."""
        base_config = {
            "cache_enabled": self.CACHE_ENABLED,
            "cache_max_size": self.CACHE_MAX_SIZE,
            "cache_ttl": self.CACHE_DEFAULT_TTL,
            "resource_monitoring": self.RESOURCE_MONITORING_ENABLED,
            "performance_tracking": self.PERFORMANCE_TRACKING_ENABLED
        }

        if self.ENV == "production":
            return {
                **base_config,
                "cache_max_size": max(2000, self.CACHE_MAX_SIZE),
                "cache_ttl": max(1800, self.CACHE_DEFAULT_TTL),
                "db_pool_size": max(10, self.DB_POOL_SIZE),
                "max_concurrent_tasks": max(20, self.MAX_CONCURRENT_TASKS),
                "resource_collection_interval": min(30, self.RESOURCE_COLLECTION_INTERVAL),
                "cpu_threshold_warning": min(70.0, self.CPU_THRESHOLD_WARNING),
                "memory_threshold_warning": min(80.0, self.MEMORY_THRESHOLD_WARNING)
            }

        elif self.ENV == "staging":
            return {
                **base_config,
                "cache_max_size": max(1500, self.CACHE_MAX_SIZE),
                "db_pool_size": max(8, self.DB_POOL_SIZE),
                "max_concurrent_tasks": max(15, self.MAX_CONCURRENT_TASKS)
            }

        else:  # development
            return {
                **base_config,
                "cache_max_size": min(500, self.CACHE_MAX_SIZE),
                "cache_ttl": min(300, self.CACHE_DEFAULT_TTL),
                "db_pool_size": min(3, self.DB_POOL_SIZE),
                "max_concurrent_tasks": min(5, self.MAX_CONCURRENT_TASKS),
                "resource_collection_interval": max(120, self.RESOURCE_COLLECTION_INTERVAL)
            }

    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache-specific configuration."""
        return {
            "enabled": self.CACHE_ENABLED,
            "max_size": self.CACHE_MAX_SIZE,
            "default_ttl": self.CACHE_DEFAULT_TTL,
            "redis_enabled": self.CACHE_REDIS_ENABLED,
            "redis_url": self.CACHE_REDIS_URL
        }

    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring-specific configuration."""
        return {
            "enabled": self.RESOURCE_MONITORING_ENABLED,
            "collection_interval": self.RESOURCE_COLLECTION_INTERVAL,
            "thresholds": {
                "cpu_warning": self.CPU_THRESHOLD_WARNING,
                "cpu_critical": self.CPU_THRESHOLD_CRITICAL,
                "memory_warning": self.MEMORY_THRESHOLD_WARNING,
                "memory_critical": self.MEMORY_THRESHOLD_CRITICAL
            },
            "metrics_retention_days": self.METRICS_RETENTION_DAYS
        }

    def get_database_config(self) -> Dict[str, Any]:
        """Get database optimization configuration."""
        return {
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "pool_timeout": self.DB_POOL_TIMEOUT,
            "pool_recycle": self.DB_POOL_RECYCLE,
            "query_cache_enabled": self.QUERY_CACHE_ENABLED,
            "query_cache_ttl": self.QUERY_CACHE_TTL,
            "slow_query_threshold": self.SLOW_QUERY_THRESHOLD
        }

    def get_task_config(self) -> Dict[str, Any]:
        """Get async task optimization configuration."""
        return {
            "max_concurrent_tasks": self.MAX_CONCURRENT_TASKS,
            "batch_size": self.TASK_BATCH_SIZE,
            "timeout": self.TASK_TIMEOUT
        }

# Global performance settings instance
performance_settings = PerformanceSettings()

# Performance optimization presets for different workloads
OPTIMIZATION_PRESETS = {
    "memory_optimized": {
        "description": "Optimized for low memory usage",
        "cache_max_size": 500,
        "cache_ttl": 300,
        "db_pool_size": 3,
        "max_concurrent_tasks": 5,
        "memory_threshold_warning": 70.0
    },

    "cpu_optimized": {
        "description": "Optimized for high CPU efficiency",
        "max_concurrent_tasks": 20,
        "task_batch_size": 10,
        "cache_enabled": True,
        "query_cache_enabled": True,
        "cpu_threshold_warning": 60.0
    },

    "throughput_optimized": {
        "description": "Optimized for maximum throughput",
        "cache_max_size": 5000,
        "cache_ttl": 1800,
        "db_pool_size": 20,
        "max_concurrent_tasks": 50,
        "task_batch_size": 20
    },

    "latency_optimized": {
        "description": "Optimized for lowest latency",
        "cache_enabled": True,
        "cache_max_size": 2000,
        "cache_ttl": 3600,
        "query_cache_ttl": 900,
        "resource_collection_interval": 15,
        "metrics_collection_interval": 10
    },

    "balanced": {
        "description": "Balanced optimization for general use",
        "cache_max_size": 1000,
        "cache_ttl": 600,
        "db_pool_size": 10,
        "max_concurrent_tasks": 15,
        "task_batch_size": 8
    }
}

def apply_optimization_preset(preset_name: str) -> Dict[str, Any]:
    """Apply a performance optimization preset."""
    if preset_name not in OPTIMIZATION_PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(OPTIMIZATION_PRESETS.keys())}")

    preset = OPTIMIZATION_PRESETS[preset_name]

    # Update global settings with preset values
    for key, value in preset.items():
        if key != "description" and hasattr(performance_settings, key.upper()):
            setattr(performance_settings, key.upper(), value)

    return {
        "preset": preset_name,
        "description": preset["description"],
        "applied_settings": {k: v for k, v in preset.items() if k != "description"}
    }

def get_optimization_recommendations(current_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Generate optimization recommendations based on current metrics."""
    recommendations = []

    # Analyze CPU usage
    cpu_usage = current_metrics.get("cpu_percent", 0)
    if cpu_usage > 80:
        recommendations.append({
            "type": "cpu_optimization",
            "priority": "high",
            "suggestion": "Consider applying 'cpu_optimized' preset",
            "actions": ["Increase concurrent tasks", "Enable aggressive caching", "Optimize query patterns"]
        })

    # Analyze memory usage
    memory_usage = current_metrics.get("memory_percent", 0)
    if memory_usage > 85:
        recommendations.append({
            "type": "memory_optimization",
            "priority": "high",
            "suggestion": "Consider applying 'memory_optimized' preset",
            "actions": ["Reduce cache size", "Decrease connection pool", "Implement memory pooling"]
        })

    # Analyze response times
    avg_response_time = current_metrics.get("avg_response_time", 0)
    if avg_response_time > 2.0:
        recommendations.append({
            "type": "latency_optimization",
            "priority": "medium",
            "suggestion": "Consider applying 'latency_optimized' preset",
            "actions": ["Increase cache TTL", "Optimize database queries", "Enable query caching"]
        })

    # Analyze throughput
    requests_per_second = current_metrics.get("requests_per_second", 0)
    if requests_per_second < 10:
        recommendations.append({
            "type": "throughput_optimization",
            "priority": "medium",
            "suggestion": "Consider applying 'throughput_optimized' preset",
            "actions": ["Increase connection pool", "Optimize batch processing", "Scale horizontally"]
        })

    return {
        "current_metrics": current_metrics,
        "recommendations": recommendations,
        "suggested_preset": _suggest_optimal_preset(current_metrics)
    }

def _suggest_optimal_preset(metrics: Dict[str, Any]) -> str:
    """Suggest optimal preset based on current metrics."""
    cpu_usage = metrics.get("cpu_percent", 0)
    memory_usage = metrics.get("memory_percent", 0)
    response_time = metrics.get("avg_response_time", 0)

    if memory_usage > 85:
        return "memory_optimized"
    elif cpu_usage > 80:
        return "cpu_optimized"
    elif response_time > 2.0:
        return "latency_optimized"
    elif metrics.get("requests_per_second", 0) > 50:
        return "throughput_optimized"
    else:
        return "balanced"

# Configuration validation
def validate_performance_config() -> Dict[str, Any]:
    """Validate current performance configuration."""
    config = performance_settings.get_environment_config()
    issues = []

    # Check for potential issues
    if config["cache_max_size"] > 5000:
        issues.append("Cache size may be too large for available memory")

    if config["db_pool_size"] > 50:
        issues.append("Database pool size may be excessive")

    if config["max_concurrent_tasks"] > 100:
        issues.append("Too many concurrent tasks may overwhelm the system")

    return {
        "config": config,
        "issues": issues,
        "status": "valid" if not issues else "warnings"
    }