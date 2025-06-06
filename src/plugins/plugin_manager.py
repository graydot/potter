#!/usr/bin/env python3
"""
Plugin Manager
Dynamic plugin loading and lifecycle management
"""

import os
import sys
import importlib
import importlib.util
import logging
from typing import Dict, Any, List, Optional, Type
from pathlib import Path

from .plugin_interface import PluginInterface, PluginContext
from .plugin_registry import PluginRegistry

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Manages plugin lifecycle and dependencies
    
    Features:
    - Dynamic plugin discovery and loading
    - Dependency resolution
    - Plugin lifecycle management
    - Error handling and recovery
    - Plugin isolation and security
    """
    
    def __init__(self, service_manager=None, plugin_directories: List[str] = None):
        self.service_manager = service_manager
        self.plugin_directories = plugin_directories or []
        self.logger = logging.getLogger("plugin.manager")
        
        # Plugin storage
        self.loaded_plugins: Dict[str, PluginInterface] = {}
        self.plugin_registry = PluginRegistry()
        
        # Plugin state
        self.is_running = False
        self.initialization_order: List[str] = []
        
        # Configuration
        self.plugin_config = {}
        self.app_config = {}
        
        # Default plugin directories
        self._setup_default_directories()
    
    def _setup_default_directories(self):
        """Setup default plugin directories"""
        # Add built-in plugins directory
        builtin_dir = os.path.join(os.path.dirname(__file__), 'core_plugins')
        if os.path.exists(builtin_dir):
            self.plugin_directories.append(builtin_dir)
        
        # Add user plugins directory
        user_dir = os.path.expanduser('~/.potter/plugins')
        if os.path.exists(user_dir):
            self.plugin_directories.append(user_dir)
        
        # Add system plugins directory
        system_dir = '/usr/local/share/potter/plugins'
        if os.path.exists(system_dir):
            self.plugin_directories.append(system_dir)
    
    def start(self) -> bool:
        """
        Start the plugin manager
        
        Returns:
            bool: True if started successfully
        """
        try:
            if self.is_running:
                self.logger.warning("Plugin manager is already running")
                return True
            
            # Discover and load plugins
            self.discover_plugins()
            self.load_all_plugins()
            
            self.is_running = True
            self.logger.info(f"🔌 Plugin manager started with {len(self.loaded_plugins)} plugins")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start plugin manager: {e}")
            return False
    
    def stop(self):
        """Stop the plugin manager and cleanup all plugins"""
        try:
            # Cleanup plugins in reverse order
            for plugin_name in reversed(self.initialization_order):
                self.unload_plugin(plugin_name)
            
            self.loaded_plugins.clear()
            self.initialization_order.clear()
            self.is_running = False
            
            self.logger.info("🔌 Plugin manager stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping plugin manager: {e}")
    
    def discover_plugins(self) -> List[Dict[str, Any]]:
        """
        Discover available plugins in plugin directories
        
        Returns:
            List of plugin information dictionaries
        """
        discovered_plugins = []
        
        for directory in self.plugin_directories:
            if not os.path.exists(directory):
                self.logger.debug(f"Plugin directory not found: {directory}")
                continue
            
            self.logger.debug(f"Discovering plugins in: {directory}")
            
            try:
                for item in os.listdir(directory):
                    item_path = os.path.join(directory, item)
                    
                    # Check for Python files
                    if item.endswith('.py') and not item.startswith('_'):
                        plugin_info = self._discover_python_plugin(item_path)
                        if plugin_info:
                            discovered_plugins.append(plugin_info)
                    
                    # Check for plugin directories
                    elif os.path.isdir(item_path) and not item.startswith('_'):
                        plugin_info = self._discover_directory_plugin(item_path)
                        if plugin_info:
                            discovered_plugins.append(plugin_info)
            
            except Exception as e:
                self.logger.error(f"Error discovering plugins in {directory}: {e}")
        
        # Register discovered plugins
        for plugin_info in discovered_plugins:
            self.plugin_registry.register_plugin(plugin_info)
        
        self.logger.info(f"Discovered {len(discovered_plugins)} plugins")
        return discovered_plugins
    
    def _discover_python_plugin(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Discover plugin from Python file"""
        try:
            # Load module to inspect for plugin classes
            spec = importlib.util.spec_from_file_location("temp_plugin", file_path)
            if not spec or not spec.loader:
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for PluginInterface subclasses
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, PluginInterface) and 
                    attr != PluginInterface):
                    
                    return {
                        'name': attr_name,
                        'path': file_path,
                        'type': 'python_file',
                        'class_name': attr_name,
                        'module_name': os.path.splitext(os.path.basename(file_path))[0]
                    }
        
        except Exception as e:
            self.logger.error(f"Error discovering plugin {file_path}: {e}")
        
        return None
    
    def _discover_directory_plugin(self, dir_path: str) -> Optional[Dict[str, Any]]:
        """Discover plugin from directory"""
        try:
            # Look for __init__.py or plugin.py
            init_file = os.path.join(dir_path, '__init__.py')
            plugin_file = os.path.join(dir_path, 'plugin.py')
            
            target_file = None
            if os.path.exists(plugin_file):
                target_file = plugin_file
            elif os.path.exists(init_file):
                target_file = init_file
            
            if target_file:
                return self._discover_python_plugin(target_file)
        
        except Exception as e:
            self.logger.error(f"Error discovering directory plugin {dir_path}: {e}")
        
        return None
    
    def load_plugin(self, plugin_name: str) -> bool:
        """
        Load a specific plugin by name
        
        Args:
            plugin_name: Name of the plugin to load
            
        Returns:
            bool: True if loaded successfully
        """
        if plugin_name in self.loaded_plugins:
            self.logger.warning(f"Plugin {plugin_name} is already loaded")
            return True
        
        try:
            # Get plugin info from registry
            plugin_info = self.plugin_registry.get_plugin_info(plugin_name)
            if not plugin_info:
                self.logger.error(f"Plugin not found in registry: {plugin_name}")
                return False
            
            # Load the plugin class
            plugin_class = self._load_plugin_class(plugin_info)
            if not plugin_class:
                return False
            
            # Create plugin instance
            plugin_instance = plugin_class()
            
            # Validate dependencies
            missing_deps = plugin_instance.validate_dependencies()
            if missing_deps:
                self.logger.error(f"Plugin {plugin_name} has missing dependencies: {missing_deps}")
                return False
            
            # Create plugin context
            context = self._create_plugin_context(plugin_name, plugin_info)
            
            # Initialize plugin
            if not plugin_instance.initialize(context):
                self.logger.error(f"Failed to initialize plugin: {plugin_name}")
                return False
            
            # Store plugin
            self.loaded_plugins[plugin_name] = plugin_instance
            self.initialization_order.append(plugin_name)
            
            self.logger.info(f"✅ Loaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading plugin {plugin_name}: {e}")
            return False
    
    def _load_plugin_class(self, plugin_info: Dict[str, Any]) -> Optional[Type[PluginInterface]]:
        """Load plugin class from plugin info"""
        try:
            if plugin_info['type'] == 'python_file':
                # Load from Python file
                spec = importlib.util.spec_from_file_location(
                    plugin_info['module_name'], 
                    plugin_info['path']
                )
                if not spec or not spec.loader:
                    return None
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Get the plugin class
                plugin_class = getattr(module, plugin_info['class_name'])
                
                if not issubclass(plugin_class, PluginInterface):
                    self.logger.error(f"Class {plugin_info['class_name']} is not a PluginInterface")
                    return None
                
                return plugin_class
            
            else:
                self.logger.error(f"Unsupported plugin type: {plugin_info['type']}")
                return None
        
        except Exception as e:
            self.logger.error(f"Error loading plugin class: {e}")
            return None
    
    def _create_plugin_context(self, plugin_name: str, plugin_info: Dict[str, Any]) -> PluginContext:
        """Create plugin context for initialization"""
        plugin_config = self.plugin_config.get(plugin_name, {})
        
        # Create data directory for plugin
        data_dir = None
        if self.app_config.get('plugin_data_directory'):
            data_dir = os.path.join(self.app_config['plugin_data_directory'], plugin_name)
            os.makedirs(data_dir, exist_ok=True)
        
        return PluginContext(
            service_manager=self.service_manager,
            plugin_config=plugin_config,
            app_config=self.app_config,
            plugin_name=plugin_name,
            data_directory=data_dir
        )
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a specific plugin
        
        Args:
            plugin_name: Name of the plugin to unload
            
        Returns:
            bool: True if unloaded successfully
        """
        if plugin_name not in self.loaded_plugins:
            self.logger.warning(f"Plugin {plugin_name} is not loaded")
            return True
        
        try:
            plugin = self.loaded_plugins[plugin_name]
            
            # Cleanup plugin
            plugin.cleanup()
            
            # Remove from storage
            del self.loaded_plugins[plugin_name]
            if plugin_name in self.initialization_order:
                self.initialization_order.remove(plugin_name)
            
            self.logger.info(f"✅ Unloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error unloading plugin {plugin_name}: {e}")
            return False
    
    def load_all_plugins(self) -> int:
        """
        Load all discovered plugins
        
        Returns:
            int: Number of plugins loaded successfully
        """
        plugin_names = self.plugin_registry.get_plugin_names()
        
        # Resolve dependencies and determine load order
        load_order = self._resolve_dependency_order(plugin_names)
        
        loaded_count = 0
        for plugin_name in load_order:
            if self.load_plugin(plugin_name):
                loaded_count += 1
        
        self.logger.info(f"Loaded {loaded_count}/{len(plugin_names)} plugins")
        return loaded_count
    
    def _resolve_dependency_order(self, plugin_names: List[str]) -> List[str]:
        """
        Resolve plugin dependency order using topological sort
        
        Args:
            plugin_names: List of plugin names to order
            
        Returns:
            List of plugin names in dependency order
        """
        # Simple dependency resolution - can be enhanced with proper topological sort
        # For now, just return the original order
        return plugin_names
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """Get loaded plugin by name"""
        return self.loaded_plugins.get(plugin_name)
    
    def get_plugins_by_capability(self, capability: str) -> List[PluginInterface]:
        """Get all plugins that provide a specific capability"""
        plugins = []
        for plugin in self.loaded_plugins.values():
            if capability in plugin.get_capabilities():
                plugins.append(plugin)
        return plugins
    
    def execute_capability(self, capability: str, *args, **kwargs) -> List[Any]:
        """
        Execute a capability across all plugins that support it
        
        Args:
            capability: Name of the capability to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            List of results from each plugin
        """
        results = []
        plugins = self.get_plugins_by_capability(capability)
        
        for plugin in plugins:
            try:
                if plugin.is_enabled:
                    result = plugin.execute(capability, *args, **kwargs)
                    results.append(result)
            except Exception as e:
                self.logger.error(f"Error executing {capability} on plugin {plugin.get_plugin_info()['name']}: {e}")
        
        return results
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """
        Reload a plugin (unload then load)
        
        Args:
            plugin_name: Name of the plugin to reload
            
        Returns:
            bool: True if reloaded successfully
        """
        if plugin_name in self.loaded_plugins:
            if not self.unload_plugin(plugin_name):
                return False
        
        return self.load_plugin(plugin_name)
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a loaded plugin"""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            plugin.enable()
            return True
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a loaded plugin"""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            plugin.disable()
            return True
        return False
    
    def get_plugin_status(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific plugin"""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            return plugin.get_status()
        return None
    
    def get_all_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all loaded plugins"""
        status = {}
        for name, plugin in self.loaded_plugins.items():
            status[name] = plugin.get_status()
        return status
    
    def set_plugin_config(self, plugin_name: str, config: Dict[str, Any]):
        """Set configuration for a plugin"""
        self.plugin_config[plugin_name] = config
    
    def set_app_config(self, config: Dict[str, Any]):
        """Set application configuration"""
        self.app_config = config
    
    def add_plugin_directory(self, directory: str):
        """Add a plugin directory to search path"""
        if directory not in self.plugin_directories:
            self.plugin_directories.append(directory)
    
    def get_loaded_plugin_names(self) -> List[str]:
        """Get list of loaded plugin names"""
        return list(self.loaded_plugins.keys())
    
    def get_available_plugin_names(self) -> List[str]:
        """Get list of available (discovered) plugin names"""
        return self.plugin_registry.get_plugin_names()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get plugin manager metrics"""
        return {
            'total_plugins_available': len(self.plugin_registry.get_plugin_names()),
            'total_plugins_loaded': len(self.loaded_plugins),
            'plugin_directories': self.plugin_directories,
            'is_running': self.is_running,
            'initialization_order': self.initialization_order
        } 