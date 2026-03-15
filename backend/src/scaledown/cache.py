"""
ScaleDown Cache for Optimized Prompts
Location: backend/src/scaledown/cache.py
"""

import time
import json
from typing import Dict, Any, Optional
from collections import OrderedDict
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ScaleDownCache:
    """
    Cache for optimized prompts with TTL and LRU eviction
    """
    
    def __init__(self, max_size: int = 10000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
        self.cache = OrderedDict()
        self.access_times = {}
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0
        }
        
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get item from cache if exists and not expired
        """
        if key in self.cache:
            # Check if expired
            if time.time() - self.access_times[key] > self.ttl:
                # Expired - remove and return None
                del self.cache[key]
                del self.access_times[key]
                self.stats["misses"] += 1
                self.stats["size"] = len(self.cache)
                return None
            
            # Update access time and move to end (most recent)
            self.access_times[key] = time.time()
            self.cache.move_to_end(key)
            self.stats["hits"] += 1
            return self.cache[key]
        
        self.stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """
        Set item in cache
        """
        # If key exists, update it
        if key in self.cache:
            self.cache[key] = value
            self.access_times[key] = time.time()
            self.cache.move_to_end(key)
            return
        
        # Check if we need to evict
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        # Add new item
        self.cache[key] = value
        self.access_times[key] = time.time()
        self.stats["size"] = len(self.cache)
        
        logger.debug(f"Cached optimized prompt: {key[:20]}...")
    
    def _evict_oldest(self) -> None:
        """Evict oldest item (LRU)"""
        if self.cache:
            oldest_key, _ = self.cache.popitem(last=False)
            del self.access_times[oldest_key]
            self.stats["evictions"] += 1
            logger.debug(f"Evicted oldest cache item: {oldest_key[:20]}...")
    
    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()
        self.access_times.clear()
        self.stats["size"] = 0
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            "hit_rate_percentage": hit_rate,
            "current_size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl
        }