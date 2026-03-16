"""
API Middleware
Location: backend/src/api/middleware.py
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Dict
import time
import uuid
from collections import defaultdict
from ..utils.logger import get_logger
from ..utils.metrics import MetricsCollector

logger = get_logger(__name__)
metrics = MetricsCollector()

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request
        logger.info(f"Request {request_id}: {request.method} {request.url.path}")
        
        # Track start time
        start_time = time.time()
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(f"Response {request_id}: {response.status_code} - {duration:.3f}s")
            
            # Track metrics
            metrics.track_request(
                endpoint=request.url.path,
                duration=duration,
                status_code=response.status_code
            )
            
            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            
            return response
            
        except Exception as e:
            logger.error(f"Error {request_id}: {str(e)}")
            duration = time.time() - start_time
            metrics.track_request(
                endpoint=request.url.path,
                duration=duration,
                status_code=500
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Clean old requests
        current_time = time.time()
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] 
            if current_time - t < 60
        ]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.calls_per_minute:
            from fastapi.responses import JSONResponse
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.calls_per_minute} requests per minute",
                    "retry_after": 60
                }
            )
        
        # Add current request
        self.requests[client_ip].append(current_time)
        
        # Process request
        return await call_next(request)


class CORSMiddleware(BaseHTTPMiddleware):
    """CORS middleware"""
    
    def __init__(self, app, allowed_origins=None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = self._get_origin(request)
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Max-Age"] = "3600"
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers
        response.headers["Access-Control-Allow-Origin"] = self._get_origin(request)
        response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response
    
    def _get_origin(self, request: Request) -> str:
        origin = request.headers.get("origin")
        if origin and (self.allowed_origins == ["*"] or origin in self.allowed_origins):
            return origin
        return self.allowed_origins[0] if self.allowed_origins else "*"


class MetricsMiddleware(BaseHTTPMiddleware):
    """Collect metrics for each request"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Track active requests
        metrics.track_active_requests(1)
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Track by endpoint and method
            metrics.track_endpoint(
                method=request.method,
                path=request.url.path,
                duration=duration,
                status=response.status_code
            )
            
            return response
            
        finally:
            metrics.track_active_requests(-1)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """Compress responses for slow connections"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Check if client accepts compression
        accept_encoding = request.headers.get("accept-encoding", "")
        
        if "gzip" in accept_encoding and len(response.body) > 1000:
            import gzip
            
            # Compress response
            compressed = gzip.compress(response.body)
            
            # Create new response with compressed body
            from fastapi.responses import Response
            compressed_response = Response(
                content=compressed,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            compressed_response.headers["Content-Encoding"] = "gzip"
            compressed_response.headers["Content-Length"] = str(len(compressed))
            
            logger.debug(f"Compressed response: {len(response.body)} -> {len(compressed)} bytes")
            return compressed_response
        
        return response


def setup_middleware(app):
    """Setup all middleware"""
    # Order matters - execute in this order
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CompressionMiddleware)
    app.add_middleware(CORSMiddleware, allowed_origins=["*"])
    app.add_middleware(RateLimitMiddleware, calls_per_minute=60)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    
    logger.info("All middleware configured")