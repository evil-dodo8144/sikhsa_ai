"""
Grade-Level Pruning Strategy
Location: backend/src/query/strategies/grade_pruner.py
"""

from typing import List, Dict, Any
from ...utils.logger import get_logger

logger = get_logger(__name__)

class GradePruner:
    """
    Prunes content based on student's grade level
    Keeps content appropriate for student's level
    """
    
    def __init__(self, tolerance: int = 1):
        self.tolerance = tolerance  # How many grades above/below to include
        self.stats = {"calls": 0, "avg_grade_diff": 0}
        
    async def prune(self,
                   candidates: List[Dict[str, Any]],
                   query: str,
                   grade: int,
                   intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Keep only candidates within grade tolerance
        """
        self.stats["calls"] += 1
        
        if not candidates:
            return []
        
        filtered = []
        grade_diffs = []
        
        for candidate in candidates:
            candidate_grade = candidate.get("grade_level", grade)
            
            # Calculate grade difference
            grade_diff = abs(candidate_grade - grade)
            grade_diffs.append(grade_diff)
            
            # Check if within tolerance
            if grade_diff <= self.tolerance:
                candidate["grade_difference"] = grade_diff
                filtered.append(candidate)
        
        # Update stats
        if grade_diffs:
            self.stats["avg_grade_diff"] = (
                (self.stats["avg_grade_diff"] * (self.stats["calls"] - 1) + 
                 sum(grade_diffs) / len(grade_diffs)) / self.stats["calls"]
            )
        
        logger.debug(f"Grade pruner: kept {len(filtered)}/{len(candidates)} "
                    f"candidates (grade={grade}, tolerance={self.tolerance})")
        
        return filtered
    
    def get_stats(self) -> Dict[str, Any]:
        return self.stats