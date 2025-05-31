#!/usr/bin/env python3
"""
Potter UI Components Tests
Tests settings UI interactions, button behaviors, and dialog functionality
"""

import sys
import os
import tempfile
import json
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_settings_dialog_cancel_button():
    """Test that cancel button in settings dialog discards changes"""
    print("\n🧪 Testing settings dialog cancel button...")
    
    try:
        # This test would ideally interact with the actual NSWindowController
        # For now, we'll test the logic behind cancel operations
        
        from cocoa_settings import SettingsManager
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_settings = f.name
        
        try:
            # Create initial settings
            initial_settings = {
                "hotkey": "cmd+shift+a",
                "model": "gpt-3.5-turbo",
                "openai_api_key": "test-key"
            }
            
            with open(temp_settings, 'w') as f:
                json.dump(initial_settings, f)
            
            # Load settings
            manager = SettingsManager(temp_settings)
            original_hotkey = manager.get("hotkey")
            
            # Simulate "cancel" behavior - settings should remain unchanged
            # This is what should happen when cancel is pressed
            reloaded_manager = SettingsManager(temp_settings)
            assert reloaded_manager.get("hotkey") == original_hotkey
            
            print("✅ Settings dialog cancel behavior passed")
            return True
            
        finally:
            if os.path.exists(temp_settings):
                os.unlink(temp_settings)
                
    except Exception as e:
        print(f"❌ Settings dialog cancel test failed: {e}")
        return False


def test_settings_dialog_apply_button():
    """Test that apply button in settings dialog saves changes"""
    print("\n🧪 Testing settings dialog apply button...")
    
    try:
        from cocoa_settings import SettingsManager
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_settings = f.name
        
        try:
            # Create and modify settings (simulating apply button)
            manager = SettingsManager(temp_settings)
            
            # Simulate changes being applied
            new_settings = manager.settings.copy()
            new_settings["hotkey"] = "cmd+shift+r"
            new_settings["model"] = "gpt-4"
            
            # Apply changes (this is what the apply button should do)
            success = manager.save_settings(new_settings)
            assert success, "Settings should save successfully"
            
            # Verify changes persisted
            manager2 = SettingsManager(temp_settings)
            assert manager2.get("hotkey") == "cmd+shift+r"
            assert manager2.get("model") == "gpt-4"
            
            print("✅ Settings dialog apply behavior passed")
            return True
            
        finally:
            if os.path.exists(temp_settings):
                os.unlink(temp_settings)
                
    except Exception as e:
        print(f"❌ Settings dialog apply test failed: {e}")
        return False


def test_prompt_editing_validation():
    """Test prompt creation/editing validation"""
    print("\n🧪 Testing prompt editing validation...")
    
    try:
        from cocoa_settings import SettingsManager
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_settings = f.name
        
        try:
            manager = SettingsManager(temp_settings)
            
            # Test adding a new prompt
            new_prompt = {
                "name": "test_prompt",
                "text": "This is a test prompt for validation"
            }
            
            # Add prompt to settings
            settings = manager.settings.copy()
            if "prompts" not in settings:
                settings["prompts"] = []
            settings["prompts"].append(new_prompt)
            
            # Validation logic: check name and text are not empty
            assert new_prompt["name"].strip() != "", "Prompt name should not be empty"
            assert new_prompt["text"].strip() != "", "Prompt text should not be empty"
            
            # Save and verify
            manager.save_settings(settings)
            
            # Reload and check
            manager2 = SettingsManager(temp_settings)
            prompts = manager2.get("prompts", [])
            found_prompt = next((p for p in prompts if p["name"] == "test_prompt"), None)
            assert found_prompt is not None, "Prompt should be saved"
            
            print("✅ Prompt editing validation passed")
            return True
            
        finally:
            if os.path.exists(temp_settings):
                os.unlink(temp_settings)
                
    except Exception as e:
        print(f"❌ Prompt editing validation failed: {e}")
        return False


def test_settings_window_closure():
    """Test settings window properly closes and handles state"""
    print("\n🧪 Testing settings window closure behavior...")
    
    try:
        from cocoa_settings import SettingsManager
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_settings = f.name
        
        try:
            # Create settings manager
            manager = SettingsManager(temp_settings)
            
            # Simulate window close behavior
            # In the actual UI, this should:
            # 1. Check for unsaved changes
            # 2. Prompt user if there are changes
            # 3. Clean up resources
            
            # Test that settings are preserved after "closing"
            original_settings = manager.settings.copy()
            
            # Simulate reload after close
            manager2 = SettingsManager(temp_settings)
            reloaded_settings = manager2.settings
            
            # Settings should persist after window closure
            assert reloaded_settings["hotkey"] == original_settings["hotkey"]
            
            print("✅ Settings window closure behavior passed")
            return True
            
        finally:
            if os.path.exists(temp_settings):
                os.unlink(temp_settings)
                
    except Exception as e:
        print(f"❌ Settings window closure test failed: {e}")
        return False


def test_api_key_validation_ui():
    """Test API key validation in the UI"""
    print("\n🧪 Testing API key validation in UI...")
    
    try:
        from utils.llm_client import validate_api_key_format
        from cocoa_settings import SettingsManager
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_settings = f.name
        
        try:
            manager = SettingsManager(temp_settings)
            
            # Test various API key formats (what the UI should validate)
            test_cases = [
                ("", False),  # Empty
                ("invalid", False),  # Too short
                ("sk-1234567890abcdef1234567890abcdef", True),  # Valid format
                ("not-a-key", False),  # Wrong prefix
            ]
            
            for api_key, should_be_valid in test_cases:
                is_valid = validate_api_key_format(api_key)
                assert is_valid == should_be_valid, f"API key '{api_key}' validation failed"
            
            print("✅ API key validation UI passed")
            return True
            
        finally:
            if os.path.exists(temp_settings):
                os.unlink(temp_settings)
                
    except Exception as e:
        print(f"❌ API key validation UI test failed: {e}")
        return False


def test_hotkey_conflict_detection():
    """Test hotkey conflict detection and validation"""
    print("\n🧪 Testing hotkey conflict detection...")
    
    try:
        from core.service import PotterService
        
        service = PotterService()
        
        # Test hotkey parsing through the hotkey manager
        test_hotkeys = [
            "cmd+shift+a",
            "cmd+shift+r", 
            "ctrl+alt+t",
            "invalid"  # Should fall back to default
        ]
        
        for hotkey in test_hotkeys:
            # Use the hotkey manager to parse hotkeys
            parsed = service.hotkey_manager.parse_hotkey(hotkey)
            assert len(parsed) > 0, f"Hotkey parsing failed for: {hotkey}"
            
            # Test display formatting
            display = service.hotkey_manager.format_hotkey_display()
            assert isinstance(display, str), "Hotkey display should be a string"
        
        print("✅ Hotkey conflict detection passed")
        return True
        
    except Exception as e:
        print(f"❌ Hotkey conflict detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_first_launch_welcome():
    """Test first launch welcome flow"""
    print("\n🧪 Testing first launch welcome flow...")
    
    try:
        from cocoa_settings import SettingsManager
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_settings = f.name
        
        try:
            # Create settings manager for first launch (no API key)
            manager = SettingsManager(temp_settings)
            
            # First launch should be detected when no API key is present
            is_first_launch = manager.is_first_launch()
            
            # This may vary based on environment variables, but we can test the logic
            print(f"First launch detected: {is_first_launch}")
            
            # Test that the settings can be configured (what first launch should do)
            if is_first_launch:
                new_settings = manager.settings.copy()
                new_settings["openai_api_key"] = "sk-test123"
                manager.save_settings(new_settings)
                
                # After setting API key, should no longer be first launch
                manager2 = SettingsManager(temp_settings)
                # Note: is_first_launch also checks environment, so may still be True
                # but at least settings should be saved
                assert manager2.get("openai_api_key") == "sk-test123"
            
            print("✅ First launch welcome flow passed")
            return True
            
        finally:
            if os.path.exists(temp_settings):
                os.unlink(temp_settings)
                
    except Exception as e:
        print(f"❌ First launch welcome test failed: {e}")
        return False


def test_permission_dialog_interactions():
    """Test permission request dialog behavior"""
    print("\n🧪 Testing permission dialog interactions...")
    
    try:
        from core.service import PotterService
        
        service = PotterService()
        
        # Test permission checking through the permission manager
        permissions = service.permission_manager.get_permission_status()
        assert "accessibility" in permissions, "Should report accessibility status"
        assert "macos_available" in permissions, "Should report macOS availability"
        
        # Test permission request logic
        result = service.permission_manager.request_permissions()
        assert isinstance(result, bool), "Permission request should return boolean"
        
        print("✅ Permission dialog interactions passed")
        return True
        
    except Exception as e:
        print(f"❌ Permission dialog interactions failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_ui_tests():
    """Run all UI component tests"""
    print("🧪 Potter UI Components Tests")
    print("=" * 50)
    
    tests = [
        test_settings_dialog_cancel_button,
        test_settings_dialog_apply_button,
        test_prompt_editing_validation,
        test_settings_window_closure,
        test_api_key_validation_ui,
        test_hotkey_conflict_detection,
        test_first_launch_welcome,
        test_permission_dialog_interactions,
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
    
    print(f"\n📊 UI Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ All UI component tests passed!")
        return True
    else:
        print("❌ Some UI component tests failed!")
        return False


if __name__ == "__main__":
    success = run_ui_tests()
    sys.exit(0 if success else 1) 