"""
LRU Cache Implementation
Location: backend/src/cache/lru_cache.py
"""

from collections import OrderedDict
from typing import Any, Optional
import time
from ..utils.logger import get_logger

logger = get_logger(__name__)

class LRUCache:
    """
    LRU Cache with TTL support
    """
    
    def __init__(self, capacity: int = 1000, ttl: int = 3600):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.ttl = ttl  # Time to live in seconds
        self.expiry = {}
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}
        
    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache
        """
        if key in self.cache:
            # Check if expired
            if time.time() > self.expiry.get(key, 0):
                self.delete(key)
                self.stats["misses"] += 1
                return None
            
            # Move to end (most recent)
            self.cache.move_to_end(key)
            self.stats["hits"] += 1
            return self.cache[key]
        
        self.stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set item in cache
        """
        # If key exists, update it
        if key in self.cache:
            self.cache[key] = value
            self.expiry[key] = time.time() + (ttl or self.ttl)
            self.cache.move_to_end(key)
            return
        
        # Check if we need to evict
        if len(self.cache) >= self.capacity:
            self._evict_oldest()
        
        # Add new item
        self.cache[key] = value
        self.expiry[key] = time.time() + (ttl or self.ttl)
        
    def delete(self, key: str) -> None:
        """
        Delete item from cache
        """
        if key in self.cache:
            del self.cache[key]
            del self.expiry[key]
            
    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()
        self.expiry.clear()
        
    def _evict_oldest(self) -> None:
        """Evict oldest item"""
        if self.cache:
            oldest_key, _ = self.cache.popitem(last=False)
            del self.expiry[oldest_key]
            self.stats["evictions"] += 1
            
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            "hit_rate": hit_rate,
            "size": len(self.cache),
            "capacity": self.capacity
        }