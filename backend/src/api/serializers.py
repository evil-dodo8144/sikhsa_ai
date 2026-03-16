"""
Response Formatting and Serialization
Location: backend/src/api/serializers.py
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ResponseSerializer:
    """Handle response formatting"""
    
    @staticmethod
    def serialize_query_response(
        response: Dict[str, Any],
        student_grade: int,
        include_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        Format query response for student
        """
        formatted = {
            "response": response.get("text", ""),
            "timestamp": datetime.utcnow().isoformat(),
            "grade_level": student_grade
        }
        
        # Add sources if available
        if "sources" in response:
            formatted["sources"] = [
                {
                    "chapter": s.get("chapter"),
                    "page": s.get("page"),
                    "relevance": round(s.get("relevance", 0) * 100, 1),
                    "title": s.get("title", "")
                }
                for s in response["sources"][:3]  # Limit to top 3
            ]
        
        # Add suggestions for follow-up questions
        if "suggestions" in response:
            formatted["suggestions"] = response["suggestions"][:3]
        
        # Add metrics if requested
        if include_metrics and "metrics" in response:
            formatted["metrics"] = {
                "model_used": response.get("model", "unknown"),
                "confidence": round(response.get("confidence", 0.8) * 100, 1),
                "processing_time_ms": round(response.get("processing_time", 0) * 1000, 2),
                "tokens_used": response.get("tokens_used", 0)
            }
        
        # Add optimization metrics from ScaleDown
        if "optimization" in response:
            formatted["optimization"] = {
                "savings_percentage": round(response["optimization"].get("savings_percentage", 0), 1),
                "original_tokens": response["optimization"].get("original_tokens", 0),
                "optimized_tokens": response["optimization"].get("optimized_tokens", 0),
                "compression_level": response["optimization"].get("compression_level", "unknown")
            }
        
        # Add caching info
        if response.get("cached"):
            formatted["cached"] = True
        
        return formatted
    
    @staticmethod
    def serialize_error(
        error: str,
        code: int = 500,
        details: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Format error response
        """
        error_response = {
            "error": True,
            "message": error,
            "code": code,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if details:
            error_response["details"] = details
        
        return error_response
    
    @staticmethod
    def serialize_optimization_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format ScaleDown optimization result
        """
        return {
            "optimized_prompt": result.get("optimized_prompt", ""),
            "original_tokens": result.get("original_tokens", 0),
            "optimized_tokens": result.get("optimized_tokens", 0),
            "savings_percentage": round(result.get("savings_percentage", 0), 1),
            "processing_time_ms": result.get("processing_time_ms", 0),
            "model_used": result.get("model_used", "unknown"),
            "cached": result.get("cached", False),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def serialize_textbook(textbook: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format textbook data for frontend
        """
        return {
            "id": textbook.get("id", ""),
            "title": textbook.get("title", ""),
            "subject": textbook.get("subject", ""),
            "grade": textbook.get("grade", 0),
            "total_pages": textbook.get("total_pages", 0),
            "chapters": [
                {
                    "id": ch.get("id"),
                    "title": ch.get("title"),
                    "page_start": ch.get("page_start"),
                    "page_end": ch.get("page_end"),
                    "sections": len(ch.get("sections", []))
                }
                for ch in textbook.get("chapters", [])
            ],
            "last_updated": textbook.get("updated_at", datetime.utcnow().isoformat())
        }
    
    @staticmethod
    def serialize_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format metrics for dashboard
        """
        return {
            "queries": {
                "total": metrics.get("total_queries", 0),
                "today": metrics.get("queries_today", 0),
                "average_per_day": metrics.get("avg_queries_per_day", 0)
            },
            "performance": {
                "average_response_time_ms": round(metrics.get("avg_response_time", 0) * 1000, 2),
                "p95_response_time_ms": round(metrics.get("p95_response_time", 0) * 1000, 2),
                "cache_hit_rate": round(metrics.get("cache_hit_rate", 0), 1)
            },
            "cost_savings": {
                "total_tokens_saved": metrics.get("total_tokens_saved", 0),
                "estimated_cost_saved_usd": round(metrics.get("estimated_cost_saved", 0), 4),
                "average_savings_percentage": round(metrics.get("avg_savings", 0), 1)
            },
            "models": metrics.get("model_usage", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def serialize_health(status: str, services: Dict[str, str]) -> Dict[str, Any]:
        """
        Format health check response
        """
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "services": services,
            "uptime": services.get("uptime", 0)
        }
    
    @staticmethod
    def serialize_student(student: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format student data
        """
        return {
            "student_id": student.get("student_id"),
            "name": student.get("name", ""),
            "grade": student.get("grade"),
            "tier": student.get("tier", "free"),
            "preferences": student.get("preferences", {}),
            "stats": {
                "total_queries": student.get("total_queries", 0),
                "queries_today": student.get("queries_today", 0),
                "total_tokens_saved": student.get("total_tokens_saved", 0)
            },
            "joined_at": student.get("created_at", datetime.utcnow().isoformat())
        }


# Convenience functions
def serialize_response(*args, **kwargs):
    """Convenience function for response serialization"""
    return ResponseSerializer.serialize_query_response(*args, **kwargs)


def serialize_error(*args, **kwargs):
    """Convenience function for error serialization"""
    return ResponseSerializer.serialize_error(*args, **kwargs)


def serialize_optimization(*args, **kwargs):
    """Convenience function for optimization serialization"""
    return ResponseSerializer.serialize_optimization_result(*args, **kwargs)


class PaginatedResponse:
    """Helper for paginated responses"""
    
    @staticmethod
    def create(
        items: List[Any],
        total: int,
        page: int,
        page_size: int,
        serializer: callable
    ) -> Dict[str, Any]:
        """
        Create paginated response
        """
        return {
            "items": [serializer(item) for item in items],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": (total + page_size - 1) // page_size,
                "has_next": page * page_size < total,
                "has_previous": page > 1
            },
            "timestamp": datetime.utcnow().isoformat()
        }


# Example usage in routes.py:
"""
from .serializers import serialize_response, serialize_error, PaginatedResponse

@router.post("/query")
async def process_query(request: Request):
    try:
        result = await process_query_internal(request)
        return serialize_response(result, grade=7, include_metrics=True)
    except Exception as e:
        return serialize_error(str(e), code=500)
"""