#!/usr/bin/env python3
"""
Plugin Registry
Plugin discovery and metadata management
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Registry for plugin discovery and metadata management
    
    Features:
    - Plugin metadata storage
    - Plugin discovery tracking
    - Dependency management
    - Version compatibility
    - Plugin categorization
    """
    
    def __init__(self):
        self.logger = logging.getLogger("plugin.registry")
        
        # Plugin storage
        self.plugins: Dict[str, Dict[str, Any]] = {}
        self.categories: Dict[str, List[str]] = {}
        self.dependencies: Dict[str, List[str]] = {}
        
        # Version tracking
        self.plugin_versions: Dict[str, str] = {}
        self.compatibility_matrix: Dict[str, Dict[str, bool]] = {}
    
    def register_plugin(self, plugin_info: Dict[str, Any]) -> bool:
        """
        Register a plugin in the registry
        
        Args:
            plugin_info: Plugin information dictionary
            
        Returns:
            bool: True if registered successfully
        """
        try:
            plugin_name = plugin_info.get('name')
            if not plugin_name:
                self.logger.error("Plugin info missing 'name' field")
                return False
            
            # Store plugin info
            self.plugins[plugin_name] = plugin_info.copy()
            
            # Extract version
            version = plugin_info.get('version', '1.0.0')
            self.plugin_versions[plugin_name] = version
            
            # Extract dependencies
            dependencies = plugin_info.get('dependencies', [])
            self.dependencies[plugin_name] = dependencies
            
            # Extract categories
            categories = plugin_info.get('categories', ['general'])
            for category in categories:
                if category not in self.categories:
                    self.categories[category] = []
                if plugin_name not in self.categories[category]:
                    self.categories[category].append(plugin_name)
            
            self.logger.debug(f"Registered plugin: {plugin_name} v{version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering plugin: {e}")
            return False
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        Unregister a plugin from the registry
        
        Args:
            plugin_name: Name of the plugin to unregister
            
        Returns:
            bool: True if unregistered successfully
        """
        try:
            if plugin_name not in self.plugins:
                self.logger.warning(f"Plugin {plugin_name} not found in registry")
                return False
            
            # Remove from plugins
            del self.plugins[plugin_name]
            
            # Remove version
            if plugin_name in self.plugin_versions:
                del self.plugin_versions[plugin_name]
            
            # Remove dependencies
            if plugin_name in self.dependencies:
                del self.dependencies[plugin_name]
            
            # Remove from categories
            for category, plugin_list in self.categories.items():
                if plugin_name in plugin_list:
                    plugin_list.remove(plugin_name)
            
            # Clean empty categories
            empty_categories = [cat for cat, plugins in self.categories.items() if not plugins]
            for cat in empty_categories:
                del self.categories[cat]
            
            self.logger.debug(f"Unregistered plugin: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error unregistering plugin {plugin_name}: {e}")
            return False
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get plugin information
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin information dictionary or None if not found
        """
        return self.plugins.get(plugin_name)
    
    def get_plugin_names(self) -> List[str]:
        """Get list of all registered plugin names"""
        return list(self.plugins.keys())
    
    def get_plugins_by_category(self, category: str) -> List[str]:
        """
        Get plugins in a specific category
        
        Args:
            category: Category name
            
        Returns:
            List of plugin names in the category
        """
        return self.categories.get(category, [])
    
    def get_categories(self) -> List[str]:
        """Get list of all categories"""
        return list(self.categories.keys())
    
    def get_plugin_dependencies(self, plugin_name: str) -> List[str]:
        """
        Get dependencies for a plugin
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            List of dependency names
        """
        return self.dependencies.get(plugin_name, [])
    
    def get_dependent_plugins(self, plugin_name: str) -> List[str]:
        """
        Get plugins that depend on the specified plugin
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            List of plugin names that depend on this plugin
        """
        dependents = []
        for name, deps in self.dependencies.items():
            if plugin_name in deps:
                dependents.append(name)
        return dependents
    
    def validate_dependencies(self, plugin_name: str) -> List[str]:
        """
        Validate dependencies for a plugin
        
        Args:
            plugin_name: Name of the plugin to validate
            
        Returns:
            List of missing dependencies
        """
        if plugin_name not in self.dependencies:
            return []
        
        missing_deps = []
        for dep in self.dependencies[plugin_name]:
            if dep not in self.plugins:
                missing_deps.append(dep)
        
        return missing_deps
    
    def get_dependency_order(self, plugin_names: List[str]) -> List[str]:
        """
        Get plugins in dependency order (topological sort)
        
        Args:
            plugin_names: List of plugin names to order
            
        Returns:
            List of plugin names in dependency order
        """
        # Simple topological sort implementation
        result = []
        visited = set()
        temp_visited = set()
        
        def visit(name: str):
            if name in temp_visited:
                # Circular dependency detected
                self.logger.warning(f"Circular dependency detected involving {name}")
                return
            
            if name in visited:
                return
            
            temp_visited.add(name)
            
            # Visit dependencies first
            for dep in self.dependencies.get(name, []):
                if dep in plugin_names:  # Only consider plugins in the input list
                    visit(dep)
            
            temp_visited.remove(name)
            visited.add(name)
            result.append(name)
        
        for name in plugin_names:
            if name not in visited:
                visit(name)
        
        return result
    
    def check_compatibility(self, plugin_name: str, target_version: str) -> bool:
        """
        Check if a plugin version is compatible
        
        Args:
            plugin_name: Name of the plugin
            target_version: Target version to check
            
        Returns:
            bool: True if compatible
        """
        if plugin_name not in self.compatibility_matrix:
            return True  # Assume compatible if no matrix defined
        
        return self.compatibility_matrix[plugin_name].get(target_version, True)
    
    def set_compatibility(self, plugin_name: str, version: str, compatible: bool):
        """
        Set compatibility information for a plugin version
        
        Args:
            plugin_name: Name of the plugin
            version: Version string
            compatible: Whether this version is compatible
        """
        if plugin_name not in self.compatibility_matrix:
            self.compatibility_matrix[plugin_name] = {}
        
        self.compatibility_matrix[plugin_name][version] = compatible
    
    def search_plugins(self, query: str) -> List[str]:
        """
        Search for plugins by name, description, or keywords
        
        Args:
            query: Search query
            
        Returns:
            List of matching plugin names
        """
        query_lower = query.lower()
        matches = []
        
        for name, info in self.plugins.items():
            # Check name
            if query_lower in name.lower():
                matches.append(name)
                continue
            
            # Check description
            description = info.get('description', '')
            if query_lower in description.lower():
                matches.append(name)
                continue
            
            # Check keywords
            keywords = info.get('keywords', [])
            for keyword in keywords:
                if query_lower in keyword.lower():
                    matches.append(name)
                    break
        
        return matches
    
    def get_plugin_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about registered plugins
        
        Returns:
            Dictionary with plugin statistics
        """
        stats = {
            'total_plugins': len(self.plugins),
            'categories': {cat: len(plugins) for cat, plugins in self.categories.items()},
            'plugins_with_dependencies': len([p for p in self.dependencies.values() if p]),
            'average_dependencies_per_plugin': 0.0,
            'most_common_category': None,
            'plugins_by_version': {}
        }
        
        # Calculate average dependencies
        if self.dependencies:
            total_deps = sum(len(deps) for deps in self.dependencies.values())
            stats['average_dependencies_per_plugin'] = total_deps / len(self.dependencies)
        
        # Find most common category
        if self.categories:
            most_common = max(self.categories.items(), key=lambda x: len(x[1]))
            stats['most_common_category'] = most_common[0]
        
        # Group by version
        for name, version in self.plugin_versions.items():
            if version not in stats['plugins_by_version']:
                stats['plugins_by_version'][version] = []
            stats['plugins_by_version'][version].append(name)
        
        return stats
    
    def export_registry(self) -> Dict[str, Any]:
        """
        Export registry data for backup or transfer
        
        Returns:
            Dictionary containing all registry data
        """
        return {
            'plugins': self.plugins.copy(),
            'categories': self.categories.copy(),
            'dependencies': self.dependencies.copy(),
            'plugin_versions': self.plugin_versions.copy(),
            'compatibility_matrix': self.compatibility_matrix.copy()
        }
    
    def import_registry(self, registry_data: Dict[str, Any]) -> bool:
        """
        Import registry data from backup or transfer
        
        Args:
            registry_data: Registry data dictionary
            
        Returns:
            bool: True if imported successfully
        """
        try:
            self.plugins = registry_data.get('plugins', {})
            self.categories = registry_data.get('categories', {})
            self.dependencies = registry_data.get('dependencies', {})
            self.plugin_versions = registry_data.get('plugin_versions', {})
            self.compatibility_matrix = registry_data.get('compatibility_matrix', {})
            
            self.logger.info(f"Imported registry with {len(self.plugins)} plugins")
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing registry: {e}")
            return False
    
    def clear_registry(self):
        """Clear all registry data"""
        self.plugins.clear()
        self.categories.clear()
        self.dependencies.clear()
        self.plugin_versions.clear()
        self.compatibility_matrix.clear()
        
        self.logger.info("Registry cleared")
    
    def get_registry_info(self) -> Dict[str, Any]:
        """
        Get information about the registry itself
        
        Returns:
            Dictionary with registry information
        """
        return {
            'total_plugins': len(self.plugins),
            'total_categories': len(self.categories),
            'total_dependencies': sum(len(deps) for deps in self.dependencies.values()),
            'plugins_with_dependencies': len([p for p in self.dependencies.values() if p]),
            'categories': list(self.categories.keys()),
            'versions': list(set(self.plugin_versions.values()))
        } 