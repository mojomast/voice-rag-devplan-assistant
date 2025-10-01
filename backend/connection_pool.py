"""
Advanced Connection Pool Management
Provides optimized connection pooling for databases and external APIs
"""

import asyncio
import time
import threading
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
import weakref
import json

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

try:
    import aioredis
    AIOREDIS_AVAILABLE = True
except ImportError:
    AIOREDIS_AVAILABLE = False

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from loguru import logger
from .config import settings
from .cache_manager import cache_manager

@dataclass
class PoolConfig:
    """Configuration for connection pools"""
    # Database pool settings
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    db_pool_pre_ping: bool = True
    
    # HTTP client pool settings
    http_pool_size: int = 100
    http_max_connections: int = 200
    http_connect_timeout: int = 10
    http_read_timeout: int = 30
    http_max_keepalive_connections: int = 20
    http_keepalive_timeout: int = 30
    
    # Redis pool settings
    redis_pool_size: int = 10
    redis_max_connections: int = 20
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5
    
    # General settings
    health_check_interval: int = 60
    connection_retry_attempts: int = 3
    connection_retry_delay: float = 1.0

@dataclass
class ConnectionStats:
    """Connection pool statistics"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_connections: int = 0
    total_requests: int = 0
    avg_response_time: float = 0.0
    last_health_check: Optional[float] = None
    pool_utilization: float = 0.0

class DatabaseConnectionPool:
    """Optimized database connection pool"""
    
    def __init__(self, config: PoolConfig):
        self.config = config
        self.engine = None
        self.session_factory = None
        self.stats = ConnectionStats()
        self._lock = threading.RLock()
        self._initialized = False
        
    async def initialize(self, database_url: str):
        """Initialize database connection pool"""
        try:
            # Create async engine with optimized settings
            self.engine = create_async_engine(
                database_url,
                pool_size=self.config.db_pool_size,
                max_overflow=self.config.db_max_overflow,
                pool_timeout=self.config.db_pool_timeout,
                pool_recycle=self.config.db_pool_recycle,
                pool_pre_ping=self.config.db_pool_pre_ping,
                echo=settings.DATABASE_ECHO,
                # Disable connection pooling for SQLite (not needed)
                poolclass=NullPool if database_url.startswith('sqlite') else None
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                expire_on_commit=False,
                class_=AsyncSession
            )
            
            self._initialized = True
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute("SELECT 1")
            
            logger.info(f"Database connection pool initialized - size: {self.config.db_pool_size}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session from pool"""
        if not self._initialized:
            raise RuntimeError("Database pool not initialized")
        
        session = None
        start_time = time.time()
        
        try:
            self.stats.total_requests += 1
            session = self.session_factory()
            
            with self._lock:
                self.stats.active_connections += 1
            
            yield session
            
            await session.commit()
            
        except Exception as e:
            if session:
                await session.rollback()
            self.stats.failed_connections += 1
            logger.error(f"Database session error: {e}")
            raise
        finally:
            if session:
                await session.close()
                
            with self._lock:
                self.stats.active_connections = max(0, self.stats.active_connections - 1)
                response_time = time.time() - start_time
                self.stats.avg_response_time = (
                    (self.stats.avg_response_time * (self.stats.total_requests - 1) + response_time) /
                    self.stats.total_requests
                )
    
    async def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute query with connection from pool"""
        async with self.get_session() as session:
            try:
                from sqlalchemy import text
                result = await session.execute(text(query), params or {})
                
                # Convert to list of dictionaries
                rows = []
                for row in result:
                    if hasattr(row, '_mapping'):
                        rows.append(dict(row._mapping))
                    else:
                        rows.append(dict(zip(result.keys(), row)))
                
                return rows
                
            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self._lock:
            if self.engine and hasattr(self.engine.pool, 'size'):
                pool = self.engine.pool
                self.stats.total_connections = pool.size()
                self.stats.active_connections = pool.checkedin()
                self.stats.idle_connections = pool.checkedout()
                self.stats.pool_utilization = (
                    self.stats.active_connections / self.config.db_pool_size
                    if self.config.db_pool_size > 0 else 0
                )
        
        return {
            'initialized': self._initialized,
            'pool_size': self.config.db_pool_size,
            'max_overflow': self.config.db_max_overflow,
            'stats': self.stats,
            'engine_status': 'running' if self.engine else 'stopped'
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on database pool"""
        health = {
            'status': 'healthy',
            'pool_stats': None,
            'test_query_time_ms': 0
        }
        
        try:
            if not self._initialized:
                health['status'] = 'not_initialized'
                return health
            
            # Test query
            start_time = time.time()
            result = await self.execute_query("SELECT 1 as test")
            query_time = (time.time() - start_time) * 1000
            
            health['test_query_time_ms'] = query_time
            health['pool_stats'] = self.get_stats()
            
            if query_time > 1000:  # 1 second threshold
                health['status'] = 'degraded'
            
            if not result:
                health['status'] = 'unhealthy'
                
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)
        
        return health
    
    async def close(self):
        """Close database connection pool"""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("Database connection pool closed")

class HTTPConnectionPool:
    """Optimized HTTP connection pool for external APIs"""
    
    def __init__(self, config: PoolConfig):
        self.config = config
        self.session = None
        self.stats = ConnectionStats()
        self._lock = threading.RLock()
        self._initialized = False
        
    async def initialize(self):
        """Initialize HTTP connection pool"""
        if not AIOHTTP_AVAILABLE:
            logger.warning("aiohttp not available, HTTP pool disabled")
            return
        
        try:
            # Create connector with optimized settings
            connector = aiohttp.TCPConnector(
                limit=self.config.http_max_connections,
                limit_per_host=self.config.http_pool_size,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=self.config.http_keepalive_timeout,
                enable_cleanup_closed=True,
                force_close=False,
                # SSL settings for production
                verify_ssl=True,
                # Connection timeouts
                connect_timeout=self.config.http_connect_timeout,
                sock_connect_timeout=self.config.http_connect_timeout,
                sock_read_timeout=self.config.http_read_timeout
            )
            
            # Create session with optimized settings
            timeout = aiohttp.ClientTimeout(
                total=self.config.http_read_timeout + self.config.http_connect_timeout,
                connect=self.config.http_connect_timeout,
                sock_read=self.config.http_read_timeout
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Voice-RAG-System/1.0',
                    'Connection': 'keep-alive',
                    'Accept-Encoding': 'gzip, deflate'
                }
            )
            
            self._initialized = True
            logger.info(f"HTTP connection pool initialized - max connections: {self.config.http_max_connections}")
            
        except Exception as e:
            logger.error(f"Failed to initialize HTTP pool: {e}")
            raise
    
    async def request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with connection from pool"""
        if not self._initialized or not self.session:
            raise RuntimeError("HTTP pool not initialized")
        
        start_time = time.time()
        
        try:
            self.stats.total_requests += 1
            
            async with self.session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                
                # Parse response based on content type
                content_type = response.headers.get('content-type', '').lower()
                
                if 'application/json' in content_type:
                    result = await response.json()
                elif 'text/' in content_type:
                    result = await response.text()
                else:
                    result = await response.read()
                
                # Update stats
                response_time = time.time() - start_time
                with self._lock:
                    self.stats.avg_response_time = (
                        (self.stats.avg_response_time * (self.stats.total_requests - 1) + response_time) /
                        self.stats.total_requests
                    )
                    self.stats.active_connections += 1
                
                return {
                    'data': result,
                    'status_code': response.status,
                    'headers': dict(response.headers),
                    'response_time_ms': response_time * 1000
                }
                
        except Exception as e:
            self.stats.failed_connections += 1
            logger.error(f"HTTP request failed: {e}")
            raise
        finally:
            with self._lock:
                self.stats.active_connections = max(0, self.stats.active_connections - 1)
    
    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make GET request"""
        return await self.request('GET', url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make POST request"""
        return await self.request('POST', url, **kwargs)
    
    async def put(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make PUT request"""
        return await self.request('PUT', url, **kwargs)
    
    async def delete(self, url: str, **kwargs) -> Dict[str, Any]:
        """Make DELETE request"""
        return await self.request('DELETE', url, **kwargs)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self._lock:
            if self.session and hasattr(self.session.connector, 'total'):
                connector = self.session.connector
                self.stats.total_connections = connector.total
                self.stats.active_connections = len(connector._conns)
                self.stats.idle_connections = connector._conns.get('available', 0)
                self.stats.pool_utilization = (
                    self.stats.active_connections / self.config.http_pool_size
                    if self.config.http_pool_size > 0 else 0
                )
        
        return {
            'initialized': self._initialized,
            'pool_size': self.config.http_pool_size,
            'max_connections': self.config.http_max_connections,
            'stats': self.stats,
            'session_status': 'running' if self.session else 'stopped'
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on HTTP pool"""
        health = {
            'status': 'healthy',
            'pool_stats': None,
            'test_request_time_ms': 0
        }
        
        try:
            if not self._initialized:
                health['status'] = 'not_initialized'
                return health
            
            # Test request to a reliable endpoint
            start_time = time.time()
            result = await self.get('https://httpbin.org/get', timeout=5)
            request_time = (time.time() - start_time) * 1000
            
            health['test_request_time_ms'] = request_time
            health['pool_stats'] = self.get_stats()
            
            if request_time > 2000:  # 2 second threshold
                health['status'] = 'degraded'
            
            if result.get('status_code') != 200:
                health['status'] = 'unhealthy'
                
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)
        
        return health
    
    async def close(self):
        """Close HTTP connection pool"""
        if self.session:
            await self.session.close()
            self._initialized = False
            logger.info("HTTP connection pool closed")

class RedisConnectionPool:
    """Optimized Redis connection pool"""
    
    def __init__(self, config: PoolConfig):
        self.config = config
        self.pool = None
        self.stats = ConnectionStats()
        self._lock = threading.RLock()
        self._initialized = False
        
    async def initialize(self, redis_url: str):
        """Initialize Redis connection pool"""
        if not AIOREDIS_AVAILABLE:
            logger.warning("aioredis not available, Redis pool disabled")
            return
        
        try:
            self.pool = await aioredis.from_url(
                redis_url,
                max_connections=self.config.redis_max_connections,
                socket_timeout=self.config.redis_socket_timeout,
                socket_connect_timeout=self.config.redis_socket_connect_timeout,
                retry_on_timeout=True,
                health_check_interval=30,
                encoding='utf-8',
                decode_responses=True
            )
            
            self._initialized = True
            
            # Test connection
            await self.pool.ping()
            
            logger.info(f"Redis connection pool initialized - max connections: {self.config.redis_max_connections}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis pool: {e}")
            raise
    
    async def execute_command(self, command: str, *args, **kwargs) -> Any:
        """Execute Redis command with connection from pool"""
        if not self._initialized or not self.pool:
            raise RuntimeError("Redis pool not initialized")
        
        start_time = time.time()
        
        try:
            self.stats.total_requests += 1
            
            # Execute command
            result = await self.pool.execute_command(command, *args, **kwargs)
            
            # Update stats
            response_time = time.time() - start_time
            with self._lock:
                self.stats.avg_response_time = (
                    (self.stats.avg_response_time * (self.stats.total_requests - 1) + response_time) /
                    self.stats.total_requests
                )
                self.stats.active_connections += 1
            
            return result
            
        except Exception as e:
            self.stats.failed_connections += 1
            logger.error(f"Redis command failed: {e}")
            raise
        finally:
            with self._lock:
                self.stats.active_connections = max(0, self.stats.active_connections - 1)
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        return await self.execute_command('GET', key)
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis"""
        args = [key, value]
        if ex:
            args.extend(['EX', ex])
        return await self.execute_command('SET', *args)
    
    async def delete(self, *keys: str) -> int:
        """Delete keys from Redis"""
        return await self.execute_command('DEL', *keys)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        return await self.execute_command('EXISTS', key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self._lock:
            if self.pool and hasattr(self.pool, '_pool'):
                pool_info = self.pool._pool
                self.stats.total_connections = pool_info.maxsize
                self.stats.active_connections = len(pool_info._in_use_connections)
                self.stats.idle_connections = len(pool_info._available_connections)
                self.stats.pool_utilization = (
                    self.stats.active_connections / self.config.redis_pool_size
                    if self.config.redis_pool_size > 0 else 0
                )
        
        return {
            'initialized': self._initialized,
            'pool_size': self.config.redis_pool_size,
            'max_connections': self.config.redis_max_connections,
            'stats': self.stats,
            'pool_status': 'running' if self.pool else 'stopped'
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Redis pool"""
        health = {
            'status': 'healthy',
            'pool_stats': None,
            'test_command_time_ms': 0
        }
        
        try:
            if not self._initialized:
                health['status'] = 'not_initialized'
                return health
            
            # Test command
            start_time = time.time()
            result = await self.ping()
            command_time = (time.time() - start_time) * 1000
            
            health['test_command_time_ms'] = command_time
            health['pool_stats'] = self.get_stats()
            
            if command_time > 1000:  # 1 second threshold
                health['status'] = 'degraded'
            
            if not result:
                health['status'] = 'unhealthy'
                
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)
        
        return health
    
    async def ping(self) -> bool:
        """Ping Redis server"""
        return await self.execute_command('PING')
    
    async def close(self):
        """Close Redis connection pool"""
        if self.pool:
            await self.pool.close()
            self._initialized = False
            logger.info("Redis connection pool closed")

class ConnectionPoolManager:
    """Manager for all connection pools"""
    
    def __init__(self, config: Optional[PoolConfig] = None):
        self.config = config or PoolConfig()
        self.db_pool = DatabaseConnectionPool(self.config)
        self.http_pool = HTTPConnectionPool(self.config)
        self.redis_pool = RedisConnectionPool(self.config)
        self._initialized = False
        self._health_check_task = None
        
    async def initialize(self, database_url: Optional[str] = None, 
                        redis_url: Optional[str] = None):
        """Initialize all connection pools"""
        try:
            # Initialize database pool
            if database_url:
                await self.db_pool.initialize(database_url)
            
            # Initialize HTTP pool
            await self.http_pool.initialize()
            
            # Initialize Redis pool
            if redis_url:
                await self.redis_pool.initialize(redis_url)
            
            self._initialized = True
            
            # Start health check task
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            logger.info("All connection pools initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize connection pools: {e}")
            raise
    
    async def _health_check_loop(self):
        """Background health check loop"""
        while self._initialized:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                
                # Perform health checks
                db_health = await self.db_pool.health_check()
                http_health = await self.http_pool.health_check()
                redis_health = await self.redis_pool.health_check()
                
                # Log any issues
                for pool_name, health in [('database', db_health), ('http', http_health), ('redis', redis_health)]:
                    if health['status'] != 'healthy':
                        logger.warning(f"Pool {pool_name} health check failed: {health.get('error', 'Unknown error')}")
                
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
    
    def get_db_pool(self) -> DatabaseConnectionPool:
        """Get database connection pool"""
        return self.db_pool
    
    def get_http_pool(self) -> HTTPConnectionPool:
        """Get HTTP connection pool"""
        return self.http_pool
    
    def get_redis_pool(self) -> RedisConnectionPool:
        """Get Redis connection pool"""
        return self.redis_pool
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all pools"""
        return {
            'database': self.db_pool.get_stats(),
            'http': self.http_pool.get_stats(),
            'redis': self.redis_pool.get_stats(),
            'config': {
                'db_pool_size': self.config.db_pool_size,
                'http_pool_size': self.config.http_pool_size,
                'redis_pool_size': self.config.redis_pool_size,
                'health_check_interval': self.config.health_check_interval
            }
        }
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Health check for all pools"""
        return {
            'database': await self.db_pool.health_check(),
            'http': await self.http_pool.health_check(),
            'redis': await self.redis_pool.health_check()
        }
    
    async def close_all(self):
        """Close all connection pools"""
        if self._health_check_task:
            self._health_check_task.cancel()
        
        await asyncio.gather(
            self.db_pool.close(),
            self.http_pool.close(),
            self.redis_pool.close(),
            return_exceptions=True
        )
        
        self._initialized = False
        logger.info("All connection pools closed")

# Global connection pool manager
pool_config = PoolConfig()
connection_manager = ConnectionPoolManager(pool_config)

# Convenience functions
async def get_db_session():
    """Get database session from pool"""
    return connection_manager.get_db_pool().get_session()

async def make_http_request(method: str, url: str, **kwargs) -> Dict[str, Any]:
    """Make HTTP request using connection pool"""
    return await connection_manager.get_http_pool().request(method, url, **kwargs)

async def get_redis_connection():
    """Get Redis connection from pool"""
    return connection_manager.get_redis_pool()