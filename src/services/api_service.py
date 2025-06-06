#!/usr/bin/env python3
"""
API Service
Manages LLM provider interactions and API key validation
"""

import logging
from typing import Dict, Any, Optional, List
from threading import Timer

from .base_service import BaseService
from core.exceptions import ServiceError
from utils.llm_client import LLMClientManager
from ui.settings.validators.api_key_validator import APIKeyValidator

logger = logging.getLogger(__name__)


class APIService(BaseService):
    """
    Service for managing LLM API interactions
    
    Features:
    - LLM provider management
    - API key validation and caching
    - Rate limiting and retry logic
    - Health monitoring of API endpoints
    - Configuration management
    """
    
    def __init__(self, settings_manager=None):
        super().__init__("api", {})
        
        self.settings_manager = settings_manager
        self.llm_manager = LLMClientManager()
        self.api_validator = APIKeyValidator()
        
        # API health tracking
        self._api_health: Dict[str, Dict[str, Any]] = {}
        self._health_check_timer: Optional[Timer] = None
        self._validation_cache: Dict[str, bool] = {}
        
    def _start_service(self) -> None:
        """Start the API service"""
        # Initialize LLM manager with current settings
        if self.settings_manager:
            self._load_api_configuration()
        
        # Start health monitoring
        self._start_health_monitoring()
        
        self.logger.info("🔗 API service started")
    
    def _stop_service(self) -> None:
        """Stop the API service"""
        # Stop health monitoring
        if self._health_check_timer:
            self._health_check_timer.cancel()
            self._health_check_timer = None
        
        # Clear validation cache
        self._validation_cache.clear()
        
        self.logger.info("🔗 API service stopped")
    
    def _get_service_status(self) -> Dict[str, Any]:
        """Get API service specific status"""
        current_provider = self.llm_manager.get_current_provider()
        available_providers = self.llm_manager.get_available_providers()
        
        return {
            'current_provider': current_provider,
            'available_providers': available_providers,
            'api_health': self._api_health.copy(),
            'validation_cache_size': len(self._validation_cache)
        }
    
    def _handle_config_update(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        """Handle configuration updates"""
        # Reload API configuration if settings change
        if 'provider' in new_config or any(key.endswith('_api_key') for key in new_config):
            self._load_api_configuration()
            self._validation_cache.clear()  # Clear cache on config change
    
    def get_current_provider(self) -> Optional[str]:
        """Get the currently active LLM provider"""
        return self.llm_manager.get_current_provider()
    
    def get_available_providers(self) -> List[str]:
        """Get list of available LLM providers"""
        return self.llm_manager.get_available_providers()
    
    def set_provider(self, provider: str, model: Optional[str] = None) -> bool:
        """
        Set the active LLM provider
        
        Args:
            provider: Provider name (openai, anthropic, google)
            model: Optional model name
            
        Returns:
            bool: True if provider set successfully
        """
        try:
            # Get API key from settings
            api_key = self._get_api_key_for_provider(provider)
            if not api_key:
                raise ServiceError(f"No API key configured for provider: {provider}")
            
            # Setup LLM manager
            success = self.llm_manager.setup_provider(
                provider=provider,
                api_key=api_key,
                model=model
            )
            
            if success:
                self.logger.info(f"✅ Set LLM provider to {provider}")
                # Update health status
                self._update_provider_health(provider, True)
            else:
                self.logger.error(f"❌ Failed to set provider to {provider}")
                self._update_provider_health(provider, False)
                
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error setting provider {provider}: {e}")
            self._update_provider_health(provider, False, str(e))
            raise ServiceError(f"Failed to set provider {provider}", details=str(e))
    
    def validate_api_key(self, provider: str, api_key: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Validate an API key for a provider
        
        Args:
            provider: Provider name
            api_key: API key to validate
            force_refresh: Force validation even if cached
            
        Returns:
            Dict with validation results
        """
        cache_key = f"{provider}:{api_key[:10]}"  # Use first 10 chars for cache key
        
        # Check cache first
        if not force_refresh and cache_key in self._validation_cache:
            return {
                'valid': self._validation_cache[cache_key],
                'cached': True,
                'provider': provider
            }
        
        try:
            # Format validation
            format_valid = self.api_validator.validate_format(api_key, provider)
            if not format_valid:
                result = {
                    'valid': False,
                    'error': 'Invalid API key format',
                    'cached': False,
                    'provider': provider
                }
                self._validation_cache[cache_key] = False
                return result
            
            # API validation
            api_valid = self.api_validator.validate_with_api(api_key, provider)
            
            # Cache result
            self._validation_cache[cache_key] = api_valid
            
            result = {
                'valid': api_valid,
                'cached': False,
                'provider': provider
            }
            
            if api_valid:
                self.logger.info(f"✅ API key validated for {provider}")
                self._update_provider_health(provider, True)
            else:
                self.logger.warning(f"❌ API key validation failed for {provider}")
                self._update_provider_health(provider, False, "API key validation failed")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error validating API key for {provider}: {e}")
            self._validation_cache[cache_key] = False
            self._update_provider_health(provider, False, str(e))
            
            return {
                'valid': False,
                'error': str(e),
                'cached': False,
                'provider': provider
            }
    
    def process_text(self, text: str, prompt: str, **kwargs) -> str:
        """
        Process text using the current LLM provider
        
        Args:
            text: Text to process
            prompt: Prompt template
            **kwargs: Additional parameters
            
        Returns:
            Processed text
        """
        if not self.llm_manager.get_current_provider():
            raise ServiceError("No LLM provider configured")
        
        try:
            result = self.llm_manager.process_text(text, prompt, **kwargs)
            self.logger.info(f"✅ Text processed successfully ({len(text)} -> {len(result)} chars)")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error processing text: {e}")
            raise ServiceError("Failed to process text", details=str(e))
    
    def get_api_health(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get API health status
        
        Args:
            provider: Specific provider or None for all
            
        Returns:
            Health status information
        """
        if provider:
            return self._api_health.get(provider, {'status': 'unknown'})
        else:
            return self._api_health.copy()
    
    def clear_validation_cache(self) -> None:
        """Clear the API key validation cache"""
        self._validation_cache.clear()
        self.logger.info("🧹 Cleared API key validation cache")
    
    def _load_api_configuration(self) -> None:
        """Load API configuration from settings"""
        if not self.settings_manager:
            return
        
        try:
            # Get current provider and model
            provider = self.settings_manager.get("provider", "")
            model = self.settings_manager.get("model", "")
            
            if provider:
                self.set_provider(provider, model if model else None)
            else:
                self.logger.warning("No LLM provider configured in settings")
                
        except Exception as e:
            self.logger.error(f"❌ Error loading API configuration: {e}")
    
    def _get_api_key_for_provider(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider from settings"""
        if not self.settings_manager:
            return None
        
        key_mapping = {
            'openai': 'openai_api_key',
            'anthropic': 'anthropic_api_key',
            'google': 'google_api_key',
            'gemini': 'google_api_key'  # Alias
        }
        
        key_name = key_mapping.get(provider.lower())
        if not key_name:
            return None
        
        return self.settings_manager.get(key_name, "")
    
    def _start_health_monitoring(self) -> None:
        """Start periodic health monitoring of API endpoints"""
        def health_check():
            if self.is_running:
                self._perform_health_check()
                # Schedule next check in 5 minutes
                self._health_check_timer = Timer(300.0, health_check)
                self._health_check_timer.start()
        
        # Start first check after 30 seconds
        self._health_check_timer = Timer(30.0, health_check)
        self._health_check_timer.start()
    
    def _perform_health_check(self) -> None:
        """Perform health check on all configured providers"""
        try:
            current_provider = self.llm_manager.get_current_provider()
            if current_provider:
                # Simple health check - try to get available models
                try:
                    models = self.llm_manager.get_available_models(current_provider)
                    if models:
                        self._update_provider_health(current_provider, True)
                    else:
                        self._update_provider_health(current_provider, False, "No models available")
                except Exception as e:
                    self._update_provider_health(current_provider, False, str(e))
            
        except Exception as e:
            self.logger.error(f"Error during health check: {e}")
    
    def _update_provider_health(self, provider: str, is_healthy: bool, error: Optional[str] = None) -> None:
        """Update health status for a provider"""
        import time
        
        self._api_health[provider] = {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'last_check': time.time(),
            'error': error
        } 