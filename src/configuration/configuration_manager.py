#!/usr/bin/env python3
"""
Configuration Manager
Core configuration management system with hierarchy, hot-reload, and validation
"""

import os
import logging
from typing import Dict, Any, Optional, List, Callable, Union
from copy import deepcopy

from .configuration_source import ConfigurationSource, FileConfigurationSource, EnvironmentConfigurationSource, MemoryConfigurationSource
from .configuration_hierarchy import ConfigurationHierarchy
from .validation_engine import ValidationEngine, ValidationResult
from .hot_reload_manager import HotReloadManager
from .environment_manager import EnvironmentManager
from .secrets_manager import SecretsManager

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """
    Advanced configuration management system
    
    Features:
    - Hierarchical configuration with inheritance
    - Multiple configuration sources
    - Hot-reloading with file watchers
    - Schema validation and custom rules
    - Secrets management with encryption
    - Environment-specific configurations
    """
    
    def __init__(self, base_path: str = None, environment: str = None):
        """
        Initialize configuration manager
        
        Args:
            base_path: Base directory for configuration files
            environment: Current environment (dev/staging/prod)
        """
        self.logger = logging.getLogger("config.manager")
        
        # Core components
        self.hierarchy = ConfigurationHierarchy()
        self.validation_engine = ValidationEngine()
        self.environment_manager = EnvironmentManager()
        self.secrets_manager = SecretsManager()
        
        # Configuration sources
        self.sources: List[ConfigurationSource] = []
        self.source_priority_map: Dict[str, int] = {}
        
        # Hot-reload management
        self.hot_reload_manager = None
        self._change_callbacks: List[Callable] = []
        
        # State
        self.base_path = base_path or os.getcwd()
        self.current_environment = environment or self._detect_environment()
        self.is_initialized = False
        self._cached_config = {}
        self._cache_valid = False
        
        self.logger.info(f"Configuration manager created for environment: {self.current_environment}")
    
    def initialize(self, config_sources: List[Dict[str, Any]] = None) -> bool:
        """
        Initialize configuration manager with sources
        
        Args:
            config_sources: List of source configurations
            
        Returns:
            True if initialization successful
        """
        try:
            # Set up environment manager
            self.environment_manager.set_current_environment(self.current_environment)
            
            # Initialize default sources if none provided
            if config_sources is None:
                config_sources = self._get_default_sources()
            
            # Initialize configuration sources
            for source_config in config_sources:
                self._initialize_source(source_config)
            
            # Load initial configuration
            self._load_all_sources()
            
            # Initialize hot-reload manager
            self.hot_reload_manager = HotReloadManager(self)
            
            # Start watching for changes
            self._start_watching()
            
            self.is_initialized = True
            self.logger.info("Configuration manager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing configuration manager: {e}")
            return False
    
    def get(self, key: str, default=None, environment: str = None, 
            validate: bool = False, schema_name: str = None) -> Any:
        """
        Get configuration value with hierarchy resolution
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            environment: Specific environment to use
            validate: Whether to validate the value
            schema_name: Schema to use for validation
            
        Returns:
            Configuration value
        """
        try:
            # Use current environment if not specified
            env = environment or self.current_environment
            
            # Check cache first
            if self._cache_valid and not environment:
                cached_value = self._get_from_cache(key)
                if cached_value is not None:
                    return cached_value
            
            # Get value from hierarchy
            value = self.hierarchy.get_value(key, default)
            
            # Apply environment-specific overrides
            if env and env != 'global':
                env_key = f"environments.{env}.{key}"
                env_value = self.hierarchy.get_value(env_key)
                if env_value is not None:
                    value = env_value
            
            # Decrypt if it's a secret
            if self.secrets_manager.is_secret(key):
                value = self.secrets_manager.decrypt_value(value)
            
            # Validate if requested
            if validate and schema_name:
                validation_result = self.validation_engine.validate_configuration(
                    {key: value}, schema_name
                )
                if not validation_result.is_valid:
                    self.logger.warning(f"Validation failed for key '{key}': {validation_result.errors}")
                    return default
            
            # Cache the value
            if not environment:
                self._cache_value(key, value)
            
            return value
            
        except Exception as e:
            self.logger.error(f"Error getting configuration value '{key}': {e}")
            return default
    
    def set(self, key: str, value: Any, level: str = "runtime", 
            environment: str = None, validate: bool = True,
            schema_name: str = None, persist: bool = False) -> bool:
        """
        Set configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            value: Configuration value
            level: Configuration level to set value in
            environment: Environment to set value for
            validate: Whether to validate the value
            schema_name: Schema to use for validation
            persist: Whether to persist to sources
            
        Returns:
            True if value was set successfully
        """
        try:
            # Validate if requested
            if validate:
                if schema_name:
                    validation_result = self.validation_engine.validate_configuration(
                        {key: value}, schema_name
                    )
                    if not validation_result.is_valid:
                        self.logger.error(f"Validation failed for key '{key}': {validation_result.errors}")
                        return False
            
            # Encrypt if it's a secret
            if self.secrets_manager.is_secret(key):
                value = self.secrets_manager.encrypt_value(value)
            
            # Set in hierarchy
            if environment and environment != 'global':
                env_key = f"environments.{environment}.{key}"
                success = self.hierarchy.set_value(env_key, value, level)
            else:
                success = self.hierarchy.set_value(key, value, level)
            
            if success:
                # Invalidate cache
                self._invalidate_cache()
                
                # Persist if requested
                if persist:
                    self._persist_configuration()
                
                # Notify change callbacks
                self._notify_change(key, value)
                
                self.logger.debug(f"Set configuration '{key}' = '{value}' in level '{level}'")
                return True
            else:
                self.logger.error(f"Failed to set configuration '{key}' in level '{level}'")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting configuration value '{key}': {e}")
            return False
    
    def reload(self, source_name: str = None) -> bool:
        """
        Reload configuration from sources
        
        Args:
            source_name: Specific source to reload (if None, reloads all)
            
        Returns:
            True if reload successful
        """
        try:
            if source_name:
                # Reload specific source
                source = self._get_source_by_name(source_name)
                if source:
                    self._load_source(source)
                    self.logger.info(f"Reloaded configuration from source: {source_name}")
                else:
                    self.logger.error(f"Source not found: {source_name}")
                    return False
            else:
                # Reload all sources
                self._load_all_sources()
                self.logger.info("Reloaded configuration from all sources")
            
            # Invalidate cache
            self._invalidate_cache()
            
            # Notify change callbacks
            self._notify_change("*", None)  # Global change notification
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error reloading configuration: {e}")
            return False
    
    def validate_all(self, schema_name: str = "global") -> ValidationResult:
        """
        Validate entire configuration
        
        Args:
            schema_name: Schema to use for validation
            
        Returns:
            ValidationResult object
        """
        try:
            # Get merged configuration
            merged_config = self.get_merged_configuration()
            
            # Validate
            result = self.validation_engine.validate_configuration(
                merged_config, schema_name
            )
            
            self.logger.info(f"Configuration validation result: {'PASS' if result.is_valid else 'FAIL'}")
            if result.errors:
                for error in result.errors:
                    self.logger.error(f"Validation error: {error}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error validating configuration: {e}")
            result = ValidationResult(is_valid=False)
            result.add_error(f"Validation error: {str(e)}")
            return result
    
    def get_merged_configuration(self, environment: str = None) -> Dict[str, Any]:
        """
        Get merged configuration from all levels
        
        Args:
            environment: Specific environment (if None, uses current)
            
        Returns:
            Merged configuration dictionary
        """
        env = environment or self.current_environment
        
        # Check cache
        cache_key = f"merged_{env}"
        if self._cache_valid and cache_key in self._cached_config:
            return deepcopy(self._cached_config[cache_key])
        
        # Get base merged config
        merged_config = self.hierarchy.get_merged_config()
        
        # Apply environment-specific overrides
        if env and env != 'global':
            env_config = self.hierarchy.get_value(f"environments.{env}", {})
            if env_config:
                merged_config = self._deep_merge(merged_config, env_config)
        
        # Decrypt secrets
        merged_config = self.secrets_manager.decrypt_config(merged_config)
        
        # Cache result
        if self._cache_valid:
            self._cached_config[cache_key] = deepcopy(merged_config)
        
        return merged_config
    
    def add_source(self, source: ConfigurationSource) -> bool:
        """
        Add configuration source
        
        Args:
            source: ConfigurationSource instance
            
        Returns:
            True if source was added successfully
        """
        try:
            if source.name in [s.name for s in self.sources]:
                self.logger.warning(f"Source with name '{source.name}' already exists")
                return False
            
            self.sources.append(source)
            self.source_priority_map[source.name] = source.priority
            
            # Sort sources by priority
            self.sources.sort(key=lambda x: x.priority)
            
            # Load configuration from new source
            if self.is_initialized:
                self._load_source(source)
                self._invalidate_cache()
            
            self.logger.debug(f"Added configuration source: {source.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding configuration source: {e}")
            return False
    
    def remove_source(self, source_name: str) -> bool:
        """
        Remove configuration source
        
        Args:
            source_name: Name of source to remove
            
        Returns:
            True if source was removed successfully
        """
        try:
            source = self._get_source_by_name(source_name)
            if source:
                self.sources.remove(source)
                del self.source_priority_map[source_name]
                
                # Stop watching if supported
                source.stop_watching()
                
                self.logger.debug(f"Removed configuration source: {source_name}")
                return True
            else:
                self.logger.warning(f"Source not found: {source_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error removing configuration source: {e}")
            return False
    
    def watch_changes(self, callback: Callable[[str, Any], None]) -> bool:
        """
        Watch for configuration changes
        
        Args:
            callback: Function to call when configuration changes
            
        Returns:
            True if watching started successfully
        """
        try:
            if callback not in self._change_callbacks:
                self._change_callbacks.append(callback)
                self.logger.debug("Added configuration change callback")
                return True
            else:
                self.logger.warning("Callback already registered")
                return False
                
        except Exception as e:
            self.logger.error(f"Error registering change callback: {e}")
            return False
    
    def set_environment(self, environment: str) -> bool:
        """
        Change current environment
        
        Args:
            environment: New environment name
            
        Returns:
            True if environment was changed successfully
        """
        try:
            old_environment = self.current_environment
            self.current_environment = environment
            self.environment_manager.set_current_environment(environment)
            
            # Invalidate cache
            self._invalidate_cache()
            
            # Notify change
            self._notify_change("environment", environment)
            
            self.logger.info(f"Changed environment from '{old_environment}' to '{environment}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting environment: {e}")
            return False
    
    def _get_default_sources(self) -> List[Dict[str, Any]]:
        """Get default configuration sources"""
        config_dir = os.path.join(self.base_path, "config")
        
        return [
            {
                'type': 'file',
                'name': 'global',
                'path': os.path.join(config_dir, "global.json"),
                'priority': 50,
                'format': 'json'
            },
            {
                'type': 'file',
                'name': 'environment',
                'path': os.path.join(config_dir, f"environments/{self.current_environment}.json"),
                'priority': 40,
                'format': 'json'
            },
            {
                'type': 'environment',
                'name': 'env_vars',
                'prefix': 'POTTER_',
                'priority': 20
            },
            {
                'type': 'memory',
                'name': 'runtime',
                'priority': 10
            }
        ]
    
    def _initialize_source(self, source_config: Dict[str, Any]) -> bool:
        """Initialize a configuration source from config"""
        try:
            source_type = source_config['type']
            name = source_config['name']
            priority = source_config.get('priority', 100)
            
            if source_type == 'file':
                source = FileConfigurationSource(
                    file_path=source_config['path'],
                    format=source_config.get('format', 'auto'),
                    create_if_missing=source_config.get('create_if_missing', True),
                    priority=priority
                )
            elif source_type == 'environment':
                source = EnvironmentConfigurationSource(
                    prefix=source_config.get('prefix', 'POTTER_'),
                    priority=priority
                )
            elif source_type == 'memory':
                source = MemoryConfigurationSource(
                    initial_config=source_config.get('initial_config'),
                    priority=priority
                )
            else:
                self.logger.error(f"Unknown source type: {source_type}")
                return False
            
            return self.add_source(source)
            
        except Exception as e:
            self.logger.error(f"Error initializing source: {e}")
            return False
    
    def _load_all_sources(self):
        """Load configuration from all sources"""
        for source in self.sources:
            self._load_source(source)
    
    def _load_source(self, source: ConfigurationSource):
        """Load configuration from a specific source"""
        try:
            if not source.is_available():
                self.logger.warning(f"Source not available: {source.name}")
                return
            
            config = source.load_configuration()
            if config:
                # Map source to hierarchy level based on priority
                level_name = self._get_level_for_source(source)
                self.hierarchy.set_level_config(level_name, config)
                
                self.logger.debug(f"Loaded configuration from source '{source.name}' into level '{level_name}'")
            
        except Exception as e:
            self.logger.error(f"Error loading source '{source.name}': {e}")
    
    def _get_level_for_source(self, source: ConfigurationSource) -> str:
        """Map source to hierarchy level based on priority"""
        if source.priority <= 20:
            return "runtime"
        elif source.priority <= 30:
            return "user"
        elif source.priority <= 40:
            return "environment"
        else:
            return "global"
    
    def _get_source_by_name(self, name: str) -> Optional[ConfigurationSource]:
        """Get source by name"""
        for source in self.sources:
            if source.name == name:
                return source
        return None
    
    def _start_watching(self):
        """Start watching sources for changes"""
        for source in self.sources:
            try:
                source.watch_changes(self._on_source_changed)
            except Exception as e:
                self.logger.error(f"Error starting watch for source '{source.name}': {e}")
    
    def _on_source_changed(self, new_config: Dict[str, Any]):
        """Handle source change notification"""
        self.logger.info("Configuration source changed, reloading...")
        self.reload()
    
    def _persist_configuration(self):
        """Persist current configuration to writable sources"""
        merged_config = self.get_merged_configuration()
        
        for source in self.sources:
            try:
                if hasattr(source, 'save_configuration'):
                    source.save_configuration(merged_config)
            except Exception as e:
                self.logger.error(f"Error persisting to source '{source.name}': {e}")
    
    def _detect_environment(self) -> str:
        """Auto-detect current environment"""
        # Check environment variable
        env = os.getenv('POTTER_ENVIRONMENT', '').lower()
        if env in ['development', 'staging', 'production']:
            return env
        
        # Check other common environment variables
        if os.getenv('DEBUG', '').lower() in ['true', '1']:
            return 'development'
        
        # Default to development
        return 'development'
    
    def _invalidate_cache(self):
        """Invalidate configuration cache"""
        self._cache_valid = False
        self._cached_config.clear()
    
    def _get_from_cache(self, key: str) -> Any:
        """Get value from cache"""
        return self._cached_config.get(key)
    
    def _cache_value(self, key: str, value: Any):
        """Cache configuration value"""
        self._cached_config[key] = value
        self._cache_valid = True
    
    def _notify_change(self, key: str, value: Any):
        """Notify all change callbacks"""
        for callback in self._change_callbacks:
            try:
                callback(key, value)
            except Exception as e:
                self.logger.error(f"Error in change callback: {e}")
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two configuration dictionaries"""
        result = deepcopy(base)
        
        for key, value in override.items():
            if (key in result and 
                isinstance(result[key], dict) and 
                isinstance(value, dict)):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        
        return result
    
    def get_manager_info(self) -> Dict[str, Any]:
        """Get information about the configuration manager"""
        return {
            'is_initialized': self.is_initialized,
            'current_environment': self.current_environment,
            'base_path': self.base_path,
            'sources_count': len(self.sources),
            'sources': [source.get_source_info() for source in self.sources],
            'hierarchy_info': self.hierarchy.get_hierarchy_info(),
            'validation_info': self.validation_engine.get_validation_info(),
            'cache_valid': self._cache_valid,
            'change_callbacks': len(self._change_callbacks)
        } 