#!/usr/bin/env python3
"""
Test script to verify the fixes for the three reported bugs:
1. Anthropic and Gemini key validation
2. OpenAI API key not being recognized after saving
3. Detailed error messages in tray icon
"""

import sys
import os
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_api_key_validation_fixes():
    """Test Bug #1: Anthropic and Gemini key validation fixes"""
    print("🧪 Testing Bug #1: API Key Validation Fixes")
    print("=" * 60)
    
    try:
        from utils.llm_client import validate_api_key_format
        
        # Test cases for different providers
        test_cases = [
            # OpenAI keys
            ("sk-proj-" + "x" * 45, "openai", True, "Valid OpenAI key format"),
            ("sk-" + "x" * 47, "openai", True, "Valid OpenAI key format (old style)"),
            ("sk-short", "openai", False, "Too short OpenAI key"),
            ("invalid-key", "openai", False, "Invalid OpenAI key prefix"),
            
            # Anthropic keys
            ("sk-ant-" + "x" * 95, "anthropic", True, "Valid Anthropic key format"),
            ("sk-ant-api03_abcdefghijklmnopqrstuvwxyz0123456789abcdefghijklmnopqrstuvwxyz0123456789abcdefghijklmnop", "anthropic", True, "Real Anthropic key format"),
            ("sk-ant-short", "anthropic", False, "Too short Anthropic key"),
            ("sk-wrong-" + "x" * 95, "anthropic", False, "Wrong Anthropic key prefix"),
            
            # Google/Gemini keys
            ("AIzaSyA" + "x" * 30, "gemini", True, "Valid Google API key format"),
            ("AIzaSyA" + "x" * 30, "google", True, "Valid Google API key format (google provider name)"),
            ("AIza" + "x" * 31, "gemini", True, "Valid Google API key format (minimal)"),
            ("AIzaSyB" + "x" * 27, "gemini", False, "Google key must start with AIza (this doesn't)"),
            ("AIza123", "gemini", False, "Too short Google key"),
            ("wrong" + "x" * 31, "gemini", False, "Wrong Google key format"),
        ]
        
        all_passed = True
        for api_key, provider, expected, description in test_cases:
            result = validate_api_key_format(api_key, provider)
            status = "✅" if result == expected else "❌"
            print(f"{status} {description}: {provider} key validation = {result}")
            if result != expected:
                all_passed = False
                print(f"   Expected: {expected}, Got: {result}")
        
        if all_passed:
            print("\n✅ Bug #1 FIXED: API key validation now works correctly!")
        else:
            print("\n❌ Bug #1 NOT FIXED: Some validation tests failed")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error testing API key validation: {e}")
        return False


def test_api_key_loading_fixes():
    """Test Bug #2: OpenAI API key loading after saving"""
    print("\n🧪 Testing Bug #2: API Key Loading Fixes")
    print("=" * 60)
    
    try:
        from settings.settings_manager import SettingsManager
        
        # Create temporary settings file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_settings_file = f.name
        
        try:
            # Create settings manager
            manager = SettingsManager(temp_settings_file)
            
            # Test saving and loading different provider API keys
            test_keys = {
                "openai": "sk-proj-" + "x" * 45,
                "anthropic": "sk-ant-" + "x" * 95,
                "gemini": "AIzaSyA" + "x" * 30
            }
            
            all_passed = True
            for provider, test_key in test_keys.items():
                print(f"\n🔑 Testing {provider} API key storage and retrieval...")
                
                # Set the provider and API key
                manager.settings["llm_provider"] = provider
                manager.settings[f"{provider}_api_key"] = test_key
                
                # Save settings
                save_success = manager.save_settings(manager.settings)
                print(f"   Save settings: {'✅' if save_success else '❌'}")
                
                # Reload settings manager to simulate app restart
                manager2 = SettingsManager(temp_settings_file)
                
                # Check provider
                loaded_provider = manager2.get_current_provider()
                provider_ok = loaded_provider == provider
                print(f"   Provider loaded: {loaded_provider} {'✅' if provider_ok else '❌'}")
                
                # Check API key
                loaded_key = manager2.get_current_api_key()
                key_ok = loaded_key == test_key
                print(f"   API key loaded: {'✅' if key_ok else '❌'} (length: {len(loaded_key)})")
                
                if not (save_success and provider_ok and key_ok):
                    all_passed = False
                    print(f"   ❌ Failed for {provider}")
            
            if all_passed:
                print("\n✅ Bug #2 FIXED: API keys are properly saved and loaded!")
            else:
                print("\n❌ Bug #2 NOT FIXED: API key loading issues remain")
            
            return all_passed
            
        finally:
            # Cleanup
            if os.path.exists(temp_settings_file):
                os.unlink(temp_settings_file)
        
    except Exception as e:
        print(f"❌ Error testing API key loading: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_message_improvements():
    """Test Bug #3: Detailed error messages in tray icon"""
    print("\n🧪 Testing Bug #3: Detailed Error Message Improvements")
    print("=" * 60)
    
    try:
        from core.text_processor import TextProcessor
        from utils.llm_client import LLMClientManager
        
        # Create text processor with mock LLM manager
        llm_manager = LLMClientManager()
        processor = TextProcessor(llm_manager)
        
        # Test error capture
        errors_captured = []
        
        def mock_error_callback(error_message):
            errors_captured.append(error_message)
            print(f"   Error captured: {error_message}")
        
        def mock_notification_callback(title, message, is_error):
            print(f"   Notification: {title} - {message} (error: {is_error})")
        
        # Test 1: No API key configured
        print("\n🧪 Test 1: No API key configured error")
        success = processor.process_clipboard_text(
            notification_callback=mock_notification_callback,
            error_callback=mock_error_callback
        )
        
        test1_passed = (
            not success and 
            len(errors_captured) > 0 and 
            "API key not configured" in errors_captured[0]
        )
        print(f"   Result: {'✅' if test1_passed else '❌'} - Specific API key error captured")
        
        # Test 2: Check error message specificity
        print("\n🧪 Test 2: Error message specificity")
        
        if errors_captured:
            error_msg = errors_captured[0]
            # Should contain provider name, not just generic "LLM"
            specific_error = "Openai" in error_msg or any(provider in error_msg for provider in ["OpenAI", "Anthropic", "Google", "Gemini"])
            print(f"   Specific provider in error: {'✅' if specific_error else '❌'}")
            print(f"   Error message: '{error_msg}'")
        else:
            specific_error = False
            print("   No errors captured to check: ❌")
        
        overall_passed = test1_passed and specific_error
        
        if overall_passed:
            print("\n✅ Bug #3 FIXED: Detailed error messages are now provided!")
        else:
            print("\n❌ Bug #3 NOT FIXED: Error messages still generic")
        
        return overall_passed
        
    except Exception as e:
        print(f"❌ Error testing error messages: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all bug fix tests"""
    print("🐛 Testing Bug Fixes for Potter")
    print("=" * 80)
    
    # Test all three bugs
    bug1_fixed = test_api_key_validation_fixes()
    bug2_fixed = test_api_key_loading_fixes()
    bug3_fixed = test_error_message_improvements()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY OF BUG FIXES")
    print("=" * 80)
    print(f"Bug #1 - API Key Validation: {'✅ FIXED' if bug1_fixed else '❌ NOT FIXED'}")
    print(f"Bug #2 - API Key Loading: {'✅ FIXED' if bug2_fixed else '❌ NOT FIXED'}")
    print(f"Bug #3 - Error Messages: {'✅ FIXED' if bug3_fixed else '❌ NOT FIXED'}")
    
    all_fixed = bug1_fixed and bug2_fixed and bug3_fixed
    print(f"\nOverall Status: {'🎉 ALL BUGS FIXED!' if all_fixed else '⚠️ Some bugs remain'}")
    
    return all_fixed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 