"""
Metrics Collection
Location: backend/src/utils/metrics.py
"""

import time
from functools import wraps
from typing import Dict, Any
from collections import defaultdict
from datetime import datetime, timedelta

class MetricsCollector:
    """
    Collect performance metrics
    """
    
    def __init__(self):
        self.request_counts = defaultdict(int)
        self.request_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.response_times = []
        self.start_time = datetime.utcnow()
        
    def track_request(self, endpoint: str, duration: float, status_code: int) -> None:
        """
        Track a request
        """
        self.request_counts[endpoint] += 1
        self.request_times[endpoint].append(duration)
        self.response_times.append(duration)
        
        # Keep only last 1000 times
        if len(self.request_times[endpoint]) > 1000:
            self.request_times[endpoint] = self.request_times[endpoint][-1000:]
        
        if status_code >= 400:
            self.error_counts[endpoint] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get metrics summary
        """
        total_requests = sum(self.request_counts.values())
        total_errors = sum(self.error_counts.values())
        
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": (total_errors / total_requests * 100) if total_requests > 0 else 0,
            "avg_response_time_ms": avg_response_time * 1000,
            "requests_per_endpoint": dict(self.request_counts),
            "errors_per_endpoint": dict(self.error_counts),
            "uptime_seconds": uptime,
            "requests_per_second": total_requests / uptime if uptime > 0 else 0
        }

# Global metrics collector
_metrics = MetricsCollector()

def track_request(func):
    """Decorator to track request metrics"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            response = await func(*args, **kwargs)
            duration = time.time() - start
            _metrics.track_request(func.__name__, duration, 200)
            return response
        except Exception as e:
            duration = time.time() - start
            _metrics.track_request(func.__name__, duration, 500)
            raise
    return wrapper

def get_metrics() -> Dict[str, Any]:
    """Get current metrics"""
    return _metrics.get_summary()