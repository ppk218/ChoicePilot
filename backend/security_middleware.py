import time
import hashlib
import logging
from fastapi import HTTPException, status, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, List
import re
import json
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware for rate limiting, input sanitization, and monitoring"""
    
    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis_client = redis_client
        # In-memory rate limiting for now (use Redis in production)
        self.rate_limiter = InMemoryRateLimiter()
        self.security_logger = SecurityLogger()
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            # 1. Rate Limiting
            await self._check_rate_limits(request)
            
            # 2. Input Sanitization
            await self._sanitize_input(request)
            
            # 3. Security Headers
            response = await call_next(request)
            self._add_security_headers(response)
            
            # 4. Log security events
            process_time = time.time() - start_time
            await self._log_request(request, response, process_time)
            
            return response
            
        except HTTPException as e:
            # Log security violations
            await self._log_security_violation(request, e)
            raise
        except Exception as e:
            # Log unexpected errors
            await self._log_error(request, e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    async def _check_rate_limits(self, request: Request):
        """Check various rate limits"""
        client_ip = self._get_client_ip(request)
        
        # Different rate limits for different endpoints
        if request.url.path.startswith('/api/chat'):
            # LLM endpoints - stricter limits
            await self.rate_limiter.check_limit(
                key=f"chat:{client_ip}",
                limit=30,  # 30 requests per hour
                window=3600
            )
        elif request.url.path.startswith('/api/auth'):
            # Auth endpoints - prevent brute force
            await self.rate_limiter.check_limit(
                key=f"auth:{client_ip}",
                limit=10,  # 10 attempts per 15 minutes
                window=900
            )
        elif request.url.path.startswith('/api/payments'):
            # Payment endpoints - very strict
            await self.rate_limiter.check_limit(
                key=f"payments:{client_ip}",
                limit=5,  # 5 requests per hour
                window=3600
            )
        else:
            # General API rate limit
            await self.rate_limiter.check_limit(
                key=f"general:{client_ip}",
                limit=100,  # 100 requests per hour
                window=3600
            )
    
    async def _sanitize_input(self, request: Request):
        """Sanitize inputs to prevent injection attacks"""
        if request.method in ["POST", "PUT", "PATCH"]:
            # Read and validate request body
            body = await request.body()
            if body:
                try:
                    data = json.loads(body)
                    self._sanitize_data(data)
                    
                    # Rebuild request with sanitized data
                    request._body = json.dumps(data).encode()
                except json.JSONDecodeError:
                    # Not JSON, check for other dangerous content
                    body_str = body.decode('utf-8', errors='ignore')
                    if self._contains_dangerous_patterns(body_str):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid input detected"
                        )
    
    def _sanitize_data(self, data):
        """Recursively sanitize data structure"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = self._sanitize_string(value)
                elif isinstance(value, (dict, list)):
                    self._sanitize_data(value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, str):
                    data[i] = self._sanitize_string(item)
                elif isinstance(item, (dict, list)):
                    self._sanitize_data(item)
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize individual strings"""
        if not text:
            return text
        
        # Remove potential prompt injection patterns
        dangerous_patterns = [
            r'(?i)ignore\s+previous\s+instructions',
            r'(?i)system\s*:',
            r'(?i)assistant\s*:',
            r'(?i)human\s*:',
            r'(?i)you\s+are\s+now',
            r'(?i)forget\s+everything',
            r'(?i)new\s+instructions',
            r'(?i)jailbreak',
            r'(?i)roleplay\s+as',
            r'</?\w+[^>]*>',  # HTML tags
            r'javascript:',   # JavaScript URLs
            r'data:text/html', # Data URLs
        ]
        
        for pattern in dangerous_patterns:
            text = re.sub(pattern, '[FILTERED]', text)
        
        # Limit length to prevent buffer overflow
        if len(text) > 10000:
            text = text[:10000] + "... [TRUNCATED]"
        
        return text.strip()
    
    def _contains_dangerous_patterns(self, text: str) -> bool:
        """Check for dangerous patterns in text"""
        dangerous_patterns = [
            r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'eval\s*\(',
            r'setTimeout\s*\(',
            r'setInterval\s*\(',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def _log_request(self, request: Request, response: Response, process_time: float):
        """Log all requests for monitoring"""
        await self.security_logger.log_request({
            "timestamp": datetime.utcnow().isoformat(),
            "ip": self._get_client_ip(request),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time": process_time,
            "user_agent": request.headers.get("User-Agent", ""),
        })
    
    async def _log_security_violation(self, request: Request, exception: HTTPException):
        """Log security violations"""
        await self.security_logger.log_security_event({
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "security_violation",
            "ip": self._get_client_ip(request),
            "path": request.url.path,
            "method": request.method,
            "error": str(exception.detail),
            "status_code": exception.status_code,
            "user_agent": request.headers.get("User-Agent", ""),
        })
    
    async def _log_error(self, request: Request, exception: Exception):
        """Log unexpected errors"""
        await self.security_logger.log_error({
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "system_error",
            "ip": self._get_client_ip(request),
            "path": request.url.path,
            "method": request.method,
            "error": str(exception),
            "user_agent": request.headers.get("User-Agent", ""),
        })

class InMemoryRateLimiter:
    """In-memory rate limiter (use Redis in production)"""
    
    def __init__(self):
        self.requests = {}
        self.lock = asyncio.Lock()
    
    async def check_limit(self, key: str, limit: int, window: int):
        """Check if request is within rate limit"""
        async with self.lock:
            now = time.time()
            
            # Clean up old entries
            if key in self.requests:
                self.requests[key] = [
                    timestamp for timestamp in self.requests[key]
                    if now - timestamp < window
                ]
            else:
                self.requests[key] = []
            
            # Check limit
            if len(self.requests[key]) >= limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again later."
                )
            
            # Add current request
            self.requests[key].append(now)

class SecurityLogger:
    """Security event logger"""
    
    def __init__(self):
        self.logger = logging.getLogger("security")
        handler = logging.FileHandler("/tmp/security.log")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    async def log_request(self, data: dict):
        """Log general requests"""
        self.logger.info(f"REQUEST: {json.dumps(data)}")
    
    async def log_security_event(self, data: dict):
        """Log security events"""
        self.logger.warning(f"SECURITY: {json.dumps(data)}")
    
    async def log_error(self, data: dict):
        """Log errors"""
        self.logger.error(f"ERROR: {json.dumps(data)}")

class CORSSecurityMiddleware:
    """Enhanced CORS configuration with security"""
    
    @staticmethod
    def get_cors_config():
        """Get secure CORS configuration"""
        return {
            "allow_origins": [
                "https://a3afc75c-858c-4f4f-b1c5-cd9fc2d2bc83.preview.emergentagent.com",
                "http://localhost:3000",  # Development only
            ],
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": [
                "Authorization",
                "Content-Type",
                "X-Requested-With",
                "Accept",
                "Origin",
                "Access-Control-Request-Method",
                "Access-Control-Request-Headers",
            ],
            "expose_headers": ["Content-Disposition"],
        }