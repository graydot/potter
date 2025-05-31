#!/usr/bin/env python3
"""
LLM Client Manager
Unified interface for multiple LLM providers (OpenAI, Anthropic, Google)
"""

import os
import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def setup_client(self, api_key: str, **kwargs) -> bool:
        """Initialize the provider client"""
        pass
    
    @abstractmethod
    def process_text(self, text: str, prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Process text using the provider's API"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available"""
        pass
    
    @abstractmethod
    def get_context_limit(self, model: str) -> int:
        """Get context window limit for a specific model"""
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Get the default model for this provider"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> list:
        """Get list of available models for this provider"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider implementation"""
    
    def __init__(self):
        self.client = None
        self.api_key = None
        self.is_initialized = False
    
    def setup_client(self, api_key: str, **kwargs) -> bool:
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
    
    def process_text(self, text: str, prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Process text using OpenAI API"""
        if not self.is_initialized or not self.client:
            logger.error("❌ OpenAI client not initialized")
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful writing assistant. Return only the processed text without any additional comments or formatting."},
                    {"role": "user", "content": f"{prompt}\n\n{text}"}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            processed_text = response.choices[0].message.content.strip()
            
            # Log usage information if available
            if hasattr(response, 'usage') and response.usage:
                logger.info(f"📊 Token usage - prompt: {response.usage.prompt_tokens}, completion: {response.usage.completion_tokens}, total: {response.usage.total_tokens}")
            
            return processed_text
            
        except Exception as e:
            self._handle_openai_error(e, model)
            return None
    
    def _handle_openai_error(self, e: Exception, model: str):
        """Handle OpenAI-specific errors"""
        error_message = str(e)
        
        if "context_length_exceeded" in error_message.lower() or "maximum context length" in error_message.lower():
            logger.error(f"❌ Context window exceeded: Text too large for {model}")
            logger.error(f"Consider using gpt-4-turbo (128K context) or splitting the text")
        elif "rate_limit" in error_message.lower():
            logger.error(f"❌ Rate limit exceeded: Too many API requests")
        elif "insufficient_quota" in error_message.lower() or "quota" in error_message.lower():
            logger.error(f"❌ API quota exceeded: Check your OpenAI billing")
        elif "invalid_api_key" in error_message.lower() or "unauthorized" in error_message.lower():
            logger.error(f"❌ Invalid API key: Please check your OpenAI API key")
        else:
            logger.error(f"❌ OpenAI API error: {e}")
    
    def is_available(self) -> bool:
        """Check if OpenAI client is available"""
        return self.is_initialized and self.client is not None
    
    def get_context_limit(self, model: str) -> int:
        """Get context window limit for OpenAI models"""
        model_limits = {
            'gpt-3.5-turbo': 4096,
            'gpt-3.5-turbo-16k': 16384,
            'gpt-4': 8192,
            'gpt-4-32k': 32768,
            'gpt-4-turbo': 128000,
            'gpt-4o': 128000
        }
        return model_limits.get(model, 4096)
    
    def get_default_model(self) -> str:
        """Get default OpenAI model"""
        return "gpt-3.5-turbo"
    
    def get_available_models(self) -> list:
        """Get available OpenAI models"""
        return [
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k", 
            "gpt-4",
            "gpt-4-32k",
            "gpt-4-turbo",
            "gpt-4o"
        ]


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation"""
    
    def __init__(self):
        self.client = None
        self.api_key = None
        self.is_initialized = False
    
    def setup_client(self, api_key: str, **kwargs) -> bool:
        """Initialize Anthropic client"""
        self.api_key = api_key
        
        if not self.api_key:
            logger.warning("No Anthropic API key provided")
            return False
        
        try:
            import anthropic
            logger.debug(f"Anthropic library available")
            
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
    
    def process_text(self, text: str, prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Process text using Anthropic API"""
        if not self.is_initialized or not self.client:
            logger.error("❌ Anthropic client not initialized")
            return None
        
        try:
            # Anthropic uses a different message format
            message = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": f"{prompt}\n\n{text}"}
                ]
            )
            
            processed_text = message.content[0].text.strip()
            
            # Log usage information if available
            if hasattr(message, 'usage') and message.usage:
                logger.info(f"📊 Token usage - input: {message.usage.input_tokens}, output: {message.usage.output_tokens}")
            
            return processed_text
            
        except Exception as e:
            self._handle_anthropic_error(e, model)
            return None
    
    def _handle_anthropic_error(self, e: Exception, model: str):
        """Handle Anthropic-specific errors"""
        error_message = str(e)
        
        if "context_length_exceeded" in error_message.lower() or "too_many_tokens" in error_message.lower():
            logger.error(f"❌ Context window exceeded: Text too large for {model}")
            logger.error(f"Consider using claude-3-haiku or splitting the text")
        elif "rate_limit" in error_message.lower():
            logger.error(f"❌ Rate limit exceeded: Too many API requests")
        elif "credit" in error_message.lower() or "quota" in error_message.lower():
            logger.error(f"❌ API quota exceeded: Check your Anthropic billing")
        elif "invalid_api_key" in error_message.lower() or "unauthorized" in error_message.lower():
            logger.error(f"❌ Invalid API key: Please check your Anthropic API key")
        else:
            logger.error(f"❌ Anthropic API error: {e}")
    
    def is_available(self) -> bool:
        """Check if Anthropic client is available"""
        return self.is_initialized and self.client is not None
    
    def get_context_limit(self, model: str) -> int:
        """Get context window limit for Anthropic models"""
        model_limits = {
            'claude-3-haiku-20240307': 200000,
            'claude-3-sonnet-20240229': 200000,
            'claude-3-opus-20240229': 200000,
            'claude-3-5-sonnet-20241022': 200000
        }
        return model_limits.get(model, 200000)
    
    def get_default_model(self) -> str:
        """Get default Anthropic model"""
        return "claude-3-haiku-20240307"
    
    def get_available_models(self) -> list:
        """Get available Anthropic models"""
        return [
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229", 
            "claude-3-opus-20240229",
            "claude-3-5-sonnet-20241022"
        ]


class GoogleProvider(LLMProvider):
    """Google Gemini provider implementation"""
    
    def __init__(self):
        self.client = None
        self.api_key = None
        self.is_initialized = False
    
    def setup_client(self, api_key: str, **kwargs) -> bool:
        """Initialize Google Gemini client"""
        self.api_key = api_key
        
        if not self.api_key:
            logger.warning("No Google API key provided")
            return False
        
        try:
            import google.generativeai as genai
            logger.debug(f"Google AI library available")
            
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
    
    def process_text(self, text: str, prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Process text using Google Gemini API"""
        if not self.is_initialized or not self.client:
            logger.error("❌ Google client not initialized")
            return None
        
        try:
            # Initialize the model
            model_obj = self.client.GenerativeModel(model)
            
            # Configure generation
            generation_config = self.client.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )
            
            # Generate response
            response = model_obj.generate_content(
                f"{prompt}\n\n{text}",
                generation_config=generation_config
            )
            
            processed_text = response.text.strip()
            return processed_text
            
        except Exception as e:
            self._handle_google_error(e, model)
            return None
    
    def _handle_google_error(self, e: Exception, model: str):
        """Handle Google-specific errors"""
        error_message = str(e)
        
        if "context_length" in error_message.lower() or "too_long" in error_message.lower():
            logger.error(f"❌ Context window exceeded: Text too large for {model}")
            logger.error(f"Consider using gemini-pro or splitting the text")
        elif "quota" in error_message.lower() or "rate" in error_message.lower():
            logger.error(f"❌ API quota/rate limit exceeded")
        elif "api_key" in error_message.lower() or "unauthorized" in error_message.lower():
            logger.error(f"❌ Invalid API key: Please check your Google API key")
        else:
            logger.error(f"❌ Google API error: {e}")
    
    def is_available(self) -> bool:
        """Check if Google client is available"""
        return self.is_initialized and self.client is not None
    
    def get_context_limit(self, model: str) -> int:
        """Get context window limit for Google models"""
        model_limits = {
            'gemini-pro': 32768,
            'gemini-1.5-pro': 1048576,  # 1M tokens
            'gemini-1.5-flash': 1048576,  # 1M tokens
        }
        return model_limits.get(model, 32768)
    
    def get_default_model(self) -> str:
        """Get default Google model"""
        return "gemini-pro"
    
    def get_available_models(self) -> list:
        """Get available Google models"""
        return [
            "gemini-pro",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ]


class LLMClientManager:
    """Unified LLM client manager supporting multiple providers"""
    
    def __init__(self):
        self.providers = {
            'openai': OpenAIProvider(),
            'anthropic': AnthropicProvider(),
            'google': GoogleProvider()
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
    
    def process_text(self, text: str, prompt: str, model: str = None, 
                    max_tokens: int = 1000, temperature: float = 0.7) -> Optional[str]:
        """Process text using the current provider"""
        if not self.current_provider:
            logger.error("❌ No LLM provider configured")
            return None
        
        provider = self.providers[self.current_provider]
        used_model = model or self.current_model
        
        if not text.strip():
            logger.warning("⚠️ No text to process")
            return None
        
        # Estimate token count and check limits
        estimated_input_tokens = (len(text) + len(prompt)) // 4
        context_limit = provider.get_context_limit(used_model)
        total_estimated_tokens = estimated_input_tokens + max_tokens
        
        logger.info(f"🚀 Making LLM API call ({self.current_provider}/{used_model}, max_tokens: {max_tokens}, temp: {temperature})...")
        logger.info(f"Input text length: {len(text)} characters (~{estimated_input_tokens} tokens estimated)")
        
        if total_estimated_tokens > context_limit * 0.9:  # 90% threshold warning
            logger.warning(f"⚠️ Large input detected: ~{estimated_input_tokens} tokens (context limit: {context_limit})")
        
        if estimated_input_tokens > context_limit:
            logger.error(f"❌ Input too large: ~{estimated_input_tokens} tokens exceeds {used_model} limit of {context_limit}")
            raise ValueError(f"Input text too large (~{estimated_input_tokens} tokens) for model {used_model} (limit: {context_limit} tokens)")
        
        try:
            result = provider.process_text(text, prompt, used_model, max_tokens, temperature)
            if result:
                logger.info(f"✅ LLM API call successful: {len(text)} -> {len(result)} characters")
                logger.debug(f"Response preview: {result[:100]}...")
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


# Legacy compatibility - maintain OpenAIClientManager interface
class OpenAIClientManager(LLMClientManager):
    """Legacy compatibility wrapper for OpenAI client"""
    
    def __init__(self, api_key: str = None):
        super().__init__()
        self.api_key = api_key
        if api_key:
            self.setup_client(api_key)
    
    def setup_client(self, api_key: str = None):
        """Initialize OpenAI client (legacy compatibility)"""
        if api_key:
            self.api_key = api_key
        if self.api_key:
            return self.setup_provider('openai', self.api_key)
        return False


def get_api_key_from_env(provider: str = 'openai') -> Optional[str]:
    """Get API key from environment variables"""
    env_vars = {
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY', 
        'google': 'GOOGLE_API_KEY'
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
        return api_key.startswith('sk-') and len(api_key) >= 50  # OpenAI keys are typically 51 chars
    elif provider == 'anthropic':
        return api_key.startswith('sk-ant-') and len(api_key) >= 100  # Anthropic keys are ~108 chars
    elif provider in ['google', 'gemini']:
        # Google API keys must start with AIza and be at least 35 chars
        return api_key.startswith('AIza') and len(api_key) >= 35
    
    logger.warning(f"Unknown provider for API key validation: {provider}")
    return len(api_key) > 10  # Basic length check