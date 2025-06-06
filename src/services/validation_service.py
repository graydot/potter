#!/usr/bin/env python3
"""
Validation Service
Centralized validation logic for the Potter application
"""

import logging
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass
from enum import Enum

from .base_service import BaseService
from ui.settings.validators.api_key_validator import APIKeyValidator
from ui.settings.validators.prompt_validator import PromptValidator
from ui.settings.validators.hotkey_validator import HotkeyValidator

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of a validation operation"""
    
    def __init__(self, is_valid: bool, message: str = "", field: str = "", code: str = ""):
        self.is_valid = is_valid
        self.message = message
        self.field = field
        self.code = code
    
    def __bool__(self):
        return self.is_valid
    
    def __repr__(self):
        return f"ValidationResult(valid={self.is_valid}, message='{self.message}')"


class ValidationType(Enum):
    """Types of validation"""
    API_KEY = "api_key"
    PROMPT = "prompt"
    HOTKEY = "hotkey"
    SETTINGS = "settings"
    CUSTOM = "custom"


class ValidationService(BaseService):
    """
    Service for centralized validation logic
    
    Features:
    - API key validation across providers
    - Prompt validation (name, content)
    - Hotkey validation and conflict detection
    - Settings validation
    - Custom validation rules
    - Validation caching
    - Batch validation
    """
    
    def __init__(self, settings_manager=None):
        super().__init__("validation", {})
        
        self.settings_manager = settings_manager
        
        # Initialize validators
        self.api_validator = APIKeyValidator()
        self.prompt_validator = PromptValidator()
        self.hotkey_validator = HotkeyValidator()
        
        # Custom validators
        self._custom_validators: Dict[str, Callable[[Any], ValidationResult]] = {}
        
        # Validation cache
        self._validation_cache: Dict[str, ValidationResult] = {}
        self._cache_enabled = True
        
    def _start_service(self) -> None:
        """Start the validation service"""
        # Load validation settings
        if self.settings_manager:
            self._load_validation_settings()
        
        self.logger.info("✅ Validation service started")
    
    def _stop_service(self) -> None:
        """Stop the validation service"""
        # Clear cache and custom validators
        self._validation_cache.clear()
        self._custom_validators.clear()
        
        self.logger.info("✅ Validation service stopped")
    
    def _get_service_status(self) -> Dict[str, Any]:
        """Get validation service specific status"""
        return {
            'cache_enabled': self._cache_enabled,
            'cache_size': len(self._validation_cache),
            'custom_validators': list(self._custom_validators.keys()),
            'validators_status': {
                'api_validator': bool(self.api_validator),
                'prompt_validator': bool(self.prompt_validator),
                'hotkey_validator': bool(self.hotkey_validator)
            }
        }
    
    def _handle_config_update(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        """Handle configuration updates"""
        if 'validation_cache_enabled' in new_config:
            self._cache_enabled = new_config['validation_cache_enabled']
            if not self._cache_enabled:
                self.clear_cache()
    
    # API Key Validation
    
    def validate_api_key(self, api_key: str, provider: str, use_cache: bool = True) -> ValidationResult:
        """
        Validate an API key
        
        Args:
            api_key: API key to validate
            provider: Provider name (openai, anthropic, google)
            use_cache: Whether to use validation cache
            
        Returns:
            ValidationResult
        """
        cache_key = f"api_key:{provider}:{api_key[:10]}" if use_cache and self._cache_enabled else None
        
        # Check cache
        if cache_key and cache_key in self._validation_cache:
            self.logger.debug(f"Using cached validation for {provider} API key")
            return self._validation_cache[cache_key]
        
        try:
            # Format validation
            if not self.api_validator.validate_format(api_key, provider):
                result = ValidationResult(
                    False,
                    f"Invalid {provider} API key format",
                    "api_key",
                    "INVALID_FORMAT"
                )
            else:
                # API validation (if enabled)
                api_valid = self.api_validator.validate_with_api(api_key, provider)
                if api_valid:
                    result = ValidationResult(
                        True,
                        f"{provider.title()} API key is valid",
                        "api_key",
                        "VALID"
                    )
                else:
                    result = ValidationResult(
                        False,
                        f"{provider.title()} API key validation failed",
                        "api_key",
                        "API_VALIDATION_FAILED"
                    )
            
            # Cache result
            if cache_key:
                self._validation_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error validating {provider} API key: {e}")
            result = ValidationResult(
                False,
                f"Error validating API key: {str(e)}",
                "api_key",
                "VALIDATION_ERROR"
            )
            
            if cache_key:
                self._validation_cache[cache_key] = result
            
            return result
    
    # Prompt Validation
    
    def validate_prompt_name(self, name: str, existing_prompts: Optional[List[str]] = None,
                           exclude_index: Optional[int] = None) -> ValidationResult:
        """
        Validate a prompt name
        
        Args:
            name: Prompt name to validate
            existing_prompts: List of existing prompt names
            exclude_index: Index to exclude from duplicate check
            
        Returns:
            ValidationResult
        """
        try:
            # Get existing prompts if not provided
            if existing_prompts is None and self.settings_manager:
                prompts_data = self.settings_manager.get("prompts", [])
                existing_prompts = [p.get("name", "") for p in prompts_data if isinstance(p, dict)]
            
            is_valid, message = self.prompt_validator.validate_name(
                name, existing_prompts or [], exclude_index
            )
            
            return ValidationResult(
                is_valid,
                message,
                "prompt_name",
                "VALID" if is_valid else "INVALID_NAME"
            )
            
        except Exception as e:
            self.logger.error(f"Error validating prompt name: {e}")
            return ValidationResult(
                False,
                f"Error validating prompt name: {str(e)}",
                "prompt_name",
                "VALIDATION_ERROR"
            )
    
    def validate_prompt_content(self, content: str) -> ValidationResult:
        """
        Validate prompt content
        
        Args:
            content: Prompt content to validate
            
        Returns:
            ValidationResult
        """
        try:
            is_valid, message = self.prompt_validator.validate_content(content)
            
            return ValidationResult(
                is_valid,
                message,
                "prompt_content",
                "VALID" if is_valid else "INVALID_CONTENT"
            )
            
        except Exception as e:
            self.logger.error(f"Error validating prompt content: {e}")
            return ValidationResult(
                False,
                f"Error validating prompt content: {str(e)}",
                "prompt_content",
                "VALIDATION_ERROR"
            )
    
    def validate_prompt(self, name: str, content: str, existing_prompts: Optional[List[str]] = None) -> Dict[str, ValidationResult]:
        """
        Validate both prompt name and content
        
        Args:
            name: Prompt name
            content: Prompt content
            existing_prompts: List of existing prompt names
            
        Returns:
            Dict mapping field names to ValidationResult
        """
        return {
            "name": self.validate_prompt_name(name, existing_prompts),
            "content": self.validate_prompt_content(content)
        }
    
    # Hotkey Validation
    
    def validate_hotkey(self, hotkey: str) -> ValidationResult:
        """
        Validate a hotkey combination
        
        Args:
            hotkey: Hotkey string (e.g., "cmd+shift+a")
            
        Returns:
            ValidationResult
        """
        try:
            is_valid, message = self.hotkey_validator.validate(hotkey)
            
            return ValidationResult(
                is_valid,
                message,
                "hotkey",
                "VALID" if is_valid else "INVALID_HOTKEY"
            )
            
        except Exception as e:
            self.logger.error(f"Error validating hotkey: {e}")
            return ValidationResult(
                False,
                f"Error validating hotkey: {str(e)}",
                "hotkey",
                "VALIDATION_ERROR"
            )
    
    def check_hotkey_conflicts(self, hotkey: str) -> List[str]:
        """
        Check for hotkey conflicts with system shortcuts
        
        Args:
            hotkey: Hotkey string to check
            
        Returns:
            List of conflicting shortcuts
        """
        try:
            return self.hotkey_validator.get_conflicts(hotkey)
        except Exception as e:
            self.logger.error(f"Error checking hotkey conflicts: {e}")
            return []
    
    # Settings Validation
    
    def validate_settings(self, settings: Dict[str, Any]) -> Dict[str, ValidationResult]:
        """
        Validate application settings
        
        Args:
            settings: Settings dictionary to validate
            
        Returns:
            Dict mapping setting names to ValidationResult
        """
        results = {}
        
        # Validate API keys
        for provider in ['openai', 'anthropic', 'google']:
            key_name = f"{provider}_api_key"
            if key_name in settings and settings[key_name]:
                results[key_name] = self.validate_api_key(settings[key_name], provider)
        
        # Validate hotkey
        if 'hotkey' in settings and settings['hotkey']:
            results['hotkey'] = self.validate_hotkey(settings['hotkey'])
        
        # Validate prompts
        if 'prompts' in settings and isinstance(settings['prompts'], list):
            prompt_names = []
            for i, prompt in enumerate(settings['prompts']):
                if isinstance(prompt, dict):
                    name = prompt.get('name', '')
                    content = prompt.get('text', '')
                    
                    if name:
                        name_result = self.validate_prompt_name(name, prompt_names)
                        results[f'prompt_{i}_name'] = name_result
                        if name_result.is_valid:
                            prompt_names.append(name)
                    
                    if content:
                        results[f'prompt_{i}_content'] = self.validate_prompt_content(content)
        
        return results
    
    def validate_setting(self, key: str, value: Any) -> tuple[bool, str]:
        """
        Validate a single setting value
        
        Args:
            key: Setting key
            value: Setting value
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Handle API key settings
            if key.endswith('_api_key') or 'api_key' in key.lower():
                if 'openai' in key.lower():
                    result = self.validate_api_key(value, 'openai')
                elif 'anthropic' in key.lower():
                    result = self.validate_api_key(value, 'anthropic')
                elif 'google' in key.lower():
                    result = self.validate_api_key(value, 'google')
                else:
                    result = self.validate_api_key(value, 'openai')  # Default
                
                return result.is_valid, result.message
            
            # Handle hotkey settings
            elif 'hotkey' in key.lower():
                result = self.validate_hotkey(str(value))
                return result.is_valid, result.message
            
            # Handle prompt settings
            elif 'prompt' in key.lower():
                if isinstance(value, str):
                    result = self.validate_prompt_content(value)
                    return result.is_valid, result.message
            
            # Default validation - just check if value is reasonable
            if value is None:
                return False, "Value cannot be None"
            
            # Basic type checks
            if isinstance(value, str) and len(value.strip()) == 0:
                return False, "Value cannot be empty"
            
            return True, ""
            
        except Exception as e:
            self.logger.error(f"Error validating setting '{key}': {e}")
            return False, str(e)
    
    # Custom Validation
    
    def register_custom_validator(self, name: str, validator: Callable[[Any], ValidationResult]) -> None:
        """
        Register a custom validator
        
        Args:
            name: Validator name
            validator: Function that takes a value and returns ValidationResult
        """
        self._custom_validators[name] = validator
        self.logger.info(f"Registered custom validator: {name}")
    
    def unregister_custom_validator(self, name: str) -> None:
        """
        Unregister a custom validator
        
        Args:
            name: Validator name to remove
        """
        if name in self._custom_validators:
            del self._custom_validators[name]
            self.logger.info(f"Unregistered custom validator: {name}")
    
    def validate_with_custom(self, validator_name: str, value: Any) -> ValidationResult:
        """
        Validate using a custom validator
        
        Args:
            validator_name: Name of registered validator
            value: Value to validate
            
        Returns:
            ValidationResult
        """
        if validator_name not in self._custom_validators:
            return ValidationResult(
                False,
                f"Custom validator '{validator_name}' not found",
                "custom",
                "VALIDATOR_NOT_FOUND"
            )
        
        try:
            return self._custom_validators[validator_name](value)
        except Exception as e:
            self.logger.error(f"Error in custom validator {validator_name}: {e}")
            return ValidationResult(
                False,
                f"Error in custom validator: {str(e)}",
                "custom",
                "VALIDATION_ERROR"
            )
    
    # Batch Validation
    
    def validate_batch(self, validations: List[Dict[str, Any]]) -> List[ValidationResult]:
        """
        Perform batch validation
        
        Args:
            validations: List of validation configs, each containing:
                         {'type': ValidationType, 'value': Any, ...}
        
        Returns:
            List of ValidationResult in same order
        """
        results = []
        
        for validation in validations:
            validation_type = validation.get('type')
            value = validation.get('value')
            
            try:
                if validation_type == ValidationType.API_KEY:
                    provider = validation.get('provider', 'openai')
                    result = self.validate_api_key(value, provider)
                
                elif validation_type == ValidationType.PROMPT:
                    if 'content' in validation:
                        result = self.validate_prompt_content(validation['content'])
                    else:
                        existing = validation.get('existing_prompts', [])
                        result = self.validate_prompt_name(value, existing)
                
                elif validation_type == ValidationType.HOTKEY:
                    result = self.validate_hotkey(value)
                
                elif validation_type == ValidationType.CUSTOM:
                    validator_name = validation.get('validator')
                    result = self.validate_with_custom(validator_name, value)
                
                else:
                    result = ValidationResult(
                        False,
                        f"Unknown validation type: {validation_type}",
                        "batch",
                        "UNKNOWN_TYPE"
                    )
                
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Error in batch validation: {e}")
                results.append(ValidationResult(
                    False,
                    f"Batch validation error: {str(e)}",
                    "batch",
                    "BATCH_ERROR"
                ))
        
        return results
    
    # Cache Management
    
    def clear_cache(self) -> None:
        """Clear the validation cache"""
        self._validation_cache.clear()
        self.logger.info("🧹 Cleared validation cache")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get validation cache statistics"""
        return {
            'total_entries': len(self._validation_cache),
            'api_key_validations': len([k for k in self._validation_cache.keys() if k.startswith('api_key:')]),
        }
    
    def _load_validation_settings(self) -> None:
        """Load validation settings from configuration"""
        if not self.settings_manager:
            return
        
        try:
            self._cache_enabled = self.settings_manager.get("validation_cache_enabled", True)
            self.logger.info(f"Loaded validation settings: cache_enabled={self._cache_enabled}")
            
        except Exception as e:
            self.logger.error(f"Failed to load validation settings: {e}")
            self._cache_enabled = True 