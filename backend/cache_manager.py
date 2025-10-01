"""
Comprehensive Caching System for Voice RAG System
Provides Redis-backed caching with local fallback for optimal performance
"""

import asyncio
import json
import hashlib
import time
import threading
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from functools import wraps
import pickle
import weakref

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from loguru import logger
from .config import settings

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.last_accessed is None:
            self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if self.expires_at is None:
            return False
        return datetime.now() >= self.expires_at
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "value": self.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "size_bytes": self.size_bytes,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CacheEntry':
        """Create from dictionary"""
        return cls(
            value=data["value"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None,
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None,
            size_bytes=data.get("size_bytes", 0),
            tags=data.get("tags", [])
        )

class CacheConfig:
    """Cache configuration settings"""
    
    def __init__(self):
        # Redis settings
        self.redis_url = getattr(settings, 'CACHE_REDIS_URL', 'redis://localhost:6379/0')
        self.redis_enabled = getattr(settings, 'CACHE_REDIS_ENABLED', False) and REDIS_AVAILABLE
        
        # Local cache settings
        self.local_max_size = getattr(settings, 'CACHE_LOCAL_MAX_SIZE', 1000)
        self.local_ttl = getattr(settings, 'CACHE_LOCAL_TTL', 3600)  # 1 hour
        
        # Default TTL settings
        self.default_ttl = getattr(settings, 'CACHE_DEFAULT_TTL', 1800)  # 30 minutes
        self.query_ttl = getattr(settings, 'CACHE_QUERY_TTL', 600)  # 10 minutes
        self.vector_ttl = getattr(settings, 'CACHE_VECTOR_TTL', 3600)  # 1 hour
        self.tts_ttl = getattr(settings, 'CACHE_TTS_TTL', 86400)  # 24 hours
        self.stt_ttl = getattr(settings, 'CACHE_STT_TTL', 3600)  # 1 hour
        
        # Performance settings
        self.cleanup_interval = getattr(settings, 'CACHE_CLEANUP_INTERVAL', 300)  # 5 minutes
        self.compression_threshold = getattr(settings, 'CACHE_COMPRESSION_THRESHOLD', 1024)  # 1KB
        self.enable_compression = getattr(settings, 'CACHE_ENABLE_COMPRESSION', True)
        
        # Cache namespaces
        self.namespaces = {
            'query': 'rag:query',
            'vector': 'rag:vector',
            'embedding': 'rag:embedding',
            'tts': 'voice:tts',
            'stt': 'voice:stt',
            'api': 'api:response',
            'db': 'db:query'
        }

class AdvancedCacheManager:
    """Advanced cache manager with Redis backend and local fallback"""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._local_cache: Dict[str, CacheEntry] = {}
        self._redis_client: Optional[redis.Redis] = None
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0,
            'errors': 0
        }
        self._last_cleanup = time.time()
        
        # Initialize Redis if enabled
        if self.config.redis_enabled:
            asyncio.create_task(self._init_redis())
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_loop())
        
        logger.info(f"Cache manager initialized - Redis: {self.config.redis_enabled}, Local max: {self.config.local_max_size}")
    
    async def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self._redis_client = redis.from_url(
                self.config.redis_url,
                encoding='utf-8',
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            await self._redis_client.ping()
            logger.info("Redis connection established")
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using local cache only")
            self.config.redis_enabled = False
            self._redis_client = None
    
    def _generate_key(self, namespace: str, key: str, **kwargs) -> str:
        """Generate cache key with namespace and parameters"""
        if kwargs:
            # Sort kwargs for consistent key generation
            sorted_kwargs = sorted(kwargs.items())
            key_data = f"{key}:{hashlib.md5(str(sorted_kwargs).encode()).hexdigest()}"
        else:
            key_data = key
        
        namespace_prefix = self.config.namespaces.get(namespace, 'default')
        return f"{namespace_prefix}:{key_data}"
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage"""
        try:
            # Use pickle for complex objects
            serialized = pickle.dumps(value)
            
            # Compress if enabled and above threshold
            if (self.config.enable_compression and 
                len(serialized) > self.config.compression_threshold):
                try:
                    import gzip
                    compressed = gzip.compress(serialized)
                    if len(compressed) < len(serialized):
                        return b'compressed:' + compressed
                except ImportError:
                    pass
            
            return serialized
            
        except Exception as e:
            logger.error(f"Serialization failed: {e}")
            raise
    
    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        try:
            # Check for compression
            if data.startswith(b'compressed:'):
                try:
                    import gzip
                    compressed_data = data[11:]  # Remove 'compressed:' prefix
                    data = gzip.decompress(compressed_data)
                except ImportError:
                    pass
            
            return pickle.loads(data)
            
        except Exception as e:
            logger.error(f"Deserialization failed: {e}")
            raise
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of value"""
        try:
            return len(pickle.dumps(value))
        except:
            return len(str(value).encode())
    
    async def get(self, namespace: str, key: str, **kwargs) -> Optional[Any]:
        """Get value from cache"""
        cache_key = self._generate_key(namespace, key, **kwargs)
        
        try:
            # Try local cache first
            with self._lock:
                entry = self._local_cache.get(cache_key)
                
                if entry and not entry.is_expired():
                    entry.access_count += 1
                    entry.last_accessed = datetime.now()
                    self._stats['hits'] += 1
                    return entry.value
                
                # Remove expired entry
                if entry and entry.is_expired():
                    del self._local_cache[cache_key]
            
            # Try Redis if available
            if self.config.redis_enabled and self._redis_client:
                try:
                    data = await self._redis_client.get(cache_key)
                    if data:
                        entry = CacheEntry.from_dict(json.loads(data.decode()))
                        
                        if not entry.is_expired():
                            # Cache in local for faster access
                            with self._lock:
                                self._local_cache[cache_key] = entry
                            
                            self._stats['hits'] += 1
                            return entry.value
                        else:
                            # Remove expired from Redis
                            await self._redis_client.delete(cache_key)
                            
                except Exception as e:
                    logger.warning(f"Redis get failed: {e}")
                    self._stats['errors'] += 1
            
            self._stats['misses'] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self._stats['errors'] += 1
            return None
    
    async def set(self, namespace: str, key: str, value: Any, 
                 ttl: Optional[int] = None, tags: List[str] = None, **kwargs) -> bool:
        """Set value in cache"""
        cache_key = self._generate_key(namespace, key, **kwargs)
        
        try:
            # Determine TTL
            if ttl is None:
                ttl = self.config.default_ttl
            
            expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
            size_bytes = self._estimate_size(value)
            
            # Create cache entry
            entry = CacheEntry(
                value=value,
                created_at=datetime.now(),
                expires_at=expires_at,
                size_bytes=size_bytes,
                tags=tags or []
            )
            
            # Set in local cache
            with self._lock:
                # Evict if necessary
                if len(self._local_cache) >= self.config.local_max_size:
                    self._evict_lru()
                
                self._local_cache[cache_key] = entry
                self._stats['sets'] += 1
            
            # Set in Redis if available
            if self.config.redis_enabled and self._redis_client:
                try:
                    serialized = json.dumps(entry.to_dict()).encode()
                    
                    if ttl > 0:
                        await self._redis_client.setex(cache_key, ttl, serialized)
                    else:
                        await self._redis_client.set(cache_key, serialized)
                        
                except Exception as e:
                    logger.warning(f"Redis set failed: {e}")
                    self._stats['errors'] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self._stats['errors'] += 1
            return False
    
    async def delete(self, namespace: str, key: str, **kwargs) -> bool:
        """Delete value from cache"""
        cache_key = self._generate_key(namespace, key, **kwargs)
        
        try:
            # Delete from local cache
            with self._lock:
                if cache_key in self._local_cache:
                    del self._local_cache[cache_key]
                    self._stats['deletes'] += 1
            
            # Delete from Redis
            if self.config.redis_enabled and self._redis_client:
                try:
                    await self._redis_client.delete(cache_key)
                except Exception as e:
                    logger.warning(f"Redis delete failed: {e}")
                    self._stats['errors'] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            self._stats['errors'] += 1
            return False
    
    async def clear_namespace(self, namespace: str) -> int:
        """Clear all entries in a namespace"""
        try:
            namespace_prefix = self.config.namespaces.get(namespace, namespace)
            count = 0
            
            # Clear from local cache
            with self._lock:
                keys_to_delete = [k for k in self._local_cache.keys() if k.startswith(namespace_prefix)]
                for key in keys_to_delete:
                    del self._local_cache[key]
                    count += 1
            
            # Clear from Redis
            if self.config.redis_enabled and self._redis_client:
                try:
                    pattern = f"{namespace_prefix}:*"
                    keys = await self._redis_client.keys(pattern)
                    if keys:
                        await self._redis_client.delete(*keys)
                        count += len(keys)
                except Exception as e:
                    logger.warning(f"Redis clear failed: {e}")
                    self._stats['errors'] += 1
            
            logger.info(f"Cleared {count} entries from namespace '{namespace}'")
            return count
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            self._stats['errors'] += 1
            return 0
    
    async def invalidate_tags(self, tags: List[str]) -> int:
        """Invalidate all entries with specified tags"""
        if not tags:
            return 0
        
        try:
            count = 0
            
            # Clear from local cache
            with self._lock:
                keys_to_delete = []
                for key, entry in self._local_cache.items():
                    if any(tag in entry.tags for tag in tags):
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self._local_cache[key]
                    count += 1
            
            # Clear from Redis (more complex - would need tag index)
            # For now, just clear local cache
            logger.info(f"Invalidated {count} entries with tags: {tags}")
            return count
            
        except Exception as e:
            logger.error(f"Tag invalidation error: {e}")
            self._stats['errors'] += 1
            return 0
    
    def _evict_lru(self):
        """Evict least recently used entries from local cache"""
        if not self._local_cache:
            return
        
        # Sort by last accessed time
        sorted_items = sorted(
            self._local_cache.items(),
            key=lambda x: x[1].last_accessed or datetime.min
        )
        
        # Remove 20% of entries
        evict_count = max(1, len(self._local_cache) // 5)
        for i in range(min(evict_count, len(sorted_items))):
            key = sorted_items[i][0]
            del self._local_cache[key]
            self._stats['evictions'] += 1
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_expired()
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
    
    async def _cleanup_expired(self):
        """Clean up expired entries"""
        current_time = time.time()
        if current_time - self._last_cleanup < self.config.cleanup_interval:
            return
        
        try:
            # Clean local cache
            with self._lock:
                expired_keys = [
                    key for key, entry in self._local_cache.items()
                    if entry.is_expired()
                ]
                
                for key in expired_keys:
                    del self._local_cache[key]
                    self._stats['evictions'] += 1
            
            # Clean Redis cache (would need scan for production)
            self._last_cleanup = current_time
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
        
        with self._lock:
            local_size = len(self._local_cache)
            local_memory = sum(entry.size_bytes for entry in self._local_cache.values())
        
        return {
            'stats': self._stats.copy(),
            'hit_rate': hit_rate,
            'local_cache': {
                'size': local_size,
                'max_size': self.config.local_max_size,
                'memory_usage_bytes': local_memory,
                'utilization': local_size / self.config.local_max_size
            },
            'redis_enabled': self.config.redis_enabled,
            'redis_connected': self._redis_client is not None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform cache health check"""
        health = {
            'status': 'healthy',
            'local_cache': True,
            'redis_cache': False,
            'latency_ms': 0
        }
        
        try:
            # Test local cache
            test_key = "health_check"
            await self.set('test', test_key, 'test_value', ttl=10)
            start_time = time.time()
            value = await self.get('test', test_key)
            latency = (time.time() - start_time) * 1000
            
            if value != 'test_value':
                health['status'] = 'degraded'
                health['local_cache'] = False
            
            health['latency_ms'] = latency
            
            # Test Redis
            if self.config.redis_enabled and self._redis_client:
                start_time = time.time()
                await self._redis_client.ping()
                redis_latency = (time.time() - start_time) * 1000
                health['redis_cache'] = True
                health['redis_latency_ms'] = redis_latency
            
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)
        
        return health

# Global cache manager instance
cache_config = CacheConfig()
cache_manager = AdvancedCacheManager(cache_config)

# Decorator for caching function results
def cached(namespace: str, ttl: Optional[int] = None, 
          key_func: Optional[Callable] = None, tags: List[str] = None):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hashlib.md5(str(args + tuple(sorted(kwargs.items()))).encode()).hexdigest()}"
            
            # Try to get from cache
            cached_result = await cache_manager.get(namespace, cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache_manager.set(namespace, cache_key, result, ttl=ttl, tags=tags)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, run in thread
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Convenience functions for specific cache types
async def get_cached_query(query: str, **kwargs) -> Optional[Any]:
    """Get cached query result"""
    return await cache_manager.get('query', query, **kwargs)

async def set_cached_query(query: str, result: Any, ttl: Optional[int] = None, **kwargs) -> bool:
    """Set cached query result"""
    cache_ttl = ttl or cache_config.query_ttl
    return await cache_manager.set('query', query, result, ttl=cache_ttl, **kwargs)

async def get_cached_vector(embedding_hash: str) -> Optional[Any]:
    """Get cached vector result"""
    return await cache_manager.get('vector', embedding_hash)

async def set_cached_vector(embedding_hash: str, vectors: Any, ttl: Optional[int] = None) -> bool:
    """Set cached vector result"""
    cache_ttl = ttl or cache_config.vector_ttl
    return await cache_manager.set('vector', embedding_hash, vectors, ttl=cache_ttl)

async def get_cached_tts(text_hash: str) -> Optional[bytes]:
    """Get cached TTS audio"""
    return await cache_manager.get('tts', text_hash)

async def set_cached_tts(text_hash: str, audio_data: bytes, ttl: Optional[int] = None) -> bool:
    """Set cached TTS audio"""
    cache_ttl = ttl or cache_config.tts_ttl
    return await cache_manager.set('tts', text_hash, audio_data, ttl=cache_ttl)

async def get_cached_stt(audio_hash: str) -> Optional[Any]:
    """Get cached STT result"""
    return await cache_manager.get('stt', audio_hash)

async def set_cached_stt(audio_hash: str, transcription: Any, ttl: Optional[int] = None) -> bool:
    """Set cached STT result"""
    cache_ttl = ttl or cache_config.stt_ttl
    return await cache_manager.set('stt', audio_hash, transcription, ttl=cache_ttl)