"""
Main Context Pruning Engine
Location: backend/src/query/context_pruner.py
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .strategies.semantic_pruner import SemanticPruner
from .strategies.grade_pruner import GradePruner
from .strategies.token_pruner import TokenPruner
from .strategies.recency_pruner import RecencyPruner
from .pruner_factory import PrunerFactory
from ..indexing.multi_level_index import MultiLevelIndex
from ..cache.embedding_cache import EmbeddingCache
from ..utils.logger import get_logger
from ..utils.text_utils import count_tokens
from ..config.settings import config

logger = get_logger(__name__)

@dataclass
class PruningResult:
    """Result of context pruning"""
    text: str
    chapters_used: List[str]
    concepts_used: List[str]
    relevance_scores: Dict[str, float]
    token_count: int
    pruning_stats: Dict[str, Any]

class ContextPruner:
    """
    Multi-stage pruning system that progressively narrows down context
    Achieves 80-95% reduction in context size
    """
    
    def __init__(self):
        self.index = MultiLevelIndex()
        self.embedding_cache = EmbeddingCache()
        
        # Initialize pruners
        self.pruners = [
            SemanticPruner(threshold=config.SEMANTIC_THRESHOLD),
            GradePruner(tolerance=config.GRADE_TOLERANCE),
            TokenPruner(max_tokens=config.MAX_CONTEXT_TOKENS),
            RecencyPruner(decay_factor=config.RECENCY_DECAY)
        ]
        
        # Pruning statistics
        self.stats = {
            "total_pruned": 0,
            "avg_reduction": 0,
            "cache_hits": 0
        }
        
    async def prune(self, 
                   query: str,
                   grade: int,
                   subject: str,
                   intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Progressive context pruning pipeline
        
        Args:
            query: Student's question
            grade: Student's grade level
            subject: Subject area
            intent: Classified intent of query
            
        Returns:
            Pruned context dictionary
        """
        logger.info(f"Pruning context for query: {query[:50]}...")
        
        # Check embedding cache
        query_embedding = await self.embedding_cache.get_or_compute(query)
        
        # Stage 1: Broad retrieval (all potentially relevant content)
        candidates = await self.index.retrieve_candidates(
            query=query,
            query_embedding=query_embedding,
            subject=subject,
            limit=100  # Start broad
        )
        
        if not candidates:
            logger.warning("No candidates found for query")
            return {
                "text": "",
                "chapters_used": [],
                "concepts_used": [],
                "token_count": 0
            }
        
        # Track pruning stats
        original_count = len(candidates)
        original_tokens = sum(c.get("token_count", 0) for c in candidates)
        
        # Apply pruners in sequence
        pruned = candidates
        pruning_stats = {}
        
        for i, pruner in enumerate(self.pruners):
            stage_before = len(pruned)
            pruned = await pruner.prune(pruned, query, grade, intent)
            stage_after = len(pruned)
            
            pruning_stats[f"stage_{i}_{pruner.__class__.__name__}"] = {
                "before": stage_before,
                "after": stage_after,
                "reduction": ((stage_before - stage_after) / stage_before * 100) if stage_before > 0 else 0
            }
        
        # Extract final context
        final_text = self._extract_text(pruned)
        final_tokens = count_tokens(final_text)
        
        # Compile result
        result = {
            "text": final_text,
            "chapters_used": list(set(c.get("chapter_id") for c in pruned if c.get("chapter_id"))),
            "concepts_used": list(set(c.get("concept") for c in pruned if c.get("concept"))),
            "relevance_scores": {c.get("id"): c.get("relevance", 0) for c in pruned},
            "token_count": final_tokens,
            "pruning_stats": {
                **pruning_stats,
                "overall": {
                    "original_candidates": original_count,
                    "final_candidates": len(pruned),
                    "original_tokens": original_tokens,
                    "final_tokens": final_tokens,
                    "reduction_percentage": ((original_tokens - final_tokens) / original_tokens * 100) if original_tokens > 0 else 0
                }
            }
        }
        
        # Update stats
        self.stats["total_pruned"] += 1
        self.stats["avg_reduction"] = (
            (self.stats["avg_reduction"] * (self.stats["total_pruned"] - 1) + 
             result["pruning_stats"]["overall"]["reduction_percentage"]) / 
            self.stats["total_pruned"]
        )
        
        logger.info(f"Pruning complete. Reduced from {original_tokens} to {final_tokens} tokens "
                   f"({result['pruning_stats']['overall']['reduction_percentage']:.1f}% reduction)")
        
        return result
    
    def _extract_text(self, candidates: List[Dict]) -> str:
        """Extract and combine text from candidates"""
        # Sort by relevance
        sorted_candidates = sorted(candidates, key=lambda x: x.get("relevance", 0), reverse=True)
        
        # Extract text snippets
        texts = []
        for c in sorted_candidates:
            if "text" in c:
                texts.append(c["text"])
            elif "snippet" in c:
                texts.append(c["snippet"])
            elif "context" in c:
                texts.append(c["context"])
        
        return "\n\n".join(texts)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pruning statistics"""
        return {
            **self.stats,
            "pruner_stats": {p.__class__.__name__: p.get_stats() for p in self.pruners}
        }