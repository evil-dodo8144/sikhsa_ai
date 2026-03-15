"""
Cost Tracking for LLM Usage
Location: backend/src/llm/cost_tracker.py
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict
from ..utils.logger import get_logger

logger = get_logger(__name__)

class CostTracker:
    """
    Track API costs across models and students
    """
    
    def __init__(self):
        self.usage_log = []
        self.daily_totals = defaultdict(float)
        self.model_totals = defaultdict(float)
        self.student_totals = defaultdict(float)
        
    def track(self, model: str, tokens: int, cost: float, student_tier: str) -> None:
        """
        Track a usage event
        """
        today = datetime.now().date().isoformat()
        
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "model": model,
            "tokens": tokens,
            "cost": cost,
            "student_tier": student_tier,
            "date": today
        }
        
        self.usage_log.append(event)
        self.daily_totals[today] += cost
        self.model_totals[model] += cost
        
        # Keep only last 10000 events
        if len(self.usage_log) > 10000:
            self.usage_log = self.usage_log[-10000:]
        
        logger.debug(f"Tracked cost: ${cost:.4f} for {model}")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get cost summary
        """
        today = datetime.now().date().isoformat()
        
        # Calculate totals
        total_cost = sum(e["cost"] for e in self.usage_log)
        total_tokens = sum(e["tokens"] for e in self.usage_log)
        
        # Get today's cost
        today_cost = self.daily_totals.get(today, 0)
        
        # Get last 30 days
        last_30_days = 0
        cutoff = (datetime.now() - timedelta(days=30)).date().isoformat()
        for date, cost in self.daily_totals.items():
            if date >= cutoff:
                last_30_days += cost
        
        return {
            "total_cost_usd": total_cost,
            "total_tokens": total_tokens,
            "average_cost_per_token": total_cost / total_tokens if total_tokens > 0 else 0,
            "today_cost_usd": today_cost,
            "last_30_days_cost_usd": last_30_days,
            "by_model": dict(self.model_totals),
            "total_queries": len(self.usage_log),
            "estimated_monthly_projection": today_cost * 30
        }
    
    def get_student_summary(self, student_id: str) -> Dict[str, Any]:
        """
        Get cost summary for specific student
        """
        student_events = [e for e in self.usage_log if e.get("student_id") == student_id]
        
        if not student_events:
            return {"total_cost": 0, "total_queries": 0}
        
        total_cost = sum(e["cost"] for e in student_events)
        total_tokens = sum(e["tokens"] for e in student_events)
        
        return {
            "total_cost_usd": total_cost,
            "total_tokens": total_tokens,
            "total_queries": len(student_events),
            "average_cost_per_query": total_cost / len(student_events) if student_events else 0
        }