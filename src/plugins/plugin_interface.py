#!/usr/bin/env python3
"""
Plugin Interface
Standard interface and context for Potter plugins
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PluginContext:
    """
    Context object provided to plugins during initialization
    
    Contains references to services, configuration, and utility functions
    that plugins can use to integrate with the Potter application.
    """
    # Service manager for accessing application services
    service_manager: Any
    
    # Configuration for this plugin
    plugin_config: Dict[str, Any] = field(default_factory=dict)
    
    # Global application configuration
    app_config: Dict[str, Any] = field(default_factory=dict)
    
    # Logger instance for this plugin
    logger: logging.Logger = None
    
    # Event bus for cross-plugin communication
    event_bus: Optional[Any] = None
    
    # Plugin data directory
    data_directory: Optional[str] = None
    
    # Plugin metadata
    plugin_name: str = ""
    plugin_version: str = "1.0.0"
    
    def __post_init__(self):
        """Post-initialization setup"""
        if not self.logger:
            self.logger = logging.getLogger(f"plugin.{self.plugin_name}")
    
    def get_service(self, service_name: str):
        """Get a service from the service manager"""
        if self.service_manager:
            return self.service_manager.get_service(service_name)
        return None
    
    def get_config(self, key: str, default=None):
        """Get configuration value for this plugin"""
        return self.plugin_config.get(key, default)
    
    def get_app_config(self, key: str, default=None):
        """Get application configuration value"""
        return self.app_config.get(key, default)
    
    def publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish an event through the event bus"""
        if self.event_bus:
            self.event_bus.publish(event_type, data)
    
    def subscribe_to_event(self, event_type: str, handler: Callable):
        """Subscribe to an event type"""
        if self.event_bus:
            return self.event_bus.subscribe(event_type, handler)
        return None


class PluginInterface(ABC):
    """
    Abstract base class for Potter plugins
    
    All plugins must implement this interface to be loaded and managed
    by the PluginManager.
    """
    
    def __init__(self):
        self.context: Optional[PluginContext] = None
        self.logger: Optional[logging.Logger] = None
        self.is_initialized = False
        self.is_enabled = True
    
    @abstractmethod
    def get_plugin_info(self) -> Dict[str, Any]:
        """
        Return plugin metadata information
        
        Returns:
            Dictionary containing:
            - name: Plugin name
            - version: Plugin version
            - description: Plugin description
            - author: Plugin author
            - dependencies: List of required dependencies
            - capabilities: List of plugin capabilities
        """
        pass
    
    @abstractmethod
    def initialize(self, context: PluginContext) -> bool:
        """
        Initialize the plugin with the provided context
        
        Args:
            context: PluginContext object with services and configuration
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """
        Clean up plugin resources before shutdown
        
        Called when the plugin is being unloaded or the application
        is shutting down.
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return list of capabilities this plugin provides
        
        Returns:
            List of capability names (e.g., ['text_processing', 'validation'])
        """
        pass
    
    def execute(self, capability: str, *args, **kwargs) -> Any:
        """
        Execute a plugin capability
        
        Args:
            capability: Name of the capability to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result of the capability execution
        """
        if capability not in self.get_capabilities():
            raise ValueError(f"Capability '{capability}' not supported by plugin")
        
        # Default implementation - subclasses should override
        method_name = f"execute_{capability}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            return method(*args, **kwargs)
        else:
            raise NotImplementedError(f"Capability '{capability}' not implemented")
    
    def get_dependencies(self) -> List[str]:
        """
        Get list of plugin dependencies
        
        Returns:
            List of plugin names this plugin depends on
        """
        plugin_info = self.get_plugin_info()
        return plugin_info.get('dependencies', [])
    
    def is_dependency_satisfied(self, dependency: str) -> bool:
        """
        Check if a dependency is satisfied
        
        Args:
            dependency: Name of the dependency to check
            
        Returns:
            bool: True if dependency is satisfied
        """
        if not self.context:
            return False
        
        # Check if dependency is available through service manager
        service = self.context.get_service(dependency)
        if service:
            return True
        
        # TODO: Check if dependency is another plugin
        return False
    
    def validate_dependencies(self) -> List[str]:
        """
        Validate all plugin dependencies
        
        Returns:
            List of missing dependencies
        """
        missing_deps = []
        for dep in self.get_dependencies():
            if not self.is_dependency_satisfied(dep):
                missing_deps.append(dep)
        return missing_deps
    
    def enable(self):
        """Enable the plugin"""
        self.is_enabled = True
        if self.logger:
            self.logger.info(f"Plugin {self.get_plugin_info()['name']} enabled")
    
    def disable(self):
        """Disable the plugin"""
        self.is_enabled = False
        if self.logger:
            self.logger.info(f"Plugin {self.get_plugin_info()['name']} disabled")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get plugin status information
        
        Returns:
            Dictionary with plugin status details
        """
        plugin_info = self.get_plugin_info()
        return {
            'name': plugin_info['name'],
            'version': plugin_info['version'],
            'initialized': self.is_initialized,
            'enabled': self.is_enabled,
            'capabilities': self.get_capabilities(),
            'dependencies': self.get_dependencies(),
            'missing_dependencies': self.validate_dependencies() if self.context else []
        }


class TextProcessingPlugin(PluginInterface):
    """
    Base class for text processing plugins
    
    Provides common functionality for plugins that process text.
    """
    
    def get_capabilities(self) -> List[str]:
        """Text processing plugins provide text processing capability"""
        return ['text_processing']
    
    @abstractmethod
    def process_text(self, text: str, options: Dict[str, Any] = None) -> str:
        """
        Process text according to plugin's functionality
        
        Args:
            text: Input text to process
            options: Processing options
            
        Returns:
            Processed text
        """
        pass
    
    def execute_text_processing(self, text: str, options: Dict[str, Any] = None) -> str:
        """Execute text processing capability"""
        return self.process_text(text, options)


class ValidationPlugin(PluginInterface):
    """
    Base class for validation plugins
    
    Provides common functionality for plugins that validate data.
    """
    
    def get_capabilities(self) -> List[str]:
        """Validation plugins provide validation capability"""
        return ['validation']
    
    @abstractmethod
    def validate(self, data: Any, schema: Dict[str, Any] = None) -> tuple[bool, Optional[str]]:
        """
        Validate data according to plugin's rules
        
        Args:
            data: Data to validate
            schema: Validation schema
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    def execute_validation(self, data: Any, schema: Dict[str, Any] = None) -> tuple[bool, Optional[str]]:
        """Execute validation capability"""
        return self.validate(data, schema)


class UIPlugin(PluginInterface):
    """
    Base class for UI plugins
    
    Provides common functionality for plugins that extend the UI.
    """
    
    def get_capabilities(self) -> List[str]:
        """UI plugins provide UI extension capability"""
        return ['ui_extension']
    
    @abstractmethod
    def get_ui_components(self) -> List[Dict[str, Any]]:
        """
        Get UI components provided by this plugin
        
        Returns:
            List of UI component definitions
        """
        pass
    
    def execute_ui_extension(self) -> List[Dict[str, Any]]:
        """Execute UI extension capability"""
        return self.get_ui_components()


class ServicePlugin(PluginInterface):
    """
    Base class for service plugins
    
    Provides common functionality for plugins that extend services.
    """
    
    def get_capabilities(self) -> List[str]:
        """Service plugins provide service extension capability"""
        return ['service_extension']
    
    @abstractmethod
    def get_service_extensions(self) -> Dict[str, Any]:
        """
        Get service extensions provided by this plugin
        
        Returns:
            Dictionary of service name -> extension definition
        """
        pass
    
    def execute_service_extension(self) -> Dict[str, Any]:
        """Execute service extension capability"""
        return self.get_service_extensions() 