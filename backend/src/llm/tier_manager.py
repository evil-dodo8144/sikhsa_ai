"""
Tier Management for Student Plans
Location: backend/src/llm/tier_manager.py
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from ..utils.logger import get_logger

logger = get_logger(__name__)

class TierManager:
    """
    Manages student tiers and usage limits
    """
    
    def __init__(self):
        self.tiers = {
            "free": {
                "max_queries_per_day": 20,
                "max_tokens_per_query": 1000,
                "max_daily_cost": 0.02,
                "allowed_models": ["local", "gpt-3.5-turbo"],
                "rate_limit": 5,  # queries per minute
                "features": ["basic_qa", "textbook_access"]
            },
            "basic": {
                "max_queries_per_day": 100,
                "max_tokens_per_query": 2000,
                "max_daily_cost": 0.10,
                "allowed_models": ["local", "gpt-3.5-turbo", "claude-instant"],
                "rate_limit": 20,
                "features": ["basic_qa", "textbook_access", "practice_questions"]
            },
            "premium": {
                "max_queries_per_day": 500,
                "max_tokens_per_query": 4000,
                "max_daily_cost": 0.50,
                "allowed_models": ["local", "gpt-3.5-turbo", "gpt-4", "claude-instant"],
                "rate_limit": 60,
                "features": ["basic_qa", "textbook_access", "practice_questions", 
                           "personalized_tutoring", "progress_tracking"]
            },
            "enterprise": {
                "max_queries_per_day": 5000,
                "max_tokens_per_query": 8000,
                "max_daily_cost": 5.00,
                "allowed_models": ["local", "gpt-3.5-turbo", "gpt-4", "claude-instant"],
                "rate_limit": 200,
                "features": ["all_features", "priority_support", "custom_models", 
                           "analytics_dashboard", "api_access"]
            }
        }
        
        # Track usage per student
        self.usage = {}
        
    def get_budget(self, tier: str = "free") -> Dict[str, Any]:
        """Get budget constraints for tier"""
        return self.tiers.get(tier, self.tiers["free"])
    
    def check_limits(self, student_id: str, tier: str = "free") -> Dict[str, Any]:
        """
        Check if student has exceeded limits
        """
        tier_config = self.get_budget(tier)
        
        # Get today's usage
        today = datetime.now().date().isoformat()
        usage_key = f"{student_id}:{today}"
        
        if usage_key not in self.usage:
            return {
                "allowed": True,
                "queries_used": 0,
                "queries_remaining": tier_config["max_queries_per_day"],
                "cost_used": 0,
                "cost_remaining": tier_config["max_daily_cost"]
            }
        
        usage = self.usage[usage_key]
        
        queries_used = usage.get("queries", 0)
        cost_used = usage.get("cost", 0)
        
        return {
            "allowed": (queries_used < tier_config["max_queries_per_day"] and 
                       cost_used < tier_config["max_daily_cost"]),
            "queries_used": queries_used,
            "queries_remaining": max(0, tier_config["max_queries_per_day"] - queries_used),
            "cost_used": cost_used,
            "cost_remaining": max(0, tier_config["max_daily_cost"] - cost_used)
        }
    
    def record_usage(self, student_id: str, tier: str, cost: float) -> None:
        """
        Record usage for a student
        """
        today = datetime.now().date().isoformat()
        usage_key = f"{student_id}:{today}"
        
        if usage_key not in self.usage:
            self.usage[usage_key] = {"queries": 0, "cost": 0.0}
        
        self.usage[usage_key]["queries"] += 1
        self.usage[usage_key]["cost"] += cost
        
        logger.debug(f"Recorded usage for {student_id}: {self.usage[usage_key]}")
    
    def get_features(self, tier: str) -> List[str]:
        """Get features available for tier"""
        return self.tiers.get(tier, self.tiers["free"]).get("features", [])
    
    def can_use_model(self, model: str, tier: str) -> bool:
        """Check if tier can use specific model"""
        allowed = self.tiers.get(tier, self.tiers["free"]).get("allowed_models", [])
        return model in allowed