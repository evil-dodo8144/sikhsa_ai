"""
Token Budget Pruning Strategy
Location: backend/src/query/strategies/token_pruner.py
"""

from typing import List, Dict, Any
from ...utils.text_utils import count_tokens
from ...utils.logger import get_logger

logger = get_logger(__name__)

class TokenPruner:
    """
    Prunes content to fit within token budget
    Keeps most relevant content up to limit
    """
    
    def __init__(self, max_tokens: int = 2000):
        self.max_tokens = max_tokens
        self.stats = {"calls": 0, "avg_tokens": 0, "overflow_count": 0}
        
    async def prune(self,
                   candidates: List[Dict[str, Any]],
                   query: str,
                   grade: int,
                   intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Keep most relevant candidates within token budget
        """
        self.stats["calls"] += 1
        
        if not candidates:
            return []
        
        # Sort by relevance
        sorted_candidates = sorted(
            candidates, 
            key=lambda x: x.get("relevance", 0),
            reverse=True
        )
        
        selected = []
        total_tokens = 0
        total_original_tokens = sum(
            count_tokens(c.get("text", c.get("snippet", c.get("context", "")))) 
            for c in candidates
        )
        
        for candidate in sorted_candidates:
            text = candidate.get("text", candidate.get("snippet", candidate.get("context", "")))
            tokens = count_tokens(text)
            
            if total_tokens + tokens <= self.max_tokens:
                selected.append(candidate)
                total_tokens += tokens
            else:
                # Try to add partial if it's highly relevant
                if candidate.get("relevance", 0) > 0.8 and tokens > 0:
                    # Truncate to fit remaining budget
                    remaining = self.max_tokens - total_tokens
                    if remaining > 50:  # Only if we can add meaningful content
                        truncated = self._truncate_text(text, remaining)
                        candidate["text"] = truncated
                        candidate["truncated"] = True
                        selected.append(candidate)
                        total_tokens += remaining
                        self.stats["overflow_count"] += 1
                break
        
        # Update stats
        self.stats["avg_tokens"] = (
            (self.stats["avg_tokens"] * (self.stats["calls"] - 1) + total_tokens) / 
            self.stats["calls"]
        )
        
        logger.debug(f"Token pruner: kept {len(selected)}/{len(candidates)} candidates "
                    f"({total_tokens}/{self.max_tokens} tokens)")
        
        return selected
    
    def _truncate_text(self, text: str, target_tokens: int) -> str:
        """Truncate text to approximate token count"""
        words = text.split()
        # Rough estimate: 1 token ≈ 0.75 words
        target_words = int(target_tokens * 0.75)
        
        if len(words) <= target_words:
            return text
        
        truncated = " ".join(words[:target_words])
        return truncated + "..."
    
    def get_stats(self) -> Dict[str, Any]:
        return self.stats