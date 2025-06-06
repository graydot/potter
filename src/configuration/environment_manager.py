#!/usr/bin/env python3
"""
Environment Manager
Environment-specific configuration management
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class EnvironmentManager:
    """
    Manages environment-specific configurations
    
    Features:
    - Environment detection
    - Environment-specific configuration loading
    - Environment switching
    - Environment validation
    """
    
    VALID_ENVIRONMENTS = ['development', 'staging', 'production']
    
    def __init__(self, base_path: str = None):
        """
        Initialize environment manager
        
        Args:
            base_path: Base directory for configuration files
        """
        self.logger = logging.getLogger("config.environment")
        self.base_path = base_path or os.getcwd()
        self.current_environment = None
        self.available_environments: Dict[str, Dict[str, Any]] = {}
        
        # Detect available environments
        self._discover_environments()
    
    def set_current_environment(self, environment: str) -> bool:
        """
        Set current environment
        
        Args:
            environment: Environment name
            
        Returns:
            True if environment was set successfully
        """
        try:
            if not self.is_valid_environment(environment):
                self.logger.error(f"Invalid environment: {environment}")
                return False
            
            old_environment = self.current_environment
            self.current_environment = environment
            
            # Set environment variable
            os.environ['POTTER_ENVIRONMENT'] = environment
            
            self.logger.info(f"Environment changed from '{old_environment}' to '{environment}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting environment: {e}")
            return False
    
    def get_current_environment(self) -> str:
        """Get current environment"""
        if self.current_environment:
            return self.current_environment
        
        # Auto-detect if not set
        detected = self.detect_environment()
        self.set_current_environment(detected)
        return detected
    
    def detect_environment(self) -> str:
        """
        Auto-detect current environment
        
        Returns:
            Detected environment name
        """
        # Check environment variable
        env = os.getenv('POTTER_ENVIRONMENT', '').lower()
        if env in self.VALID_ENVIRONMENTS:
            return env
        
        # Check other common environment variables
        if os.getenv('DEBUG', '').lower() in ['true', '1']:
            return 'development'
        
        if os.getenv('NODE_ENV', '').lower() == 'production':
            return 'production'
        
        if os.getenv('FLASK_ENV', '').lower() == 'development':
            return 'development'
        
        # Check for common development indicators
        if any(indicator in os.getcwd().lower() for indicator in ['dev', 'development', 'local']):
            return 'development'
        
        # Default to development
        return 'development'
    
    def is_valid_environment(self, environment: str) -> bool:
        """
        Check if environment name is valid
        
        Args:
            environment: Environment name to check
            
        Returns:
            True if environment is valid
        """
        return environment.lower() in self.VALID_ENVIRONMENTS
    
    def get_available_environments(self) -> List[str]:
        """Get list of available environments"""
        return list(self.available_environments.keys())
    
    def get_environment_config_path(self, environment: str) -> Optional[str]:
        """
        Get configuration file path for environment
        
        Args:
            environment: Environment name
            
        Returns:
            Path to environment configuration file
        """
        if not self.is_valid_environment(environment):
            return None
        
        config_dir = os.path.join(self.base_path, "config", "environments")
        config_file = os.path.join(config_dir, f"{environment}.json")
        
        return config_file
    
    def create_environment_config(self, environment: str, config: Dict[str, Any] = None) -> bool:
        """
        Create configuration file for environment
        
        Args:
            environment: Environment name
            config: Initial configuration (if None, uses template)
            
        Returns:
            True if configuration was created successfully
        """
        try:
            if not self.is_valid_environment(environment):
                self.logger.error(f"Invalid environment: {environment}")
                return False
            
            config_path = self.get_environment_config_path(environment)
            if not config_path:
                return False
            
            # Create directory if needed
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Use provided config or create from template
            env_config = config or self._get_environment_template(environment)
            
            # Write configuration file
            import json
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(env_config, f, indent=2, ensure_ascii=False)
            
            # Update available environments
            self.available_environments[environment] = {
                'path': config_path,
                'exists': True,
                'config': env_config
            }
            
            self.logger.info(f"Created environment configuration: {environment}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating environment config for '{environment}': {e}")
            return False
    
    def load_environment_config(self, environment: str) -> Optional[Dict[str, Any]]:
        """
        Load configuration for specific environment
        
        Args:
            environment: Environment name
            
        Returns:
            Environment configuration dictionary
        """
        try:
            if not self.is_valid_environment(environment):
                self.logger.error(f"Invalid environment: {environment}")
                return None
            
            config_path = self.get_environment_config_path(environment)
            if not config_path or not os.path.exists(config_path):
                self.logger.warning(f"Environment config file not found: {config_path}")
                return self._get_environment_template(environment)
            
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.logger.debug(f"Loaded environment configuration: {environment}")
            return config
            
        except Exception as e:
            self.logger.error(f"Error loading environment config for '{environment}': {e}")
            return None
    
    def save_environment_config(self, environment: str, config: Dict[str, Any]) -> bool:
        """
        Save configuration for specific environment
        
        Args:
            environment: Environment name
            config: Configuration to save
            
        Returns:
            True if configuration was saved successfully
        """
        try:
            if not self.is_valid_environment(environment):
                self.logger.error(f"Invalid environment: {environment}")
                return False
            
            config_path = self.get_environment_config_path(environment)
            if not config_path:
                return False
            
            # Create directory if needed
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Write configuration file
            import json
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # Update available environments
            self.available_environments[environment] = {
                'path': config_path,
                'exists': True,
                'config': config
            }
            
            self.logger.info(f"Saved environment configuration: {environment}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving environment config for '{environment}': {e}")
            return False
    
    def validate_environment_config(self, environment: str, config: Dict[str, Any] = None) -> List[str]:
        """
        Validate environment configuration
        
        Args:
            environment: Environment name
            config: Configuration to validate (if None, loads from file)
            
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            if not self.is_valid_environment(environment):
                errors.append(f"Invalid environment: {environment}")
                return errors
            
            # Load config if not provided
            if config is None:
                config = self.load_environment_config(environment)
                if config is None:
                    errors.append(f"Could not load configuration for environment: {environment}")
                    return errors
            
            # Environment-specific validation
            if environment == 'production':
                # Production should not have debug enabled
                if config.get('app', {}).get('debug', False):
                    errors.append("Debug mode should not be enabled in production")
                
                # Production should have proper logging
                logging_config = config.get('logging', {})
                if logging_config.get('level', 'INFO') == 'DEBUG':
                    errors.append("Production should not use DEBUG logging level")
                
                # Production should have API keys configured
                providers = config.get('llm_providers', {})
                if not providers:
                    errors.append("Production should have LLM providers configured")
            
            elif environment == 'development':
                # Development should have debug enabled
                if not config.get('app', {}).get('debug', True):
                    errors.append("Development environment should have debug mode enabled")
            
            # Common validation
            app_config = config.get('app', {})
            if not app_config.get('name'):
                errors.append("Application name is required")
            
            if app_config.get('environment') and app_config['environment'] != environment:
                errors.append(f"Environment mismatch: config says '{app_config['environment']}', expected '{environment}'")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    def _discover_environments(self):
        """Discover available environment configurations"""
        config_dir = os.path.join(self.base_path, "config", "environments")
        
        if not os.path.exists(config_dir):
            self.logger.debug(f"Environment config directory not found: {config_dir}")
            return
        
        for env in self.VALID_ENVIRONMENTS:
            config_path = os.path.join(config_dir, f"{env}.json")
            exists = os.path.exists(config_path)
            
            self.available_environments[env] = {
                'path': config_path,
                'exists': exists,
                'config': None
            }
            
            if exists:
                self.logger.debug(f"Found environment configuration: {env}")
    
    def _get_environment_template(self, environment: str) -> Dict[str, Any]:
        """
        Get template configuration for environment
        
        Args:
            environment: Environment name
            
        Returns:
            Template configuration dictionary
        """
        base_template = {
            "app": {
                "name": "Potter",
                "environment": environment,
                "debug": environment == 'development'
            },
            "logging": {
                "level": "DEBUG" if environment == 'development' else "INFO",
                "file": f"logs/{environment}.log"
            },
            "api": {
                "rate_limit": 100 if environment == 'production' else 1000,
                "timeout": 30
            }
        }
        
        # Environment-specific templates
        if environment == 'development':
            base_template.update({
                "llm_providers": {
                    "openai": {
                        "model": "gpt-3.5-turbo",
                        "timeout": 30
                    }
                }
            })
        
        elif environment == 'production':
            base_template.update({
                "llm_providers": {
                    "openai": {
                        "model": "gpt-4",
                        "timeout": 60,
                        "retry_attempts": 3
                    }
                }
            })
        
        return base_template
    
    def get_environment_info(self) -> Dict[str, Any]:
        """
        Get information about environment manager
        
        Returns:
            Dictionary with environment information
        """
        return {
            'current_environment': self.current_environment,
            'detected_environment': self.detect_environment(),
            'valid_environments': self.VALID_ENVIRONMENTS,
            'available_environments': self.get_available_environments(),
            'base_path': self.base_path,
            'environment_configs': {
                env: info['exists'] for env, info in self.available_environments.items()
            }
        } 