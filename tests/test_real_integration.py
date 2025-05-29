#!/usr/bin/env python3
"""
Potter Real Integration Tests
Tests actual component integration without heavy mocking
These tests catch real issues that mocked tests miss
"""

import sys
import os
import tempfile
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_real_settings_window_creation():
    """Test that settings window can actually be created (no mocking)"""
    print("\n🧪 Testing REAL settings window creation...")
    
    try:
        from cocoa_settings import SettingsManager, show_settings
        
        # Create settings manager
        settings_manager = SettingsManager()
        
        # Try to create the actual settings window
        settings_window = show_settings(settings_manager)
        
        # Verify window was created
        if settings_window and settings_window.window():
            print("✅ Real settings window created successfully")
            
            # Test that we can access basic properties
            window = settings_window.window()
            title = window.title()
            print(f"   Window title: {title}")
            
            # Clean up
            window.close()
            return True
        else:
            print("❌ Settings window creation returned None")
            return False
            
    except Exception as e:
        print(f"❌ Real settings window creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_real_service_settings_integration():
    """Test that PotterService can actually open settings (no mocking)"""
    print("\n🧪 Testing REAL service-settings integration...")
    
    try:
        from core.service import PotterService
        
        # Create service (this loads actual components)
        service = PotterService()
        
        # Test that show_preferences method exists and doesn't crash
        # Note: We won't actually call it to avoid opening windows during tests
        assert hasattr(service, '_show_preferences'), "Service should have _show_preferences method"
        
        # Test that the method is callable
        import inspect
        assert inspect.ismethod(service._show_preferences), "Should be a callable method"
        
        print("✅ Service-settings integration structure verified")
        return True
        
    except Exception as e:
        print(f"❌ Service-settings integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_real_component_imports():
    """Test that all components can actually be imported (no mocking)"""
    print("\n🧪 Testing REAL component imports...")
    
    try:
        # Test core imports
        from core.service import PotterService
        from core.permissions import PermissionManager
        from core.hotkeys import HotkeyManager
        from core.text_processor import TextProcessor
        
        # Test UI imports
        from ui.tray_icon import TrayIconManager
        from ui.notifications import NotificationManager
        
        # Test utils imports
        from utils.instance_checker import SingleInstanceChecker
        from utils.openai_client import OpenAIClientManager
        
        # Test settings UI import (the critical one)
        from cocoa_settings import SettingsManager, show_settings
        
        # Verify classes can be referenced (prevents "imported but unused" errors)
        classes = [
            PotterService, PermissionManager, HotkeyManager, TextProcessor,
            TrayIconManager, NotificationManager, SingleInstanceChecker,
            OpenAIClientManager, SettingsManager, show_settings
        ]
        
        # Verify all are callable/classes
        for cls in classes:
            assert callable(cls), f"{cls.__name__} should be callable"
        
        print("✅ All real component imports successful")
        return True
        
    except Exception as e:
        print(f"❌ Real component imports failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_real_settings_persistence():
    """Test that settings actually persist to disk (no mocking)"""
    print("\n🧪 Testing REAL settings persistence...")
    
    try:
        from cocoa_settings import SettingsManager
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_settings = f.name
        
        try:
            # Create and modify settings
            manager = SettingsManager(temp_settings)
            
            # Make actual changes
            new_settings = manager.settings.copy()
            new_settings["hotkey"] = "cmd+shift+z"
            new_settings["model"] = "gpt-4-turbo"
            new_settings["test_flag"] = True
            
            # Save settings
            success = manager.save_settings(new_settings)
            assert success, "Settings save should succeed"
            
            # Create new manager instance and verify persistence
            manager2 = SettingsManager(temp_settings)
            assert manager2.get("hotkey") == "cmd+shift+z"
            assert manager2.get("model") == "gpt-4-turbo"
            assert manager2.get("test_flag") is True
            
            # Verify file actually exists on disk
            assert os.path.exists(temp_settings), "Settings file should exist"
            with open(temp_settings, 'r') as f:
                file_content = json.load(f)
                assert file_content["hotkey"] == "cmd+shift+z"
            
            print("✅ Real settings persistence verified")
            return True
            
        finally:
            if os.path.exists(temp_settings):
                os.unlink(temp_settings)
                
    except Exception as e:
        print(f"❌ Real settings persistence failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_real_pyobjc_integration():
    """Test that PyObjC classes can actually be instantiated (no mocking)"""
    print("\n🧪 Testing REAL PyObjC integration...")
    
    try:
        from cocoa_settings import SettingsManager, SettingsWindow
        
        # Create settings manager
        settings_manager = SettingsManager()
        
        # Try to create the actual NSWindowController subclass
        settings_window = SettingsWindow.alloc().initWithSettingsManager_(settings_manager)
        
        # Verify it's actually a PyObjC object
        assert settings_window is not None, "SettingsWindow should be created"
        
        # Test that PyObjC methods are accessible
        assert hasattr(settings_window, 'window'), "Should have window method"
        assert hasattr(settings_window, 'showWindow_'), "Should have showWindow_ method"
        
        print("✅ Real PyObjC integration verified")
        return True
        
    except Exception as e:
        print(f"❌ Real PyObjC integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_real_api_key_detection():
    """Test that API key detection actually works (no mocking)"""
    print("\n🧪 Testing REAL API key detection...")
    
    try:
        from utils.openai_client import OpenAIClientManager
        from cocoa_settings import SettingsManager
        import os
        
        # Save original env var
        original_key = os.environ.get('OPENAI_API_KEY')
        
        try:
            # Test with no API key anywhere
            if 'OPENAI_API_KEY' in os.environ:
                del os.environ['OPENAI_API_KEY']
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                temp_settings = f.name
            
            try:
                # Create settings without API key
                settings = {"openai_api_key": ""}
                with open(temp_settings, 'w') as f:
                    json.dump(settings, f)
                
                settings_manager = SettingsManager(temp_settings)
                
                # Create OpenAI manager without arguments (like the service does)
                openai_manager = OpenAIClientManager()
                
                # Try to setup with empty API key (should fail)
                api_key = settings_manager.get("openai_api_key", "").strip()
                if api_key:  # Should be empty
                    openai_manager.setup_client(api_key)
                
                # Should detect no API key
                assert not openai_manager.is_available(), "Should detect missing API key"
                
                # Test first launch detection
                assert settings_manager.is_first_launch(), "Should detect first launch"
                
                print("✅ Real API key detection verified")
                return True
                
            finally:
                if os.path.exists(temp_settings):
                    os.unlink(temp_settings)
                
        finally:
            # Restore original env var
            if original_key:
                os.environ['OPENAI_API_KEY'] = original_key
                
    except Exception as e:
        print(f"❌ Real API key detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_real_integration_tests():
    """Run all real integration tests (minimal mocking)"""
    print("=" * 60)
    print("🔧 POTTER REAL INTEGRATION TESTS (No Heavy Mocking)")
    print("=" * 60)
    
    tests = [
        test_real_component_imports,
        test_real_pyobjc_integration,
        test_real_settings_window_creation,
        test_real_service_settings_integration,
        test_real_settings_persistence,
        test_real_api_key_detection,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 REAL INTEGRATION TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 ALL REAL INTEGRATION TESTS PASSED!")
        return True
    else:
        print(f"💥 {failed} REAL INTEGRATION TESTS FAILED")
        print("These failures indicate actual integration problems, not test issues.")
        return False


if __name__ == "__main__":
    success = run_real_integration_tests()
    sys.exit(0 if success else 1) 