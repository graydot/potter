#!/usr/bin/env python3
"""
LLM Client Manager
Unified interface for multiple LLM providers (OpenAI, Anthropic, Google)
"""

import os
import logging
from typing import Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def setup_client(self, api_key: str) -> bool:
        """Initialize the provider client"""
        pass
    
    @abstractmethod
    def process_text(self, text: str, prompt: str, model: str) -> Optional[str]:
        """Process text using the provider's API"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available"""
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Get the default model for this provider"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> list:
        """Get list of available models for this provider"""
        pass
    
    @abstractmethod
    def validate_api_key(self, api_key: str) -> tuple[bool, Optional[str]]:
        """
        Validate API key format and optionally test with API
        Returns (is_valid, error_message)
        """
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider implementation"""
    
    def __init__(self):
        self.client = None
        self.api_key = None
        self.is_initialized = False
    
    def setup_client(self, api_key: str) -> bool:
        """Initialize OpenAI client"""
        self.api_key = api_key
        
        if not self.api_key:
            logger.warning("No OpenAI API key provided")
            return False
        
        try:
            import openai
            logger.debug(f"OpenAI library version: {openai.__version__}")
            
            self.client = openai.OpenAI(
                api_key=self.api_key,
                timeout=30.0
            )
            self.is_initialized = True
            logger.info("✅ OpenAI client initialized successfully")
            return True
                
        except ImportError as e:
            logger.error(f"❌ OpenAI library not available: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI client: {e}")
            return False
    
    def process_text(self, text: str, prompt: str, model: str) -> Optional[str]:
        """Process text using OpenAI API"""
        if not self.is_initialized or not self.client:
            logger.error("❌ OpenAI client not initialized")
            return None
        
        try:
            # Create request parameters with sensible defaults
            request_params = {
                "model": model,
                "input": [
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "input_text",
                                "text": "You are a helpful writing assistant. Return only the processed text without any additional comments or formatting."
                            }
                        ]
                    },
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type": "input_text",
                                "text": f"{prompt}\n\n{text}"
                            }
                        ]
                    }
                ],
                "max_output_tokens": 2000  # Sensible default
            }
            
            # Only add temperature for non-reasoning models (use conservative value)
            if not self._is_reasoning_model(model):
                request_params["temperature"] = 0.3  # Lower for consistency
                logger.debug(f"✅ Using temperature=0.3 for model {model}")
            else:
                logger.debug(f"⚠️ Skipping temperature for reasoning model {model}")
            
            # Use responses endpoint
            response = self.client.responses.create(**request_params)
            
            if response and response.body and response.body.choices:
                choice = response.body.choices[0]
                content = None
                
                if hasattr(choice, 'message') and choice.message:
                    if hasattr(choice.message, 'content'):
                        content = choice.message.content
                    elif hasattr(choice.message, 'text'):
                        content = choice.message.text
                
                if not content and hasattr(choice, 'text'):
                    content = choice.text
                
                if content:
                    logger.info(f"✅ OpenAI API call successful, response length: {len(content)} chars")
                    return content.strip()
                else:
                    logger.error("❌ No content found in OpenAI response")
                    return None
            else:
                logger.error("❌ Invalid OpenAI response structure")
                return None
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ OpenAI API error: {error_msg}")
            return None
    
    def _is_reasoning_model(self, model: str) -> bool:
        """Check if model is a reasoning model that doesn't support temperature"""
        reasoning_models = {
            'o1', 'o1-pro', 'o1-preview', 'o1-mini',
            'o3-mini', 'o3-mini-2025-01-31'
        }
        return model in reasoning_models
    
    def is_available(self) -> bool:
        """Check if OpenAI client is available"""
        return self.is_initialized and self.client is not None
    
    def get_default_model(self) -> str:
        """Get default OpenAI model"""
        return "gpt-4o-mini"  # Good balance of cost and quality
    
    def get_available_models(self) -> list:
        """Get available OpenAI models"""
        return [
            # O1 series (reasoning models)
            "o1-pro",               # Advanced reasoning flagship
            "o1",                   # Strong reasoning
            "o1-preview",           # Fast reasoning preview
            "o1-mini",              # Quick & affordable reasoning
            
            # GPT series (general purpose)
            "gpt-4o-mini",          # Most affordable GPT-4 class model
            "gpt-3.5-turbo",        # Budget friendly
            "gpt-4o",               # Multimodal flagship  
            "gpt-4-turbo",          # High performance
            "gpt-4",                # Reliable classic
            "gpt-3.5-turbo-16k"     # Extended context
        ]

    def validate_api_key(self, api_key: str) -> tuple[bool, Optional[str]]:
        """
        Validate API key format and optionally test with API
        Returns (is_valid, error_message)
        """
        if not api_key:
            return False, "API key is empty"
        
        # Strip whitespace for validation
        api_key = api_key.strip()
        
        # Provider-specific validation
        if not api_key.startswith('sk-') or len(api_key) < 50:
            return False, "Invalid OpenAI API key format"
        
        return True, None


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation"""
    
    def __init__(self):
        self.client = None
        self.api_key = None
        self.is_initialized = False
    
    def setup_client(self, api_key: str) -> bool:
        """Initialize Anthropic client"""
        self.api_key = api_key
        
        if not self.api_key:
            logger.warning("No Anthropic API key provided")
            return False
        
        try:
            import anthropic
            logger.debug("Anthropic library available")
            
            self.client = anthropic.Anthropic(
                api_key=self.api_key,
                timeout=30.0
            )
            self.is_initialized = True
            logger.info("✅ Anthropic client initialized successfully")
            return True
                
        except ImportError as e:
            logger.error(f"❌ Anthropic library not available: {e}")
            logger.error("Install with: pip install anthropic")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to initialize Anthropic client: {e}")
            return False
    
    def process_text(self, text: str, prompt: str, model: str) -> Optional[str]:
        """Process text using Anthropic API"""
        if not self.is_initialized or not self.client:
            logger.error("❌ Anthropic client not initialized")
            return None
        
        try:
            # Use sensible defaults
            message = self.client.messages.create(
                model=model,
                max_tokens=2000,  # Sensible default
                temperature=0.3,  # Lower for consistency
                messages=[
                    {"role": "user", "content": f"{prompt}\n\n{text}"}
                ]
            )
            
            processed_text = message.content[0].text.strip()
            logger.info(f"✅ Anthropic API call successful, response length: {len(processed_text)} chars")
            return processed_text
            
        except Exception as e:
            logger.error(f"❌ Anthropic API error: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if Anthropic client is available"""
        return self.is_initialized and self.client is not None
    
    def get_default_model(self) -> str:
        """Get default Anthropic model"""
        return "claude-3-haiku-20240307"  # Fast and affordable
    
    def get_available_models(self) -> list:
        """Get available Anthropic models"""
        return [
            "claude-3-haiku-20240307",      # Fast and affordable
            "claude-3-sonnet-20240229",     # Balanced
            "claude-3-opus-20240229",       # Most capable
            "claude-3-5-sonnet-20241022"    # Latest
        ]

    def validate_api_key(self, api_key: str) -> tuple[bool, Optional[str]]:
        """
        Validate API key format and optionally test with API
        Returns (is_valid, error_message)
        """
        if not api_key:
            return False, "API key is empty"
        
        # Strip whitespace for validation
        api_key = api_key.strip()
        
        # Provider-specific validation
        if not api_key.startswith('sk-ant-') or len(api_key) < 50:
            return False, "Invalid Anthropic API key format"
        
        return True, None


class GoogleProvider(LLMProvider):
    """Google Gemini provider implementation"""
    
    def __init__(self):
        self.client = None
        self.api_key = None
        self.is_initialized = False
    
    def setup_client(self, api_key: str) -> bool:
        """Initialize Google Gemini client"""
        self.api_key = api_key
        
        if not self.api_key:
            logger.warning("No Google API key provided")
            return False
        
        try:
            import google.generativeai as genai
            logger.debug("Google AI library available")
            
            genai.configure(api_key=self.api_key)
            self.client = genai
            self.is_initialized = True
            logger.info("✅ Google Gemini client initialized successfully")
            return True
                
        except ImportError as e:
            logger.error(f"❌ Google AI library not available: {e}")
            logger.error("Install with: pip install google-generativeai")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google client: {e}")
            return False
    
    def process_text(self, text: str, prompt: str, model: str) -> Optional[str]:
        """Process text using Google Gemini API"""
        if not self.is_initialized or not self.client:
            logger.error("❌ Google client not initialized")
            return None
        
        try:
            # Initialize the model
            model_obj = self.client.GenerativeModel(model)
            
            # Configure with sensible defaults
            generation_config = self.client.types.GenerationConfig(
                max_output_tokens=2000,  # Sensible default
                temperature=0.3          # Lower for consistency
            )
            
            # Generate response
            response = model_obj.generate_content(
                f"{prompt}\n\n{text}",
                generation_config=generation_config
            )
            
            processed_text = response.text.strip()
            logger.info(f"✅ Google API call successful, response length: {len(processed_text)} chars")
            return processed_text
            
        except Exception as e:
            logger.error(f"❌ Google API error: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if Google client is available"""
        return self.is_initialized and self.client is not None
    
    def get_default_model(self) -> str:
        """Get default Google model"""
        return "gemini-1.5-flash"  # Fast and free
    
    def get_available_models(self) -> list:
        """Get available Google models"""
        return [
            # Free tier models
            "gemini-1.5-flash",        # Fast and efficient (FREE)
            "gemini-1.5-flash-8b",     # Most efficient (FREE)
            "gemini-1.5-pro",          # More capable (FREE with limits)
            
            # Paid models
            "gemini-2.0-flash",        # Latest multimodal (PAID)
            "gemini-2.0-flash-lite",   # Lightweight latest (PAID)
            "gemini-2.5-pro-exp",      # Experimental advanced (PAID)
            "gemini-2.5-flash-exp",    # Experimental fast (PAID)
        ]

    def validate_api_key(self, api_key: str) -> tuple[bool, Optional[str]]:
        """
        Validate API key format and optionally test with API
        Returns (is_valid, error_message)
        """
        if not api_key:
            return False, "API key is empty"
        
        # Strip whitespace for validation
        api_key = api_key.strip()
        
        # Provider-specific validation
        if not api_key.startswith('AIza') or len(api_key) < 35:
            return False, "Invalid Google API key format"
        
        return True, None


class LLMClientManager:
    """Unified LLM client manager supporting multiple providers"""
    
    def __init__(self):
        google_provider = GoogleProvider()
        self.providers = {
            'openai': OpenAIProvider(),
            'anthropic': AnthropicProvider(),
            'google': google_provider,
            'gemini': google_provider  # Alias for Google provider
        }
        self.current_provider = None
        self.current_model = None
        
    def setup_provider(self, provider_name: str, api_key: str, model: str = None) -> bool:
        """Setup a specific LLM provider"""
        if provider_name not in self.providers:
            logger.error(f"❌ Unknown provider: {provider_name}")
            return False
        
        provider = self.providers[provider_name]
        
        if provider.setup_client(api_key):
            self.current_provider = provider_name
            self.current_model = model or provider.get_default_model()
            logger.info(f"✅ LLM provider set to {provider_name} with model {self.current_model}")
            return True
        else:
            logger.error(f"❌ Failed to setup {provider_name} provider")
            return False
    
    def process_text(self, text: str, prompt: str, model: str = None) -> Optional[str]:
        """Process text using the current provider"""
        if not self.current_provider:
            logger.error("❌ No LLM provider configured")
            return None
        
        provider = self.providers[self.current_provider]
        used_model = model or self.current_model
        
        if not text.strip():
            logger.warning("⚠️ No text to process")
            return None
        
        logger.info(f"🚀 Making LLM API call ({self.current_provider}/{used_model})...")
        logger.info(f"Input text length: {len(text)} characters")
        
        try:
            result = provider.process_text(text, prompt, used_model)
            if result:
                logger.info(f"✅ LLM processing complete: {len(text)} -> {len(result)} characters")
            return result
        except Exception as e:
            logger.error(f"❌ Error processing text with {self.current_provider}: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if current provider is available"""
        if not self.current_provider:
            return False
        return self.providers[self.current_provider].is_available()
    
    def get_current_provider(self) -> Optional[str]:
        """Get current provider name"""
        return self.current_provider
    
    def get_current_model(self) -> Optional[str]:
        """Get current model"""
        return self.current_model
    
    def get_available_providers(self) -> list:
        """Get list of available provider names"""
        return list(self.providers.keys())
    
    def get_available_models(self, provider_name: str = None) -> list:
        """Get available models for a provider"""
        provider_name = provider_name or self.current_provider
        if provider_name and provider_name in self.providers:
            return self.providers[provider_name].get_available_models()
        return []
    
    def update_api_key(self, api_key: str) -> bool:
        """Update API key for current provider"""
        if not self.current_provider:
            logger.error("❌ No provider configured to update")
            return False
        
        return self.providers[self.current_provider].setup_client(api_key)
    
    def validate_api_key(self, provider_name: str, api_key: str) -> tuple[bool, Optional[str]]:
        """
        Validate API key format for a specific provider
        Returns (is_valid, error_message)
        """
        if provider_name not in self.providers:
            return False, f"Unknown provider: {provider_name}"
        
        provider = self.providers[provider_name]
        return provider.validate_api_key(api_key)
    
    def test_api_key(self, provider_name: str, api_key: str) -> tuple[bool, Optional[str]]:
        """
        Test API key by making an actual API call
        Returns (is_valid, error_message)
        """
        if provider_name not in self.providers:
            return False, f"Unknown provider: {provider_name}"
        
        # First validate format
        is_valid_format, format_error = self.validate_api_key(provider_name, api_key)
        if not is_valid_format:
            return False, format_error
        
        # Test with actual API call
        provider = self.providers[provider_name]
        try:
            if provider.setup_client(api_key):
                # Make a minimal test call
                result = provider.process_text("test", "respond with just 'ok'", 
                                               provider.get_default_model())
                if result and "ok" in result.lower():
                    return True, None
                else:
                    return False, "API key appears valid but test call failed"
            else:
                return False, "Failed to initialize client with this API key"
        except Exception as e:
            return False, f"API test failed: {str(e)}"


def get_api_key_from_env(provider: str = 'openai') -> Optional[str]:
    """Get API key from environment variables"""
    env_vars = {
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY', 
        'google': 'GOOGLE_API_KEY',
        'gemini': 'GOOGLE_API_KEY'  # Gemini uses same env var as Google
    }
    
    env_var = env_vars.get(provider, 'OPENAI_API_KEY')
    return os.getenv(env_var, "").strip() or None


def validate_api_key_format(api_key: str, provider: str = 'openai') -> bool:
    """Validate API key format for different providers"""
    if not api_key:
        return False
    
    # Strip whitespace for validation
    api_key = api_key.strip()
    
    # Provider-specific validation
    if provider == 'openai':
        return api_key.startswith('sk-') and len(api_key) >= 50
    elif provider == 'anthropic':
        return api_key.startswith('sk-ant-') and len(api_key) >= 50
    elif provider in ['google', 'gemini']:
        return api_key.startswith('AIza') and len(api_key) >= 35
    
    logger.warning(f"Unknown provider for API key validation: {provider}")
    return len(api_key) > 10  # Basic length check