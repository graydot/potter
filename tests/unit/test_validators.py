#!/usr/bin/env python3
"""
Unit tests for UI validators
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Import after path setup
from ui.settings.validators.api_key_validator import APIKeyValidator  # noqa: E402
from ui.settings.validators.prompt_validator import PromptValidator  # noqa: E402
from ui.settings.validators.hotkey_validator import HotkeyValidator  # noqa: E402


class TestAPIKeyValidator(unittest.TestCase):
    """Test API key validator"""
    
    def setUp(self):
        self.validator = APIKeyValidator()
    
    def test_validate_format_empty_key(self):
        """Test validation with empty key"""
        is_valid, error = self.validator.validate_format("", "openai")
        self.assertFalse(is_valid)
        self.assertEqual(error, "API key cannot be empty")
    
    def test_validate_format_valid_keys(self):
        """Test validation with valid keys"""
        test_cases = [
            ("sk-" + "x" * 48, "openai"),
            ("sk-ant-" + "x" * 48, "anthropic"),
            ("AIza" + "x" * 35, "google"),
            ("AIza" + "x" * 35, "gemini"),
        ]
        
        for key, provider in test_cases:
            is_valid, error = self.validator.validate_format(key, provider)
            self.assertTrue(is_valid, f"Failed for {provider}")
            self.assertIsNone(error)
    
    def test_validate_format_invalid_keys(self):
        """Test validation with invalid keys"""
        test_cases = [
            ("wrong-prefix", "openai", "OpenAI API keys should start with 'sk-'"),
            ("sk-short", "openai", "OpenAI API keys should start with 'sk-'"),
            ("sk-" + "x" * 48, "anthropic", "Anthropic API keys should start with 'sk-ant-'"),
            ("wrong" + "x" * 35, "google", "Google API keys should start with 'AIza'"),
        ]
        
        for key, provider, expected_msg in test_cases:
            is_valid, error = self.validator.validate_format(key, provider)
            self.assertFalse(is_valid)
            self.assertIn(expected_msg, error)
    
    def test_get_masked_key(self):
        """Test key masking"""
        test_cases = [
            ("", ""),
            ("short", "*****"),
            ("12345678", "********"),
            ("1234567890abcdef", "1234...cdef"),
            ("sk-" + "x" * 48, "sk-x...xxxx"),
        ]
        
        for key, expected in test_cases:
            masked = self.validator.get_masked_key(key)
            self.assertEqual(masked, expected)
    
    @patch.object(APIKeyValidator, '__init__', lambda self: None)
    def test_validate_with_api_success(self):
        """Test API validation success"""
        validator = APIKeyValidator()
        validator.llm_manager = Mock()
        validator.llm_manager.test_api_key.return_value = (True, None)
        
        # Mock validate_format to return success
        with patch.object(validator, 'validate_format', return_value=(True, None)):
            is_valid, error = validator.validate_with_api("test-key", "openai")
            
            self.assertTrue(is_valid)
            self.assertIsNone(error)
            validator.llm_manager.test_api_key.assert_called_once_with("openai", "test-key")


class TestPromptValidator(unittest.TestCase):
    """Test prompt validator"""
    
    def setUp(self):
        self.validator = PromptValidator()
    
    def test_validate_name_empty(self):
        """Test name validation with empty name"""
        is_valid, error = self.validator.validate_name("", [])
        self.assertFalse(is_valid)
        self.assertEqual(error, "Prompt name cannot be empty")
    
    def test_validate_name_too_long(self):
        """Test name validation with too long name"""
        is_valid, error = self.validator.validate_name("a" * 11, [])
        self.assertFalse(is_valid)
        self.assertIn("10 characters or less", error)
    
    def test_validate_name_invalid_chars(self):
        """Test name validation with invalid characters"""
        test_cases = ["test!", "test@", "test-name", "test name", "test.name"]
        
        for name in test_cases:
            is_valid, error = self.validator.validate_name(name, [])
            self.assertFalse(is_valid)
            self.assertIn("letters, numbers, and underscores", error)
    
    def test_validate_name_reserved(self):
        """Test name validation with reserved names"""
        for reserved in self.validator.RESERVED_NAMES:
            is_valid, error = self.validator.validate_name(reserved, [])
            self.assertFalse(is_valid)
            self.assertIn("reserved name", error)
    
    def test_validate_name_duplicate(self):
        """Test name validation with duplicate names"""
        existing = ["test1", "test2", "test3"]
        
        is_valid, error = self.validator.validate_name("test2", existing)
        self.assertFalse(is_valid)
        self.assertIn("already exists", error)
        
        # Case insensitive check
        is_valid, error = self.validator.validate_name("TEST2", existing)
        self.assertFalse(is_valid)
    
    def test_validate_name_duplicate_with_exclude(self):
        """Test name validation with exclude index"""
        existing = ["test1", "test2", "test3"]
        
        # Should be valid when excluding index 1 (test2)
        is_valid, error = self.validator.validate_name("test2", existing, exclude_index=1)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_name_valid(self):
        """Test name validation with valid names"""
        test_cases = ["test", "Test123", "my_prompt", "_private", "a", "a" * 10]
        
        for name in test_cases:
            is_valid, error = self.validator.validate_name(name, [])
            self.assertTrue(is_valid, f"Failed for name: {name}")
            self.assertIsNone(error)
    
    def test_validate_content_empty(self):
        """Test content validation with empty content"""
        is_valid, error = self.validator.validate_content("")
        self.assertFalse(is_valid)
        self.assertEqual(error, "Prompt content cannot be empty")
    
    def test_validate_content_too_short(self):
        """Test content validation with too short content"""
        is_valid, error = self.validator.validate_content("short")
        self.assertFalse(is_valid)
        self.assertIn("at least 10 characters", error)
    
    def test_validate_content_too_long(self):
        """Test content validation with too long content"""
        is_valid, error = self.validator.validate_content("x" * 5001)
        self.assertFalse(is_valid)
        self.assertIn("5000 characters or less", error)
    
    def test_validate_content_placeholder(self):
        """Test content validation with placeholder text"""
        placeholders = ["enter prompt here", "Type your prompt", "PROMPT TEXT"]
        
        for placeholder in placeholders:
            is_valid, error = self.validator.validate_content(placeholder)
            self.assertFalse(is_valid)
            self.assertIn("meaningful prompt", error)
    
    def test_validate_content_valid(self):
        """Test content validation with valid content"""
        is_valid, error = self.validator.validate_content("This is a valid prompt text")
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_sanitize_name(self):
        """Test name sanitization"""
        test_cases = [
            ("test!", "test"),
            ("test name", "testname"),
            ("test-name", "testname"),
            ("test_name", "test_name"),
            ("Test123!", "Test123"),
            ("a" * 20, "a" * 10),  # Truncation
        ]
        
        for input_name, expected in test_cases:
            sanitized = self.validator.sanitize_name(input_name)
            self.assertEqual(sanitized, expected)


class TestHotkeyValidator(unittest.TestCase):
    """Test hotkey validator"""
    
    def setUp(self):
        self.validator = HotkeyValidator()
    
    def test_validate_empty(self):
        """Test validation with empty hotkey"""
        is_valid, error = self.validator.validate("")
        self.assertFalse(is_valid)
        self.assertEqual(error, "Hotkey cannot be empty")
    
    def test_validate_no_modifier(self):
        """Test validation with no modifier"""
        is_valid, error = self.validator.validate("a")
        self.assertFalse(is_valid)
        # The error could be either "Invalid hotkey format" or about modifiers
        self.assertTrue(
            "Invalid hotkey format" in error or "at least one modifier" in error,
            f"Unexpected error: {error}"
        )
    
    def test_validate_invalid_key(self):
        """Test validation with invalid key"""
        test_cases = ["cmd+", "cmd+!", "cmd+space+bar", "cmd++"]
        
        for hotkey in test_cases:
            is_valid, error = self.validator.validate(hotkey)
            self.assertFalse(is_valid)
    
    def test_validate_reserved(self):
        """Test validation with reserved hotkeys"""
        reserved = ["cmd+q", "cmd+w", "cmd+space", "cmd+shift+3"]
        
        for hotkey in reserved:
            is_valid, error = self.validator.validate(hotkey)
            self.assertFalse(is_valid)
            self.assertIn("reserved hotkey", error)
    
    def test_validate_valid(self):
        """Test validation with valid hotkeys"""
        valid_hotkeys = [
            "cmd+a", "cmd+shift+a", "ctrl+alt+x", "cmd+ctrl+shift+z",
            "CMD+A", "Command+Shift+A"  # Case insensitive
        ]
        
        for hotkey in valid_hotkeys:
            is_valid, error = self.validator.validate(hotkey)
            self.assertTrue(is_valid, f"Failed for hotkey: {hotkey}")
            self.assertIsNone(error)
    
    def test_parse_hotkey(self):
        """Test hotkey parsing"""
        test_cases = [
            ("cmd+a", ({'cmd'}, 'a')),
            ("cmd+shift+a", ({'cmd', 'shift'}, 'a')),
            ("command+option+x", ({'cmd', 'alt'}, 'x')),  # Aliases
            ("a", None),  # Invalid
            ("", None),  # Invalid
        ]
        
        for hotkey, expected in test_cases:
            result = self.validator._parse_hotkey(hotkey)
            if expected is None:
                self.assertIsNone(result)
            else:
                self.assertEqual(result, expected)
    
    def test_normalize_hotkey(self):
        """Test hotkey normalization"""
        test_cases = [
            ({'cmd', 'shift'}, 'a', "cmd+shift+a"),
            ({'shift', 'cmd'}, 'a', "cmd+shift+a"),  # Order normalized
            ({'alt', 'ctrl', 'cmd'}, 'x', "cmd+ctrl+alt+x"),
        ]
        
        for modifiers, key, expected in test_cases:
            normalized = self.validator._normalize_hotkey(modifiers, key)
            self.assertEqual(normalized, expected)
    
    def test_format_hotkey(self):
        """Test hotkey formatting for display"""
        test_cases = [
            ("cmd+a", "⌘A"),
            ("cmd+shift+a", "⌘⇧A"),
            ("ctrl+alt+x", "⌃⌥X"),
        ]
        
        for hotkey, expected in test_cases:
            formatted = self.validator.format_hotkey(hotkey)
            self.assertEqual(formatted, expected)
    
    def test_get_conflicts(self):
        """Test conflict detection"""
        existing = ["cmd+a", "cmd+shift+b", "ctrl+x"]
        
        # Should find conflict
        conflicts = self.validator.get_conflicts("cmd+a", existing)
        self.assertEqual(conflicts, ["cmd+a"])
        
        # Case insensitive conflict
        conflicts = self.validator.get_conflicts("CMD+A", existing)
        self.assertEqual(conflicts, ["cmd+a"])
        
        # No conflict
        conflicts = self.validator.get_conflicts("cmd+z", existing)
        self.assertEqual(conflicts, [])


if __name__ == '__main__':
    unittest.main() 