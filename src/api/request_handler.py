#!/usr/bin/env python3
"""
Request Handler
Standardized request/response handling for API Gateway
"""

import logging
import time
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class HTTPMethod(Enum):
    """HTTP methods supported by the API"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class HTTPStatus(Enum):
    """HTTP status codes"""
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    SERVICE_UNAVAILABLE = 503


@dataclass
class APIRequest:
    """
    Standardized API request format
    
    Provides a unified structure for all API requests with:
    - Request metadata (method, endpoint, headers)
    - Request data and parameters
    - User context and authorization
    - Tracing and correlation information
    """
    method: HTTPMethod
    endpoint: str
    data: Dict[str, Any] = field(default_factory=dict)
    params: Dict[str, str] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    
    # User context
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Request tracking
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    
    # Request metadata
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        # Ensure method is HTTPMethod enum
        if isinstance(self.method, str):
            self.method = HTTPMethod(self.method.upper())
        
        # Generate correlation ID if not provided
        if not self.correlation_id:
            self.correlation_id = str(uuid.uuid4())
    
    def get_header(self, name: str, default: str = None) -> str:
        """Get header value (case-insensitive)"""
        for key, value in self.headers.items():
            if key.lower() == name.lower():
                return value
        return default
    
    def has_header(self, name: str) -> bool:
        """Check if header exists (case-insensitive)"""
        return any(key.lower() == name.lower() for key in self.headers.keys())
    
    def get_content_type(self) -> str:
        """Get content type from headers"""
        return self.get_header('Content-Type', 'application/json')
    
    def is_authenticated(self) -> bool:
        """Check if request has authentication information"""
        return self.user_id is not None or self.has_header('Authorization')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary for logging/serialization"""
        return {
            'method': self.method.value,
            'endpoint': self.endpoint,
            'params': self.params,
            'headers': {k: v for k, v in self.headers.items() if k.lower() not in ['authorization']},
            'user_id': self.user_id,
            'correlation_id': self.correlation_id,
            'timestamp': self.timestamp,
            'client_ip': self.client_ip,
            'user_agent': self.user_agent,
            'data_size': len(str(self.data)) if self.data else 0
        }


@dataclass
class APIResponse:
    """
    Standardized API response format
    
    Provides a unified structure for all API responses with:
    - Status and error information
    - Response data and metadata
    - Performance metrics
    - Correlation tracking
    """
    status: HTTPStatus
    data: Any = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Response metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    
    # Performance tracking
    processing_time: Optional[float] = None
    correlation_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Post-initialization processing"""
        # Ensure status is HTTPStatus enum
        if isinstance(self.status, int):
            try:
                self.status = HTTPStatus(self.status)
            except ValueError:
                self.status = HTTPStatus.INTERNAL_SERVER_ERROR
    
    def is_success(self) -> bool:
        """Check if response indicates success"""
        return 200 <= self.status.value < 300
    
    def is_error(self) -> bool:
        """Check if response indicates an error"""
        return self.status.value >= 400
    
    def is_client_error(self) -> bool:
        """Check if response indicates a client error (4xx)"""
        return 400 <= self.status.value < 500
    
    def is_server_error(self) -> bool:
        """Check if response indicates a server error (5xx)"""
        return self.status.value >= 500
    
    def add_header(self, name: str, value: str):
        """Add response header"""
        self.headers[name] = value
    
    def set_cache_control(self, max_age: int = None, no_cache: bool = False):
        """Set cache control headers"""
        if no_cache:
            self.add_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.add_header('Pragma', 'no-cache')
            self.add_header('Expires', '0')
        elif max_age is not None:
            self.add_header('Cache-Control', f'max-age={max_age}')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for serialization"""
        result = {
            'status': self.status.value,
            'data': self.data,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }
        
        if self.error:
            result['error'] = self.error
            
        if self.error_code:
            result['error_code'] = self.error_code
            
        if self.error_details:
            result['error_details'] = self.error_details
            
        if self.processing_time:
            result['processing_time'] = self.processing_time
            
        if self.correlation_id:
            result['correlation_id'] = self.correlation_id
        
        return result


class RequestHandler:
    """
    Unified request processing and routing
    
    Features:
    - Request validation and preprocessing
    - Route matching and parameter extraction
    - Request context management
    - Performance tracking
    - Error handling
    """
    
    def __init__(self):
        self.logger = logging.getLogger("api.request_handler")
        self.routes: Dict[str, Dict[str, Any]] = {}
        self.middleware_stack = []
        
        # Performance tracking
        self.request_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0
        }
    
    def register_route(self, method: HTTPMethod, path: str, handler, 
                      middleware: List[Any] = None):
        """
        Register an API route
        
        Args:
            method: HTTP method
            path: URL path pattern
            handler: Request handler function
            middleware: Route-specific middleware
        """
        route_key = f"{method.value}:{path}"
        self.routes[route_key] = {
            'method': method,
            'path': path,
            'handler': handler,
            'middleware': middleware or []
        }
        
        self.logger.debug(f"Registered route: {route_key}")
    
    def add_global_middleware(self, middleware):
        """Add middleware that applies to all routes"""
        self.middleware_stack.append(middleware)
        self.logger.debug(f"Added global middleware: {middleware.__class__.__name__}")
    
    async def handle_request(self, request: APIRequest) -> APIResponse:
        """
        Process an API request
        
        Args:
            request: APIRequest object
            
        Returns:
            APIResponse object
        """
        start_time = time.time()
        
        try:
            # Update metrics
            self.request_metrics['total_requests'] += 1
            
            # Log request
            self.logger.info(
                f"Processing request: {request.method.value} {request.endpoint} "
                f"[{request.correlation_id}]"
            )
            
            # Validate request
            validation_response = self._validate_request(request)
            if validation_response:
                return validation_response
            
            # Find matching route
            route = self._find_route(request)
            if not route:
                return APIResponse(
                    status=HTTPStatus.NOT_FOUND,
                    error=f"Route not found: {request.method.value} {request.endpoint}",
                    error_code="ROUTE_NOT_FOUND",
                    correlation_id=request.correlation_id
                )
            
            # Execute middleware chain
            middleware_response = await self._execute_middleware(request, route)
            if middleware_response:
                return middleware_response
            
            # Execute route handler
            response = await self._execute_handler(request, route)
            
            # Post-process response
            response.correlation_id = request.correlation_id
            response.processing_time = time.time() - start_time
            
            # Update metrics
            if response.is_success():
                self.request_metrics['successful_requests'] += 1
            else:
                self.request_metrics['failed_requests'] += 1
            
            # Update average response time
            total_requests = self.request_metrics['total_requests']
            current_avg = self.request_metrics['average_response_time']
            new_avg = ((current_avg * (total_requests - 1)) + response.processing_time) / total_requests
            self.request_metrics['average_response_time'] = new_avg
            
            self.logger.info(
                f"Request completed: {response.status.value} "
                f"({response.processing_time:.3f}s) [{request.correlation_id}]"
            )
            
            return response
            
        except Exception as e:
            # Handle unexpected errors
            processing_time = time.time() - start_time
            self.request_metrics['failed_requests'] += 1
            
            self.logger.error(
                f"Request failed: {e} ({processing_time:.3f}s) [{request.correlation_id}]",
                exc_info=True
            )
            
            return APIResponse(
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                error=f"Internal server error: {str(e)}",
                error_code="INTERNAL_ERROR",
                correlation_id=request.correlation_id,
                processing_time=processing_time
            )
    
    def _validate_request(self, request: APIRequest) -> Optional[APIResponse]:
        """Validate incoming request"""
        # Basic validation
        if not request.endpoint:
            return APIResponse(
                status=HTTPStatus.BAD_REQUEST,
                error="Missing endpoint",
                error_code="MISSING_ENDPOINT",
                correlation_id=request.correlation_id
            )
        
        if not request.method:
            return APIResponse(
                status=HTTPStatus.BAD_REQUEST,
                error="Missing HTTP method",
                error_code="MISSING_METHOD",
                correlation_id=request.correlation_id
            )
        
        return None
    
    def _find_route(self, request: APIRequest) -> Optional[Dict[str, Any]]:
        """Find matching route for request"""
        route_key = f"{request.method.value}:{request.endpoint}"
        
        # Exact match first
        if route_key in self.routes:
            return self.routes[route_key]
        
        # Pattern matching (simple implementation)
        for key, route in self.routes.items():
            if self._match_route_pattern(route['path'], request.endpoint):
                return route
        
        return None
    
    def _match_route_pattern(self, pattern: str, path: str) -> bool:
        """Simple route pattern matching"""
        # For now, just exact matching
        # TODO: Implement proper pattern matching with parameters
        return pattern == path
    
    async def _execute_middleware(self, request: APIRequest, route: Dict[str, Any]) -> Optional[APIResponse]:
        """Execute middleware chain"""
        # Global middleware
        for middleware in self.middleware_stack:
            if hasattr(middleware, 'process_request'):
                result = await middleware.process_request(request)
                if isinstance(result, APIResponse):
                    return result
        
        # Route-specific middleware
        for middleware in route.get('middleware', []):
            if hasattr(middleware, 'process_request'):
                result = await middleware.process_request(request)
                if isinstance(result, APIResponse):
                    return result
        
        return None
    
    async def _execute_handler(self, request: APIRequest, route: Dict[str, Any]) -> APIResponse:
        """Execute the route handler"""
        handler = route['handler']
        
        try:
            # Call handler (support both sync and async)
            if hasattr(handler, '__call__'):
                if hasattr(handler, '__code__') and 'async' in str(handler.__code__):
                    result = await handler(request)
                else:
                    result = handler(request)
                
                # If handler returns APIResponse, use it directly
                if isinstance(result, APIResponse):
                    return result
                
                # Otherwise, wrap in successful response
                return APIResponse(
                    status=HTTPStatus.OK,
                    data=result,
                    correlation_id=request.correlation_id
                )
            else:
                return APIResponse(
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                    error="Invalid handler",
                    error_code="INVALID_HANDLER",
                    correlation_id=request.correlation_id
                )
                
        except Exception as e:
            self.logger.error(f"Handler error: {e}", exc_info=True)
            return APIResponse(
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                error=f"Handler error: {str(e)}",
                error_code="HANDLER_ERROR",
                correlation_id=request.correlation_id
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get request handling metrics"""
        return self.request_metrics.copy()
    
    def get_registered_routes(self) -> List[Dict[str, Any]]:
        """Get list of registered routes"""
        return [
            {
                'method': route['method'].value,
                'path': route['path'],
                'middleware_count': len(route['middleware'])
            }
            for route in self.routes.values()
        ] 