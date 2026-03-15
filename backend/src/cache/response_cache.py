"""
Response Cache for LLM Answers
Location: backend/src/cache/response_cache.py
"""

import hashlib
from typing import Optional, Dict, Any
from .redis_client import RedisClient
from .lru_cache import LRUCache
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ResponseCache:
    """
    Cache for LLM responses
    Uses both local LRU and Redis
    """
    
    def __init__(self):
        self.local_cache = LRUCache(capacity=1000, ttl=3600)
        self.redis_client = RedisClient()
        self.stats = {"local_hits": 0, "redis_hits": 0, "misses": 0}
        
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached response
        """
        # Check local cache first
        local_result = self.local_cache.get(key)
        if local_result:
            self.stats["local_hits"] += 1
            return local_result
        
        # Check Redis
        redis_result = await self.redis_client.get(key)
        if redis_result:
            self.stats["redis_hits"] += 1
            # Update local cache
            self.local_cache.set(key, redis_result)
            return redis_result
        
        self.stats["misses"] += 1
        return None
    
    async def set(self, key: str, value: Dict[str, Any], ttl: int = 3600) -> None:
        """
        Cache response
        """
        # Store in local cache
        self.local_cache.set(key, value, ttl)
        
        # Store in Redis
        await self.redis_client.set(key, value, ttl)
        
    def generate_key(self, query: str, student_id: str, grade: int) -> str:
        """
        Generate cache key from query parameters
        """
        key_string = f"{student_id}:{grade}:{query.lower().strip()}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.stats["local_hits"] + self.stats["redis_hits"] + self.stats["misses"]
        hit_rate = ((self.stats["local_hits"] + self.stats["redis_hits"]) / total * 100) if total > 0 else 0
        
        return {
            **self.stats,
            "hit_rate": hit_rate,
            "local_cache_stats": self.local_cache.get_stats()
        }