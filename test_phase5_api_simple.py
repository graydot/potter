#!/usr/bin/env python3
"""
Phase 5 API Simple Tests
Simplified testing of API Gateway and Plugin Architecture (avoiding circular imports)
"""

import asyncio
import sys
import os
from unittest.mock import Mock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import Phase 5 components directly
from api.request_handler import RequestHandler, APIRequest, APIResponse, HTTPMethod, HTTPStatus
from api.middleware import MiddlewareStack, AuthenticationMiddleware, RateLimitingMiddleware
from api.response_formatter import ResponseFormatter
from plugins.plugin_interface import PluginInterface, PluginContext
from plugins.plugin_registry import PluginRegistry


class MockServiceManager:
    """Mock service manager for testing"""
    def is_running(self): return True
    def get_service(self, name): return Mock()
    def get_status(self): return {"status": "running"}
    def get_all_services(self): return {}


class TestAPIComponents:
    """Test API components without circular dependencies"""
    
    def test_request_handler(self):
        """Test Request Handler functionality"""
        print("📝 Testing Request Handler...")
        
        handler = RequestHandler()
        
        # Test request creation
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
        print("  ✅ Request creation test passed")
        
        # Test response creation
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
        print("  ✅ Response creation test passed")
        
        # Test route registration
        def test_handler(request):
            return APIResponse(status=HTTPStatus.OK, data={'test': True})
        
        handler.register_route(HTTPMethod.GET, '/test', test_handler)
        
        routes = handler.get_registered_routes()
        assert len(routes) > 0
        
        found_route = any(route['path'] == '/test' and route['method'] == 'GET' for route in routes)
        assert found_route
        print("  ✅ Route registration test passed")
        
        print("✅ Request Handler: All tests passed\n")
    
    async def test_middleware(self):
        """Test Middleware functionality"""
        print("🛡️ Testing Middleware...")
        
        stack = MiddlewareStack()
        
        # Create test middleware
        class TestMiddleware:
            def __init__(self, name):
                self.name = name
            
            async def process_request(self, request):
                return None
        
        middleware1 = TestMiddleware("Test1")
        middleware2 = TestMiddleware("Test2")
        
        # Add middleware
        stack.add(middleware1)
        stack.add(middleware2)
        
        # Check middleware info
        info = stack.get_middleware_info()
        assert len(info) == 2
        assert any(m['name'] == 'Test1' for m in info)
        assert any(m['name'] == 'Test2' for m in info)
        print("  ✅ Middleware stack test passed")
        
        # Test authentication middleware
        auth_middleware = AuthenticationMiddleware()
        
        # Test request without auth header
        request = APIRequest(
            method=HTTPMethod.GET,
            endpoint='/protected'
        )
        
        response = await auth_middleware.process_request(request)
        assert response is not None
        assert response.status == HTTPStatus.UNAUTHORIZED
        print("  ✅ Authentication middleware test passed")
        
        # Test rate limiting middleware
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
        print("  ✅ Rate limiting middleware test passed")
        
        print("✅ Middleware: All tests passed\n")
    
    def test_response_formatter(self):
        """Test Response Formatter functionality"""
        print("📄 Testing Response Formatter...")
        
        formatter = ResponseFormatter()
        
        # Test JSON formatting
        response = APIResponse(
            status=HTTPStatus.OK,
            data={'message': 'success'},
            correlation_id='test-123'
        )
        
        formatted = formatter.format_response(response, 'json')
        
        assert formatted['success'] is True
        assert formatted['status'] == 200
        assert formatted['data']['message'] == 'success'
        assert formatted['correlation_id'] == 'test-123'
        assert 'timestamp' in formatted
        print("  ✅ JSON formatting test passed")
        
        # Test error formatting
        error_response = formatter.format_error_response(
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
        print("  ✅ Error formatting test passed")
        
        print("✅ Response Formatter: All tests passed\n")


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


class TestPluginComponents:
    """Test Plugin components"""
    
    def test_plugin_interface(self):
        """Test Plugin Interface functionality"""
        print("🧩 Testing Plugin Interface...")
        
        # Test plugin creation
        plugin = TestPlugin()
        
        info = plugin.get_plugin_info()
        assert info['name'] == 'TestPlugin'
        assert info['version'] == '1.0.0'
        assert 'test_capability' in info['capabilities']
        
        capabilities = plugin.get_capabilities()
        assert 'test_capability' in capabilities
        print("  ✅ Plugin creation test passed")
        
        # Test plugin initialization
        context = PluginContext(
            service_manager=MockServiceManager(),
            plugin_name='TestPlugin'
        )
        
        result = plugin.initialize(context)
        assert result is True
        assert plugin.is_initialized
        assert plugin.context == context
        print("  ✅ Plugin initialization test passed")
        
        # Test plugin execution
        result = plugin.execute('test_capability', 'test_data')
        assert result == 'Processed: test_data'
        print("  ✅ Plugin execution test passed")
        
        # Test plugin status
        status = plugin.get_status()
        assert status['name'] == 'TestPlugin'
        assert status['initialized'] is True
        assert status['enabled'] is True
        assert 'test_capability' in status['capabilities']
        print("  ✅ Plugin status test passed")
        
        print("✅ Plugin Interface: All tests passed\n")
    
    def test_plugin_registry(self):
        """Test Plugin Registry functionality"""
        print("📚 Testing Plugin Registry...")
        
        registry = PluginRegistry()
        
        # Test plugin registration
        plugin_info = {
            'name': 'TestPlugin',
            'version': '1.0.0',
            'description': 'Test plugin',
            'categories': ['test'],
            'dependencies': []
        }
        
        result = registry.register_plugin(plugin_info)
        assert result is True
        
        # Check if registered
        stored_info = registry.get_plugin_info('TestPlugin')
        assert stored_info is not None
        assert stored_info['name'] == 'TestPlugin'
        
        plugin_names = registry.get_plugin_names()
        assert 'TestPlugin' in plugin_names
        print("  ✅ Plugin registration test passed")
        
        # Test plugin categories
        categories = registry.get_categories()
        assert 'test' in categories
        
        test_plugins = registry.get_plugins_by_category('test')
        assert 'TestPlugin' in test_plugins
        print("  ✅ Plugin categorization test passed")
        
        # Test dependency tracking
        plugin_info_with_deps = {
            'name': 'DependentPlugin',
            'version': '1.0.0',
            'description': 'Plugin with dependencies',
            'categories': ['test'],
            'dependencies': ['BasePlugin']
        }
        
        registry.register_plugin(plugin_info_with_deps)
        
        deps = registry.get_plugin_dependencies('DependentPlugin')
        assert 'BasePlugin' in deps
        
        # Test missing dependencies
        missing = registry.validate_dependencies('DependentPlugin')
        assert 'BasePlugin' in missing
        print("  ✅ Dependency tracking test passed")
        
        print("✅ Plugin Registry: All tests passed\n")


def run_simple_tests():
    """Run simplified Phase 5 tests"""
    print("🧪 Running Phase 5 API Simple Tests...\n")
    
    # Test API Components
    api_tests = TestAPIComponents()
    api_tests.test_request_handler()
    
    # Run async middleware tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(api_tests.test_middleware())
    finally:
        loop.close()
    
    api_tests.test_response_formatter()
    
    # Test Plugin Components
    plugin_tests = TestPluginComponents()
    plugin_tests.test_plugin_interface()
    plugin_tests.test_plugin_registry()
    
    print("🎉 Phase 5 API Simple Tests Summary")
    print("=" * 50)
    print("✅ Request Handler: 3/3 tests passed")
    print("✅ Middleware: 3/3 tests passed")
    print("✅ Response Formatter: 2/2 tests passed")
    print("✅ Plugin Interface: 4/4 tests passed")
    print("✅ Plugin Registry: 3/3 tests passed")
    print("=" * 50)
    print("🏆 Total: 15/15 tests passed (100% success rate)")
    print("\n✨ Phase 5 API & Plugin Architecture core components are working perfectly!")


if __name__ == "__main__":
    run_simple_tests() 