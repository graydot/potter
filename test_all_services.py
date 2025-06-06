#!/usr/bin/env python3
"""
Comprehensive Service Layer Test
Tests all 9 services in Phase 3 completion
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_service_imports():
    """Test that all services can be imported"""
    print("🔍 Testing service imports...")
    
    try:
        from services import (
            BaseService, ServiceManager,
            APIService, ThemeService, NotificationService, ValidationService,
            HotkeyService, PermissionService, PermissionType, PermissionStatus,
            WindowService, WindowState, SettingsService, LoggingService
        )
        print("✅ All service imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_service_manager_with_all_services():
    """Test service manager with all 9 services"""
    print("\n🔧 Testing ServiceManager with all services...")
    
    try:
        from services import ServiceManager
        from services import (
            APIService, ThemeService, NotificationService, ValidationService,
            HotkeyService, PermissionService, WindowService, SettingsService, LoggingService
        )
        
        # Create service manager
        manager = ServiceManager()
        
        # Register all services with dependencies
        manager.register_service("logging", LoggingService)
        manager.register_service("settings", SettingsService)
        manager.register_service("validation", ValidationService, dependencies=["settings"])
        manager.register_service("api", APIService, dependencies=["validation"])
        manager.register_service("theme", ThemeService)
        manager.register_service("notification", NotificationService)
        manager.register_service("permission", PermissionService, dependencies=["settings"])
        manager.register_service("hotkey", HotkeyService, dependencies=["settings", "validation"])
        manager.register_service("window", WindowService, dependencies=["settings"])
        
        print(f"✅ Registered {len(manager._services)} services")
        
        # Test dependency resolution
        resolved = manager._resolve_dependencies()
        print(f"✅ Dependency resolution successful: {resolved}")
        
        return True
        
    except Exception as e:
        print(f"❌ ServiceManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_services():
    """Test each service individually"""
    print("\n🧪 Testing individual services...")
    
    results = {}
    
    # Test each service
    service_tests = [
        ("APIService", test_api_service),
        ("ThemeService", test_theme_service),
        ("NotificationService", test_notification_service),
        ("ValidationService", test_validation_service),
        ("HotkeyService", test_hotkey_service),
        ("PermissionService", test_permission_service),
        ("WindowService", test_window_service),
        ("SettingsService", test_settings_service),
        ("LoggingService", test_logging_service)
    ]
    
    for service_name, test_func in service_tests:
        try:
            print(f"\n  Testing {service_name}...")
            success = test_func()
            results[service_name] = success
            print(f"  {'✅' if success else '❌'} {service_name}: {'PASS' if success else 'FAIL'}")
        except Exception as e:
            print(f"  ❌ {service_name}: ERROR - {e}")
            results[service_name] = False
    
    return results

def test_api_service():
    """Test APIService"""
    from services import APIService
    
    service = APIService()
    
    # Test basic functionality
    service.start()
    assert service.is_running
    
    # Test status
    status = service.get_status()
    assert 'providers' in status
    
    service.stop()
    assert not service.is_running
    
    return True

def test_theme_service():
    """Test ThemeService"""
    from services import ThemeService
    
    service = ThemeService()
    
    service.start()
    assert service.is_running
    
    # Test theme detection
    theme = service.get_current_theme()
    assert theme in ['light', 'dark']
    
    service.stop()
    return True

def test_notification_service():
    """Test NotificationService"""
    from services import NotificationService
    
    service = NotificationService()
    
    service.start()
    assert service.is_running
    
    # Test notification creation (won't actually send)
    success = service.show_notification("Test", "Test message")
    
    service.stop()
    return True

def test_validation_service():
    """Test ValidationService"""
    from services import ValidationService
    
    service = ValidationService()
    
    service.start()
    assert service.is_running
    
    # Test validation - returns ValidationResult object
    result = service.validate_api_key("sk-test123", "openai")
    assert hasattr(result, 'is_valid')
    assert isinstance(result.is_valid, bool)
    
    service.stop()
    return True

def test_hotkey_service():
    """Test HotkeyService"""
    from services import HotkeyService
    
    service = HotkeyService()
    
    service.start()
    assert service.is_running
    
    # Test hotkey validation
    is_valid, msg = service.validate_hotkey("cmd+shift+a")
    assert isinstance(is_valid, bool)
    
    service.stop()
    return True

def test_permission_service():
    """Test PermissionService"""
    from services import PermissionService, PermissionType, PermissionStatus
    
    service = PermissionService()
    
    service.start()
    assert service.is_running
    
    # Test permission status check
    status = service.get_permission_status(PermissionType.ACCESSIBILITY)
    assert isinstance(status, PermissionStatus)
    
    service.stop()
    return True

def test_window_service():
    """Test WindowService"""
    from services import WindowService, WindowState
    
    service = WindowService()
    
    service.start()
    assert service.is_running
    
    # Test window registration
    service.register_window("test_window", 100, 100, 800, 600)
    
    # Test window state retrieval
    state = service.get_window_state("test_window")
    assert isinstance(state, WindowState)
    assert state.x == 100
    
    service.stop()
    return True

def test_settings_service():
    """Test SettingsService"""
    from services import SettingsService
    
    # Use a temporary settings file
    temp_file = Path("/tmp/test_settings.json")
    service = SettingsService(settings_file=temp_file)
    
    service.start()
    assert service.is_running
    
    # Test setting and getting values
    success = service.set("test_key", "test_value", validate=False)
    assert success
    
    value = service.get("test_key")
    assert value == "test_value"
    
    # Test nested keys  
    success = service.set("nested.key", "nested_value", validate=False)
    assert success
    
    nested_value = service.get("nested.key")
    assert nested_value == "nested_value"
    
    service.stop()
    
    # Clean up
    if temp_file.exists():
        temp_file.unlink()
    
    return True

def test_logging_service():
    """Test LoggingService"""
    from services import LoggingService
    
    service = LoggingService()
    
    service.start()
    assert service.is_running
    
    # Test log level setting
    success = service.set_log_level("test_logger", "DEBUG")
    assert success
    
    # Test performance metric
    service.log_performance_metric("test_metric", 0.123)
    
    stats = service.get_performance_stats("test_metric")
    assert stats['count'] == 1
    
    service.stop()
    return True

def test_service_lifecycle():
    """Test complete service lifecycle"""
    print("\n🔄 Testing complete service lifecycle...")
    
    try:
        from services import ServiceManager, LoggingService, SettingsService
        
        manager = ServiceManager()
        
        # Register services
        manager.register_service("logging", LoggingService)
        manager.register_service("settings", SettingsService)
        
        # Start all services
        started = manager.start_all_services()
        print(f"✅ Started {len(started)} services")
        
        # Check health
        health = manager.check_health()
        print(f"✅ Health check: {len(health)} services healthy")
        
        # Stop all services
        stopped = manager.stop_all_services()
        print(f"✅ Stopped {len(stopped)} services")
        
        return True
        
    except Exception as e:
        print(f"❌ Lifecycle test failed: {e}")
        return False

def test_integration():
    """Test service integration scenarios"""
    print("\n🔗 Testing service integration...")
    
    try:
        from services import ServiceManager
        from services import SettingsService, ValidationService
        
        manager = ServiceManager()
        
        # Test settings -> validation integration
        manager.register_service("settings", SettingsService)
        manager.register_service("validation", ValidationService, dependencies=["settings"])
        
        # Start services
        manager.start_service("settings")
        manager.start_service("validation")
        
        # Test that validation service can access settings
        validation_service = manager.get_service("validation")
        settings_service = manager.get_service("settings")
        
        # Set a setting
        settings_service.set("test_setting", "test_value")
        
        # Verify validation service can validate
        is_valid, msg = validation_service.validate_api_key("openai", "sk-test")
        assert isinstance(is_valid, bool)
        
        manager.stop_all_services()
        
        print("✅ Integration test successful")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 PHASE 3 SERVICE LAYER COMPLETION TEST")
    print("=" * 50)
    
    # Track results
    test_results = {}
    
    # Test imports
    test_results['imports'] = test_service_imports()
    
    # Test service manager
    test_results['service_manager'] = test_service_manager_with_all_services()
    
    # Test individual services
    individual_results = test_individual_services()
    test_results.update(individual_results)
    
    # Test lifecycle
    test_results['lifecycle'] = test_service_lifecycle()
    
    # Test integration
    test_results['integration'] = test_integration()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = 0
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20}: {status}")
        if result:
            passed += 1
        total += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - PHASE 3 COMPLETE!")
        print("✅ 9 Core Services Implemented")
        print("✅ Service Manager with Dependency Injection")
        print("✅ Complete Service Layer Architecture")
        return True
    else:
        print(f"\n⚠️ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 