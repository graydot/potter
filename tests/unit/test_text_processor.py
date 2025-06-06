#!/usr/bin/env python3
"""
Unit tests for Text Processor
Tests clipboard operations, text processing workflows, and mode management
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, call

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Import after path setup
from core.text_processor import TextProcessor  # noqa: E402


class TestTextProcessor(unittest.TestCase):
    """Test TextProcessor functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock dependencies
        self.mock_llm_manager = Mock()
        self.mock_settings_manager = Mock()
        
        # Default settings
        self.mock_settings_manager.get.return_value = "polish"
        self.mock_settings_manager.get_all_settings.return_value = {
            "current_prompt": "polish",
            "prompts": [
                {"name": "polish", "text": "Polish this text"},
                {"name": "summarize", "text": "Summarize this text"}
            ]
        }
        
        # Mock prompts manager behavior
        with patch('core.text_processor.get_prompts_manager') as mock_get_prompts:
            self.mock_prompts_manager = Mock()
            self.mock_prompts_manager.get_default_mode.return_value = "polish"
            self.mock_prompts_manager.validate_mode.return_value = True
            self.mock_prompts_manager.get_prompts.return_value = {
                "polish": "Polish this text",
                "summarize": "Summarize this text"
            }
            self.mock_prompts_manager.get_prompt_text.return_value = "Polish this text"
            mock_get_prompts.return_value = self.mock_prompts_manager
            
            self.processor = TextProcessor(self.mock_llm_manager, self.mock_settings_manager)
    
    def test_initialization_success(self):
        """Test successful initialization"""
        self.assertIsNotNone(self.processor)
        self.assertEqual(self.processor.llm_manager, self.mock_llm_manager)
        self.assertEqual(self.processor.settings_manager, self.mock_settings_manager)
    
    def test_initialization_no_prompts_raises_error(self):
        """Test initialization fails when no prompts available"""
        # Create a fresh mock without the setUp patches
        fresh_llm_manager = Mock()
        fresh_settings_manager = Mock()
        fresh_settings_manager.get.return_value = None
        
        with patch('core.text_processor.get_prompts_manager') as mock_get_prompts:
            mock_prompts_manager = Mock()
            mock_prompts_manager.get_default_mode.side_effect = RuntimeError("No prompts")
            mock_get_prompts.return_value = mock_prompts_manager
            
            with self.assertRaises(RuntimeError) as context:
                TextProcessor(fresh_llm_manager, fresh_settings_manager)
            
            self.assertIn("Cannot initialize TextProcessor", str(context.exception))
    
    def test_get_current_mode_from_settings(self):
        """Test getting current mode from settings"""
        self.mock_settings_manager.get.return_value = "summarize"
        self.mock_prompts_manager.validate_mode.return_value = True
        
        mode = self.processor._get_current_mode()
        
        self.assertEqual(mode, "summarize")
        self.mock_settings_manager.get.assert_called_with("current_prompt", None)
    
    def test_get_current_mode_fallback_to_default(self):
        """Test fallback to default mode when settings invalid"""
        self.mock_settings_manager.get.return_value = "invalid_mode"
        self.mock_prompts_manager.validate_mode.return_value = False
        self.mock_prompts_manager.get_default_mode.return_value = "polish"
        
        mode = self.processor._get_current_mode()
        
        self.assertEqual(mode, "polish")
    
    def test_change_mode_valid(self):
        """Test changing to valid mode"""
        self.mock_prompts_manager.validate_mode.return_value = True
        
        result = self.processor.change_mode("summarize")
        
        self.assertTrue(result)
        self.mock_settings_manager.save_settings.assert_called_once()
        saved_settings = self.mock_settings_manager.save_settings.call_args[0][0]
        self.assertEqual(saved_settings["current_prompt"], "summarize")
    
    def test_change_mode_invalid(self):
        """Test changing to invalid mode"""
        self.mock_prompts_manager.validate_mode.return_value = False
        
        result = self.processor.change_mode("invalid_mode")
        
        self.assertFalse(result)
        self.mock_settings_manager.save_settings.assert_not_called()
    
    @patch('core.text_processor.pyperclip')
    def test_get_clipboard_text_success(self, mock_pyperclip):
        """Test successful clipboard read"""
        mock_pyperclip.paste.return_value = "Test clipboard content"
        
        result = self.processor.get_clipboard_text()
        
        self.assertEqual(result, "Test clipboard content")
        mock_pyperclip.paste.assert_called_once()
    
    @patch('core.text_processor.pyperclip')
    def test_get_clipboard_text_empty(self, mock_pyperclip):
        """Test clipboard read with empty content"""
        mock_pyperclip.paste.return_value = ""
        
        result = self.processor.get_clipboard_text()
        
        self.assertIsNone(result)
    
    @patch('core.text_processor.pyperclip')
    def test_get_clipboard_text_whitespace_only(self, mock_pyperclip):
        """Test clipboard read with whitespace only"""
        mock_pyperclip.paste.return_value = "   \n\t   "
        
        result = self.processor.get_clipboard_text()
        
        self.assertIsNone(result)
    
    @patch('core.text_processor.pyperclip')
    def test_get_clipboard_text_exception(self, mock_pyperclip):
        """Test clipboard read with exception"""
        mock_pyperclip.paste.side_effect = Exception("Clipboard error")
        
        result = self.processor.get_clipboard_text()
        
        self.assertIsNone(result)
    
    @patch('core.text_processor.pyperclip')
    def test_set_clipboard_text_success(self, mock_pyperclip):
        """Test successful clipboard write"""
        result = self.processor.set_clipboard_text("New content")
        
        self.assertTrue(result)
        mock_pyperclip.copy.assert_called_once_with("New content")
    
    @patch('core.text_processor.pyperclip')
    def test_set_clipboard_text_exception(self, mock_pyperclip):
        """Test clipboard write with exception"""
        mock_pyperclip.copy.side_effect = Exception("Write error")
        
        result = self.processor.set_clipboard_text("Content")
        
        self.assertFalse(result)
    
    @patch('core.text_processor.pyperclip')
    @patch('core.text_processor.time.sleep')
    def test_verify_clipboard_update_success(self, mock_sleep, mock_pyperclip):
        """Test successful clipboard verification"""
        mock_pyperclip.paste.return_value = "Expected content"
        
        result = self.processor.verify_clipboard_update("Expected content")
        
        self.assertTrue(result)
        mock_sleep.assert_called_once_with(0.1)
    
    @patch('core.text_processor.pyperclip')
    @patch('core.text_processor.time.sleep')
    def test_verify_clipboard_update_mismatch(self, mock_sleep, mock_pyperclip):
        """Test clipboard verification with mismatch"""
        mock_pyperclip.paste.return_value = "Different content"
        
        result = self.processor.verify_clipboard_update("Expected content")
        
        self.assertFalse(result)
    
    def test_process_text_with_current_mode_success(self):
        """Test successful text processing"""
        # Setup mocks
        self.mock_llm_manager.is_available.return_value = True
        self.mock_llm_manager.get_current_model.return_value = "gpt-4"
        self.mock_llm_manager.process_text.return_value = "Processed text"
        self.mock_prompts_manager.get_prompt_text.return_value = "Polish this text"
        
        result = self.processor.process_text_with_current_mode("Input text")
        
        self.assertEqual(result, "Processed text")
        self.mock_llm_manager.process_text.assert_called_once_with(
            text="Input text",
            prompt="Polish this text",
            model="gpt-4"
        )
    
    def test_process_text_llm_not_available(self):
        """Test text processing when LLM not available"""
        self.mock_llm_manager.is_available.return_value = False
        
        result = self.processor.process_text_with_current_mode("Input text")
        
        self.assertIsNone(result)
    
    def test_process_text_no_prompt_found(self):
        """Test text processing when prompt not found"""
        self.mock_llm_manager.is_available.return_value = True
        self.mock_prompts_manager.get_prompt_text.return_value = None
        
        result = self.processor.process_text_with_current_mode("Input text")
        
        self.assertIsNone(result)
    
    def test_process_text_with_default_model(self):
        """Test text processing with default model"""
        # Setup mocks
        self.mock_llm_manager.is_available.return_value = True
        self.mock_llm_manager.get_current_model.return_value = None
        self.mock_llm_manager.get_current_provider.return_value = "openai"
        
        mock_provider = Mock()
        mock_provider.get_default_model.return_value = "gpt-4o-mini"
        self.mock_llm_manager.providers = {"openai": mock_provider}
        
        self.mock_llm_manager.process_text.return_value = "Processed"
        
        result = self.processor.process_text_with_current_mode("Input")
        
        self.assertEqual(result, "Processed")
        self.mock_llm_manager.process_text.assert_called_once_with(
            text="Input",
            prompt="Polish this text",
            model="gpt-4o-mini"
        )
    
    @patch('core.text_processor.pyperclip')
    def test_process_clipboard_text_full_success(self, mock_pyperclip):
        """Test full clipboard processing workflow"""
        # Setup mocks
        mock_pyperclip.paste.side_effect = ["Original text", "Polished text"]  # First for read, second for verify
        mock_pyperclip.copy.return_value = None
        
        self.mock_llm_manager.is_available.return_value = True
        self.mock_llm_manager.get_current_model.return_value = "gpt-4"
        self.mock_llm_manager.process_text.return_value = "Polished text"
        
        # Mock callbacks
        notification_callback = Mock()
        progress_callback = Mock()
        error_callback = Mock()
        
        result = self.processor.process_clipboard_text(
            notification_callback=notification_callback,
            progress_callback=progress_callback,
            error_callback=error_callback
        )
        
        self.assertTrue(result)
        
        # Verify callbacks
        progress_callback.assert_has_calls([call(True), call(False)])
        notification_callback.assert_called_with(
            "Processing Complete",
            "✅ Text polishd and copied to clipboard! Press Cmd+V to paste.",
            False
        )
        error_callback.assert_not_called()
        
        # Verify clipboard operations
        mock_pyperclip.paste.assert_called()
        mock_pyperclip.copy.assert_called_once_with("Polished text")
    
    def test_process_clipboard_text_no_llm(self):
        """Test clipboard processing when LLM not available"""
        self.mock_llm_manager.is_available.return_value = False
        self.mock_settings_manager.get_current_provider.return_value = "openai"
        
        notification_callback = Mock()
        error_callback = Mock()
        
        result = self.processor.process_clipboard_text(
            notification_callback=notification_callback,
            error_callback=error_callback
        )
        
        self.assertFalse(result)
        notification_callback.assert_called_with(
            "Configuration Error",
            "Openai API key not configured. Please check Settings.",
            True
        )
        error_callback.assert_called_with("Openai API key not configured")
    
    @patch('core.text_processor.pyperclip')
    def test_process_clipboard_text_empty_clipboard(self, mock_pyperclip):
        """Test processing with empty clipboard"""
        mock_pyperclip.paste.return_value = ""
        self.mock_llm_manager.is_available.return_value = True
        
        notification_callback = Mock()
        error_callback = Mock()
        
        result = self.processor.process_clipboard_text(
            notification_callback=notification_callback,
            error_callback=error_callback
        )
        
        self.assertFalse(result)
        notification_callback.assert_called_with(
            "No Text",
            "No text found in clipboard. Copy some text first, then press the hotkey.",
            True
        )
        error_callback.assert_called_with("No text in clipboard")
    
    def test_get_available_modes(self):
        """Test getting available modes"""
        self.mock_prompts_manager.get_prompts.return_value = {
            "polish": "Polish text",
            "summarize": "Summarize text",
            "formal": "Make formal"
        }
        
        modes = self.processor.get_available_modes()
        
        self.assertEqual(sorted(modes), ["formal", "polish", "summarize"])
    
    def test_get_available_modes_no_prompts(self):
        """Test getting modes when no prompts available"""
        self.mock_prompts_manager.get_prompts.side_effect = RuntimeError("No prompts")
        
        modes = self.processor.get_available_modes()
        
        self.assertEqual(modes, [])
    
    def test_get_mode_description(self):
        """Test getting mode description"""
        self.mock_prompts_manager.get_prompt_text.return_value = "Polish and improve text"
        
        description = self.processor.get_mode_description("polish")
        
        self.assertEqual(description, "Polish and improve text")
        self.mock_prompts_manager.get_prompt_text.assert_called_with("polish")


if __name__ == '__main__':
    unittest.main() 