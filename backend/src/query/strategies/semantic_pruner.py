"""
Semantic Similarity Pruning Strategy
Location: backend/src/query/strategies/semantic_pruner.py
"""

import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from ...utils.logger import get_logger

logger = get_logger(__name__)

class SemanticPruner:
    """
    Prunes context based on semantic similarity to query
    Uses embeddings to find most relevant content
    """
    
    def __init__(self, threshold: float = 0.3):
        self.threshold = threshold
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.stats = {"calls": 0, "avg_similarity": 0}
        
    async def prune(self, 
                   candidates: List[Dict[str, Any]], 
                   query: str,
                   grade: int,
                   intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Keep only candidates with semantic similarity above threshold
        """
        self.stats["calls"] += 1
        
        if not candidates:
            return []
        
        # Get query embedding
        query_emb = self.model.encode(query, normalize_embeddings=True)
        
        # Score each candidate
        scored_candidates = []
        similarities = []
        
        for candidate in candidates:
            # Get candidate embedding (use cached if available)
            candidate_emb = candidate.get("embedding")
            if candidate_emb is None:
                # Compute on the fly
                candidate_text = candidate.get("text", candidate.get("snippet", candidate.get("context", "")))
                if candidate_text:
                    candidate_emb = self.model.encode(candidate_text, normalize_embeddings=True)
                else:
                    continue
            
            # Compute cosine similarity
            similarity = np.dot(query_emb, candidate_emb)
            similarities.append(similarity)
            
            if similarity >= self.threshold:
                candidate["relevance"] = float(similarity)
                scored_candidates.append(candidate)
        
        # Update stats
        if similarities:
            self.stats["avg_similarity"] = (
                (self.stats["avg_similarity"] * (self.stats["calls"] - 1) + 
                 float(np.mean(similarities))) / self.stats["calls"]
            )
        
        logger.debug(f"Semantic pruner: kept {len(scored_candidates)}/{len(candidates)} "
                    f"candidates (threshold={self.threshold})")
        
        return scored_candidates
    
    def get_stats(self) -> Dict[str, Any]:
        return self.stats