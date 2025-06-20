from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
import time
import logging

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for FastAPI"""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and add security headers"""
        # Record start time
        start_time = time.time()
        
        # Process the request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'"
        
        # Log request processing time
        process_time = time.time() - start_time
        logger.debug(f"Request {request.method} {request.url.path} processed in {process_time:.4f} seconds")
        
        return response

class CORSSecurityMiddleware(CORSMiddleware):
    """Enhanced CORS middleware with security features"""
    
    def __init__(self, app, **options):
        """Initialize with secure defaults"""
        # Set secure defaults
        secure_options = {
            "allow_origins": options.get("allow_origins", ["*"]),
            "allow_methods": options.get("allow_methods", ["GET", "POST", "PUT", "DELETE", "OPTIONS"]),
            "allow_headers": options.get("allow_headers", ["*"]),
            "allow_credentials": options.get("allow_credentials", True),
            "expose_headers": options.get("expose_headers", []),
            "max_age": options.get("max_age", 600)  # 10 minutes
        }
        
        super().__init__(app, **secure_options)