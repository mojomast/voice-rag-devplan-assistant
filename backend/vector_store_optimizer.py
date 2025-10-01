"""
Vector Store Performance Optimizer
Optimizes FAISS index performance and provides advanced vector operations
"""

import os
import time
import hashlib
import pickle
import threading
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import numpy as np
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import asyncio

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    from langchain_community.vectorstores import FAISS as LangchainFAISS
    from langchain.embeddings.base import Embeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

from loguru import logger
from .cache_manager import cache_manager, get_cached_vector, set_cached_vector
from .config import settings

@dataclass
class VectorSearchConfig:
    """Configuration for vector search optimization"""
    index_type: str = "IVF"  # IVF, HNSW, FLAT
    nlist: int = 100  # Number of clusters for IVF
    nprobe: int = 10  # Number of clusters to search
    ef_search: int = 50  # Search parameter for HNSW
    ef_construction: int = 200  # Construction parameter for HNSW
    m: int = 16  # M parameter for HNSW
    use_gpu: bool = False
    batch_size: int = 32
    max_cache_size: int = 10000
    cache_ttl: int = 3600  # 1 hour

@dataclass
class VectorSearchResult:
    """Enhanced vector search result"""
    ids: List[str]
    scores: List[float]
    metadata: List[Dict[str, Any]]
    search_time_ms: float
    total_results: int
    index_used: str
    cache_hit: bool = False

class OptimizedVectorStore:
    """Optimized vector store with caching and performance enhancements"""
    
    def __init__(self, config: Optional[VectorSearchConfig] = None):
        self.config = config or VectorSearchConfig()
        self.index: Optional[faiss.Index] = None
        self.embeddings_model: Optional[Embeddings] = None
        self.id_mapping: Dict[int, str] = {}
        self.metadata_mapping: Dict[int, Dict[str, Any]] = {}
        self.dimension: Optional[int] = None
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Performance tracking
        self._stats = {
            'searches': 0,
            'cache_hits': 0,
            'total_search_time': 0.0,
            'index_loads': 0,
            'embeddings_generated': 0
        }
        
        # Initialize GPU if available and requested
        if self.config.use_gpu and FAISS_AVAILABLE:
            try:
                if hasattr(faiss, 'StandardGpuResources'):
                    self.gpu_resources = faiss.StandardGpuResources()
                    logger.info("GPU resources initialized for FAISS")
                else:
                    logger.warning("FAISS GPU not available, using CPU")
                    self.config.use_gpu = False
            except Exception as e:
                logger.warning(f"GPU initialization failed: {e}")
                self.config.use_gpu = False
        
        logger.info(f"Optimized vector store initialized with index type: {self.config.index_type}")
    
    def load_index(self, index_path: str, embeddings_model: Embeddings) -> bool:
        """Load FAISS index with optimizations"""
        try:
            if not FAISS_AVAILABLE:
                logger.error("FAISS not available")
                return False
            
            if not os.path.exists(index_path):
                logger.error(f"Index path does not exist: {index_path}")
                return False
            
            start_time = time.time()
            
            # Load the index
            with self._lock:
                if self.config.use_gpu:
                    # Load with GPU
                    cpu_index = faiss.read_index(index_path)
                    self.index = faiss.index_cpu_to_gpu(self.gpu_resources, 0, cpu_index)
                else:
                    self.index = faiss.read_index(index_path)
                
                self.embeddings_model = embeddings_model
                self.dimension = self.index.d
                
                # Load metadata
                metadata_path = index_path.replace('.faiss', '_metadata.pkl')
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'rb') as f:
                        metadata = pickle.load(f)
                        self.id_mapping = metadata.get('id_mapping', {})
                        self.metadata_mapping = metadata.get('metadata_mapping', {})
                
                # Optimize index parameters
                self._optimize_index()
            
            load_time = time.time() - start_time
            self._stats['index_loads'] += 1
            
            logger.info(f"Index loaded successfully in {load_time:.2f}s - dimension: {self.dimension}, vectors: {self.index.ntotal}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False
    
    def _optimize_index(self):
        """Optimize index parameters for better performance"""
        if not self.index:
            return
        
        try:
            # Optimize based on index type
            if hasattr(self.index, 'nprobe'):
                # IVF index
                self.index.nprobe = min(self.config.nprobe, self.index.nlist)
                logger.debug(f"Set nprobe to {self.index.nprobe}")
            
            elif hasattr(self.index, 'efSearch'):
                # HNSW index
                self.index.efSearch = self.config.ef_search
                logger.debug(f"Set efSearch to {self.index.efSearch}")
            
            # Set search parameters for better recall/speed trade-off
            if hasattr(self.index, 'parallel_mode'):
                self.index.parallel_mode = 1  # Enable parallel search
            
        except Exception as e:
            logger.warning(f"Index optimization failed: {e}")
    
    async def search(self, query: str, k: int = 10, 
                   metadata_filter: Optional[Dict[str, Any]] = None) -> VectorSearchResult:
        """Perform optimized vector search with caching"""
        start_time = time.time()
        
        try:
            # Generate cache key
            query_hash = hashlib.md5(f"{query}:{k}:{str(metadata_filter)}".encode()).hexdigest()
            
            # Check cache first
            cached_result = await get_cached_vector(query_hash)
            if cached_result:
                self._stats['cache_hits'] += 1
                cached_result.cache_hit = True
                return cached_result
            
            # Generate embeddings
            query_embedding = await self._generate_embeddings([query])
            if not query_embedding:
                raise ValueError("Failed to generate query embeddings")
            
            # Perform search
            with self._lock:
                if not self.index:
                    raise ValueError("Index not loaded")
                
                # Convert to numpy array
                query_array = np.array(query_embedding).astype('float32')
                
                # Search with optimized parameters
                scores, indices = self.index.search(query_array, min(k * 2, self.index.ntotal))
            
            # Process results
            results = self._process_search_results(indices[0], scores[0], metadata_filter, k)
            
            search_time = (time.time() - start_time) * 1000
            
            # Create result
            search_result = VectorSearchResult(
                ids=results['ids'],
                scores=results['scores'],
                metadata=results['metadata'],
                search_time_ms=search_time,
                total_results=len(results['ids']),
                index_used=self.config.index_type,
                cache_hit=False
            )
            
            # Cache result
            await set_cached_vector(query_hash, search_result)
            
            # Update stats
            self._stats['searches'] += 1
            self._stats['total_search_time'] += search_time
            
            return search_result
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise
    
    async def _generate_embeddings(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Generate embeddings with caching and batching"""
        if not self.embeddings_model:
            return None
        
        try:
            # Check cache for each text
            cached_embeddings = []
            texts_to_embed = []
            cache_keys = []
            
            for text in texts:
                text_hash = hashlib.md5(text.encode()).hexdigest()
                cached_embedding = await get_cached_vector(f"embedding:{text_hash}")
                
                if cached_embedding:
                    cached_embeddings.append(cached_embedding)
                else:
                    texts_to_embed.append(text)
                    cache_keys.append(text_hash)
                    cached_embeddings.append(None)
            
            # Generate embeddings for uncached texts
            if texts_to_embed:
                if hasattr(self.embeddings_model, 'embed_documents'):
                    # Use async embedding if available
                    loop = asyncio.get_event_loop()
                    new_embeddings = await loop.run_in_executor(
                        self._executor, 
                        self.embeddings_model.embed_documents, 
                        texts_to_embed
                    )
                else:
                    # Fallback to sync embedding
                    loop = asyncio.get_event_loop()
                    new_embeddings = await loop.run_in_executor(
                        self._executor,
                        self.embeddings_model.embed,
                        texts_to_embed
                    )
                
                # Cache new embeddings
                for text, embedding, cache_key in zip(texts_to_embed, new_embeddings, cache_keys):
                    await set_cached_vector(f"embedding:{cache_key}", embedding, ttl=7200)  # 2 hours
                
                # Merge cached and new embeddings
                final_embeddings = []
                new_embedding_idx = 0
                for i, cached in enumerate(cached_embeddings):
                    if cached is not None:
                        final_embeddings.append(cached)
                    else:
                        final_embeddings.append(new_embeddings[new_embedding_idx])
                        new_embedding_idx += 1
                
                self._stats['embeddings_generated'] += len(new_embeddings)
                return final_embeddings
            else:
                return cached_embeddings
                
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None
    
    def _process_search_results(self, indices: np.ndarray, scores: np.ndarray, 
                              metadata_filter: Optional[Dict[str, Any]], k: int) -> Dict[str, List]:
        """Process and filter search results"""
        results = {
            'ids': [],
            'scores': [],
            'metadata': []
        }
        
        for idx, score in zip(indices, scores):
            if idx == -1:  # FAISS returns -1 for invalid results
                continue
            
            # Get ID and metadata
            vector_id = self.id_mapping.get(idx, f"unknown_{idx}")
            metadata = self.metadata_mapping.get(idx, {})
            
            # Apply metadata filter
            if metadata_filter:
                if not self._matches_filter(metadata, metadata_filter):
                    continue
            
            results['ids'].append(vector_id)
            results['scores'].append(float(score))
            results['metadata'].append(metadata)
            
            if len(results['ids']) >= k:
                break
        
        return results
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """Check if metadata matches filter criteria"""
        for key, value in filter_dict.items():
            if key not in metadata:
                return False
            
            metadata_value = metadata[key]
            
            # Handle different filter types
            if isinstance(value, list):
                if metadata_value not in value:
                    return False
            elif isinstance(value, dict):
                # Handle range filters
                if 'min' in value and metadata_value < value['min']:
                    return False
                if 'max' in value and metadata_value > value['max']:
                    return False
            else:
                if metadata_value != value:
                    return False
        
        return True
    
    async def add_vectors(self, texts: List[str], ids: List[str], 
                         metadata: List[Dict[str, Any]]) -> bool:
        """Add vectors to the index"""
        try:
            if not self.index or not self.embeddings_model:
                return False
            
            # Generate embeddings
            embeddings = await self._generate_embeddings(texts)
            if not embeddings:
                return False
            
            # Convert to numpy array
            vectors = np.array(embeddings).astype('float32')
            
            with self._lock:
                # Add vectors to index
                start_idx = self.index.ntotal
                self.index.add(vectors)
                
                # Update mappings
                for i, (text_id, meta) in enumerate(zip(ids, metadata)):
                    vector_idx = start_idx + i
                    self.id_mapping[vector_idx] = text_id
                    self.metadata_mapping[vector_idx] = meta
            
            logger.info(f"Added {len(vectors)} vectors to index")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add vectors: {e}")
            return False
    
    def create_optimized_index(self, vectors: np.ndarray, index_type: str = None) -> faiss.Index:
        """Create optimized FAISS index based on configuration"""
        if not FAISS_AVAILABLE:
            raise ValueError("FAISS not available")
        
        dimension = vectors.shape[1]
        index_type = index_type or self.config.index_type
        
        try:
            if index_type == "FLAT":
                # Simple flat index (exact search)
                index = faiss.IndexFlatL2(dimension)
                
            elif index_type == "IVF":
                # IVF index (faster search, approximate)
                nlist = min(self.config.nlist, len(vectors) // 10)
                quantizer = faiss.IndexFlatL2(dimension)
                index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
                
                # Train the index
                index.train(vectors)
                index.nprobe = self.config.nprobe
                
            elif index_type == "HNSW":
                # HNSW index (good for high-dimensional data)
                index = faiss.IndexHNSWFlat(dimension, self.config.m)
                index.hnsw.efConstruction = self.config.ef_construction
                index.hnsw.efSearch = self.config.ef_search
                
            else:
                raise ValueError(f"Unsupported index type: {index_type}")
            
            # Add vectors to index
            index.add(vectors)
            
            logger.info(f"Created {index_type} index with {index.ntotal} vectors")
            return index
            
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            raise
    
    def save_index(self, index_path: str) -> bool:
        """Save index and metadata to disk"""
        try:
            if not self.index:
                return False
            
            # Save index
            if self.config.use_gpu and hasattr(faiss, 'index_gpu_to_cpu'):
                cpu_index = faiss.index_gpu_to_cpu(self.index)
                faiss.write_index(cpu_index, index_path)
            else:
                faiss.write_index(self.index, index_path)
            
            # Save metadata
            metadata_path = index_path.replace('.faiss', '_metadata.pkl')
            metadata = {
                'id_mapping': self.id_mapping,
                'metadata_mapping': self.metadata_mapping,
                'config': self.config
            }
            
            with open(metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
            
            logger.info(f"Index saved to {index_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        avg_search_time = (self._stats['total_search_time'] / self._stats['searches'] 
                          if self._stats['searches'] > 0 else 0)
        
        cache_hit_rate = (self._stats['cache_hits'] / 
                         (self._stats['searches'] + self._stats['cache_hits']) 
                         if (self._stats['searches'] + self._stats['cache_hits']) > 0 else 0)
        
        return {
            'index_type': self.config.index_type,
            'dimension': self.dimension,
            'total_vectors': self.index.ntotal if self.index else 0,
            'searches_performed': self._stats['searches'],
            'cache_hits': self._stats['cache_hits'],
            'cache_hit_rate': cache_hit_rate,
            'avg_search_time_ms': avg_search_time,
            'embeddings_generated': self._stats['embeddings_generated'],
            'index_loads': self._stats['index_loads'],
            'gpu_enabled': self.config.use_gpu
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on vector store"""
        health = {
            'status': 'healthy',
            'index_loaded': self.index is not None,
            'dimension': self.dimension,
            'total_vectors': self.index.ntotal if self.index else 0,
            'search_latency_ms': 0
        }
        
        try:
            if self.index and self.embeddings_model:
                # Test search
                start_time = time.time()
                test_query = "test query"
                result = await self.search(test_query, k=1)
                search_latency = (time.time() - start_time) * 1000
                health['search_latency_ms'] = search_latency
                
                if search_latency > 1000:  # 1 second threshold
                    health['status'] = 'degraded'
            
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)
        
        return health

class VectorStoreManager:
    """Manager for multiple optimized vector stores"""
    
    def __init__(self):
        self.stores: Dict[str, OptimizedVectorStore] = {}
        self.default_config = VectorSearchConfig()
    
    def get_store(self, name: str, config: Optional[VectorSearchConfig] = None) -> OptimizedVectorStore:
        """Get or create vector store"""
        if name not in self.stores:
            store_config = config or self.default_config
            self.stores[name] = OptimizedVectorStore(store_config)
        
        return self.stores[name]
    
    async def search_all(self, query: str, k: int = 10, 
                        stores: Optional[List[str]] = None) -> Dict[str, VectorSearchResult]:
        """Search across multiple vector stores"""
        if stores is None:
            stores = list(self.stores.keys())
        
        results = {}
        
        # Execute searches in parallel
        tasks = []
        for store_name in stores:
            if store_name in self.stores:
                task = self.stores[store_name].search(query, k)
                tasks.append((store_name, task))
        
        if tasks:
            completed_tasks = await asyncio.gather([task for _, task in tasks], return_exceptions=True)
            
            for (store_name, _), result in zip(tasks, completed_tasks):
                if isinstance(result, Exception):
                    logger.error(f"Search failed for store {store_name}: {result}")
                    results[store_name] = None
                else:
                    results[store_name] = result
        
        return results
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all vector stores"""
        stats = {}
        for name, store in self.stores.items():
            stats[name] = store.get_stats()
        return stats
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Health check for all vector stores"""
        health = {}
        for name, store in self.stores.items():
            health[name] = await store.health_check()
        return health

# Global vector store manager
vector_store_manager = VectorStoreManager()