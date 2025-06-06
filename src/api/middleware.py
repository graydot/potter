#!/usr/bin/env python3
"""
Middleware System
Pluggable request/response processing for API Gateway
"""

import logging
import time
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod

from .request_handler import APIRequest, APIResponse, HTTPStatus

logger = logging.getLogger(__name__)


class Middleware(ABC):
    """
    Abstract base class for middleware components
    
    Middleware can process requests before they reach handlers
    and responses before they're returned to clients.
    """
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"middleware.{self.name.lower()}")
    
    async def process_request(self, request: APIRequest) -> Optional[APIResponse]:
        """
        Process incoming request
        
        Args:
            request: APIRequest object
            
        Returns:
            None to continue processing, APIResponse to short-circuit
        """
        return None
    
    async def process_response(self, request: APIRequest, response: APIResponse) -> APIResponse:
        """
        Process outgoing response
        
        Args:
            request: Original APIRequest
            response: APIResponse to process
            
        Returns:
            Modified APIResponse
        """
        return response


class MiddlewareStack:
    """
    Manages a stack of middleware components
    
    Processes requests through middleware in order,
    and responses in reverse order.
    """
    
    def __init__(self):
        self.middleware: List[Middleware] = []
        self.logger = logging.getLogger("middleware.stack")
    
    def add(self, middleware: Middleware):
        """Add middleware to the stack"""
        self.middleware.append(middleware)
        self.logger.debug(f"Added middleware: {middleware.name}")
    
    def remove(self, middleware_name: str) -> bool:
        """Remove middleware by name"""
        for i, middleware in enumerate(self.middleware):
            if middleware.name == middleware_name:
                removed = self.middleware.pop(i)
                self.logger.debug(f"Removed middleware: {removed.name}")
                return True
        return False
    
    async def process_request(self, request: APIRequest) -> Optional[APIResponse]:
        """Process request through middleware stack"""
        for middleware in self.middleware:
            try:
                result = await middleware.process_request(request)
                if result is not None:
                    self.logger.debug(f"Middleware {middleware.name} short-circuited request")
                    return result
            except Exception as e:
                self.logger.error(f"Error in middleware {middleware.name}: {e}")
                return APIResponse(
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                    error=f"Middleware error: {e}",
                    error_code="MIDDLEWARE_ERROR",
                    correlation_id=request.correlation_id
                )
        return None
    
    async def process_response(self, request: APIRequest, response: APIResponse) -> APIResponse:
        """Process response through middleware stack (in reverse order)"""
        for middleware in reversed(self.middleware):
            try:
                response = await middleware.process_response(request, response)
            except Exception as e:
                self.logger.error(f"Error in middleware {middleware.name} response processing: {e}")
                # Don't break the response, just log the error
        return response
    
    def get_middleware_info(self) -> List[Dict[str, str]]:
        """Get information about registered middleware"""
        return [
            {
                'name': middleware.name,
                'type': middleware.__class__.__name__
            }
            for middleware in self.middleware
        ]


class AuthenticationMiddleware(Middleware):
    """
    Authentication middleware
    
    Validates authentication tokens and populates user context.
    """
    
    def __init__(self, required_endpoints: List[str] = None):
        super().__init__("Authentication")
        self.required_endpoints = required_endpoints or []
        self.auth_cache = {}  # Simple cache for validated tokens
    
    async def process_request(self, request: APIRequest) -> Optional[APIResponse]:
        """Validate authentication for protected endpoints"""
        # Check if endpoint requires authentication
        if self.required_endpoints and request.endpoint not in self.required_endpoints:
            return None
        
        # Get authorization header
        auth_header = request.get_header('Authorization')
        if not auth_header:
            return APIResponse(
                status=HTTPStatus.UNAUTHORIZED,
                error="Missing authentication token",
                error_code="MISSING_AUTH",
                correlation_id=request.correlation_id
            )
        
        # Validate token (simplified implementation)
        token = auth_header.replace('Bearer ', '')
        user_id = await self._validate_token(token)
        
        if not user_id:
            return APIResponse(
                status=HTTPStatus.UNAUTHORIZED,
                error="Invalid authentication token",
                error_code="INVALID_AUTH",
                correlation_id=request.correlation_id
            )
        
        # Set user context
        request.user_id = user_id
        self.logger.debug(f"Authenticated user: {user_id}")
        
        return None
    
    async def _validate_token(self, token: str) -> Optional[str]:
        """Validate authentication token"""
        # Check cache first
        if token in self.auth_cache:
            return self.auth_cache[token]
        
        # TODO: Implement real token validation
        # For now, accept any non-empty token and extract user ID
        if token and len(token) > 10:
            user_id = f"user_{token[:8]}"
            self.auth_cache[token] = user_id
            return user_id
        
        return None


class RateLimitingMiddleware(Middleware):
    """
    Rate limiting middleware
    
    Limits the number of requests per user/IP within a time window.
    """
    
    def __init__(self, requests_per_minute: int = 60, window_minutes: int = 1):
        super().__init__("RateLimiting")
        self.requests_per_minute = requests_per_minute
        self.window_minutes = window_minutes
        self.request_counts = {}  # Simple in-memory rate limiting
    
    async def process_request(self, request: APIRequest) -> Optional[APIResponse]:
        """Check rate limits"""
        # Determine rate limit key (user ID or IP)
        rate_key = request.user_id or request.client_ip or 'anonymous'
        
        # Get current time window
        current_window = int(time.time() / (self.window_minutes * 60))
        
        # Initialize or update request count
        if rate_key not in self.request_counts:
            self.request_counts[rate_key] = {}
        
        # Clean old windows
        old_windows = [w for w in self.request_counts[rate_key].keys() if w < current_window]
        for old_window in old_windows:
            del self.request_counts[rate_key][old_window]
        
        # Count requests in current window
        current_count = self.request_counts[rate_key].get(current_window, 0)
        
        if current_count >= self.requests_per_minute:
            # Create a custom 429 status since it's not in our enum
            from .request_handler import HTTPStatus
            try:
                too_many_requests = HTTPStatus.TOO_MANY_REQUESTS
            except AttributeError:
                # Fallback if not defined
                too_many_requests = HTTPStatus.BAD_REQUEST
            
            return APIResponse(
                status=too_many_requests,
                error="Rate limit exceeded",
                error_code="RATE_LIMIT_EXCEEDED",
                correlation_id=request.correlation_id,
                headers={
                    'X-RateLimit-Limit': str(self.requests_per_minute),
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': str((current_window + 1) * self.window_minutes * 60)
                }
            )
        
        # Increment request count
        self.request_counts[rate_key][current_window] = current_count + 1
        
        return None
    
    async def process_response(self, request: APIRequest, response: APIResponse) -> APIResponse:
        """Add rate limit headers to response"""
        rate_key = request.user_id or request.client_ip or 'anonymous'
        current_window = int(time.time() / (self.window_minutes * 60))
        
        current_count = 0
        if rate_key in self.request_counts and current_window in self.request_counts[rate_key]:
            current_count = self.request_counts[rate_key][current_window]
        
        response.add_header('X-RateLimit-Limit', str(self.requests_per_minute))
        response.add_header('X-RateLimit-Remaining', str(max(0, self.requests_per_minute - current_count)))
        response.add_header('X-RateLimit-Reset', str((current_window + 1) * self.window_minutes * 60))
        
        return response


class ValidationMiddleware(Middleware):
    """
    Request validation middleware
    
    Validates request data against schemas and business rules.
    """
    
    def __init__(self, validation_service=None):
        super().__init__("Validation")
        self.validation_service = validation_service
        self.validation_rules = {}
    
    def add_validation_rule(self, endpoint: str, rule: Dict[str, Any]):
        """Add validation rule for an endpoint"""
        self.validation_rules[endpoint] = rule
    
    async def process_request(self, request: APIRequest) -> Optional[APIResponse]:
        """Validate request data"""
        # Check if endpoint has validation rules
        if request.endpoint not in self.validation_rules:
            return None
        
        rule = self.validation_rules[request.endpoint]
        
        # Validate required fields
        required_fields = rule.get('required_fields', [])
        for field in required_fields:
            if field not in request.data:
                return APIResponse(
                    status=HTTPStatus.BAD_REQUEST,
                    error=f"Missing required field: {field}",
                    error_code="MISSING_FIELD",
                    correlation_id=request.correlation_id
                )
        
        # Validate field types
        field_types = rule.get('field_types', {})
        for field, expected_type in field_types.items():
            if field in request.data:
                if not isinstance(request.data[field], expected_type):
                    return APIResponse(
                        status=HTTPStatus.BAD_REQUEST,
                        error=f"Invalid type for field {field}: expected {expected_type.__name__}",
                        error_code="INVALID_TYPE",
                        correlation_id=request.correlation_id
                    )
        
        # Use validation service if available
        if self.validation_service:
            try:
                is_valid, error_message = self.validation_service.validate_request(request)
                if not is_valid:
                    return APIResponse(
                        status=HTTPStatus.BAD_REQUEST,
                        error=error_message,
                        error_code="VALIDATION_FAILED",
                        correlation_id=request.correlation_id
                    )
            except Exception as e:
                self.logger.error(f"Validation service error: {e}")
                return APIResponse(
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                    error="Validation error",
                    error_code="VALIDATION_ERROR",
                    correlation_id=request.correlation_id
                )
        
        return None


class LoggingMiddleware(Middleware):
    """
    Request/response logging middleware
    
    Logs detailed information about requests and responses.
    """
    
    def __init__(self, log_request_body: bool = False, log_response_body: bool = False):
        super().__init__("Logging")
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
    
    async def process_request(self, request: APIRequest) -> Optional[APIResponse]:
        """Log incoming request"""
        log_data = {
            'correlation_id': request.correlation_id,
            'method': request.method.value,
            'endpoint': request.endpoint,
            'user_id': request.user_id,
            'client_ip': request.client_ip,
            'user_agent': request.user_agent,
            'timestamp': request.timestamp
        }
        
        if self.log_request_body and request.data:
            log_data['request_body'] = request.data
        
        self.logger.info(f"Request received: {log_data}")
        return None
    
    async def process_response(self, request: APIRequest, response: APIResponse) -> APIResponse:
        """Log outgoing response"""
        log_data = {
            'correlation_id': response.correlation_id,
            'status': response.status.value,
            'processing_time': response.processing_time,
            'error': response.error,
            'error_code': response.error_code
        }
        
        if self.log_response_body and response.data:
            log_data['response_body'] = str(response.data)[:1000]  # Truncate for logs
        
        self.logger.info(f"Response sent: {log_data}")
        return response


class CORSMiddleware(Middleware):
    """
    CORS (Cross-Origin Resource Sharing) middleware
    
    Handles CORS preflight requests and adds CORS headers.
    """
    
    def __init__(self, allowed_origins: List[str] = None, allowed_methods: List[str] = None):
        super().__init__("CORS")
        self.allowed_origins = allowed_origins or ['*']
        self.allowed_methods = allowed_methods or ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    
    async def process_request(self, request: APIRequest) -> Optional[APIResponse]:
        """Handle CORS preflight requests"""
        if request.method.value == 'OPTIONS':
            return APIResponse(
                status=HTTPStatus.OK,
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': ', '.join(self.allowed_methods),
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                    'Access-Control-Max-Age': '86400'
                }
            )
        return None
    
    async def process_response(self, request: APIRequest, response: APIResponse) -> APIResponse:
        """Add CORS headers to response"""
        origin = request.get_header('Origin')
        
        if '*' in self.allowed_origins:
            response.add_header('Access-Control-Allow-Origin', '*')
        elif origin and origin in self.allowed_origins:
            response.add_header('Access-Control-Allow-Origin', origin)
        
        response.add_header('Access-Control-Allow-Methods', ', '.join(self.allowed_methods))
        response.add_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        
        return response 