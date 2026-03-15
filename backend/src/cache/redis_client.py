"""
Redis Client Wrapper
Location: backend/src/cache/redis_client.py
"""

import redis.asyncio as redis
import json
from typing import Any, Optional
from ..utils.logger import get_logger
from ..config.settings import config

logger = get_logger(__name__)

class RedisClient:
    """
    Async Redis client wrapper
    """
    
    def __init__(self):
        self.redis_url = config.REDIS_URL
        self.client = None
        self._connected = False
        
    async def connect(self):
        """Connect to Redis"""
        if not self._connected:
            try:
                self.client = await redis.from_url(
                    self.redis_url,
                    decode_responses=True
                )
                self._connected = True
                logger.info("Connected to Redis")
            except Exception as e:
                logger.error(f"Redis connection failed: {str(e)}")
                self._connected = False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        if not self._connected:
            await self.connect()
        
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in Redis"""
        if not self._connected:
            await self.connect()
        
        try:
            await self.client.setex(
                key,
                ttl,
                json.dumps(value)
            )
            return True
        except Exception as e:
            logger.error(f"Redis set error: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self._connected:
            await self.connect()
        
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {str(e)}")
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            self._connected = False