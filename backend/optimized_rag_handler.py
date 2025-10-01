"""
Optimized RAG Handler with Performance Enhancements
Integrates caching, connection pooling, and vector store optimizations
"""

import asyncio
import hashlib
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading

from loguru import logger
from .cache_manager import (
    cache_manager, get_cached_query, set_cached_query, 
    get_cached_vector, set_cached_vector
)
from .vector_store_optimizer import (
    OptimizedVectorStore, VectorSearchResult, VectorSearchConfig,
    vector_store_manager
)
from .connection_pool import connection_manager, get_db_session
from .requesty_client import RequestyClient
from .config import settings

@dataclass
class OptimizedRAGConfig:
    """Configuration for optimized RAG handler"""
    # Search settings
    default_k: int = 6
    max_k: int = 20
    similarity_threshold: float = 0.7
    
    # Caching settings
    enable_query_cache: bool = True
    enable_vector_cache: bool = True
    query_cache_ttl: int = 600  # 10 minutes
    vector_cache_ttl: int = 3600  # 1 hour
    
    # Performance settings
    enable_parallel_search: bool = True
    max_concurrent_searches: int = 3
    enable_result_ranking: bool = True
    
    # Vector store settings
    vector_index_type: str = "IVF"
    vector_nprobe: int = 10
    vector_ef_search: int = 50

class OptimizedRAGHandler:
    """Optimized RAG handler with performance enhancements"""
    
    def __init__(self, config: Optional[OptimizedRAGConfig] = None):
        self.config = config or OptimizedRAGConfig()
        self.vector_stores: Dict[str, OptimizedVectorStore] = {}
        self.requesty_client = None
        self.embeddings_model = None
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._lock = threading.RLock()
        
        # Performance tracking
        self._stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'avg_response_time': 0.0,
            'vector_searches': 0,
            'embeddings_generated': 0
        }
        
        # Initialize components
        self._initialize_components()
        
        logger.info("Optimized RAG handler initialized")
    
    def _initialize_components(self):
        """Initialize RAG components"""
        try:
            # Initialize Requesty client
            self.requesty_client = RequestyClient()
            
            # Initialize embeddings model
            if settings.OPENAI_API_KEY:
                from langchain_openai import OpenAIEmbeddings
                self.embeddings_model = OpenAIEmbeddings(
                    openai_api_key=settings.OPENAI_API_KEY,
                    model=settings.EMBEDDING_MODEL
                )
            else:
                from langchain_community.embeddings import FakeEmbeddings
                self.embeddings_model = FakeEmbeddings(size=1536)
            
            # Load vector stores
            self._load_vector_stores()
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG components: {e}")
            raise
    
    def _load_vector_stores(self):
        """Load optimized vector stores"""
        try:
            # Configure vector search
            vector_config = VectorSearchConfig(
                index_type=self.config.vector_index_type,
                nprobe=self.config.vector_nprobe,
                ef_search=self.config.vector_ef_search
            )
            
            # Load main document store
            main_store = vector_store_manager.get_store('main', vector_config)
            if os.path.exists(settings.VECTOR_STORE_PATH):
                success = main_store.load_index(
                    os.path.join(settings.VECTOR_STORE_PATH, 'index.faiss'),
                    self.embeddings_model
                )
                if success:
                    self.vector_stores['main'] = main_store
                    logger.info("Main vector store loaded")
            
            # Load devplan store
            devplan_store = vector_store_manager.get_store('devplan', vector_config)
            devplan_index_path = os.path.join(settings.DEVPLAN_VECTOR_STORE_PATH, 'index.faiss')
            if os.path.exists(devplan_index_path):
                success = devplan_store.load_index(devplan_index_path, self.embeddings_model)
                if success:
                    self.vector_stores['devplan'] = devplan_store
                    logger.info("Devplan vector store loaded")
            
            # Load project store
            project_store = vector_store_manager.get_store('project', vector_config)
            project_index_path = os.path.join(settings.PROJECT_VECTOR_STORE_PATH, 'index.faiss')
            if os.path.exists(project_index_path):
                success = project_store.load_index(project_index_path, self.embeddings_model)
                if success:
                    self.vector_stores['project'] = project_store
                    logger.info("Project vector store loaded")
            
        except Exception as e:
            logger.error(f"Failed to load vector stores: {e}")
    
    async def ask_question(self, query: str, include_sources: bool = True) -> Dict[str, Any]:
        """Process question with optimized RAG pipeline"""
        start_time = time.time()
        
        try:
            self._stats['total_queries'] += 1
            
            # Generate query hash for caching
            query_hash = hashlib.md5(f"{query}:{include_sources}".encode()).hexdigest()
            
            # Check cache first
            if self.config.enable_query_cache:
                cached_result = await get_cached_query(query_hash)
                if cached_result:
                    self._stats['cache_hits'] += 1
                    cached_result['cached'] = True
                    return cached_result
            
            # Process query
            result = await self._process_query(query, include_sources)
            
            # Cache result
            if self.config.enable_query_cache and result.get('status') == 'success':
                await set_cached_query(query_hash, result, ttl=self.config.query_cache_ttl)
            
            # Update stats
            response_time = time.time() - start_time
            self._stats['avg_response_time'] = (
                (self._stats['avg_response_time'] * (self._stats['total_queries'] - 1) + response_time) /
                self._stats['total_queries']
            )
            
            result['response_time_ms'] = response_time * 1000
            result['cached'] = False
            
            return result
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return {
                'answer': f"I apologize, but I encountered an error processing your question: {str(e)}",
                'sources': [],
                'query': query,
                'status': 'error',
                'error': str(e),
                'response_time_ms': (time.time() - start_time) * 1000
            }
    
    async def _process_query(self, query: str, include_sources: bool) -> Dict[str, Any]:
        """Process query through optimized RAG pipeline"""
        try:
            # Step 1: Vector search across all stores
            search_results = await self._perform_vector_search(query)
            
            if not search_results:
                return {
                    'answer': "I couldn't find relevant information to answer your question.",
                    'sources': [],
                    'query': query,
                    'status': 'no_results'
                }
            
            # Step 2: Rank and filter results
            ranked_results = await self._rank_results(search_results, query)
            
            # Step 3: Generate answer using LLM
            answer = await self._generate_answer(query, ranked_results)
            
            # Step 4: Format response
            sources = []
            if include_sources:
                sources = self._format_sources(ranked_results)
            
            return {
                'answer': answer,
                'sources': sources,
                'query': query,
                'status': 'success',
                'metadata': {
                    'total_results': len(ranked_results),
                    'stores_searched': list(search_results.keys()),
                    'avg_similarity': sum(r['score'] for r in ranked_results) / len(ranked_results) if ranked_results else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            raise
    
    async def _perform_vector_search(self, query: str, k: Optional[int] = None) -> Dict[str, VectorSearchResult]:
        """Perform vector search across all stores"""
        k = k or self.config.default_k
        
        try:
            if self.config.enable_parallel_search and len(self.vector_stores) > 1:
                # Parallel search across stores
                tasks = []
                for store_name, store in self.vector_stores.items():
                    task = store.search(query, k)
                    tasks.append((store_name, task))
                
                results = {}
                if tasks:
                    completed_tasks = await asyncio.gather(
                        [task for _, task in tasks], 
                        return_exceptions=True
                    )
                    
                    for (store_name, _), result in zip(tasks, completed_tasks):
                        if isinstance(result, Exception):
                            logger.error(f"Search failed for store {store_name}: {result}")
                        else:
                            results[store_name] = result
                
                self._stats['vector_searches'] += 1
                return results
            else:
                # Sequential search
                results = {}
                for store_name, store in self.vector_stores.items():
                    try:
                        result = await store.search(query, k)
                        results[store_name] = result
                    except Exception as e:
                        logger.error(f"Search failed for store {store_name}: {e}")
                
                self._stats['vector_searches'] += 1
                return results
                
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise
    
    async def _rank_results(self, search_results: Dict[str, VectorSearchResult], query: str) -> List[Dict[str, Any]]:
        """Rank and combine search results from multiple stores"""
        try:
            all_results = []
            
            # Combine results from all stores
            for store_name, result in search_results.items():
                for i, (doc_id, score, metadata) in enumerate(zip(result.ids, result.scores, result.metadata)):
                    all_results.append({
                        'id': doc_id,
                        'score': score,
                        'metadata': metadata,
                        'store': store_name,
                        'store_rank': i,
                        'search_time': result.search_time_ms
                    })
            
            if not all_results:
                return []
            
            # Filter by similarity threshold
            filtered_results = [
                r for r in all_results 
                if r['score'] >= self.config.similarity_threshold
            ]
            
            if not filtered_results:
                # If no results meet threshold, take top results
                filtered_results = sorted(all_results, key=lambda x: x['score'], reverse=True)[:self.config.default_k]
            
            # Sort by score (descending)
            filtered_results.sort(key=lambda x: x['score'], reverse=True)
            
            # Apply additional ranking if enabled
            if self.config.enable_result_ranking:
                filtered_results = await self._apply_advanced_ranking(filtered_results, query)
            
            # Limit results
            return filtered_results[:self.config.max_k]
            
        except Exception as e:
            logger.error(f"Result ranking failed: {e}")
            return []
    
    async def _apply_advanced_ranking(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Apply advanced ranking algorithms"""
        try:
            # Simple re-ranking based on multiple factors
            for result in results:
                # Boost score based on store priority
                store_priority = {'main': 1.0, 'devplan': 1.1, 'project': 1.05}
                store_boost = store_priority.get(result['store'], 1.0)
                
                # Boost score based on metadata quality
                metadata_boost = 1.0
                metadata = result.get('metadata', {})
                
                if metadata.get('title'):
                    metadata_boost += 0.1
                if metadata.get('section_title'):
                    metadata_boost += 0.05
                if metadata.get('updated_at'):
                    metadata_boost += 0.02
                
                # Apply boosts
                result['original_score'] = result['score']
                result['score'] = result['score'] * store_boost * metadata_boost
            
            # Re-sort by boosted scores
            results.sort(key=lambda x: x['score'], reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"Advanced ranking failed: {e}")
            return results
    
    async def _generate_answer(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Generate answer using LLM with context"""
        try:
            if not results:
                return "I couldn't find relevant information to answer your question."
            
            # Prepare context
            context_parts = []
            for result in results[:5]:  # Use top 5 results
                metadata = result.get('metadata', {})
                title = metadata.get('title', 'Untitled')
                content = metadata.get('content', '')
                
                if content:
                    context_parts.append(f"Document: {title}\nContent: {content[:500]}...")
            
            context = "\n\n".join(context_parts)
            
            # Generate answer using Requesty client
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on the provided context. Answer only using the information given in the context. If the context doesn't contain the answer, say 'I don't have enough information in the provided documents to answer this question.'"
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
                }
            ]
            
            answer = self.requesty_client.chat_completion(messages)
            
            return answer.strip()
            
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            return f"I apologize, but I encountered an error generating the answer: {str(e)}"
    
    def _format_sources(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format sources for response"""
        sources = []
        for result in results:
            metadata = result.get('metadata', {})
            source = {
                'id': result.get('id', 'unknown'),
                'title': metadata.get('title', 'Untitled'),
                'score': result.get('score', 0.0),
                'store': result.get('store', 'unknown'),
                'metadata': {
                    'section_title': metadata.get('section_title'),
                    'updated_at': metadata.get('updated_at'),
                    'project_id': metadata.get('project_id'),
                    'status': metadata.get('status')
                }
            }
            sources.append(source)
        
        return sources
    
    async def search(self, query: str, k: int = 5, 
                   metadata_filter: Optional[Dict[str, Any]] = None,
                   store_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Perform optimized search with optional filtering"""
        try:
            # Determine which stores to search
            if store_type:
                stores_to_search = {store_type: self.vector_stores.get(store_type)}
            else:
                stores_to_search = self.vector_stores
            
            # Remove None stores
            stores_to_search = {k: v for k, v in stores_to_search.items() if v is not None}
            
            if not stores_to_search:
                return []
            
            # Perform search
            search_results = {}
            if self.config.enable_parallel_search and len(stores_to_search) > 1:
                # Parallel search
                tasks = []
                for store_name, store in stores_to_search.items():
                    task = store.search(query, k)
                    tasks.append((store_name, task))
                
                if tasks:
                    completed_tasks = await asyncio.gather(
                        [task for _, task in tasks], 
                        return_exceptions=True
                    )
                    
                    for (store_name, _), result in zip(tasks, completed_tasks):
                        if isinstance(result, Exception):
                            logger.error(f"Search failed for store {store_name}: {result}")
                        else:
                            search_results[store_name] = result
            else:
                # Sequential search
                for store_name, store in stores_to_search.items():
                    try:
                        result = await store.search(query, k)
                        search_results[store_name] = result
                    except Exception as e:
                        logger.error(f"Search failed for store {store_name}: {e}")
            
            # Combine and format results
            all_results = []
            for store_name, result in search_results.items():
                for doc_id, score, metadata in zip(result.ids, result.scores, result.metadata):
                    # Apply metadata filter
                    if metadata_filter and not self._matches_filter(metadata, metadata_filter):
                        continue
                    
                    all_results.append({
                        'id': doc_id,
                        'score': score,
                        'metadata': metadata,
                        'store': store_name,
                        'search_time_ms': result.search_time_ms
                    })
            
            # Sort by score and limit
            all_results.sort(key=lambda x: x['score'], reverse=True)
            return all_results[:k]
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """Check if metadata matches filter criteria"""
        for key, value in filter_dict.items():
            if key not in metadata:
                return False
            
            metadata_value = metadata[key]
            
            if isinstance(value, list):
                if metadata_value not in value:
                    return False
            elif isinstance(value, dict):
                if 'min' in value and metadata_value < value['min']:
                    return False
                if 'max' in value and metadata_value > value['max']:
                    return False
            else:
                if metadata_value != value:
                    return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG handler statistics"""
        cache_hit_rate = (self._stats['cache_hits'] / 
                         max(1, self._stats['total_queries']))
        
        return {
            'queries_processed': self._stats['total_queries'],
            'cache_hits': self._stats['cache_hits'],
            'cache_hit_rate': cache_hit_rate,
            'avg_response_time_ms': self._stats['avg_response_time'] * 1000,
            'vector_searches': self._stats['vector_searches'],
            'embeddings_generated': self._stats['embeddings_generated'],
            'vector_stores': {
                name: store.get_stats() 
                for name, store in self.vector_stores.items()
            },
            'config': {
                'default_k': self.config.default_k,
                'similarity_threshold': self.config.similarity_threshold,
                'enable_query_cache': self.config.enable_query_cache,
                'enable_parallel_search': self.config.enable_parallel_search
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on RAG handler"""
        health = {
            'status': 'healthy',
            'components': {},
            'performance': {}
        }
        
        try:
            # Check vector stores
            for name, store in self.vector_stores.items():
                store_health = await store.health_check()
                health['components'][f'vector_store_{name}'] = store_health
                
                if store_health['status'] != 'healthy':
                    health['status'] = 'degraded'
            
            # Check Requesty client
            try:
                if self.requesty_client:
                    # Simple test
                    test_response = self.requesty_client.chat_completion([
                        {"role": "user", "content": "test"}
                    ])
                    health['components']['requesty_client'] = {
                        'status': 'healthy',
                        'test_response_length': len(test_response)
                    }
                else:
                    health['components']['requesty_client'] = {
                        'status': 'not_configured'
                    }
            except Exception as e:
                health['components']['requesty_client'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health['status'] = 'degraded'
            
            # Performance metrics
            health['performance'] = {
                'avg_response_time_ms': self._stats['avg_response_time'] * 1000,
                'cache_hit_rate': (self._stats['cache_hits'] / 
                                 max(1, self._stats['total_queries'])),
                'queries_per_minute': self._stats['total_queries'] / max(1, time.time() / 60)
            }
            
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)
        
        return health
    
    async def clear_cache(self):
        """Clear all caches"""
        try:
            await cache_manager.clear_namespace('query')
            await cache_manager.clear_namespace('vector')
            await cache_manager.clear_namespace('embedding')
            logger.info("RAG caches cleared")
        except Exception as e:
            logger.error(f"Failed to clear caches: {e}")
    
    async def reload_vector_stores(self):
        """Reload all vector stores"""
        try:
            self._load_vector_stores()
            logger.info("Vector stores reloaded")
        except Exception as e:
            logger.error(f"Failed to reload vector stores: {e}")
            raise

# Global optimized RAG handler instance
optimized_rag_handler = OptimizedRAGHandler()