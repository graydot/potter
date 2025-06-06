#!/usr/bin/env python3
"""
Configuration Hierarchy
Multi-level configuration with inheritance and overrides
"""

import logging
from typing import Dict, Any, Optional, List, Union
from copy import deepcopy

logger = logging.getLogger(__name__)


class ConfigurationLevel:
    """
    Represents a single level in the configuration hierarchy
    """
    
    def __init__(self, name: str, priority: int, config: Dict[str, Any] = None):
        """
        Initialize configuration level
        
        Args:
            name: Level name (e.g., 'global', 'environment', 'user')
            priority: Level priority (lower = higher priority)
            config: Configuration data for this level
        """
        self.name = name
        self.priority = priority
        self.config = config or {}
        self.enabled = True
    
    def get_value(self, key: str, default=None) -> Any:
        """Get configuration value from this level"""
        return self._get_nested_value(self.config, key, default)
    
    def set_value(self, key: str, value: Any):
        """Set configuration value in this level"""
        self._set_nested_value(self.config, key, value)
    
    def has_key(self, key: str) -> bool:
        """Check if key exists in this level"""
        try:
            self._get_nested_value(self.config, key)
            return True
        except KeyError:
            return False
    
    def _get_nested_value(self, config: Dict[str, Any], key: str, default=None) -> Any:
        """Get nested value using dot notation"""
        parts = key.split('.')
        current = config
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                if default is not None:
                    return default
                raise KeyError(f"Key not found: {key}")
        
        return current
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any):
        """Set nested value using dot notation"""
        parts = key.split('.')
        current = config
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    def merge_config(self, other_config: Dict[str, Any]):
        """Merge another configuration into this level"""
        self.config = self._deep_merge(self.config, other_config)
    
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert level to dictionary representation"""
        return {
            'name': self.name,
            'priority': self.priority,
            'enabled': self.enabled,
            'config': deepcopy(self.config)
        }


class ConfigurationHierarchy:
    """
    Manages hierarchical configuration with multiple levels and inheritance
    
    Configuration hierarchy (lower priority number = higher priority):
    1. Runtime (priority: 10)
    2. User (priority: 20)  
    3. Service (priority: 30)
    4. Environment (priority: 40)
    5. Global (priority: 50)
    """
    
    def __init__(self):
        self.levels: Dict[str, ConfigurationLevel] = {}
        self.logger = logging.getLogger("config.hierarchy")
        
        # Create default levels
        self._create_default_levels()
    
    def _create_default_levels(self):
        """Create default configuration levels"""
        self.add_level("global", 50)
        self.add_level("environment", 40)
        self.add_level("service", 30)
        self.add_level("user", 20)
        self.add_level("runtime", 10)
    
    def add_level(self, name: str, priority: int, config: Dict[str, Any] = None) -> bool:
        """
        Add a configuration level
        
        Args:
            name: Level name
            priority: Level priority (lower = higher priority)
            config: Initial configuration for this level
            
        Returns:
            True if level was added successfully
        """
        try:
            if name in self.levels:
                self.logger.warning(f"Configuration level '{name}' already exists")
                return False
            
            self.levels[name] = ConfigurationLevel(name, priority, config)
            self.logger.debug(f"Added configuration level: {name} (priority: {priority})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding configuration level '{name}': {e}")
            return False
    
    def remove_level(self, name: str) -> bool:
        """
        Remove a configuration level
        
        Args:
            name: Level name to remove
            
        Returns:
            True if level was removed successfully
        """
        if name in self.levels:
            del self.levels[name]
            self.logger.debug(f"Removed configuration level: {name}")
            return True
        else:
            self.logger.warning(f"Configuration level '{name}' not found")
            return False
    
    def get_level(self, name: str) -> Optional[ConfigurationLevel]:
        """Get configuration level by name"""
        return self.levels.get(name)
    
    def set_level_config(self, level_name: str, config: Dict[str, Any]) -> bool:
        """
        Set configuration for a specific level
        
        Args:
            level_name: Name of the level
            config: Configuration data
            
        Returns:
            True if configuration was set successfully
        """
        level = self.get_level(level_name)
        if level:
            level.config = deepcopy(config)
            self.logger.debug(f"Set configuration for level '{level_name}'")
            return True
        else:
            self.logger.error(f"Configuration level '{level_name}' not found")
            return False
    
    def merge_level_config(self, level_name: str, config: Dict[str, Any]) -> bool:
        """
        Merge configuration into a specific level
        
        Args:
            level_name: Name of the level
            config: Configuration data to merge
            
        Returns:
            True if configuration was merged successfully
        """
        level = self.get_level(level_name)
        if level:
            level.merge_config(config)
            self.logger.debug(f"Merged configuration into level '{level_name}'")
            return True
        else:
            self.logger.error(f"Configuration level '{level_name}' not found")
            return False
    
    def get_value(self, key: str, default=None, levels: List[str] = None) -> Any:
        """
        Get configuration value with hierarchy resolution
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            levels: Specific levels to search (if None, searches all)
            
        Returns:
            Configuration value from highest priority level containing the key
        """
        search_levels = levels or list(self.levels.keys())
        
        # Sort levels by priority (lower number = higher priority)
        sorted_levels = sorted(
            [self.levels[name] for name in search_levels if name in self.levels],
            key=lambda x: x.priority
        )
        
        for level in sorted_levels:
            if level.enabled and level.has_key(key):
                value = level.get_value(key)
                self.logger.debug(f"Found key '{key}' in level '{level.name}': {value}")
                return value
        
        self.logger.debug(f"Key '{key}' not found in hierarchy, returning default: {default}")
        return default
    
    def set_value(self, key: str, value: Any, level_name: str = "runtime") -> bool:
        """
        Set configuration value in a specific level
        
        Args:
            key: Configuration key (supports dot notation)
            value: Configuration value
            level_name: Level to set the value in
            
        Returns:
            True if value was set successfully
        """
        level = self.get_level(level_name)
        if level:
            level.set_value(key, value)
            self.logger.debug(f"Set '{key}' = '{value}' in level '{level_name}'")
            return True
        else:
            self.logger.error(f"Configuration level '{level_name}' not found")
            return False
    
    def has_key(self, key: str, levels: List[str] = None) -> bool:
        """
        Check if key exists in any level of the hierarchy
        
        Args:
            key: Configuration key
            levels: Specific levels to search (if None, searches all)
            
        Returns:
            True if key exists in any searched level
        """
        search_levels = levels or list(self.levels.keys())
        
        for level_name in search_levels:
            level = self.levels.get(level_name)
            if level and level.enabled and level.has_key(key):
                return True
        
        return False
    
    def get_merged_config(self, levels: List[str] = None) -> Dict[str, Any]:
        """
        Get merged configuration from all levels
        
        Args:
            levels: Specific levels to merge (if None, merges all)
            
        Returns:
            Merged configuration dictionary
        """
        merge_levels = levels or list(self.levels.keys())
        
        # Sort levels by priority (higher number = lower priority, merged first)
        sorted_levels = sorted(
            [self.levels[name] for name in merge_levels if name in self.levels],
            key=lambda x: x.priority,
            reverse=True
        )
        
        merged_config = {}
        
        for level in sorted_levels:
            if level.enabled:
                merged_config = self._deep_merge(merged_config, level.config)
                self.logger.debug(f"Merged configuration from level '{level.name}'")
        
        return merged_config
    
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
    
    def enable_level(self, level_name: str) -> bool:
        """Enable a configuration level"""
        level = self.get_level(level_name)
        if level:
            level.enabled = True
            self.logger.debug(f"Enabled configuration level: {level_name}")
            return True
        return False
    
    def disable_level(self, level_name: str) -> bool:
        """Disable a configuration level"""
        level = self.get_level(level_name)
        if level:
            level.enabled = False
            self.logger.debug(f"Disabled configuration level: {level_name}")
            return True
        return False
    
    def get_level_names(self) -> List[str]:
        """Get list of all level names"""
        return list(self.levels.keys())
    
    def get_enabled_levels(self) -> List[str]:
        """Get list of enabled level names"""
        return [name for name, level in self.levels.items() if level.enabled]
    
    def get_hierarchy_info(self) -> Dict[str, Any]:
        """
        Get information about the configuration hierarchy
        
        Returns:
            Dictionary with hierarchy information
        """
        levels_info = []
        
        # Sort by priority
        sorted_levels = sorted(self.levels.values(), key=lambda x: x.priority)
        
        for level in sorted_levels:
            levels_info.append({
                'name': level.name,
                'priority': level.priority,
                'enabled': level.enabled,
                'config_keys': len(level.config),
                'has_config': bool(level.config)
            })
        
        return {
            'total_levels': len(self.levels),
            'enabled_levels': len(self.get_enabled_levels()),
            'levels': levels_info
        }
    
    def reset_level(self, level_name: str) -> bool:
        """
        Reset a configuration level (clear all configuration)
        
        Args:
            level_name: Name of the level to reset
            
        Returns:
            True if level was reset successfully
        """
        level = self.get_level(level_name)
        if level:
            level.config = {}
            self.logger.debug(f"Reset configuration level: {level_name}")
            return True
        else:
            self.logger.error(f"Configuration level '{level_name}' not found")
            return False
    
    def clone_level(self, source_level: str, target_level: str, priority: int) -> bool:
        """
        Clone configuration from one level to another
        
        Args:
            source_level: Source level name
            target_level: Target level name  
            priority: Priority for the new level
            
        Returns:
            True if level was cloned successfully
        """
        source = self.get_level(source_level)
        if not source:
            self.logger.error(f"Source level '{source_level}' not found")
            return False
        
        # Create or update target level
        if target_level in self.levels:
            self.levels[target_level].config = deepcopy(source.config)
            self.levels[target_level].priority = priority
        else:
            self.add_level(target_level, priority, deepcopy(source.config))
        
        self.logger.debug(f"Cloned level '{source_level}' to '{target_level}'")
        return True 