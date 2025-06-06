#!/usr/bin/env python3
"""
Unit tests for Prompts Manager
Tests prompt loading, caching, and fallback behavior
"""

import os
import sys
import unittest
from unittest.mock import Mock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Import after path setup
from utils.prompts_manager import PromptsManager, get_prompts_manager  # noqa: E402


class TestPromptsManager(unittest.TestCase):
    """Test PromptsManager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Reset global instance
        import utils.prompts_manager
        utils.prompts_manager._prompts_manager = None
        
        # Mock settings manager
        self.mock_settings_manager = Mock()
        self.manager = PromptsManager(self.mock_settings_manager)
    
    def test_get_default_prompts(self):
        """Test default prompts structure"""
        defaults = self.manager._get_default_prompts()
        
        # Check all expected prompts exist
        expected_prompts = ["summarize", "formal", "casual", "friendly", "polish"]
        for prompt in expected_prompts:
            self.assertIn(prompt, defaults)
            self.assertIsInstance(defaults[prompt], str)
            self.assertGreater(len(defaults[prompt]), 50)  # Should be substantial prompts
    
    def test_get_prompts_from_settings(self):
        """Test loading prompts from settings"""
        # Mock settings data
        self.mock_settings_manager.get.return_value = [
            {"name": "custom1", "text": "Custom prompt 1"},
            {"name": "custom2", "text": "Custom prompt 2"}
        ]
        
        prompts = self.manager.get_prompts()
        
        self.assertEqual(len(prompts), 2)
        self.assertEqual(prompts["custom1"], "Custom prompt 1")
        self.assertEqual(prompts["custom2"], "Custom prompt 2")
        self.mock_settings_manager.get.assert_called_once_with("prompts", [])
    
    def test_get_prompts_empty_settings_uses_defaults(self):
        """Test fallback to defaults when settings empty"""
        self.mock_settings_manager.get.return_value = []
        
        prompts = self.manager.get_prompts()
        
        # Should get default prompts
        self.assertIn("polish", prompts)
        self.assertIn("summarize", prompts)
        self.assertIn("formal", prompts)
        self.assertEqual(len(prompts), 5)  # All defaults
    
    def test_get_prompts_invalid_data_skipped(self):
        """Test invalid prompt data is skipped"""
        self.mock_settings_manager.get.return_value = [
            {"name": "valid", "text": "Valid prompt"},
            {"name": "", "text": "No name"},  # Invalid - empty name
            {"name": "no_text"},  # Invalid - missing text
            {"text": "No name field"},  # Invalid - missing name
            {"name": "  ", "text": "  "}  # Invalid - whitespace only
        ]
        
        prompts = self.manager.get_prompts()
        
        # Only valid prompt should be loaded
        self.assertEqual(len(prompts), 1)
        self.assertEqual(prompts["valid"], "Valid prompt")
    
    def test_get_prompts_exception_uses_defaults(self):
        """Test exception handling falls back to defaults"""
        self.mock_settings_manager.get.side_effect = Exception("Settings error")
        
        prompts = self.manager.get_prompts()
        
        # Should get default prompts
        self.assertEqual(len(prompts), 5)
        self.assertIn("polish", prompts)
    
    def test_get_prompts_caching(self):
        """Test prompts are cached after first load"""
        self.mock_settings_manager.get.return_value = [
            {"name": "test", "text": "Test prompt"}
        ]
        
        # First call
        prompts1 = self.manager.get_prompts()
        # Second call
        prompts2 = self.manager.get_prompts()
        
        # Should be same object (cached)
        self.assertIs(prompts1, prompts2)
        # Settings should only be called once
        self.mock_settings_manager.get.assert_called_once()
    
    def test_get_default_mode(self):
        """Test getting default mode"""
        self.mock_settings_manager.get.return_value = [
            {"name": "first", "text": "First prompt"},
            {"name": "second", "text": "Second prompt"}
        ]
        
        mode = self.manager.get_default_mode()
        
        # Should return first available mode
        self.assertEqual(mode, "first")
    
    def test_get_default_mode_with_defaults(self):
        """Test default mode when using default prompts"""
        self.mock_settings_manager.get.return_value = []
        
        mode = self.manager.get_default_mode()
        
        # Should be one of the default modes
        self.assertIn(mode, ["summarize", "formal", "casual", "friendly", "polish"])
    
    def test_validate_mode_exists(self):
        """Test validating existing mode"""
        self.mock_settings_manager.get.return_value = [
            {"name": "test_mode", "text": "Test prompt"}
        ]
        
        result = self.manager.validate_mode("test_mode")
        
        self.assertTrue(result)
    
    def test_validate_mode_not_exists(self):
        """Test validating non-existent mode"""
        self.mock_settings_manager.get.return_value = [
            {"name": "test_mode", "text": "Test prompt"}
        ]
        
        result = self.manager.validate_mode("invalid_mode")
        
        self.assertFalse(result)
    
    def test_validate_mode_exception_returns_false(self):
        """Test validate mode returns False on exception"""
        self.mock_settings_manager.get.side_effect = Exception("Error")
        
        result = self.manager.validate_mode("any_mode")
        
        self.assertFalse(result)
    
    def test_get_prompt_text_exists(self):
        """Test getting prompt text for existing mode"""
        self.mock_settings_manager.get.return_value = [
            {"name": "test", "text": "Test prompt text"}
        ]
        
        text = self.manager.get_prompt_text("test")
        
        self.assertEqual(text, "Test prompt text")
    
    def test_get_prompt_text_not_exists(self):
        """Test getting prompt text for non-existent mode"""
        self.mock_settings_manager.get.return_value = [
            {"name": "test", "text": "Test prompt"}
        ]
        
        text = self.manager.get_prompt_text("invalid")
        
        self.assertIsNone(text)
    
    def test_get_prompt_text_exception_returns_none(self):
        """Test get prompt text returns None on exception"""
        self.mock_settings_manager.get.side_effect = Exception("Error")
        
        text = self.manager.get_prompt_text("any")
        
        self.assertIsNone(text)
    
    def test_invalidate_cache(self):
        """Test cache invalidation"""
        # Load prompts to cache them
        self.mock_settings_manager.get.return_value = [
            {"name": "cached", "text": "Cached prompt"}
        ]
        self.manager.get_prompts()  # Load into cache
        
        # Invalidate cache
        self.manager.invalidate_cache()
        
        # Change settings
        self.mock_settings_manager.get.return_value = [
            {"name": "new", "text": "New prompt"}
        ]
        
        # Get prompts again
        prompts2 = self.manager.get_prompts()
        
        # Should have new prompts
        self.assertNotIn("cached", prompts2)
        self.assertIn("new", prompts2)
        # Settings should be called twice
        self.assertEqual(self.mock_settings_manager.get.call_count, 2)
    
    def test_no_settings_manager(self):
        """Test behavior without settings manager"""
        manager = PromptsManager(None)
        
        prompts = manager.get_prompts()
        
        # Should get defaults
        self.assertEqual(len(prompts), 5)
        self.assertIn("polish", prompts)


class TestPromptsManagerGlobal(unittest.TestCase):
    """Test global prompts manager instance"""
    
    def setUp(self):
        """Reset global instance before each test"""
        import utils.prompts_manager
        utils.prompts_manager._prompts_manager = None
    
    def test_get_prompts_manager_singleton(self):
        """Test global instance is singleton"""
        manager1 = get_prompts_manager()
        manager2 = get_prompts_manager()
        
        self.assertIs(manager1, manager2)
    
    def test_get_prompts_manager_with_settings(self):
        """Test creating global instance with settings"""
        mock_settings = Mock()
        
        manager = get_prompts_manager(mock_settings)
        
        self.assertEqual(manager.settings_manager, mock_settings)
    
    def test_get_prompts_manager_subsequent_calls_ignore_settings(self):
        """Test subsequent calls ignore settings parameter"""
        mock_settings1 = Mock()
        mock_settings2 = Mock()
        
        manager1 = get_prompts_manager(mock_settings1)
        manager2 = get_prompts_manager(mock_settings2)
        
        # Should be same instance with first settings
        self.assertIs(manager1, manager2)
        self.assertEqual(manager2.settings_manager, mock_settings1)


if __name__ == '__main__':
    unittest.main() 