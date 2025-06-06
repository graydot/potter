#!/usr/bin/env python3
"""
Phase 5 API Integration Tests
Comprehensive testing of API Gateway and Plugin Architecture
"""

import asyncio
import pytest
import sys
import os
from unittest.mock import Mock, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import Phase 5 components
from api.gateway import APIGateway
from api.request_handler import RequestHandler, APIRequest, APIResponse, HTTPMethod, HTTPStatus
from api.middleware import MiddlewareStack, AuthenticationMiddleware, RateLimitingMiddleware
from api.response_formatter import ResponseFormatter
from plugins.plugin_manager import PluginManager
from plugins.plugin_interface import PluginInterface, PluginContext
from plugins.plugin_registry import PluginRegistry
from services.service_manager import ServiceManager


class TestAPIGateway:
    """Test API Gateway functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        # Create mock service manager
        self.service_manager = Mock(spec=ServiceManager)
        self.service_manager.is_running.return_value = True
        self.service_manager.get_service.return_value = Mock()
        self.service_manager.get_status.return_value = {"status": "running"}
        self.service_manager.get_all_services.return_value = {}
        
        # Create API Gateway
        self.gateway = APIGateway(self.service_manager)
    
    def test_gateway_initialization(self):
        """Test API Gateway initialization"""
        assert self.gateway.service_manager == self.service_manager
        assert isinstance(self.gateway.request_handler, RequestHandler)
        assert isinstance(self.gateway.response_formatter, ResponseFormatter)
        assert isinstance(self.gateway.middleware_stack, MiddlewareStack)
        assert not self.gateway.is_running
        
        print("✅ API Gateway initialization test passed")
    
    def test_gateway_start_stop(self):
        """Test API Gateway start and stop"""
        # Test start
        result = self.gateway.start()
        assert result is True
        assert self.gateway.is_running
        
        # Test stop
        self.gateway.stop()
        assert not self.gateway.is_running
        
        print("✅ API Gateway start/stop test passed")
    
    async def test_health_check_endpoint(self):
        """Test health check endpoint"""
        self.gateway.start()
        
        response = await self.gateway.process_request(
            method='GET',
            endpoint='/health'
        )
        
        assert response['success'] is True
        assert response['status'] == 200
        assert 'data' in response
        assert response['data']['status'] == 'healthy'
        
        print("✅ Health check endpoint test passed")
    
    async def test_status_endpoint(self):
        """Test status endpoint"""
        self.gateway.start()
        
        response = await self.gateway.process_request(
            method='GET',
            endpoint='/status'
        )
        
        assert response['success'] is True
        assert response['status'] == 200
        assert 'data' in response
        assert 'gateway' in response['data']
        assert 'services' in response['data']
        
        print("✅ Status endpoint test passed")
    
    async def test_request_validation(self):
        """Test request validation"""
        self.gateway.start()
        
        # Test invalid method
        response = await self.gateway.process_request(
            method='INVALID',
            endpoint='/health'
        )
        
        assert response['success'] is False
        assert response['status'] >= 400
        
        print("✅ Request validation test passed")
    
    async def test_middleware_processing(self):
        """Test middleware processing"""
        self.gateway.start()
        
        # Add custom middleware
        class TestMiddleware:
            def __init__(self):
                self.name = "TestMiddleware"
            
            async def process_request(self, request):
                request.headers['X-Test'] = 'processed'
                return None
        
        self.gateway.add_middleware(TestMiddleware())
        
        response = await self.gateway.process_request(
            method='GET',
            endpoint='/health',
            headers={'X-Original': 'value'}
        )
        
        assert response['success'] is True
        
        print("✅ Middleware processing test passed")


class TestRequestHandler:
    """Test Request Handler functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.handler = RequestHandler()
    
    def test_request_creation(self):
        """Test API request creation"""
        request = APIRequest(
            method=HTTPMethod.GET,
            endpoint='/test',
            data={'key': 'value'},
            headers={'Content-Type': 'application/json'}
        )
        
        assert request.method == HTTPMethod.GET
        assert request.endpoint == '/test'
        assert request.data['key'] == 'value'
        assert request.get_header('Content-Type') == 'application/json'
        assert request.correlation_id is not None
        
        print("✅ Request creation test passed")
    
    def test_response_creation(self):
        """Test API response creation"""
        response = APIResponse(
            status=HTTPStatus.OK,
            data={'message': 'success'},
            correlation_id='test-123'
        )
        
        assert response.status == HTTPStatus.OK
        assert response.is_success()
        assert not response.is_error()
        assert response.data['message'] == 'success'
        assert response.correlation_id == 'test-123'
        
        print("✅ Response creation test passed")
    
    def test_route_registration(self):
        """Test route registration"""
        def test_handler(request):
            return APIResponse(status=HTTPStatus.OK, data={'test': True})
        
        self.handler.register_route(HTTPMethod.GET, '/test', test_handler)
        
        routes = self.handler.get_registered_routes()
        assert len(routes) > 0
        
        found_route = any(route['path'] == '/test' and route['method'] == 'GET' for route in routes)
        assert found_route
        
        print("✅ Route registration test passed")
    
    async def test_request_processing(self):
        """Test request processing"""
        def test_handler(request):
            return APIResponse(
                status=HTTPStatus.OK,
                data={'echo': request.data}
            )
        
        self.handler.register_route(HTTPMethod.POST, '/echo', test_handler)
        
        request = APIRequest(
            method=HTTPMethod.POST,
            endpoint='/echo',
            data={'message': 'hello'}
        )
        
        response = await self.handler.handle_request(request)
        
        assert response.status == HTTPStatus.OK
        assert response.data['echo']['message'] == 'hello'
        
        print("✅ Request processing test passed")


class TestMiddleware:
    """Test Middleware functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.stack = MiddlewareStack()
    
    def test_middleware_stack(self):
        """Test middleware stack operations"""
        # Create test middleware
        class TestMiddleware:
            def __init__(self, name):
                self.name = name
            
            async def process_request(self, request):
                return None
        
        middleware1 = TestMiddleware("Test1")
        middleware2 = TestMiddleware("Test2")
        
        # Add middleware
        self.stack.add(middleware1)
        self.stack.add(middleware2)
        
        # Check middleware info
        info = self.stack.get_middleware_info()
        assert len(info) == 2
        assert any(m['name'] == 'Test1' for m in info)
        assert any(m['name'] == 'Test2' for m in info)
        
        # Remove middleware
        result = self.stack.remove("Test1")
        assert result is True
        
        info = self.stack.get_middleware_info()
        assert len(info) == 1
        assert info[0]['name'] == 'Test2'
        
        print("✅ Middleware stack test passed")
    
    async def test_authentication_middleware(self):
        """Test authentication middleware"""
        auth_middleware = AuthenticationMiddleware()
        
        # Test request without auth header
        request = APIRequest(
            method=HTTPMethod.GET,
            endpoint='/protected'
        )
        
        response = await auth_middleware.process_request(request)
        assert response is not None
        assert response.status == HTTPStatus.UNAUTHORIZED
        
        # Test request with auth header
        request_with_auth = APIRequest(
            method=HTTPMethod.GET,
            endpoint='/protected',
            headers={'Authorization': 'Bearer valid_token_123'}
        )
        
        response = await auth_middleware.process_request(request_with_auth)
        assert response is None  # Should pass through
        assert request_with_auth.user_id is not None
        
        print("✅ Authentication middleware test passed")
    
    async def test_rate_limiting_middleware(self):
        """Test rate limiting middleware"""
        rate_limiter = RateLimitingMiddleware(requests_per_minute=2)
        
        request = APIRequest(
            method=HTTPMethod.GET,
            endpoint='/test',
            client_ip='192.168.1.1'
        )
        
        # First request should pass
        response1 = await rate_limiter.process_request(request)
        assert response1 is None
        
        # Second request should pass
        response2 = await rate_limiter.process_request(request)
        assert response2 is None
        
        # Third request should be rate limited
        response3 = await rate_limiter.process_request(request)
        assert response3 is not None
        assert response3.status.value == 429  # Too Many Requests
        
        print("✅ Rate limiting middleware test passed")


class TestResponseFormatter:
    """Test Response Formatter functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.formatter = ResponseFormatter()
    
    def test_json_formatting(self):
        """Test JSON response formatting"""
        response = APIResponse(
            status=HTTPStatus.OK,
            data={'message': 'success'},
            correlation_id='test-123'
        )
        
        formatted = self.formatter.format_response(response, 'json')
        
        assert formatted['success'] is True
        assert formatted['status'] == 200
        assert formatted['data']['message'] == 'success'
        assert formatted['correlation_id'] == 'test-123'
        assert 'timestamp' in formatted
        
        print("✅ JSON formatting test passed")
    
    def test_error_formatting(self):
        """Test error response formatting"""
        error_response = self.formatter.format_error_response(
            status=HTTPStatus.BAD_REQUEST,
            error="Invalid input",
            error_code="INVALID_INPUT",
            correlation_id="test-456"
        )
        
        assert error_response['success'] is False
        assert error_response['status'] == 400
        assert error_response['error']['message'] == "Invalid input"
        assert error_response['error']['code'] == "INVALID_INPUT"
        assert error_response['correlation_id'] == "test-456"
        
        print("✅ Error formatting test passed")
    
    def test_validation_error_formatting(self):
        """Test validation error formatting"""
        validation_errors = {
            'email': 'Invalid email format',
            'password': 'Password too short'
        }
        
        formatted = self.formatter.format_validation_error(
            validation_errors,
            correlation_id="test-789"
        )
        
        assert formatted['success'] is False
        assert formatted['status'] == 400
        assert formatted['error']['code'] == "VALIDATION_ERROR"
        assert 'validation_errors' in formatted['error']['details']
        
        print("✅ Validation error formatting test passed")


class TestPluginManager:
    """Test Plugin Manager functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.service_manager = Mock(spec=ServiceManager)
        self.plugin_manager = PluginManager(self.service_manager)
    
    def test_plugin_manager_initialization(self):
        """Test plugin manager initialization"""
        assert self.plugin_manager.service_manager == self.service_manager
        assert isinstance(self.plugin_manager.plugin_registry, PluginRegistry)
        assert not self.plugin_manager.is_running
        assert len(self.plugin_manager.loaded_plugins) == 0
        
        print("✅ Plugin manager initialization test passed")
    
    def test_plugin_discovery(self):
        """Test plugin discovery"""
        # This would normally scan directories, but for testing we'll mock it
        discovered = self.plugin_manager.discover_plugins()
        assert isinstance(discovered, list)
        
        print("✅ Plugin discovery test passed")
    
    def test_plugin_manager_start_stop(self):
        """Test plugin manager start and stop"""
        # Test start
        result = self.plugin_manager.start()
        assert result is True
        assert self.plugin_manager.is_running
        
        # Test stop
        self.plugin_manager.stop()
        assert not self.plugin_manager.is_running
        assert len(self.plugin_manager.loaded_plugins) == 0
        
        print("✅ Plugin manager start/stop test passed")


class TestPlugin(PluginInterface):
    """Test plugin implementation"""
    
    def get_plugin_info(self):
        return {
            'name': 'TestPlugin',
            'version': '1.0.0',
            'description': 'Test plugin for unit tests',
            'author': 'Test',
            'dependencies': [],
            'capabilities': ['test_capability']
        }
    
    def initialize(self, context: PluginContext):
        self.context = context
        self.logger = context.logger
        self.is_initialized = True
        return True
    
    def cleanup(self):
        pass
    
    def get_capabilities(self):
        return ['test_capability']
    
    def execute_test_capability(self, data):
        return f"Processed: {data}"


class TestPluginInterface:
    """Test Plugin Interface functionality"""
    
    def test_plugin_creation(self):
        """Test plugin creation and info"""
        plugin = TestPlugin()
        
        info = plugin.get_plugin_info()
        assert info['name'] == 'TestPlugin'
        assert info['version'] == '1.0.0'
        assert 'test_capability' in info['capabilities']
        
        capabilities = plugin.get_capabilities()
        assert 'test_capability' in capabilities
        
        print("✅ Plugin creation test passed")
    
    def test_plugin_initialization(self):
        """Test plugin initialization"""
        plugin = TestPlugin()
        context = PluginContext(
            service_manager=Mock(),
            plugin_name='TestPlugin'
        )
        
        result = plugin.initialize(context)
        assert result is True
        assert plugin.is_initialized
        assert plugin.context == context
        
        print("✅ Plugin initialization test passed")
    
    def test_plugin_execution(self):
        """Test plugin capability execution"""
        plugin = TestPlugin()
        context = PluginContext(
            service_manager=Mock(),
            plugin_name='TestPlugin'
        )
        
        plugin.initialize(context)
        
        result = plugin.execute('test_capability', 'test_data')
        assert result == 'Processed: test_data'
        
        print("✅ Plugin execution test passed")
    
    def test_plugin_status(self):
        """Test plugin status reporting"""
        plugin = TestPlugin()
        context = PluginContext(
            service_manager=Mock(),
            plugin_name='TestPlugin'
        )
        
        plugin.initialize(context)
        
        status = plugin.get_status()
        assert status['name'] == 'TestPlugin'
        assert status['initialized'] is True
        assert status['enabled'] is True
        assert 'test_capability' in status['capabilities']
        
        print("✅ Plugin status test passed")


class TestPluginRegistry:
    """Test Plugin Registry functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.registry = PluginRegistry()
    
    def test_plugin_registration(self):
        """Test plugin registration"""
        plugin_info = {
            'name': 'TestPlugin',
            'version': '1.0.0',
            'description': 'Test plugin',
            'categories': ['test'],
            'dependencies': []
        }
        
        result = self.registry.register_plugin(plugin_info)
        assert result is True
        
        # Check if registered
        stored_info = self.registry.get_plugin_info('TestPlugin')
        assert stored_info is not None
        assert stored_info['name'] == 'TestPlugin'
        
        plugin_names = self.registry.get_plugin_names()
        assert 'TestPlugin' in plugin_names
        
        print("✅ Plugin registration test passed")
    
    def test_plugin_categories(self):
        """Test plugin categorization"""
        plugin_info = {
            'name': 'TestPlugin',
            'version': '1.0.0',
            'description': 'Test plugin',
            'categories': ['test', 'utility'],
            'dependencies': []
        }
        
        self.registry.register_plugin(plugin_info)
        
        categories = self.registry.get_categories()
        assert 'test' in categories
        assert 'utility' in categories
        
        test_plugins = self.registry.get_plugins_by_category('test')
        assert 'TestPlugin' in test_plugins
        
        print("✅ Plugin categorization test passed")
    
    def test_dependency_tracking(self):
        """Test dependency tracking"""
        # Register dependent plugin
        plugin_info = {
            'name': 'DependentPlugin',
            'version': '1.0.0',
            'description': 'Plugin with dependencies',
            'categories': ['test'],
            'dependencies': ['BasePlugin']
        }
        
        self.registry.register_plugin(plugin_info)
        
        deps = self.registry.get_plugin_dependencies('DependentPlugin')
        assert 'BasePlugin' in deps
        
        # Test missing dependencies
        missing = self.registry.validate_dependencies('DependentPlugin')
        assert 'BasePlugin' in missing
        
        print("✅ Dependency tracking test passed")


def run_phase5_tests():
    """Run all Phase 5 tests"""
    print("🧪 Running Phase 5 API Integration Tests...\n")
    
    # Test API Gateway
    print("📡 Testing API Gateway...")
    gateway_tests = TestAPIGateway()
    gateway_tests.setup_method()
    gateway_tests.test_gateway_initialization()
    gateway_tests.test_gateway_start_stop()
    
    # Run async tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(gateway_tests.test_health_check_endpoint())
        loop.run_until_complete(gateway_tests.test_status_endpoint())
        loop.run_until_complete(gateway_tests.test_request_validation())
        loop.run_until_complete(gateway_tests.test_middleware_processing())
    finally:
        loop.close()
    
    # Test Request Handler
    print("\n📝 Testing Request Handler...")
    handler_tests = TestRequestHandler()
    handler_tests.setup_method()
    handler_tests.test_request_creation()
    handler_tests.test_response_creation()
    handler_tests.test_route_registration()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(handler_tests.test_request_processing())
    finally:
        loop.close()
    
    # Test Middleware
    print("\n🛡️ Testing Middleware...")
    middleware_tests = TestMiddleware()
    middleware_tests.setup_method()
    middleware_tests.test_middleware_stack()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(middleware_tests.test_authentication_middleware())
        loop.run_until_complete(middleware_tests.test_rate_limiting_middleware())
    finally:
        loop.close()
    
    # Test Response Formatter
    print("\n📄 Testing Response Formatter...")
    formatter_tests = TestResponseFormatter()
    formatter_tests.setup_method()
    formatter_tests.test_json_formatting()
    formatter_tests.test_error_formatting()
    formatter_tests.test_validation_error_formatting()
    
    # Test Plugin Manager
    print("\n🔌 Testing Plugin Manager...")
    plugin_tests = TestPluginManager()
    plugin_tests.setup_method()
    plugin_tests.test_plugin_manager_initialization()
    plugin_tests.test_plugin_discovery()
    plugin_tests.test_plugin_manager_start_stop()
    
    # Test Plugin Interface
    print("\n🧩 Testing Plugin Interface...")
    interface_tests = TestPluginInterface()
    interface_tests.test_plugin_creation()
    interface_tests.test_plugin_initialization()
    interface_tests.test_plugin_execution()
    interface_tests.test_plugin_status()
    
    # Test Plugin Registry
    print("\n📚 Testing Plugin Registry...")
    registry_tests = TestPluginRegistry()
    registry_tests.setup_method()
    registry_tests.test_plugin_registration()
    registry_tests.test_plugin_categories()
    registry_tests.test_dependency_tracking()
    
    print("\n🎉 Phase 5 API Integration Tests Summary")
    print("=" * 50)
    print("✅ API Gateway: 6/6 tests passed")
    print("✅ Request Handler: 4/4 tests passed")
    print("✅ Middleware: 3/3 tests passed")
    print("✅ Response Formatter: 3/3 tests passed")
    print("✅ Plugin Manager: 3/3 tests passed")
    print("✅ Plugin Interface: 4/4 tests passed")
    print("✅ Plugin Registry: 3/3 tests passed")
    print("=" * 50)
    print("🏆 Total: 26/26 tests passed (100% success rate)")
    print("\n✨ Phase 5 API & Integration Layer is working perfectly!")


if __name__ == "__main__":
    run_phase5_tests() 