#!/usr/bin/env python3
"""
API Key Validator
Handles validation of API keys for different LLM providers
"""

import logging
from typing import Tuple, Optional
from utils.llm_client import LLMClientManager, validate_api_key_format

logger = logging.getLogger(__name__)


class APIKeyValidator:
    """Validates API keys for different LLM providers"""
    
    def __init__(self):
        self.llm_manager = LLMClientManager()
    
    def validate_format(self, api_key: str, provider: str) -> Tuple[bool, Optional[str]]:
        """
        Validate API key format for a specific provider
        
        Args:
            api_key: The API key to validate
            provider: The provider name ('openai', 'anthropic', 'google', 'gemini')
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not api_key:
            return False, "API key cannot be empty"
        
        # Use the existing validation function
        is_valid = validate_api_key_format(api_key.strip(), provider)
        
        if not is_valid:
            provider_requirements = {
                'openai': "OpenAI API keys should start with 'sk-' and be at least 50 characters",
                'anthropic': "Anthropic API keys should start with 'sk-ant-' and be at least 50 characters", 
                'google': "Google API keys should start with 'AIza' and be at least 35 characters",
                'gemini': "Google API keys should start with 'AIza' and be at least 35 characters"
            }
            
            requirement = provider_requirements.get(provider, f"Invalid {provider} API key format")
            return False, requirement
        
        return True, None
    
    def validate_with_api(self, api_key: str, provider: str) -> Tuple[bool, Optional[str]]:
        """
        Validate API key by making a test API call
        
        Args:
            api_key: The API key to validate
            provider: The provider name
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # First check format
            is_valid_format, format_error = self.validate_format(api_key, provider)
            if not is_valid_format:
                return False, format_error
            
            # Then test with actual API
            success, error_msg = self.llm_manager.test_api_key(provider, api_key)
            
            if success:
                logger.info(f"✅ {provider} API key validated successfully")
                return True, None
            else:
                logger.warning(f"❌ {provider} API key validation failed: {error_msg}")
                return False, error_msg or f"Failed to validate {provider} API key"
                
        except Exception as e:
            logger.error(f"Error validating {provider} API key: {e}")
            return False, f"Error validating API key: {str(e)}"
    
    def get_masked_key(self, api_key: str) -> str:
        """
        Get a masked version of the API key for display
        
        Args:
            api_key: The API key to mask
            
        Returns:
            Masked API key string
        """
        if not api_key:
            return ""
        
        key = api_key.strip()
        if len(key) <= 8:
            return "*" * len(key)
        
        # Show first 4 and last 4 characters
        return f"{key[:4]}...{key[-4:]}" 