"""
Enhanced Performance Configuration
Provides comprehensive performance tuning options and presets
"""

import os
from typing import Dict, Any, Optional, List
from pydantic import BaseSettings, Field
from loguru import logger

class EnhancedPerformanceSettings(BaseSettings):
    """Enhanced performance configuration with comprehensive tuning options"""

    # ===== Cache Configuration =====
    CACHE_ENABLED: bool = Field(True, description="Enable intelligent caching")
    CACHE_MAX_SIZE: int = Field(2000, description="Maximum cache items in memory")
    CACHE_DEFAULT_TTL: int = Field(1800, description="Default cache TTL in seconds")
    CACHE_REDIS_ENABLED: bool = Field(False, description="Enable Redis for distributed caching")
    CACHE_REDIS_URL: Optional[str] = Field(None, description="Redis connection URL")
    CACHE_LOCAL_MAX_SIZE: int = Field(1000, description="Local cache max size")
    CACHE_LOCAL_TTL: int = Field(600, description="Local cache TTL in seconds")
    CACHE_QUERY_TTL: int = Field(600, description="Query cache TTL in seconds")
    CACHE_VECTOR_TTL: int = Field(3600, description="Vector cache TTL in seconds")
    CACHE_TTS_TTL: int = Field(86400, description="TTS cache TTL in seconds")
    CACHE_STT_TTL: int = Field(3600, description="STT cache TTL in seconds")
    CACHE_CLEANUP_INTERVAL: int = Field(300, description="Cache cleanup interval in seconds")
    CACHE_COMPRESSION_THRESHOLD: int = Field(1024, description="Cache compression threshold in bytes")
    CACHE_ENABLE_COMPRESSION: bool = Field(True, description="Enable cache compression")

    # ===== Vector Store Configuration =====
    VECTOR_INDEX_TYPE: str = Field("IVF", description="FAISS index type (FLAT, IVF, HNSW)")
    VECTOR_NLIST: int = Field(100, description="Number of clusters for IVF index")
    VECTOR_NPROBE: int = Field(10, description="Number of clusters to search")
    VECTOR_EF_SEARCH: int = Field(50, description="Search parameter for HNSW")
    VECTOR_EF_CONSTRUCTION: int = Field(200, description="Construction parameter for HNSW")
    VECTOR_M: int = Field(16, description="M parameter for HNSW")
    VECTOR_USE_GPU: bool = Field(False, description="Enable GPU acceleration")
    VECTOR_BATCH_SIZE: int = Field(32, description="Vector batch processing size")
    VECTOR_MAX_CACHE_SIZE: int = Field(10000, description="Vector cache max size")
    VECTOR_PARALLEL_SEARCH: bool = Field(True, description="Enable parallel vector search")
    VECTOR_MAX_CONCURRENT_SEARCHES: int = Field(3, description="Max concurrent vector searches")

    # ===== Database Connection Pool Configuration =====
    DB_POOL_SIZE: int = Field(10, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(20, description="Database connection pool max overflow")
    DB_POOL_TIMEOUT: int = Field(30, description="Database connection timeout in seconds")
    DB_POOL_RECYCLE: int = Field(3600, description="Database connection recycle time in seconds")
    DB_POOL_PRE_PING: bool = Field(True, description="Enable connection pre-ping")

    # ===== HTTP Connection Pool Configuration =====
    HTTP_POOL_SIZE: int = Field(100, description="HTTP connection pool size")
    HTTP_MAX_CONNECTIONS: int = Field(200, description="HTTP max connections")
    HTTP_CONNECT_TIMEOUT: int = Field(10, description="HTTP connect timeout in seconds")
    HTTP_READ_TIMEOUT: int = Field(30, description="HTTP read timeout in seconds")
    HTTP_MAX_KEEPALIVE_CONNECTIONS: int = Field(20, description="HTTP keepalive connections")
    HTTP_KEEPALIVE_TIMEOUT: int = Field(30, description="HTTP keepalive timeout in seconds")

    # ===== Redis Connection Pool Configuration =====
    REDIS_POOL_SIZE: int = Field(10, description="Redis connection pool size")
    REDIS_MAX_CONNECTIONS: int = Field(20, description="Redis max connections")
    REDIS_SOCKET_TIMEOUT: int = Field(5, description="Redis socket timeout in seconds")
    REDIS_SOCKET_CONNECT_TIMEOUT: int = Field(5, description="Redis connect timeout in seconds")

    # ===== Voice Processing Configuration =====
    VOICE_MAX_CONCURRENT_TTS: int = Field(5, description="Max concurrent TTS requests")
    VOICE_MAX_CONCURRENT_STT: int = Field(3, description="Max concurrent STT requests")
    VOICE_TTS_BATCH_SIZE: int = Field(10, description="TTS batch processing size")
    VOICE_STT_BATCH_SIZE: int = Field(5, description="STT batch processing size")
    VOICE_ENABLE_AUDIO_OPTIMIZATION: bool = Field(True, description="Enable audio optimization")
    VOICE_AUDIO_QUALITY_THRESHOLD: float = Field(0.3, description="Audio quality threshold")
    VOICE_MAX_AUDIO_LENGTH: int = Field(600, description="Max audio length in seconds")
    VOICE_OPENAI_TIMEOUT: int = Field(30, description="OpenAI API timeout in seconds")
    VOICE_OPENAI_MAX_RETRIES: int = Field(3, description="OpenAI API max retries")
    VOICE_OPENAI_RETRY_DELAY: float = Field(1.0, description="OpenAI API retry delay")

    # ===== Query Optimization Configuration =====
    QUERY_CACHE_ENABLED: bool = Field(True, description="Enable query result caching")
    QUERY_CACHE_TTL: int = Field(600, description="Query cache TTL in seconds")
    QUERY_SIMILARITY_THRESHOLD: float = Field(0.7, description="Query similarity threshold")
    QUERY_DEFAULT_K: int = Field(6, description="Default number of search results")
    QUERY_MAX_K: int = Field(20, description="Maximum number of search results")
    QUERY_ENABLE_RESULT_RANKING: bool = Field(True, description="Enable advanced result ranking")

    # ===== Resource Monitoring Configuration =====
    RESOURCE_MONITORING_ENABLED: bool = Field(True, description="Enable system resource monitoring")
    RESOURCE_COLLECTION_INTERVAL: int = Field(30, description="Resource collection interval in seconds")
    CPU_THRESHOLD_WARNING: float = Field(80.0, description="CPU usage warning threshold (%)")
    CPU_THRESHOLD_CRITICAL: float = Field(90.0, description="CPU usage critical threshold (%)")
    MEMORY_THRESHOLD_WARNING: float = Field(85.0, description="Memory usage warning threshold (%)")
    MEMORY_THRESHOLD_CRITICAL: float = Field(95.0, description="Memory usage critical threshold (%)")
    HEALTH_CHECK_INTERVAL: int = Field(60, description="Health check interval in seconds")

    # ===== Performance Targets Configuration =====
    TARGET_RESPONSE_TIME_MS: float = Field(500.0, description="Target response time in milliseconds")
    TARGET_THROUGHPUT_QPS: float = Field(20.0, description="Target throughput in queries per second")
    TARGET_ERROR_RATE: float = Field(0.01, description="Target error rate (1% = 0.01)")
    TARGET_CACHE_HIT_RATE: float = Field(0.8, description="Target cache hit rate (80% = 0.8)")

    # ===== Benchmark Configuration =====
    BENCHMARK_NUM_QUERIES: int = Field(100, description="Number of benchmark queries")
    BENCHMARK_CONCURRENT_USERS: int = Field(10, description="Number of concurrent users for benchmark")
    BENCHMARK_TEST_DURATION: int = Field(60, description="Benchmark test duration in seconds")
    BENCHMARK_WARMUP_QUERIES: int = Field(10, description="Number of warmup queries")
    BENCHMARK_ENABLE_DETAILED_LOGGING: bool = Field(False, description="Enable detailed benchmark logging")
    BENCHMARK_SAVE_RESULTS: bool = Field(True, description="Save benchmark results")

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
            "vector_parallel_search": self.VECTOR_PARALLEL_SEARCH
        }

        if self.ENV == "production":
            return {
                **base_config,
                "cache_max_size": max(5000, self.CACHE_MAX_SIZE),
                "cache_ttl": max(3600, self.CACHE_DEFAULT_TTL),
                "db_pool_size": max(20, self.DB_POOL_SIZE),
                "http_pool_size": max(200, self.HTTP_POOL_SIZE),
                "vector_max_concurrent_searches": max(5, self.VECTOR_MAX_CONCURRENT_SEARCHES),
                "voice_max_concurrent_tts": max(10, self.VOICE_MAX_CONCURRENT_TTS),
                "voice_max_concurrent_stt": max(5, self.VOICE_MAX_CONCURRENT_STT),
                "resource_collection_interval": min(15, self.RESOURCE_COLLECTION_INTERVAL),
                "cpu_threshold_warning": min(70.0, self.CPU_THRESHOLD_WARNING),
                "memory_threshold_warning": min(80.0, self.MEMORY_THRESHOLD_WARNING),
                "target_response_time_ms": min(300.0, self.TARGET_RESPONSE_TIME_MS),
                "target_throughput_qps": max(50.0, self.TARGET_THROUGHPUT_QPS)
            }

        elif self.ENV == "staging":
            return {
                **base_config,
                "cache_max_size": max(3000, self.CACHE_MAX_SIZE),
                "cache_ttl": max(1800, self.CACHE_DEFAULT_TTL),
                "db_pool_size": max(15, self.DB_POOL_SIZE),
                "http_pool_size": max(150, self.HTTP_POOL_SIZE),
                "vector_max_concurrent_searches": max(4, self.VECTOR_MAX_CONCURRENT_SEARCHES),
                "voice_max_concurrent_tts": max(7, self.VOICE_MAX_CONCURRENT_TTS),
                "voice_max_concurrent_stt": max(4, self.VOICE_MAX_CONCURRENT_STT),
                "resource_collection_interval": min(30, self.RESOURCE_COLLECTION_INTERVAL)
            }

        else:  # development
            return {
                **base_config,
                "cache_max_size": min(1000, self.CACHE_MAX_SIZE),
                "cache_ttl": min(300, self.CACHE_DEFAULT_TTL),
                "db_pool_size": min(5, self.DB_POOL_SIZE),
                "http_pool_size": min(50, self.HTTP_POOL_SIZE),
                "vector_max_concurrent_searches": min(2, self.VECTOR_MAX_CONCURRENT_SEARCHES),
                "voice_max_concurrent_tts": min(3, self.VOICE_MAX_CONCURRENT_TTS),
                "voice_max_concurrent_stt": min(2, self.VOICE_MAX_CONCURRENT_STT),
                "resource_collection_interval": max(60, self.RESOURCE_COLLECTION_INTERVAL)
            }

    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache-specific configuration."""
        return {
            "enabled": self.CACHE_ENABLED,
            "max_size": self.CACHE_MAX_SIZE,
            "default_ttl": self.CACHE_DEFAULT_TTL,
            "redis_enabled": self.CACHE_REDIS_ENABLED,
            "redis_url": self.CACHE_REDIS_URL,
            "local_max_size": self.CACHE_LOCAL_MAX_SIZE,
            "local_ttl": self.CACHE_LOCAL_TTL,
            "query_ttl": self.CACHE_QUERY_TTL,
            "vector_ttl": self.CACHE_VECTOR_TTL,
            "tts_ttl": self.CACHE_TTS_TTL,
            "stt_ttl": self.CACHE_STT_TTL,
            "cleanup_interval": self.CACHE_CLEANUP_INTERVAL,
            "compression_threshold": self.CACHE_COMPRESSION_THRESHOLD,
            "enable_compression": self.CACHE_ENABLE_COMPRESSION
        }

    def get_vector_config(self) -> Dict[str, Any]:
        """Get vector store configuration."""
        return {
            "index_type": self.VECTOR_INDEX_TYPE,
            "nlist": self.VECTOR_NLIST,
            "nprobe": self.VECTOR_NPROBE,
            "ef_search": self.VECTOR_EF_SEARCH,
            "ef_construction": self.VECTOR_EF_CONSTRUCTION,
            "m": self.VECTOR_M,
            "use_gpu": self.VECTOR_USE_GPU,
            "batch_size": self.VECTOR_BATCH_SIZE,
            "max_cache_size": self.VECTOR_MAX_CACHE_SIZE,
            "parallel_search": self.VECTOR_PARALLEL_SEARCH,
            "max_concurrent_searches": self.VECTOR_MAX_CONCURRENT_SEARCHES
        }

    def get_database_config(self) -> Dict[str, Any]:
        """Get database optimization configuration."""
        return {
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "pool_timeout": self.DB_POOL_TIMEOUT,
            "pool_recycle": self.DB_POOL_RECYCLE,
            "pool_pre_ping": self.DB_POOL_PRE_PING
        }

    def get_http_config(self) -> Dict[str, Any]:
        """Get HTTP connection pool configuration."""
        return {
            "pool_size": self.HTTP_POOL_SIZE,
            "max_connections": self.HTTP_MAX_CONNECTIONS,
            "connect_timeout": self.HTTP_CONNECT_TIMEOUT,
            "read_timeout": self.HTTP_READ_TIMEOUT,
            "max_keepalive_connections": self.HTTP_MAX_KEEPALIVE_CONNECTIONS,
            "keepalive_timeout": self.HTTP_KEEPALIVE_TIMEOUT
        }

    def get_voice_config(self) -> Dict[str, Any]:
        """Get voice processing configuration."""
        return {
            "max_concurrent_tts": self.VOICE_MAX_CONCURRENT_TTS,
            "max_concurrent_stt": self.VOICE_MAX_CONCURRENT_STT,
            "tts_batch_size": self.VOICE_TTS_BATCH_SIZE,
            "stt_batch_size": self.VOICE_STT_BATCH_SIZE,
            "enable_audio_optimization": self.VOICE_ENABLE_AUDIO_OPTIMIZATION,
            "audio_quality_threshold": self.VOICE_AUDIO_QUALITY_THRESHOLD,
            "max_audio_length": self.VOICE_MAX_AUDIO_LENGTH,
            "openai_timeout": self.VOICE_OPENAI_TIMEOUT,
            "openai_max_retries": self.VOICE_OPENAI_MAX_RETRIES,
            "openai_retry_delay": self.VOICE_OPENAI_RETRY_DELAY
        }

    def get_query_config(self) -> Dict[str, Any]:
        """Get query optimization configuration."""
        return {
            "cache_enabled": self.QUERY_CACHE_ENABLED,
            "cache_ttl": self.QUERY_CACHE_TTL,
            "similarity_threshold": self.QUERY_SIMILARITY_THRESHOLD,
            "default_k": self.QUERY_DEFAULT_K,
            "max_k": self.QUERY_MAX_K,
            "enable_result_ranking": self.QUERY_ENABLE_RESULT_RANKING
        }

    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        return {
            "enabled": self.RESOURCE_MONITORING_ENABLED,
            "collection_interval": self.RESOURCE_COLLECTION_INTERVAL,
            "health_check_interval": self.HEALTH_CHECK_INTERVAL,
            "thresholds": {
                "cpu_warning": self.CPU_THRESHOLD_WARNING,
                "cpu_critical": self.CPU_THRESHOLD_CRITICAL,
                "memory_warning": self.MEMORY_THRESHOLD_WARNING,
                "memory_critical": self.MEMORY_THRESHOLD_CRITICAL
            }
        }

    def get_performance_targets(self) -> Dict[str, Any]:
        """Get performance targets."""
        return {
            "response_time_ms": self.TARGET_RESPONSE_TIME_MS,
            "throughput_qps": self.TARGET_THROUGHPUT_QPS,
            "error_rate": self.TARGET_ERROR_RATE,
            "cache_hit_rate": self.TARGET_CACHE_HIT_RATE
        }

    def get_benchmark_config(self) -> Dict[str, Any]:
        """Get benchmark configuration."""
        return {
            "num_queries": self.BENCHMARK_NUM_QUERIES,
            "concurrent_users": self.BENCHMARK_CONCURRENT_USERS,
            "test_duration": self.BENCHMARK_TEST_DURATION,
            "warmup_queries": self.BENCHMARK_WARMUP_QUERIES,
            "enable_detailed_logging": self.BENCHMARK_ENABLE_DETAILED_LOGGING,
            "save_results": self.BENCHMARK_SAVE_RESULTS,
            "targets": self.get_performance_targets()
        }

# Performance optimization presets
PERFORMANCE_PRESETS = {
    "development": {
        "description": "Optimized for development with minimal resource usage",
        "cache_max_size": 500,
        "cache_ttl": 300,
        "db_pool_size": 3,
        "http_pool_size": 20,
        "vector_max_concurrent_searches": 2,
        "voice_max_concurrent_tts": 2,
        "voice_max_concurrent_stt": 1,
        "resource_collection_interval": 120,
        "target_response_time_ms": 1000.0,
        "target_throughput_qps": 5.0
    },

    "testing": {
        "description": "Optimized for testing with balanced performance",
        "cache_max_size": 1000,
        "cache_ttl": 600,
        "db_pool_size": 5,
        "http_pool_size": 50,
        "vector_max_concurrent_searches": 3,
        "voice_max_concurrent_tts": 3,
        "voice_max_concurrent_stt": 2,
        "resource_collection_interval": 60,
        "target_response_time_ms": 750.0,
        "target_throughput_qps": 10.0
    },

    "staging": {
        "description": "Optimized for staging with production-like settings",
        "cache_max_size": 3000,
        "cache_ttl": 1800,
        "db_pool_size": 15,
        "http_pool_size": 150,
        "vector_max_concurrent_searches": 4,
        "voice_max_concurrent_tts": 7,
        "voice_max_concurrent_stt": 4,
        "resource_collection_interval": 30,
        "target_response_time_ms": 600.0,
        "target_throughput_qps": 25.0
    },

    "production": {
        "description": "Optimized for production with maximum performance",
        "cache_max_size": 5000,
        "cache_ttl": 3600,
        "db_pool_size": 20,
        "http_pool_size": 200,
        "vector_max_concurrent_searches": 5,
        "voice_max_concurrent_tts": 10,
        "voice_max_concurrent_stt": 5,
        "resource_collection_interval": 15,
        "target_response_time_ms": 500.0,
        "target_throughput_qps": 50.0
    },

    "high_performance": {
        "description": "Maximum performance configuration for high-load scenarios",
        "cache_max_size": 10000,
        "cache_ttl": 7200,
        "db_pool_size": 50,
        "http_pool_size": 500,
        "vector_max_concurrent_searches": 10,
        "voice_max_concurrent_tts": 20,
        "voice_max_concurrent_stt": 10,
        "resource_collection_interval": 10,
        "target_response_time_ms": 300.0,
        "target_throughput_qps": 100.0
    },

    "memory_optimized": {
        "description": "Optimized for low memory usage",
        "cache_max_size": 200,
        "cache_ttl": 180,
        "db_pool_size": 2,
        "http_pool_size": 10,
        "vector_max_concurrent_searches": 1,
        "voice_max_concurrent_tts": 1,
        "voice_max_concurrent_stt": 1,
        "resource_collection_interval": 300,
        "target_response_time_ms": 1500.0,
        "target_throughput_qps": 2.0
    }
}

def apply_performance_preset(preset_name: str, settings_instance: EnhancedPerformanceSettings) -> Dict[str, Any]:
    """Apply a performance optimization preset."""
    if preset_name not in PERFORMANCE_PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(PERFORMANCE_PRESETS.keys())}")

    preset = PERFORMANCE_PRESETS[preset_name]
    
    # Apply preset values to settings
    for key, value in preset.items():
        if key == "description":
            continue
        if hasattr(settings_instance, key.upper()):
            setattr(settings_instance, key.upper(), value)

    return {
        "preset": preset_name,
        "description": preset["description"],
        "applied_settings": {k: v for k, v in preset.items() if k != "description"}
    }

def get_performance_recommendations(current_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Generate performance recommendations based on current metrics."""
    recommendations = []

    # Analyze response time
    avg_response_time = current_metrics.get("avg_response_time_ms", 0)
    if avg_response_time > 1000:
        recommendations.append({
            "type": "response_time_optimization",
            "priority": "high",
            "current_value": avg_response_time,
            "suggestion": "Consider enabling aggressive caching and increasing connection pool sizes",
            "recommended_preset": "high_performance"
        })
    elif avg_response_time > 500:
        recommendations.append({
            "type": "response_time_optimization",
            "priority": "medium",
            "current_value": avg_response_time,
            "suggestion": "Consider optimizing vector search and enabling result caching",
            "recommended_preset": "production"
        })

    # Analyze throughput
    throughput = current_metrics.get("throughput_qps", 0)
    if throughput < 10:
        recommendations.append({
            "type": "throughput_optimization",
            "priority": "medium",
            "current_value": throughput,
            "suggestion": "Consider increasing concurrent processing limits and connection pools",
            "recommended_preset": "staging"
        })

    # Analyze cache hit rate
    cache_hit_rate = current_metrics.get("cache_hit_rate", 0)
    if cache_hit_rate < 0.5:
        recommendations.append({
            "type": "cache_optimization",
            "priority": "high",
            "current_value": cache_hit_rate,
            "suggestion": "Increase cache TTL and size to improve hit rate",
            "recommended_preset": "production"
        })

    # Analyze resource usage
    cpu_usage = current_metrics.get("cpu_percent", 0)
    memory_usage = current_metrics.get("memory_percent", 0)
    
    if cpu_usage > 80 or memory_usage > 85:
        recommendations.append({
            "type": "resource_optimization",
            "priority": "high",
            "current_values": {"cpu": cpu_usage, "memory": memory_usage},
            "suggestion": "Consider memory-optimized preset or scale resources",
            "recommended_preset": "memory_optimized"
        })

    return {
        "current_metrics": current_metrics,
        "recommendations": recommendations,
        "suggested_preset": _suggest_optimal_preset(current_metrics)
    }

def _suggest_optimal_preset(metrics: Dict[str, Any]) -> str:
    """Suggest optimal preset based on current metrics."""
    avg_response_time = metrics.get("avg_response_time_ms", 0)
    throughput = metrics.get("throughput_qps", 0)
    cache_hit_rate = metrics.get("cache_hit_rate", 0)
    cpu_usage = metrics.get("cpu_percent", 0)
    memory_usage = metrics.get("memory_percent", 0)

    if cpu_usage > 80 or memory_usage > 85:
        return "memory_optimized"
    elif avg_response_time > 1000 or throughput < 5:
        return "high_performance"
    elif avg_response_time > 500 or cache_hit_rate < 0.5:
        return "production"
    elif throughput > 30:
        return "high_performance"
    else:
        return "staging"

# Global enhanced performance settings instance
enhanced_performance_settings = EnhancedPerformanceSettings()

def validate_performance_config() -> Dict[str, Any]:
    """Validate current performance configuration."""
    config = enhanced_performance_settings.get_environment_config()
    issues = []

    # Check for potential issues
    if config["cache_max_size"] > 10000:
        issues.append("Cache size may be too large for available memory")

    if config.get("db_pool_size", 0) > 100:
        issues.append("Database pool size may be excessive")

    if config.get("vector_max_concurrent_searches", 0) > 20:
        issues.append("Too many concurrent vector searches may overwhelm the system")

    return {
        "config": config,
        "issues": issues,
        "status": "valid" if not issues else "warnings"
    }