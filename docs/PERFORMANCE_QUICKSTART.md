# Performance Optimization Quickstart

This guide provides quick setup instructions for enabling performance optimizations in the Voice RAG System.

## Quick Setup

### 1. Enable Performance Optimizations

```python
# In your main application
from backend.enhanced_performance_config import apply_performance_preset, EnhancedPerformanceSettings

# Apply production preset for best performance
settings = EnhancedPerformanceSettings()
result = apply_performance_preset("production", settings)

print(f"Applied preset: {result['preset']}")
print(f"Cache enabled: {settings.CACHE_ENABLED}")
print(f"Vector index: {settings.VECTOR_INDEX_TYPE}")
```

### 2. Initialize Performance Components

```python
# Initialize all performance components
from backend.cache_manager import cache_manager
from backend.vector_store_optimizer import vector_store_manager
from backend.connection_pool import connection_manager
from backend.optimized_rag_handler import optimized_rag_handler
from backend.optimized_voice_service import optimized_voice_service

# Start all services
await cache_manager.start()
await vector_store_manager.initialize()
await connection_manager.initialize()
await optimized_rag_handler.initialize()
await optimized_voice_service.initialize()
```

### 3. Configure Caching

```python
# Basic cache configuration
CACHE_CONFIG = {
    "local_max_size": 2000,
    "local_ttl": 3600,
    "redis_enabled": True,
    "redis_host": "localhost",
    "redis_port": 6379
}

# Apply cache configuration
from backend.cache_manager import CacheConfig, AdvancedCacheManager
config = CacheConfig(**CACHE_CONFIG)
cache_mgr = AdvancedCacheManager(config)
```

### 4. Optimize Vector Search

```python
# Vector store optimization
from backend.vector_store_optimizer import VectorSearchConfig

vector_config = VectorSearchConfig(
    index_type="IVF",           # Best for medium datasets
    nlist=100,                  # Number of clusters
    nprobe=10,                  # Search clusters
    enable_cache=True,          # Enable caching
    batch_size=32               # Batch processing
)
```

### 5. Enable Connection Pooling

```python
# Connection pool configuration
from backend.connection_pool import PoolConfig

pool_config = PoolConfig(
    db_pool_size=10,            # Database connections
    http_pool_size=20,          # HTTP connections
    redis_pool_size=5,          # Redis connections
    connection_timeout=30       # Connection timeout
)
```

## Performance Targets

| Component | Target Latency | Optimization |
|-----------|----------------|--------------|
| Search Query | < 500ms | Vector caching + optimized index |
| TTS Synthesis | < 2s | Audio caching + connection pooling |
| STT Transcription | < 3s | Audio optimization + caching |
| API Response | < 100ms | Response caching + pooling |

## Monitoring Performance

```python
# Monitor performance metrics
from backend.performance_benchmark import performance_benchmark

# Run quick benchmark
summary = await performance_benchmark.run_quick_benchmark()
print(f"Average response time: {summary.avg_response_time_ms}ms")
print(f"Cache hit rate: {summary.cache_hit_rate}%")
print(f"Throughput: {summary.throughput_qps} QPS")
```

## Common Performance Issues

### 1. Slow Search Queries
**Solution**: Enable vector caching and use appropriate index type
```python
# Use IVF index for better performance
vector_config = VectorSearchConfig(index_type="IVF", enable_cache=True)
```

### 2. High Memory Usage
**Solution**: Adjust cache sizes and enable cleanup
```python
# Reduce cache sizes
cache_config = CacheConfig(
    local_max_size=1000,        # Reduce from 2000
    cleanup_interval=300        # Enable cleanup
)
```

### 3. Database Connection Issues
**Solution**: Configure connection pooling
```python
# Enable connection pooling
pool_config = PoolConfig(
    db_pool_size=10,
    connection_timeout=30,
    max_overflow=20
)
```

## Performance Presets

### Development
```python
apply_performance_preset("development", settings)
# - Smaller cache sizes
# - Debug logging enabled
# - Lower resource usage
```

### Production
```python
apply_performance_preset("production", settings)
# - Maximum cache sizes
# - Optimized indexes
# - Connection pooling enabled
```

### High Performance
```python
apply_performance_preset("high_performance", settings)
# - Aggressive caching
# - Parallel processing
# - Maximum optimization
```

## Next Steps

1. Run performance benchmarks to establish baselines
2. Monitor cache hit rates and adjust configurations
3. Test with realistic workloads
4. Fine-tune based on your specific use case

For detailed configuration options, see the [Performance Tuning Guide](PERFORMANCE_TUNING_GUIDE.md).