"""
Prompt Optimizer with Caching
Location: backend/src/scaledown/optimizer.py
"""

import hashlib
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from .client import ScaleDownClient
from .cache import ScaleDownCache
from .metrics import ScaleDownMetrics
from .fallback import FallbackHandler
from ..utils.logger import get_logger
from ..config.settings import config

logger = get_logger(__name__)

class PromptOptimizer:
    """
    Wraps ScaleDown API with caching and fallback strategies
    This is where the cost savings happen!
    """
    
    def __init__(self):
        self.config = config
        self.client = ScaleDownClient(
            api_key=self.config.SCALEDOWN_API_KEY,
            api_url=self.config.SCALEDOWN_API_URL,
            timeout=self.config.SCALEDOWN_TIMEOUT
        )
        
        # Cache for optimized prompts
        self.cache = ScaleDownCache(max_size=10000, ttl=3600)
        self.metrics = ScaleDownMetrics()
        self.fallback = FallbackHandler()
        
        # Compression levels by tier
        self.compression_levels = {
            "free": "maximum",      # 80% savings
            "basic": "aggressive",   # 60% savings
            "premium": "balanced",   # 40% savings
            "enterprise": "light"     # 20% savings
        }
        
        self.min_savings_threshold = 0.3  # 30% minimum savings to cache
        
    async def optimize(self, 
                      base_prompt: str,
                      model: str = "gpt-3.5-turbo",
                      student_tier: str = "free",
                      force_refresh: bool = False) -> Dict[str, Any]:
        """
        Optimize prompt with multi-layer strategy
        
        Args:
            base_prompt: Original prompt to optimize
            model: Target LLM model
            student_tier: Student's subscription tier
            force_refresh: Skip cache and force API call
            
        Returns:
            Dict with optimized prompt and metrics
        """
        start_time = datetime.now()
        
        # Determine compression level based on tier
        compression_level = self.compression_levels.get(student_tier, "aggressive")
        
        # Model-specific adjustments
        if "gpt-4" in model:
            compression_level = "conservative"  # Be careful with GPT-4
        elif "claude" in model:
            compression_level = "balanced"
        
        # Generate cache key
        cache_key = self._generate_cache_key(base_prompt, model, compression_level)
        
        # Check cache (unless forced refresh)
        if not force_refresh:
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for prompt: {base_prompt[:50]}...")
                
                # Record cache hit metrics
                self.metrics.record_optimization(
                    saved_tokens=cached.get("optimized_tokens", 0),
                    model=model,
                    source="cache"
                )
                
                cached["from_cache"] = True
                cached["processing_time_ms"] = (datetime.now() - start_time).microseconds / 1000
                return cached
        
        # Try ScaleDown API
        logger.info(f"Optimizing prompt with ScaleDown. Tier: {student_tier}, Model: {model}")
        
        try:
            result = await self.client.optimize_prompt_async(
                prompt=base_prompt,
                model=model,
                compression_level=compression_level
            )
            
            # If API failed, use fallback
            if not result.get("success", False):
                logger.warning(f"ScaleDown API failed, using fallback: {result.get('error')}")
                result = self.fallback.optimize(
                    base_prompt=base_prompt,
                    model=model,
                    compression_level=compression_level
                )
            
        except Exception as e:
            logger.error(f"Error in ScaleDown optimization: {str(e)}")
            result = self.fallback.optimize(
                base_prompt=base_prompt,
                model=model,
                compression_level=compression_level
            )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000  # ms
        
        # Record metrics
        self.metrics.record_optimization(
            original_tokens=result.get("original_tokens", len(base_prompt) // 4),
            optimized_tokens=result.get("optimized_tokens", 0),
            savings=result.get("savings_percentage", 0),
            model=model,
            source="api"
        )
        
        # Add metadata
        result.update({
            "original_prompt": base_prompt,
            "cache_key": cache_key,
            "compression_level": compression_level,
            "student_tier": student_tier,
            "timestamp": datetime.utcnow().isoformat(),
            "processing_time_ms": processing_time,
            "from_cache": False
        })
        
        # Cache if savings are significant
        if (result.get("success", False) and 
            result.get("savings_percentage", 0) > self.min_savings_threshold):
            self.cache.set(cache_key, result)
            logger.debug(f"Cached optimized prompt with {result['savings_percentage']:.1f}% savings")
        
        return result
    
    def _generate_cache_key(self, prompt: str, model: str, compression: str) -> str:
        """Generate cache key from prompt and parameters"""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        return f"opt:{model}:{compression}:{prompt_hash}"
    
    async def batch_optimize(self, 
                            prompts: List[str],
                            model: str = "gpt-3.5-turbo",
                            student_tier: str = "free") -> List[Dict[str, Any]]:
        """
        Optimize multiple prompts in batch
        """
        results = []
        for prompt in prompts:
            result = await self.optimize(prompt, model, student_tier)
            results.append(result)
        return results
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        return self.cache.get_stats()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get optimization metrics"""
        return self.metrics.get_summary()