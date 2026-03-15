"""
ScaleDown Metrics Tracking
Location: backend/src/scaledown/metrics.py
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import statistics
from collections import defaultdict
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ScaleDownMetrics:
    """
    Track token savings and optimization metrics
    """
    
    def __init__(self):
        self.optimizations = []
        self.total_tokens_saved = 0
        self.total_original_tokens = 0
        self.total_optimized_tokens = 0
        self.api_calls = 0
        self.cache_hits = 0
        
        # Per-model stats
        self.model_stats = defaultdict(lambda: {
            "calls": 0,
            "tokens_saved": 0,
            "total_savings_percentage": 0
        })
        
    def record_optimization(self, 
                           original_tokens: int,
                           optimized_tokens: int,
                           savings: float,
                           model: str,
                           source: str = "api") -> None:
        """
        Record an optimization event
        """
        tokens_saved = original_tokens - optimized_tokens
        
        self.optimizations.append({
            "timestamp": datetime.utcnow().isoformat(),
            "original_tokens": original_tokens,
            "optimized_tokens": optimized_tokens,
            "tokens_saved": tokens_saved,
            "savings_percentage": savings,
            "model": model,
            "source": source
        })
        
        self.total_original_tokens += original_tokens
        self.total_optimized_tokens += optimized_tokens
        self.total_tokens_saved += tokens_saved
        
        if source == "api":
            self.api_calls += 1
        else:
            self.cache_hits += 1
        
        # Update model stats
        stats = self.model_stats[model]
        stats["calls"] += 1
        stats["tokens_saved"] += tokens_saved
        stats["total_savings_percentage"] = (
            (stats["total_savings_percentage"] * (stats["calls"] - 1) + savings) / stats["calls"]
        )
        
        # Keep only last 1000 optimizations
        if len(self.optimizations) > 1000:
            self.optimizations = self.optimizations[-1000:]
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get metrics summary
        """
        if not self.optimizations:
            return {
                "total_calls": 0,
                "total_tokens_saved": 0,
                "average_savings": 0,
                "api_calls": 0,
                "cache_hits": 0,
                "cache_hit_rate": 0
            }
        
        # Calculate averages
        recent_savings = [o["savings_percentage"] for o in self.optimizations[-100:]]
        avg_savings = statistics.mean(recent_savings) if recent_savings else 0
        
        total_calls = len(self.optimizations)
        cache_hit_rate = (self.cache_hits / total_calls * 100) if total_calls > 0 else 0
        
        return {
            "total_calls": total_calls,
            "total_tokens_saved": self.total_tokens_saved,
            "total_original_tokens": self.total_original_tokens,
            "total_optimized_tokens": self.total_optimized_tokens,
            "average_savings_percentage": avg_savings,
            "api_calls": self.api_calls,
            "cache_hits": self.cache_hits,
            "cache_hit_rate_percentage": cache_hit_rate,
            "model_stats": dict(self.model_stats),
            "estimated_cost_saved_usd": self.total_tokens_saved * 0.000002,  # Rough estimate
            "last_24h_calls": self._get_calls_last_24h()
        }
    
    def _get_calls_last_24h(self) -> int:
        """Get number of calls in last 24 hours"""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        count = 0
        for opt in self.optimizations:
            if datetime.fromisoformat(opt["timestamp"]) > cutoff:
                count += 1
        return count
    
    def reset(self) -> None:
        """Reset all metrics"""
        self.optimizations = []
        self.total_tokens_saved = 0
        self.total_original_tokens = 0
        self.total_optimized_tokens = 0
        self.api_calls = 0
        self.cache_hits = 0
        self.model_stats.clear()
        logger.info("Metrics reset")