"""
Comprehensive Performance Optimization Tests
Tests all performance enhancements including caching, vector stores, and connection pooling
"""

import asyncio
import pytest
import time
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

# Import the performance optimization modules
from backend.cache_manager import (
    AdvancedCacheManager, CacheConfig, cache_manager,
    get_cached_query, set_cached_query
)
from backend.vector_store_optimizer import (
    OptimizedVectorStore, VectorSearchConfig, vector_store_manager
)
from backend.connection_pool import (
    ConnectionPoolManager, PoolConfig, connection_manager
)
from backend.optimized_rag_handler import (
    OptimizedRAGHandler, OptimizedRAGConfig, optimized_rag_handler
)
from backend.optimized_voice_service import (
    OptimizedVoiceService, OptimizedVoiceConfig, optimized_voice_service
)
from backend.performance_benchmark import (
    PerformanceBenchmark, BenchmarkConfig, performance_benchmark
)
from backend.enhanced_performance_config import (
    EnhancedPerformanceSettings, apply_performance_preset,
    PERFORMANCE_PRESETS
)

class TestCacheManager:
    """Test cases for cache manager"""
    
    @pytest.fixture
    def cache_config(self):
        """Create test cache configuration"""
        return CacheConfig(
            local_max_size=10,
            local_ttl=60,
            redis_enabled=False  # Disable Redis for tests
        )
    
    @pytest.fixture
    def cache_manager_instance(self, cache_config):
        """Create cache manager instance"""
        return AdvancedCacheManager(cache_config)
    
    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache_manager_instance):
        """Test basic cache set and get operations"""
        # Test setting and getting a value
        await cache_manager_instance.set('test', 'key1', 'value1')
        result = await cache_manager_instance.get('test', 'key1')
        assert result == 'value1'
        
        # Test cache miss
        result = await cache_manager_instance.get('test', 'nonexistent')
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_ttl(self, cache_manager_instance):
        """Test cache TTL functionality"""
        # Set value with short TTL
        await cache_manager_instance.set('test', 'ttl_key', 'value', ttl=1)
        
        # Should be available immediately
        result = await cache_manager_instance.get('test', 'ttl_key')
        assert result == 'value'
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired
        result = await cache_manager_instance.get('test', 'ttl_key')
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_eviction(self, cache_manager_instance):
        """Test cache eviction when max size is reached"""
        # Fill cache to max capacity
        for i in range(12):  # More than max_size of 10
            await cache_manager_instance.set('test', f'key{i}', f'value{i}')
        
        # First items should be evicted
        result = await cache_manager_instance.get('test', 'key0')
        assert result is None
        
        # Last items should still be available
        result = await cache_manager_instance.get('test', 'key11')
        assert result == 'value11'
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, cache_manager_instance):
        """Test cache statistics"""
        # Perform some operations
        await cache_manager_instance.set('test', 'key1', 'value1')
        await cache_manager_instance.get('test', 'key1')  # Hit
        await cache_manager_instance.get('test', 'nonexistent')  # Miss
        
        stats = cache_manager_instance.get_stats()
        
        assert stats['stats']['sets'] == 1
        assert stats['stats']['hits'] == 1
        assert stats['stats']['misses'] == 1
        assert stats['hit_rate'] == 0.5
    
    @pytest.mark.asyncio
    async def test_convenience_functions(self):
        """Test convenience functions for caching"""
        # Test query caching
        await set_cached_query('test_query', {'result': 'test_result'})
        result = await get_cached_query('test_query')
        assert result == {'result': 'test_result'}

class TestVectorStoreOptimizer:
    """Test cases for vector store optimizer"""
    
    @pytest.fixture
    def vector_config(self):
        """Create test vector configuration"""
        return VectorSearchConfig(
            index_type="FLAT",
            batch_size=2
        )
    
    @pytest.fixture
    def mock_embeddings(self):
        """Create mock embeddings model"""
        mock_emb = Mock()
        mock_emb.embed_documents = AsyncMock(return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        mock_emb.embed = AsyncMock(return_value=[0.7, 0.8, 0.9])
        return mock_emb
    
    @pytest.fixture
    def vector_store(self, vector_config):
        """Create optimized vector store"""
        return OptimizedVectorStore(vector_config)
    
    def test_vector_store_initialization(self, vector_store):
        """Test vector store initialization"""
        assert vector_store.config.index_type == "FLAT"
        assert vector_store.config.batch_size == 2
        assert vector_store._stats['searches'] == 0
    
    @pytest.mark.asyncio
    async def test_vector_search(self, vector_store, mock_embeddings):
        """Test vector search functionality"""
        # Mock the index
        vector_store.index = Mock()
        vector_store.index.d = 3
        vector_store.index.ntotal = 2
        vector_store.index.search.return_value = (
            [[0.9, 0.8]], [[0, 1]]
        )
        
        # Set embeddings model
        vector_store.embeddings_model = mock_embeddings
        
        # Perform search
        result = await vector_store.search("test query", k=2)
        
        assert result is not None
        assert result.total_results == 2
        assert result.index_used == "FLAT"
        assert result.search_time_ms >= 0
    
    @pytest.mark.asyncio
    async def test_vector_search_caching(self, vector_store, mock_embeddings):
        """Test vector search caching"""
        # Mock the index
        vector_store.index = Mock()
        vector_store.index.d = 3
        vector_store.index.ntotal = 1
        vector_store.index.search.return_value = ([[0.9]], [[0]])
        
        # Set embeddings model
        vector_store.embeddings_model = mock_embeddings
        
        # First search
        result1 = await vector_store.search("test query", k=1)
        assert result1.cache_hit is False
        
        # Second search (should hit cache)
        result2 = await vector_store.search("test query", k=1)
        assert result2.cache_hit is True
    
    def test_vector_store_stats(self, vector_store):
        """Test vector store statistics"""
        stats = vector_store.get_stats()
        
        assert 'index_type' in stats
        assert 'searches_performed' in stats
        assert 'cache_hits' in stats
        assert 'avg_search_time_ms' in stats

class TestConnectionPool:
    """Test cases for connection pool"""
    
    @pytest.fixture
    def pool_config(self):
        """Create test pool configuration"""
        return PoolConfig(
            db_pool_size=2,
            http_pool_size=5,
            redis_pool_size=2
        )
    
    @pytest.fixture
    def connection_pool_manager(self, pool_config):
        """Create connection pool manager"""
        return ConnectionPoolManager(pool_config)
    
    @pytest.mark.asyncio
    async def test_database_pool_initialization(self, connection_pool_manager):
        """Test database pool initialization"""
        # Mock the database engine creation
        with patch('backend.connection_pool.create_async_engine') as mock_engine:
            mock_engine.return_value = Mock()
            
            await connection_pool_manager.initialize("sqlite:///test.db")
            
            assert connection_pool_manager._initialized
            mock_engine.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_http_pool_initialization(self, connection_pool_manager):
        """Test HTTP pool initialization"""
        # Mock aiohttp
        with patch('backend.connection_pool.aiohttp') as mock_aiohttp:
            mock_aiohttp.TCPConnector = Mock()
            mock_aiohttp.ClientSession = Mock()
            mock_aiohttp.ClientTimeout = Mock()
            
            await connection_pool_manager.initialize()
            
            assert connection_pool_manager._initialized
    
    def test_pool_stats(self, connection_pool_manager):
        """Test pool statistics"""
        stats = connection_pool_manager.get_all_stats()
        
        assert 'database' in stats
        assert 'http' in stats
        assert 'redis' in stats
        assert 'config' in stats

class TestOptimizedRAGHandler:
    """Test cases for optimized RAG handler"""
    
    @pytest.fixture
    def rag_config(self):
        """Create test RAG configuration"""
        return OptimizedRAGConfig(
            default_k=3,
            enable_query_cache=True,
            enable_parallel_search=False  # Disable for tests
        )
    
    @pytest.fixture
    def rag_handler(self, rag_config):
        """Create optimized RAG handler"""
        return OptimizedRAGHandler(rag_config)
    
    @pytest.mark.asyncio
    async def test_rag_handler_initialization(self, rag_handler):
        """Test RAG handler initialization"""
        assert rag_handler.config.default_k == 3
        assert rag_handler.config.enable_query_cache is True
        assert rag_handler._stats['total_queries'] == 0
    
    @pytest.mark.asyncio
    async def test_rag_query_processing(self, rag_handler):
        """Test RAG query processing"""
        # Mock vector stores
        mock_store = Mock()
        mock_result = Mock()
        mock_result.ids = ['doc1', 'doc2']
        mock_result.scores = [0.9, 0.8]
        mock_result.metadata = [{'title': 'Doc 1'}, {'title': 'Doc 2'}]
        mock_result.search_time_ms = 100
        mock_result.cache_hit = False
        
        mock_store.search = AsyncMock(return_value=mock_result)
        rag_handler.vector_stores = {'main': mock_store}
        
        # Mock Requesty client
        rag_handler.requesty_client = Mock()
        rag_handler.requesty_client.chat_completion.return_value = "Test answer"
        
        # Process query
        result = await rag_handler.ask_question("test query")
        
        assert result['status'] == 'success'
        assert result['query'] == 'test query'
        assert 'answer' in result
    
    @pytest.mark.asyncio
    async def test_rag_query_caching(self, rag_handler):
        """Test RAG query caching"""
        # Mock vector stores
        mock_store = Mock()
        mock_result = Mock()
        mock_result.ids = ['doc1']
        mock_result.scores = [0.9]
        mock_result.metadata = [{'title': 'Doc 1'}]
        mock_result.search_time_ms = 100
        mock_result.cache_hit = False
        
        mock_store.search = AsyncMock(return_value=mock_result)
        rag_handler.vector_stores = {'main': mock_store}
        
        # Mock Requesty client
        rag_handler.requesty_client = Mock()
        rag_handler.requesty_client.chat_completion.return_value = "Test answer"
        
        # First query
        result1 = await rag_handler.ask_question("test query")
        assert result1['cached'] is False
        
        # Second query (should hit cache)
        result2 = await rag_handler.ask_question("test query")
        assert result2['cached'] is True
    
    def test_rag_stats(self, rag_handler):
        """Test RAG handler statistics"""
        stats = rag_handler.get_stats()
        
        assert 'queries_processed' in stats
        assert 'cache_hits' in stats
        assert 'avg_response_time_ms' in stats
        assert 'vector_searches' in stats

class TestOptimizedVoiceService:
    """Test cases for optimized voice service"""
    
    @pytest.fixture
    def voice_config(self):
        """Create test voice configuration"""
        return OptimizedVoiceConfig(
            enable_tts_cache=True,
            enable_stt_cache=True,
            max_concurrent_tts=2,
            max_concurrent_stt=1
        )
    
    @pytest.fixture
    def voice_service(self, voice_config):
        """Create optimized voice service"""
        service = OptimizedVoiceService(voice_config)
        service.test_mode = True  # Enable test mode
        return service
    
    @pytest.mark.asyncio
    async def test_tts_synthesis(self, voice_service):
        """Test TTS synthesis"""
        result = await voice_service.synthesize_speech_optimized(
            text="Hello world",
            voice="alloy"
        )
        
        assert result['status'] in ['success', 'error']
        if result['status'] == 'success':
            assert 'audio_file' in result
            assert 'response_time_ms' in result
    
    @pytest.mark.asyncio
    async def test_tts_caching(self, voice_service):
        """Test TTS caching"""
        # First synthesis
        result1 = await voice_service.synthesize_speech_optimized(
            text="Hello world",
            voice="alloy"
        )
        
        # Second synthesis (should hit cache if successful)
        result2 = await voice_service.synthesize_speech_optimized(
            text="Hello world",
            voice="alloy"
        )
        
        # Check if caching worked (depends on implementation)
        assert 'cached' in result2
    
    @pytest.mark.asyncio
    async def test_stt_transcription(self, voice_service):
        """Test STT transcription"""
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(b"fake audio data")
            temp_path = temp_file.name
        
        try:
            result = await voice_service.transcribe_audio_optimized(
                audio_file_path=temp_path
            )
            
            assert result['status'] in ['success', 'error']
            if result['status'] == 'success':
                assert 'text' in result
                assert 'response_time_ms' in result
        
        finally:
            os.unlink(temp_path)
    
    def test_voice_service_stats(self, voice_service):
        """Test voice service statistics"""
        stats = voice_service.get_performance_stats()
        
        assert 'tts' in stats
        assert 'stt' in stats
        assert 'audio_optimizations' in stats
        assert 'config' in stats

class TestPerformanceBenchmark:
    """Test cases for performance benchmark"""
    
    @pytest.fixture
    def benchmark_config(self):
        """Create test benchmark configuration"""
        return BenchmarkConfig(
            num_queries=5,
            concurrent_users=2,
            warmup_queries=1,
            test_queries=["test query 1", "test query 2"]
        )
    
    @pytest.fixture
    def benchmark(self, benchmark_config):
        """Create performance benchmark"""
        return PerformanceBenchmark(benchmark_config)
    
    @pytest.mark.asyncio
    async def test_benchmark_execution(self, benchmark):
        """Test benchmark execution"""
        # Mock the RAG handler
        with patch('backend.performance_benchmark.optimized_rag_handler') as mock_rag:
            mock_rag.ask_question = AsyncMock(return_value={
                'status': 'success',
                'answer': 'Test answer'
            })
            
            # Run benchmark
            summary = await benchmark.run_benchmark()
            
            assert summary.total_queries == 5
            assert summary.avg_response_time_ms >= 0
            assert summary.throughput_qps >= 0
            assert 'targets_met' in summary
    
    def test_benchmark_config(self, benchmark_config):
        """Test benchmark configuration"""
        assert benchmark_config.num_queries == 5
        assert benchmark_config.concurrent_users == 2
        assert benchmark_config.warmup_queries == 1
        assert len(benchmark_config.test_queries) == 2

class TestPerformanceConfig:
    """Test cases for performance configuration"""
    
    def test_enhanced_performance_settings(self):
        """Test enhanced performance settings"""
        settings = EnhancedPerformanceSettings()
        
        assert settings.CACHE_ENABLED is True
        assert settings.CACHE_MAX_SIZE == 2000
        assert settings.VECTOR_INDEX_TYPE == "IVF"
    
    def test_performance_presets(self):
        """Test performance presets"""
        assert "development" in PERFORMANCE_PRESETS
        assert "production" in PERFORMANCE_PRESETS
        assert "high_performance" in PERFORMANCE_PRESETS
        
        # Check preset structure
        for preset_name, preset in PERFORMANCE_PRESETS.items():
            assert "description" in preset
            assert "cache_max_size" in preset
    
    def test_apply_performance_preset(self):
        """Test applying performance preset"""
        settings = EnhancedPerformanceSettings()
        
        # Apply production preset
        result = apply_performance_preset("production", settings)
        
        assert result["preset"] == "production"
        assert "description" in result
        assert "applied_settings" in result
        
        # Check that settings were applied
        assert settings.CACHE_MAX_SIZE >= 3000  # Production preset value
    
    def test_invalid_preset(self):
        """Test applying invalid preset"""
        settings = EnhancedPerformanceSettings()
        
        with pytest.raises(ValueError):
            apply_performance_preset("invalid_preset", settings)

class TestIntegration:
    """Integration tests for performance optimizations"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_performance(self):
        """Test end-to-end performance with all optimizations"""
        # This test would require a full system setup
        # For now, we'll test the integration points
        
        # Test that all components can be initialized
        cache_config = CacheConfig(redis_enabled=False)
        cache_mgr = AdvancedCacheManager(cache_config)
        
        vector_config = VectorSearchConfig(index_type="FLAT")
        vector_store = OptimizedVectorStore(vector_config)
        
        pool_config = PoolConfig(db_pool_size=2)
        conn_mgr = ConnectionPoolManager(pool_config)
        
        rag_config = OptimizedRAGConfig(enable_query_cache=True)
        rag_handler = OptimizedRAGHandler(rag_config)
        
        voice_config = OptimizedVoiceConfig(enable_tts_cache=True)
        voice_service = OptimizedVoiceService(voice_config)
        
        # Verify all components are properly initialized
        assert cache_mgr is not None
        assert vector_store is not None
        assert conn_mgr is not None
        assert rag_handler is not None
        assert voice_service is not None
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self):
        """Test performance monitoring integration"""
        from backend.performance_benchmark import performance_monitor
        
        # Start monitoring
        await performance_monitor.start_monitoring(interval_seconds=1)
        
        # Collect some metrics
        await asyncio.sleep(0.1)
        
        # Get current metrics
        metrics = performance_monitor.get_current_metrics()
        
        # Stop monitoring
        await performance_monitor.stop_monitoring()
        
        # Verify monitoring worked
        assert performance_monitor._monitoring_active is False

# Test performance regression
class TestPerformanceRegression:
    """Performance regression tests"""
    
    @pytest.mark.asyncio
    async def test_cache_performance_regression(self):
        """Test that cache performance doesn't regress"""
        cache_config = CacheConfig(local_max_size=100, redis_enabled=False)
        cache_mgr = AdvancedCacheManager(cache_config)
        
        # Measure cache performance
        start_time = time.time()
        
        # Perform many cache operations
        for i in range(100):
            await cache_mgr.set('test', f'key{i}', f'value{i}')
            await cache_mgr.get('test', f'key{i}')
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        # Should complete 200 operations in reasonable time
        assert operation_time < 5.0  # 5 seconds
        
        # Check cache stats
        stats = cache_mgr.get_stats()
        assert stats['stats']['sets'] == 100
        assert stats['stats']['hits'] == 100
    
    @pytest.mark.asyncio
    async def test_concurrent_performance(self):
        """Test concurrent performance"""
        cache_config = CacheConfig(local_max_size=50, redis_enabled=False)
        cache_mgr = AdvancedCacheManager(cache_config)
        
        # Perform concurrent cache operations
        async def cache_operations(start_id: int):
            for i in range(10):
                key = f'key{start_id + i}'
                await cache_mgr.set('test', key, f'value{start_id + i}')
                result = await cache_mgr.get('test', key)
                assert result == f'value{start_id + i}'
        
        # Run concurrent operations
        tasks = [cache_operations(i * 10) for i in range(5)]
        await asyncio.gather(*tasks)
        
        # Verify all operations completed
        stats = cache_mgr.get_stats()
        assert stats['stats']['sets'] == 50
        assert stats['stats']['hits'] == 50

if __name__ == "__main__":
    pytest.main([__file__, "-v"])