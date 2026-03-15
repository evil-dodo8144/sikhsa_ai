"""API package"""
from .routes import router
from .middleware import setup_middleware
from .validators import validate_query, validate_student
from .serializers import serialize_response

__all__ = ['router', 'setup_middleware', 'validate_query', 'validate_student', 'serialize_response']