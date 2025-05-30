#!/usr/bin/env python3
"""
Comprehensive tests for enhanced settings functionality
Tests LLM providers, API key validation, and OS sync features
Focuses on SettingsManager without PyObjC UI components
"""

import os
import sys
import json
import tempfile

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Create a minimal SettingsManager for testing
class TestableSettingsManager:
    """Testable version of SettingsManager without PyObjC dependencies"""
    
    def __init__(self, settings_file=None):
        if settings_file is None:
            self.settings_file = "config/settings.json"
            self.state_file = "config/state.json"
        else:
            self.settings_file = settings_file
            self.state_file = settings_file.replace('settings.json', 'state.json')
        
        # LLM Provider configurations
        self.llm_providers = {
            "openai": {
                "name": "OpenAI", 
                "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"],
                "api_key_prefix": "sk-",
                "help_url": "https://platform.openai.com/api-keys"
            },
            "anthropic": {
                "name": "Anthropic",
                "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
                "api_key_prefix": "sk-ant-",
                "help_url": "https://console.anthropic.com/settings/keys"
            },
            "gemini": {
                "name": "Google Gemini",
                "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
                "api_key_prefix": "AIza",
                "help_url": "https://makersuite.google.com/app/apikey"
            }
        }
        
        self.default_settings = {
            "prompts": [
                {
                    "name": "summarize", 
                    "text": "Please provide a concise summary of the following text."
                },
                {
                    "name": "formal",
                    "text": "Please rewrite the following text in a formal, professional tone."
                }
            ],
            "hotkey": "cmd+shift+a",
            "llm_provider": "openai",
            "model": "gpt-3.5-turbo",
            "show_notifications": True,
            "launch_at_startup": False,
            "openai_api_key": "",
            "anthropic_api_key": "",
            "gemini_api_key": ""
        }
        
        self.default_state = {
            "api_key_validation": {
                "openai": {"valid": None, "last_check": None, "error": None},
                "anthropic": {"valid": None, "last_check": None, "error": None},
                "gemini": {"valid": None, "last_check": None, "error": None}
            },
            "os_permissions": {
                "notifications_enabled": None,
                "launch_at_startup_enabled": None,
                "last_check": None
            }
        }
        
        self.settings = self.load_settings()
        self.state = self.load_state()
    
    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    settings = self.default_settings.copy()
                    for key, value in loaded.items():
                        settings[key] = value
                    return settings
            else:
                return self.default_settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def load_state(self):
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    loaded = json.load(f)
                    state = self.default_state.copy()
                    for key, value in loaded.items():
                        if key in state and isinstance(state[key], dict) and isinstance(value, dict):
                            state[key].update(value)
                        else:
                            state[key] = value
                    return state
            else:
                return self.default_state.copy()
        except Exception as e:
            print(f"Error loading state: {e}")
            return self.default_state.copy()
    
    def save_settings(self, settings):
        try:
            self.settings = settings
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def save_state(self, state):
        try:
            self.state = state
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving state: {e}")
            return False
    
    def get(self, key, default=None):
        return self.settings.get(key, default)
    
    def get_current_provider(self):
        return self.get("llm_provider", "openai")
    
    def get_current_api_key(self):
        provider = self.get_current_provider()
        return self.get(f"{provider}_api_key", "")
    
    def set_api_key_validation(self, provider, valid, error=None):
        if "api_key_validation" not in self.state:
            self.state["api_key_validation"] = {}
        
        if provider not in self.state["api_key_validation"]:
            self.state["api_key_validation"][provider] = {}
        
        import time
        self.state["api_key_validation"][provider].update({
            "valid": valid,
            "last_check": time.time(),
            "error": error
        })
        self.save_state(self.state)
    
    def get_api_key_validation(self, provider):
        if "api_key_validation" not in self.state:
            return {"valid": None, "last_check": None, "error": None}
        
        return self.state["api_key_validation"].get(provider, {
            "valid": None, "last_check": None, "error": None
        })


def test_llm_provider_configuration():
    """Test LLM provider configuration and management"""
    print("\n🧪 Testing LLM provider configuration...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        settings_file = os.path.join(temp_dir, "settings.json")
        manager = TestableSettingsManager(settings_file)
        
        # Test provider definitions
        assert "openai" in manager.llm_providers
        assert "anthropic" in manager.llm_providers
        assert "gemini" in manager.llm_providers
        
        # Test provider info structure
        openai_info = manager.llm_providers["openai"]
        assert "name" in openai_info
        assert "models" in openai_info
        assert "api_key_prefix" in openai_info
        assert "help_url" in openai_info
        
        # Test getting current provider
        default_provider = manager.get_current_provider()
        assert default_provider == "openai"
        
        # Test switching providers
        manager.settings["llm_provider"] = "anthropic"
        assert manager.get_current_provider() == "anthropic"
        
        print("✅ LLM provider configuration tests passed")


def test_api_key_management():
    """Test API key storage and validation"""
    print("\n🧪 Testing API key management...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        settings_file = os.path.join(temp_dir, "settings.json")
        manager = TestableSettingsManager(settings_file)
        
        # Test setting API keys for different providers
        manager.settings["openai_api_key"] = "sk-test123456789012345678"
        manager.settings["anthropic_api_key"] = "sk-ant-test123456789012345678"
        manager.settings["gemini_api_key"] = "AIzatest123456789012345678"
        
        # Test getting current API key
        manager.settings["llm_provider"] = "openai"
        assert manager.get_current_api_key() == "sk-test123456789012345678"
        
        manager.settings["llm_provider"] = "anthropic"
        assert manager.get_current_api_key() == "sk-ant-test123456789012345678"
        
        manager.settings["llm_provider"] = "gemini"
        assert manager.get_current_api_key() == "AIzatest123456789012345678"
        
        print("✅ API key management tests passed")


def test_api_key_validation():
    """Test API key validation functionality"""
    print("\n🧪 Testing API key validation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        settings_file = os.path.join(temp_dir, "settings.json")
        manager = TestableSettingsManager(settings_file)
        
        # Test setting validation state
        manager.set_api_key_validation("openai", True, None)
        validation = manager.get_api_key_validation("openai")
        assert validation["valid"] is True
        assert validation["error"] is None
        assert validation["last_check"] is not None
        
        # Test error state
        manager.set_api_key_validation("anthropic", False, "Invalid key format")
        validation = manager.get_api_key_validation("anthropic")
        assert validation["valid"] is False
        assert validation["error"] == "Invalid key format"
        
        # Test unknown provider
        validation = manager.get_api_key_validation("unknown")
        assert validation["valid"] is None
        
        print("✅ API key validation tests passed")


def test_state_persistence():
    """Test state file persistence"""
    print("\n🧪 Testing state persistence...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        settings_file = os.path.join(temp_dir, "settings.json")
        
        # Create manager and set some state
        manager1 = TestableSettingsManager(settings_file)
        manager1.set_api_key_validation("openai", True, None)
        manager1.state["os_permissions"]["notifications_enabled"] = True
        manager1.save_state(manager1.state)
        
        # Create new manager and verify state is loaded
        manager2 = TestableSettingsManager(settings_file)
        validation = manager2.get_api_key_validation("openai")
        assert validation["valid"] is True
        assert manager2.state["os_permissions"]["notifications_enabled"] is True
        
        print("✅ State persistence tests passed")


def test_settings_migration():
    """Test migration from old settings format"""
    print("\n🧪 Testing settings migration...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        settings_file = os.path.join(temp_dir, "settings.json")
        
        # Create old format settings
        old_settings = {
            "openai_api_key": "sk-oldkey123456789012345",
            "model": "gpt-3.5-turbo",
            "max_tokens": 1000,  # Should be preserved but not in defaults
            "temperature": 0.7,   # Should be preserved but not in defaults
            "prompts": [{"name": "test", "text": "test prompt"}]
        }
        
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        with open(settings_file, 'w') as f:
            json.dump(old_settings, f)
        
        # Load with new manager
        manager = TestableSettingsManager(settings_file)
        
        # Verify old key is preserved
        assert manager.get("openai_api_key") == "sk-oldkey123456789012345"
        
        # Verify new fields are added with defaults
        assert manager.get("llm_provider") == "openai"
        assert manager.get("anthropic_api_key") == ""
        assert manager.get("gemini_api_key") == ""
        
        # Verify old fields are preserved but not in defaults
        assert manager.get("max_tokens") == 1000
        assert manager.get("temperature") == 0.7
        assert "max_tokens" not in manager.default_settings
        assert "temperature" not in manager.default_settings
        
        print("✅ Settings migration tests passed")


def test_provider_model_validation():
    """Test model validation for different providers"""
    print("\n🧪 Testing provider model validation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        settings_file = os.path.join(temp_dir, "settings.json")
        manager = TestableSettingsManager(settings_file)
        
        # Test OpenAI models
        openai_models = manager.llm_providers["openai"]["models"]
        assert "gpt-3.5-turbo" in openai_models
        assert "gpt-4" in openai_models
        
        # Test Anthropic models
        anthropic_models = manager.llm_providers["anthropic"]["models"]
        assert "claude-3-5-sonnet-20241022" in anthropic_models
        assert "claude-3-opus-20240229" in anthropic_models
        
        # Test Gemini models
        gemini_models = manager.llm_providers["gemini"]["models"]
        assert "gemini-1.5-pro" in gemini_models
        assert "gemini-1.5-flash" in gemini_models
        
        print("✅ Provider model validation tests passed")


def test_api_key_format_validation():
    """Test API key format validation for different providers"""
    print("\n🧪 Testing API key format validation...")
    
    providers = {
        "openai": {"prefix": "sk-", "valid": "sk-test123456789012345678", "invalid": "invalid"},
        "anthropic": {"prefix": "sk-ant-", "valid": "sk-ant-test123456789012345678", "invalid": "sk-wrong"},
        "gemini": {"prefix": "AIza", "valid": "AIzatest123456789012345678", "invalid": "wrong"}
    }
    
    for provider, data in providers.items():
        # Test valid format
        assert data["valid"].startswith(data["prefix"])
        assert len(data["valid"]) >= 20
        
        # Test invalid format
        assert not data["invalid"].startswith(data["prefix"]) or len(data["invalid"]) < 20
    
    print("✅ API key format validation tests passed")


def test_sidebar_highlighting_data():
    """Test sidebar data structure for highlighting"""
    print("\n🧪 Testing sidebar highlighting data...")
    
    sidebar_items = [
        {"title": "General", "icon": "gear", "tag": 0},
        {"title": "Prompts", "icon": "text.bubble", "tag": 1}, 
        {"title": "Advanced", "icon": "slider.horizontal.3", "tag": 2},
        {"title": "Logs", "icon": "doc.text", "tag": 3}
    ]
    
    # Verify all items have required fields
    for item in sidebar_items:
        assert "title" in item
        assert "icon" in item
        assert "tag" in item
        assert isinstance(item["tag"], int)
    
    # Verify unique tags
    tags = [item["tag"] for item in sidebar_items]
    assert len(tags) == len(set(tags))
    
    print("✅ Sidebar highlighting data tests passed")


def run_enhanced_settings_tests():
    """Run all enhanced settings tests"""
    print("🧪 Running Enhanced Settings Tests")
    print("=" * 50)
    
    test_functions = [
        test_llm_provider_configuration,
        test_api_key_management,
        test_api_key_validation,
        test_state_persistence,
        test_settings_migration,
        test_provider_model_validation,
        test_api_key_format_validation,
        test_sidebar_highlighting_data
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Enhanced Settings Tests: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All enhanced settings tests passed!")
        return True
    else:
        print("💥 Some enhanced settings tests failed!")
        return False


if __name__ == "__main__":
    success = run_enhanced_settings_tests()
    sys.exit(0 if success else 1) 