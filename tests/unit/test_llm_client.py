#!/usr/bin/env python3
"""
Unit tests for LLM Client Manager
Tests provider initialization, API key validation, and text processing
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Import after path setup
from utils.llm_client import LLMClientManager, OpenAIProvider, AnthropicProvider, GoogleProvider  # noqa: E402
from utils.llm_client import get_api_key_from_env, validate_api_key_format  # noqa: E402


class TestLLMProviderBase(unittest.TestCase):
    """Base test class for LLM providers"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_openai_key = "sk-" + "x" * 48
        self.valid_anthropic_key = "sk-ant-" + "x" * 48
        self.valid_google_key = "AIza" + "x" * 35
        
        self.invalid_keys = [
            "",
            "invalid",
            "sk-",  # Too short
            "wrong-prefix-" + "x" * 50
        ]


class TestOpenAIProvider(TestLLMProviderBase):
    """Test OpenAI provider implementation"""
    
    def setUp(self):
        super().setUp()
        self.provider = OpenAIProvider()
    
    def test_validate_api_key_valid(self):
        """Test validation of valid OpenAI API keys"""
        is_valid, error = self.provider.validate_api_key(self.valid_openai_key)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_api_key_invalid(self):
        """Test validation of invalid API keys"""
        for invalid_key in self.invalid_keys:
            is_valid, error = self.provider.validate_api_key(invalid_key)
            self.assertFalse(is_valid)
            self.assertIsNotNone(error)
    
    @patch('openai.OpenAI')
    def test_setup_client_success(self, mock_openai_class):
        """Test successful client setup"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        result = self.provider.setup_client(self.valid_openai_key)
        
        self.assertTrue(result)
        self.assertTrue(self.provider.is_initialized)
        self.assertEqual(self.provider.client, mock_client)
        mock_openai_class.assert_called_once_with(
            api_key=self.valid_openai_key,
            timeout=30.0
        )
    
    def test_setup_client_no_api_key(self):
        """Test client setup with no API key"""
        result = self.provider.setup_client("")
        self.assertFalse(result)
        self.assertFalse(self.provider.is_initialized)
    
    def test_is_reasoning_model(self):
        """Test reasoning model detection"""
        reasoning_models = ['o1', 'o1-pro', 'o1-preview', 'o1-mini', 'o3-mini']
        for model in reasoning_models:
            self.assertTrue(self.provider._is_reasoning_model(model))
        
        non_reasoning_models = ['gpt-4', 'gpt-3.5-turbo', 'gpt-4o-mini']
        for model in non_reasoning_models:
            self.assertFalse(self.provider._is_reasoning_model(model))
    
    def test_get_default_model(self):
        """Test default model selection"""
        self.assertEqual(self.provider.get_default_model(), "gpt-4o-mini")
    
    def test_get_available_models(self):
        """Test available models list"""
        models = self.provider.get_available_models()
        self.assertIsInstance(models, list)
        self.assertIn("gpt-4o-mini", models)
        self.assertIn("o1", models)
        self.assertGreater(len(models), 5)


class TestAnthropicProvider(TestLLMProviderBase):
    """Test Anthropic provider implementation"""
    
    def setUp(self):
        super().setUp()
        self.provider = AnthropicProvider()
    
    def test_validate_api_key_valid(self):
        """Test validation of valid Anthropic API keys"""
        is_valid, error = self.provider.validate_api_key(self.valid_anthropic_key)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_api_key_invalid_prefix(self):
        """Test validation with wrong prefix"""
        wrong_key = "sk-" + "x" * 50  # OpenAI format
        is_valid, error = self.provider.validate_api_key(wrong_key)
        self.assertFalse(is_valid)
        self.assertIn("Invalid Anthropic API key format", error)
    
    @patch('anthropic.Anthropic')
    def test_setup_client_success(self, mock_anthropic_class):
        """Test successful client setup"""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        result = self.provider.setup_client(self.valid_anthropic_key)
        
        self.assertTrue(result)
        self.assertTrue(self.provider.is_initialized)
        self.assertEqual(self.provider.client, mock_client)
    
    def test_get_default_model(self):
        """Test default model selection"""
        self.assertEqual(self.provider.get_default_model(), "claude-3-haiku-20240307")
    
    def test_get_available_models(self):
        """Test available models list"""
        models = self.provider.get_available_models()
        self.assertIn("claude-3-haiku-20240307", models)
        self.assertIn("claude-3-opus-20240229", models)


class TestGoogleProvider(TestLLMProviderBase):
    """Test Google provider implementation"""
    
    def setUp(self):
        super().setUp()
        self.provider = GoogleProvider()
    
    def test_validate_api_key_valid(self):
        """Test validation of valid Google API keys"""
        is_valid, error = self.provider.validate_api_key(self.valid_google_key)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_api_key_invalid_prefix(self):
        """Test validation with wrong prefix"""
        wrong_key = "sk-" + "x" * 40
        is_valid, error = self.provider.validate_api_key(wrong_key)
        self.assertFalse(is_valid)
        self.assertIn("Invalid Google API key format", error)
    
    def test_setup_client_success(self):
        """Test successful client setup"""
        with patch('google.generativeai.configure') as mock_configure:
            result = self.provider.setup_client(self.valid_google_key)
            
            self.assertTrue(result)
            self.assertTrue(self.provider.is_initialized)
            self.assertIsNotNone(self.provider.client)
            mock_configure.assert_called_once_with(api_key=self.valid_google_key)
    
    def test_get_default_model(self):
        """Test default model selection"""
        self.assertEqual(self.provider.get_default_model(), "gemini-1.5-flash")
    
    def test_get_available_models(self):
        """Test available models list"""
        models = self.provider.get_available_models()
        self.assertIn("gemini-1.5-flash", models)
        self.assertIn("gemini-1.5-pro", models)
        self.assertGreater(len(models), 3)


class TestLLMClientManager(TestLLMProviderBase):
    """Test LLM Client Manager orchestration"""
    
    def setUp(self):
        super().setUp()
        self.manager = LLMClientManager()
    
    def test_initial_state(self):
        """Test manager initial state"""
        self.assertIsNone(self.manager.current_provider)
        self.assertIsNone(self.manager.current_model)
        self.assertFalse(self.manager.is_available())
    
    def test_get_available_providers(self):
        """Test available providers list"""
        providers = self.manager.get_available_providers()
        self.assertIn('openai', providers)
        self.assertIn('anthropic', providers)
        self.assertIn('google', providers)
        self.assertIn('gemini', providers)  # Alias
    
    @patch.object(OpenAIProvider, 'setup_client')
    def test_setup_provider_success(self, mock_setup):
        """Test successful provider setup"""
        mock_setup.return_value = True
        
        result = self.manager.setup_provider('openai', self.valid_openai_key, 'gpt-4')
        
        self.assertTrue(result)
        self.assertEqual(self.manager.current_provider, 'openai')
        self.assertEqual(self.manager.current_model, 'gpt-4')
        mock_setup.assert_called_once_with(self.valid_openai_key)
    
    def test_setup_provider_invalid_name(self):
        """Test setup with invalid provider name"""
        result = self.manager.setup_provider('invalid_provider', 'some_key')
        self.assertFalse(result)
        self.assertIsNone(self.manager.current_provider)
    
    @patch.object(OpenAIProvider, 'setup_client')
    @patch.object(OpenAIProvider, 'is_available')
    @patch.object(OpenAIProvider, 'process_text')
    def test_process_text_success(self, mock_process, mock_available, mock_setup):
        """Test successful text processing"""
        mock_setup.return_value = True
        mock_available.return_value = True
        mock_process.return_value = "Processed text"
        
        # Setup provider first
        self.manager.setup_provider('openai', self.valid_openai_key)
        
        # Process text
        result = self.manager.process_text("Input text", "Process this", "gpt-4")
        
        self.assertEqual(result, "Processed text")
        mock_process.assert_called_once_with("Input text", "Process this", "gpt-4")
    
    def test_process_text_no_provider(self):
        """Test text processing without provider"""
        result = self.manager.process_text("Input", "Prompt")
        self.assertIsNone(result)
    
    def test_validate_api_key(self):
        """Test API key validation through manager"""
        # Valid keys
        is_valid, error = self.manager.validate_api_key('openai', self.valid_openai_key)
        self.assertTrue(is_valid)
        
        is_valid, error = self.manager.validate_api_key('anthropic', self.valid_anthropic_key)
        self.assertTrue(is_valid)
        
        is_valid, error = self.manager.validate_api_key('google', self.valid_google_key)
        self.assertTrue(is_valid)
        
        # Invalid provider
        is_valid, error = self.manager.validate_api_key('invalid', 'key')
        self.assertFalse(is_valid)
        self.assertIn("Unknown provider", error)
    
    def test_gemini_alias(self):
        """Test that 'gemini' works as alias for 'google'"""
        # Both should point to same provider instance
        self.assertIs(
            self.manager.providers['gemini'],
            self.manager.providers['google']
        )


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_get_api_key_from_env_openai(self):
        """Test getting OpenAI key from environment"""
        key = get_api_key_from_env('openai')
        self.assertEqual(key, 'test-key')
    
    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-anthropic'})
    def test_get_api_key_from_env_anthropic(self):
        """Test getting Anthropic key from environment"""
        key = get_api_key_from_env('anthropic')
        self.assertEqual(key, 'test-anthropic')
    
    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-google'})
    def test_get_api_key_from_env_google(self):
        """Test getting Google key from environment"""
        key = get_api_key_from_env('google')
        self.assertEqual(key, 'test-google')
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_api_key_from_env_missing(self):
        """Test getting key when not in environment"""
        key = get_api_key_from_env('openai')
        self.assertIsNone(key)
    
    def test_validate_api_key_format(self):
        """Test API key format validation"""
        # Valid formats
        self.assertTrue(validate_api_key_format("sk-" + "x" * 48, 'openai'))
        self.assertTrue(validate_api_key_format("sk-ant-" + "x" * 48, 'anthropic'))
        self.assertTrue(validate_api_key_format("AIza" + "x" * 35, 'google'))
        self.assertTrue(validate_api_key_format("AIza" + "x" * 35, 'gemini'))
        
        # Invalid formats
        self.assertFalse(validate_api_key_format("", 'openai'))
        self.assertFalse(validate_api_key_format("wrong", 'openai'))
        self.assertFalse(validate_api_key_format("sk-short", 'openai'))
        self.assertFalse(validate_api_key_format("sk-" + "x" * 48, 'anthropic'))  # Wrong prefix


if __name__ == '__main__':
    unittest.main() 