#!/usr/bin/env python3
"""
API Gateway
Central entry point for all Potter API operations
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable

from .request_handler import RequestHandler, APIRequest, APIResponse, HTTPMethod, HTTPStatus
from .middleware import MiddlewareStack, AuthenticationMiddleware, RateLimitingMiddleware, ValidationMiddleware, LoggingMiddleware, CORSMiddleware
from .response_formatter import ResponseFormatter
# Conditional import to avoid circular dependency during testing
try:
    from services.service_manager import ServiceManager
except ImportError:
    # For testing - create a simple mock interface
    class ServiceManager:
        def is_running(self): return True
        def get_service(self, name): return None
        def get_status(self): return {"status": "mock"}
        def get_all_services(self): return {}

logger = logging.getLogger(__name__)


class APIGateway:
    """
    Central API Gateway for Potter application
    
    Features:
    - Unified request processing
    - Service integration
    - Middleware support
    - Response formatting
    - Route management
    - Performance monitoring
    """
    
    def __init__(self, service_manager: ServiceManager):
        self.service_manager = service_manager
        self.request_handler = RequestHandler()
        self.response_formatter = ResponseFormatter()
        self.middleware_stack = MiddlewareStack()
        
        self.logger = logging.getLogger("api.gateway")
        self.is_running = False
        
        # Gateway metrics
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'active_connections': 0
        }
        
        # Initialize default middleware and routes
        self._setup_default_middleware()
        self._setup_default_routes()
    
    def start(self) -> bool:
        """
        Start the API Gateway
        
        Returns:
            bool: True if started successfully
        """
        try:
            if self.is_running:
                self.logger.warning("API Gateway is already running")
                return True
            
            # Ensure service manager is running
            if not self.service_manager.is_running():
                self.logger.error("Service manager is not running")
                return False
            
            self.is_running = True
            self.logger.info("🚀 API Gateway started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start API Gateway: {e}")
            return False
    
    def stop(self):
        """Stop the API Gateway"""
        try:
            self.is_running = False
            self.logger.info("🛑 API Gateway stopped")
        except Exception as e:
            self.logger.error(f"Error stopping API Gateway: {e}")
    
    async def process_request(self, method: str, endpoint: str, data: Dict[str, Any] = None,
                            headers: Dict[str, str] = None, **kwargs) -> Dict[str, Any]:
        """
        Process an API request
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            headers: Request headers
            **kwargs: Additional request parameters
            
        Returns:
            Formatted response dictionary
        """
        if not self.is_running:
            return self.response_formatter.format_error_response(
                status=HTTPStatus.SERVICE_UNAVAILABLE,
                error="API Gateway not running",
                error_code="GATEWAY_OFFLINE"
            )
        
        # Create API request
        request = APIRequest(
            method=HTTPMethod(method.upper()),
            endpoint=endpoint,
            data=data or {},
            headers=headers or {},
            **kwargs
        )
        
        # Update metrics
        self.metrics['total_requests'] += 1
        self.metrics['active_connections'] += 1
        
        try:
            # Process through middleware stack first
            middleware_response = await self.middleware_stack.process_request(request)
            if middleware_response:
                # Middleware short-circuited the request
                response = middleware_response
            else:
                # Process through request handler
                response = await self.request_handler.handle_request(request)
            
            # Process response through middleware
            response = await self.middleware_stack.process_response(request, response)
            
            # Update metrics
            if response.is_success():
                self.metrics['successful_requests'] += 1
            else:
                self.metrics['failed_requests'] += 1
            
            # Update average response time
            if response.processing_time:
                total_requests = self.metrics['total_requests']
                current_avg = self.metrics['average_response_time']
                new_avg = ((current_avg * (total_requests - 1)) + response.processing_time) / total_requests
                self.metrics['average_response_time'] = new_avg
            
            # Format response
            format_type = self.response_formatter.determine_format_from_request(request)
            formatted_response = self.response_formatter.format_response(response, format_type)
            
            return formatted_response
            
        except Exception as e:
            self.logger.error(f"Error processing request: {e}", exc_info=True)
            self.metrics['failed_requests'] += 1
            
            return self.response_formatter.format_error_response(
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                error=f"Gateway error: {str(e)}",
                error_code="GATEWAY_ERROR",
                correlation_id=request.correlation_id
            )
        finally:
            self.metrics['active_connections'] -= 1
    
    def _setup_default_middleware(self):
        """Setup default middleware stack"""
        # CORS middleware (first to handle preflight requests)
        self.middleware_stack.add(CORSMiddleware())
        
        # Logging middleware (early for complete request logging)
        self.middleware_stack.add(LoggingMiddleware(log_request_body=False, log_response_body=False))
        
        # Rate limiting middleware
        self.middleware_stack.add(RateLimitingMiddleware(requests_per_minute=100))
        
        # Authentication middleware (for protected endpoints)
        protected_endpoints = ['/api/settings', '/api/process', '/api/admin']
        self.middleware_stack.add(AuthenticationMiddleware(required_endpoints=protected_endpoints))
        
        # Validation middleware
        validation_service = self.service_manager.get_service('validation')
        self.middleware_stack.add(ValidationMiddleware(validation_service))
        
        self.logger.debug("Default middleware stack configured")
    
    def _setup_default_routes(self):
        """Setup default API routes"""
        # Health check endpoint
        self.request_handler.register_route(
            HTTPMethod.GET, '/health', self._handle_health_check
        )
        
        # Gateway status endpoint
        self.request_handler.register_route(
            HTTPMethod.GET, '/status', self._handle_status
        )
        
        # Service management endpoints
        self.request_handler.register_route(
            HTTPMethod.GET, '/api/services', self._handle_list_services
        )
        
        self.request_handler.register_route(
            HTTPMethod.GET, '/api/services/{service_name}', self._handle_get_service_status
        )
        
        # Text processing endpoint
        self.request_handler.register_route(
            HTTPMethod.POST, '/api/process', self._handle_process_text
        )
        
        # Settings endpoints
        self.request_handler.register_route(
            HTTPMethod.GET, '/api/settings', self._handle_get_settings
        )
        
        self.request_handler.register_route(
            HTTPMethod.PUT, '/api/settings', self._handle_update_settings
        )
        
        # Metrics endpoint
        self.request_handler.register_route(
            HTTPMethod.GET, '/api/metrics', self._handle_get_metrics
        )
        
        self.logger.debug("Default routes configured")
    
    # Route handlers
    
    async def _handle_health_check(self, request: APIRequest) -> APIResponse:
        """Health check endpoint"""
        return APIResponse(
            status=HTTPStatus.OK,
            data={
                'status': 'healthy',
                'gateway_running': self.is_running,
                'service_manager_running': self.service_manager.is_running(),
                'timestamp': request.timestamp
            }
        )
    
    async def _handle_status(self, request: APIRequest) -> APIResponse:
        """Gateway status endpoint"""
        return APIResponse(
            status=HTTPStatus.OK,
            data={
                'gateway': {
                    'running': self.is_running,
                    'version': '1.0.0',
                    'metrics': self.metrics
                },
                'services': self.service_manager.get_status(),
                'middleware': self.middleware_stack.get_middleware_info(),
                'routes': self.request_handler.get_registered_routes()
            }
        )
    
    async def _handle_list_services(self, request: APIRequest) -> APIResponse:
        """List all services endpoint"""
        try:
            services = self.service_manager.get_all_services()
            service_info = {}
            
            for name, service in services.items():
                service_info[name] = {
                    'name': name,
                    'running': service.is_running if hasattr(service, 'is_running') else False,
                    'status': service.get_status() if hasattr(service, 'get_status') else 'unknown'
                }
            
            return APIResponse(
                status=HTTPStatus.OK,
                data={'services': service_info}
            )
        except Exception as e:
            return APIResponse(
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                error=f"Error listing services: {str(e)}",
                error_code="SERVICE_LIST_ERROR"
            )
    
    async def _handle_get_service_status(self, request: APIRequest) -> APIResponse:
        """Get specific service status endpoint"""
        service_name = request.params.get('service_name')
        
        if not service_name:
            return APIResponse(
                status=HTTPStatus.BAD_REQUEST,
                error="Service name required",
                error_code="MISSING_SERVICE_NAME"
            )
        
        try:
            service = self.service_manager.get_service(service_name)
            if not service:
                return APIResponse(
                    status=HTTPStatus.NOT_FOUND,
                    error=f"Service not found: {service_name}",
                    error_code="SERVICE_NOT_FOUND"
                )
            
            status_data = {
                'name': service_name,
                'running': service.is_running if hasattr(service, 'is_running') else False,
                'status': service.get_status() if hasattr(service, 'get_status') else 'unknown'
            }
            
            return APIResponse(
                status=HTTPStatus.OK,
                data=status_data
            )
        except Exception as e:
            return APIResponse(
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                error=f"Error getting service status: {str(e)}",
                error_code="SERVICE_STATUS_ERROR"
            )
    
    async def _handle_process_text(self, request: APIRequest) -> APIResponse:
        """Text processing endpoint"""
        try:
            # Validate required fields
            if 'text' not in request.data:
                return APIResponse(
                    status=HTTPStatus.BAD_REQUEST,
                    error="Missing required field: text",
                    error_code="MISSING_TEXT"
                )
            
            if 'prompt' not in request.data:
                return APIResponse(
                    status=HTTPStatus.BAD_REQUEST,
                    error="Missing required field: prompt",
                    error_code="MISSING_PROMPT"
                )
            
            # Get processing service
            processing_service = self.service_manager.get_service('processing')
            if not processing_service:
                return APIResponse(
                    status=HTTPStatus.SERVICE_UNAVAILABLE,
                    error="Processing service not available",
                    error_code="PROCESSING_SERVICE_UNAVAILABLE"
                )
            
            # Process text
            result = processing_service.process_text(
                text=request.data['text'],
                prompt=request.data['prompt'],
                **{k: v for k, v in request.data.items() if k not in ['text', 'prompt']}
            )
            
            return APIResponse(
                status=HTTPStatus.OK,
                data={
                    'processed_text': result,
                    'original_length': len(request.data['text']),
                    'processed_length': len(result) if result else 0
                }
            )
            
        except Exception as e:
            return APIResponse(
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                error=f"Error processing text: {str(e)}",
                error_code="PROCESSING_ERROR"
            )
    
    async def _handle_get_settings(self, request: APIRequest) -> APIResponse:
        """Get settings endpoint"""
        try:
            settings_service = self.service_manager.get_service('settings')
            if not settings_service:
                return APIResponse(
                    status=HTTPStatus.SERVICE_UNAVAILABLE,
                    error="Settings service not available",
                    error_code="SETTINGS_SERVICE_UNAVAILABLE"
                )
            
            settings = settings_service.get_all_settings()
            
            return APIResponse(
                status=HTTPStatus.OK,
                data={'settings': settings}
            )
            
        except Exception as e:
            return APIResponse(
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                error=f"Error getting settings: {str(e)}",
                error_code="SETTINGS_GET_ERROR"
            )
    
    async def _handle_update_settings(self, request: APIRequest) -> APIResponse:
        """Update settings endpoint"""
        try:
            if 'settings' not in request.data:
                return APIResponse(
                    status=HTTPStatus.BAD_REQUEST,
                    error="Missing required field: settings",
                    error_code="MISSING_SETTINGS"
                )
            
            settings_service = self.service_manager.get_service('settings')
            if not settings_service:
                return APIResponse(
                    status=HTTPStatus.SERVICE_UNAVAILABLE,
                    error="Settings service not available",
                    error_code="SETTINGS_SERVICE_UNAVAILABLE"
                )
            
            # Update settings
            settings_to_update = request.data['settings']
            for key, value in settings_to_update.items():
                settings_service.set_setting(key, value)
            
            return APIResponse(
                status=HTTPStatus.OK,
                data={
                    'message': 'Settings updated successfully',
                    'updated_keys': list(settings_to_update.keys())
                }
            )
            
        except Exception as e:
            return APIResponse(
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                error=f"Error updating settings: {str(e)}",
                error_code="SETTINGS_UPDATE_ERROR"
            )
    
    async def _handle_get_metrics(self, request: APIRequest) -> APIResponse:
        """Get gateway metrics endpoint"""
        try:
            gateway_metrics = self.metrics.copy()
            request_handler_metrics = self.request_handler.get_metrics()
            
            combined_metrics = {
                'gateway': gateway_metrics,
                'request_handler': request_handler_metrics,
                'middleware_stack': len(self.middleware_stack.get_middleware_info()),
                'registered_routes': len(self.request_handler.get_registered_routes())
            }
            
            return APIResponse(
                status=HTTPStatus.OK,
                data=combined_metrics
            )
            
        except Exception as e:
            return APIResponse(
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                error=f"Error getting metrics: {str(e)}",
                error_code="METRICS_ERROR"
            )
    
    # Gateway management methods
    
    def add_middleware(self, middleware):
        """Add middleware to the stack"""
        self.middleware_stack.add(middleware)
        self.logger.debug(f"Added middleware: {middleware.name}")
    
    def remove_middleware(self, middleware_name: str) -> bool:
        """Remove middleware from the stack"""
        result = self.middleware_stack.remove(middleware_name)
        if result:
            self.logger.debug(f"Removed middleware: {middleware_name}")
        return result
    
    def register_route(self, method: HTTPMethod, path: str, handler: Callable,
                      middleware: List[Any] = None):
        """Register a new API route"""
        self.request_handler.register_route(method, path, handler, middleware)
        self.logger.debug(f"Registered route: {method.value} {path}")
    
    def add_response_formatter(self, format_name: str, formatter_func: Callable):
        """Add custom response formatter"""
        self.response_formatter.add_formatter(format_name, formatter_func)
        self.logger.debug(f"Added response formatter: {format_name}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get gateway metrics"""
        return {
            'gateway_metrics': self.metrics,
            'request_handler_metrics': self.request_handler.get_metrics(),
            'middleware_count': len(self.middleware_stack.get_middleware_info()),
            'route_count': len(self.request_handler.get_registered_routes()),
            'is_running': self.is_running
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive gateway status"""
        return {
            'running': self.is_running,
            'service_manager_running': self.service_manager.is_running(),
            'metrics': self.get_metrics(),
            'middleware': self.middleware_stack.get_middleware_info(),
            'routes': self.request_handler.get_registered_routes(),
            'supported_formats': self.response_formatter.get_supported_formats()
        } 