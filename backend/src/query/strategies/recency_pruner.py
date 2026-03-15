"""
Recency-Based Pruning Strategy
Location: backend/src/query/strategies/recency_pruner.py
"""

from typing import List, Dict, Any
from datetime import datetime
from ...utils.logger import get_logger

logger = get_logger(__name__)

class RecencyPruner:
    """
    Prunes content based on recency (for time-sensitive topics)
    Only relevant for subjects like current events, history, etc.
    """
    
    def __init__(self, decay_factor: float = 0.1):
        self.decay_factor = decay_factor
        self.stats = {"calls": 0, "avg_recency_score": 0}
        
    async def prune(self,
                   candidates: List[Dict[str, Any]],
                   query: str,
                   grade: int,
                   intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Adjust relevance based on recency
        """
        self.stats["calls"] += 1
        
        if not candidates:
            return []
        
        # Check if query is time-sensitive
        time_sensitive = self._is_time_sensitive(query, intent)
        
        if not time_sensitive:
            # Return all candidates unchanged
            return candidates
        
        # Apply recency weighting
        current_year = datetime.now().year
        recency_scores = []
        
        for candidate in candidates:
            # Get content year (if available)
            content_year = candidate.get("year", candidate.get("grade_level", 2000))
            
            # Calculate recency score (higher for more recent)
            years_old = current_year - content_year
            recency_score = max(0, 1 - (years_old * self.decay_factor))
            recency_scores.append(recency_score)
            
            # Combine with existing relevance
            base_relevance = candidate.get("relevance", 0.5)
            candidate["relevance"] = base_relevance * (0.7 + 0.3 * recency_score)
        
        # Re-sort by updated relevance
        candidates.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        
        # Update stats
        if recency_scores:
            self.stats["avg_recency_score"] = (
                (self.stats["avg_recency_score"] * (self.stats["calls"] - 1) + 
                 sum(recency_scores) / len(recency_scores)) / self.stats["calls"]
            )
        
        logger.debug(f"Recency pruner: applied recency weighting to {len(candidates)} candidates")
        
        return candidates
    
    def _is_time_sensitive(self, query: str, intent: Dict[str, Any]) -> bool:
        """Check if query is time-sensitive"""
        time_keywords = [
            'current', 'recent', 'latest', 'now', 'today',
            'modern', 'contemporary', 'update', 'news'
        ]
        
        query_lower = query.lower()
        for keyword in time_keywords:
            if keyword in query_lower:
                return True
        
        # History questions might want older content
        if intent.get('subject') == 'history' and 'recent' not in query_lower:
            return False
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        return self.stats