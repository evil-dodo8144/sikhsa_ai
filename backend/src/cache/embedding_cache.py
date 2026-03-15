"""
Embedding Cache
Location: backend/src/cache/embedding_cache.py
"""

import hashlib
import numpy as np
from typing import Optional, List
from .lru_cache import LRUCache
from ..utils.logger import get_logger

logger = get_logger(__name__)

class EmbeddingCache:
    """
    Cache for text embeddings
    """
    
    def __init__(self, capacity: int = 10000):
        self.cache = LRUCache(capacity=capacity, ttl=86400)  # 24 hour TTL
        self.stats = {"hits": 0, "misses": 0}
        
    def get(self, text: str) -> Optional[np.ndarray]:
        """
        Get embedding from cache
        """
        key = self._generate_key(text)
        cached = self.cache.get(key)
        
        if cached is not None:
            self.stats["hits"] += 1
            return np.array(cached)
        
        self.stats["misses"] += 1
        return None
    
    def set(self, text: str, embedding: np.ndarray) -> None:
        """
        Store embedding in cache
        """
        key = self._generate_key(text)
        self.cache.set(key, embedding.tolist())
        
    async def get_or_compute(self, 
                            text: str, 
                            compute_func: callable) -> np.ndarray:
        """
        Get from cache or compute if not exists
        """
        cached = self.get(text)
        if cached is not None:
            return cached
        
        # Compute embedding
        embedding = await compute_func(text)
        
        # Cache it
        self.set(text, embedding)
        
        return embedding
    
    def _generate_key(self, text: str) -> str:
        """Generate cache key from text"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0
        
        return {
            **self.stats,
            "hit_rate": hit_rate,
            "cache_stats": self.cache.get_stats()
        }