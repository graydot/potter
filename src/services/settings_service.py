#!/usr/bin/env python3
"""
Settings Service
Enhanced settings management with validation and service integration
"""

import logging
import json
from typing import Dict, Any, Optional, Callable, List, Union
from threading import Lock, RLock
from pathlib import Path
from copy import deepcopy

from .base_service import BaseService
from core.exceptions import ServiceError, ValidationException

logger = logging.getLogger(__name__)


class SettingsService(BaseService):
    """
    Service for managing application settings
    
    Features:
    - Settings persistence and loading
    - Settings validation
    - Change notifications
    - Settings migration
    - Type conversion
    - Default value management
    - Backup and restore
    - Settings encryption (optional)
    """
    
    def __init__(self, settings_file: Optional[Path] = None, validation_service=None):
        super().__init__("settings", {})
        
        self.validation_service = validation_service
        
        # Settings storage
        self._settings: Dict[str, Any] = {}
        self._settings_lock = RLock()  # Reentrant lock for nested access
        
        # File management
        self._settings_file = settings_file or Path.home() / ".potter" / "settings.json"
        self._backup_file = self._settings_file.with_suffix('.json.backup')
        
        # Change tracking
        self._change_callbacks: List[Callable[[str, Any, Any], None]] = []
        self._callbacks_lock = Lock()
        
        # Default values
        self._defaults: Dict[str, Any] = {}
        
        # Settings schema for validation
        self._schema: Dict[str, Dict[str, Any]] = {}
        
        # Migration handlers
        self._migration_handlers: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}
        
        # Auto-save configuration
        self._auto_save = True
        self._dirty = False
        
    def _start_service(self) -> None:
        """Start the settings service"""
        # Create settings directory
        self._settings_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load default settings schema
        self._load_default_schema()
        
        # Load settings from file
        self._load_settings()
        
        # Apply migrations if needed
        self._apply_migrations()
        
        # Validate loaded settings
        self._validate_all_settings()
        
        self.logger.info("⚙️ Settings service started")
    
    def _stop_service(self) -> None:
        """Stop the settings service"""
        # Save any pending changes
        if self._dirty and self._auto_save:
            self._save_settings()
        
        # Clear callbacks
        with self._callbacks_lock:
            self._change_callbacks.clear()
        
        self.logger.info("⚙️ Settings service stopped")
    
    def _get_service_status(self) -> Dict[str, Any]:
        """Get settings service specific status"""
        with self._settings_lock:
            return {
                'settings_file': str(self._settings_file),
                'backup_file': str(self._backup_file),
                'auto_save_enabled': self._auto_save,
                'dirty': self._dirty,
                'settings_count': len(self._settings),
                'defaults_count': len(self._defaults),
                'schema_count': len(self._schema),
                'change_callbacks': len(self._change_callbacks),
                'validation_service': self.validation_service is not None
            }
    
    def _handle_config_update(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        """Handle configuration updates"""
        if 'auto_save_settings' in new_config:
            self._auto_save = new_config['auto_save_settings']
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value
        
        Args:
            key: Setting key (supports dot notation like 'api.openai.key')
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        with self._settings_lock:
            # Handle dot notation
            if '.' in key:
                return self._get_nested_value(self._settings, key, default)
            else:
                return self._settings.get(key, default)
    
    def set(self, key: str, value: Any, validate: bool = True) -> bool:
        """
        Set a setting value
        
        Args:
            key: Setting key (supports dot notation)
            value: Value to set
            validate: Whether to validate the value
            
        Returns:
            bool: True if set successfully
        """
        try:
            # Validate value if requested
            if validate and self.validation_service:
                is_valid, error_msg = self._validate_setting(key, value)
                if not is_valid:
                    raise ValidationException(f"Invalid value for '{key}': {error_msg}")
            
            with self._settings_lock:
                old_value = self.get(key)
                
                # Set the value
                if '.' in key:
                    self._set_nested_value(self._settings, key, value)
                else:
                    self._settings[key] = value
                
                self._dirty = True
            
            # Notify callbacks
            self._notify_change_callbacks(key, old_value, value)
            
            # Auto-save if enabled
            if self._auto_save:
                self._save_settings()
            
            self.logger.debug(f"Set setting '{key}' = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting '{key}': {e}")
            return False
    
    def update(self, settings: Dict[str, Any], validate: bool = True) -> bool:
        """
        Update multiple settings at once
        
        Args:
            settings: Dict of settings to update
            validate: Whether to validate values
            
        Returns:
            bool: True if all updates successful
        """
        try:
            # Validate all settings first if requested
            if validate and self.validation_service:
                for key, value in settings.items():
                    is_valid, error_msg = self._validate_setting(key, value)
                    if not is_valid:
                        raise ValidationException(f"Invalid value for '{key}': {error_msg}")
            
            # Apply all changes
            changes = []
            with self._settings_lock:
                for key, value in settings.items():
                    old_value = self.get(key)
                    
                    if '.' in key:
                        self._set_nested_value(self._settings, key, value)
                    else:
                        self._settings[key] = value
                    
                    changes.append((key, old_value, value))
                
                self._dirty = True
            
            # Notify callbacks for all changes
            for key, old_value, new_value in changes:
                self._notify_change_callbacks(key, old_value, new_value)
            
            # Auto-save if enabled
            if self._auto_save:
                self._save_settings()
            
            self.logger.debug(f"Updated {len(settings)} settings")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating settings: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a setting
        
        Args:
            key: Setting key to delete
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            with self._settings_lock:
                old_value = self.get(key)
                
                if '.' in key:
                    self._delete_nested_value(self._settings, key)
                else:
                    if key in self._settings:
                        del self._settings[key]
                    else:
                        return False
                
                self._dirty = True
            
            # Notify callbacks
            self._notify_change_callbacks(key, old_value, None)
            
            # Auto-save if enabled
            if self._auto_save:
                self._save_settings()
            
            self.logger.debug(f"Deleted setting: {key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting '{key}': {e}")
            return False
    
    def has(self, key: str) -> bool:
        """
        Check if a setting exists
        
        Args:
            key: Setting key to check
            
        Returns:
            bool: True if setting exists
        """
        with self._settings_lock:
            if '.' in key:
                try:
                    self._get_nested_value(self._settings, key)
                    return True
                except KeyError:
                    return False
            else:
                return key in self._settings
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all settings
        
        Returns:
            Copy of all settings
        """
        with self._settings_lock:
            return deepcopy(self._settings)
    
    def clear(self, confirm: bool = False) -> bool:
        """
        Clear all settings
        
        Args:
            confirm: Must be True to actually clear
            
        Returns:
            bool: True if cleared
        """
        if not confirm:
            self.logger.warning("clear() called without confirmation")
            return False
        
        with self._settings_lock:
            self._settings.clear()
            self._dirty = True
        
        # Auto-save if enabled
        if self._auto_save:
            self._save_settings()
        
        self.logger.warning("⚠️ Cleared all settings")
        return True
    
    def save(self) -> bool:
        """
        Manually save settings to file
        
        Returns:
            bool: True if saved successfully
        """
        return self._save_settings()
    
    def load(self) -> bool:
        """
        Manually load settings from file
        
        Returns:
            bool: True if loaded successfully
        """
        return self._load_settings()
    
    def backup(self) -> bool:
        """
        Create a backup of current settings
        
        Returns:
            bool: True if backup created successfully
        """
        try:
            if self._settings_file.exists():
                import shutil
                shutil.copy2(self._settings_file, self._backup_file)
                self.logger.info(f"Created settings backup: {self._backup_file}")
                return True
            else:
                self.logger.warning("No settings file to backup")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return False
    
    def restore_backup(self) -> bool:
        """
        Restore settings from backup
        
        Returns:
            bool: True if restored successfully
        """
        try:
            if self._backup_file.exists():
                import shutil
                shutil.copy2(self._backup_file, self._settings_file)
                
                # Reload settings
                self._load_settings()
                
                self.logger.info("Restored settings from backup")
                return True
            else:
                self.logger.error("No backup file found")
                return False
                
        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            return False
    
    def add_change_callback(self, callback: Callable[[str, Any, Any], None]) -> None:
        """
        Add a callback for setting changes
        
        Args:
            callback: Function to call when settings change (key, old_value, new_value)
        """
        with self._callbacks_lock:
            if callback not in self._change_callbacks:
                self._change_callbacks.append(callback)
                self.logger.debug("Added settings change callback")
    
    def remove_change_callback(self, callback: Callable[[str, Any, Any], None]) -> None:
        """
        Remove a change callback
        
        Args:
            callback: Callback function to remove
        """
        with self._callbacks_lock:
            if callback in self._change_callbacks:
                self._change_callbacks.remove(callback)
                self.logger.debug("Removed settings change callback")
    
    def set_default(self, key: str, value: Any) -> None:
        """
        Set a default value for a setting
        
        Args:
            key: Setting key
            value: Default value
        """
        self._defaults[key] = value
    
    def get_default(self, key: str) -> Any:
        """
        Get the default value for a setting
        
        Args:
            key: Setting key
            
        Returns:
            Default value or None
        """
        return self._defaults.get(key)
    
    def reset_to_default(self, key: str) -> bool:
        """
        Reset a setting to its default value
        
        Args:
            key: Setting key to reset
            
        Returns:
            bool: True if reset successfully
        """
        if key in self._defaults:
            return self.set(key, self._defaults[key], validate=False)
        else:
            return self.delete(key)
    
    def _get_nested_value(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Get value using dot notation"""
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                if default is not None:
                    return default
                raise KeyError(f"Key '{key}' not found")
        
        return current
    
    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any) -> None:
        """Set value using dot notation"""
        keys = key.split('.')
        current = data
        
        # Navigate to parent
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            elif not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        # Set final value
        current[keys[-1]] = value
    
    def _delete_nested_value(self, data: Dict[str, Any], key: str) -> None:
        """Delete value using dot notation"""
        keys = key.split('.')
        current = data
        
        # Navigate to parent
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                raise KeyError(f"Key '{key}' not found")
            current = current[k]
        
        # Delete final key
        if keys[-1] in current:
            del current[keys[-1]]
        else:
            raise KeyError(f"Key '{key}' not found")
    
    def _load_settings(self) -> bool:
        """Load settings from file"""
        try:
            if not self._settings_file.exists():
                self.logger.debug("No settings file found, starting with defaults")
                with self._settings_lock:
                    self._settings = deepcopy(self._defaults)
                return True
            
            with open(self._settings_file, 'r') as f:
                data = json.load(f)
            
            with self._settings_lock:
                self._settings = data
                self._dirty = False
            
            self.logger.debug(f"Loaded settings from {self._settings_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
            # Fall back to defaults
            with self._settings_lock:
                self._settings = deepcopy(self._defaults)
            return False
    
    def _save_settings(self) -> bool:
        """Save settings to file"""
        try:
            # Create backup first
            self.backup()
            
            with self._settings_lock:
                data = deepcopy(self._settings)
                self._dirty = False
            
            # Write to temporary file first
            temp_file = self._settings_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2, sort_keys=True)
            
            # Atomic rename
            temp_file.rename(self._settings_file)
            
            self.logger.debug(f"Saved settings to {self._settings_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            return False
    
    def _validate_setting(self, key: str, value: Any) -> tuple[bool, str]:
        """Validate a setting value"""
        if not self.validation_service:
            return True, ""
        
        # Use validation service if available
        try:
            return self.validation_service.validate_setting(key, value)
        except Exception as e:
            self.logger.error(f"Error validating setting '{key}': {e}")
            return False, str(e)
    
    def _validate_all_settings(self) -> None:
        """Validate all current settings"""
        if not self.validation_service:
            return
        
        with self._settings_lock:
            invalid_settings = []
            
            for key, value in self._settings.items():
                is_valid, error_msg = self._validate_setting(key, value)
                if not is_valid:
                    invalid_settings.append((key, error_msg))
            
            if invalid_settings:
                self.logger.warning(f"Found {len(invalid_settings)} invalid settings")
                for key, error in invalid_settings:
                    self.logger.warning(f"  {key}: {error}")
    
    def _notify_change_callbacks(self, key: str, old_value: Any, new_value: Any) -> None:
        """Notify change callbacks"""
        with self._callbacks_lock:
            callbacks = self._change_callbacks.copy()
        
        for callback in callbacks:
            try:
                callback(key, old_value, new_value)
            except Exception as e:
                self.logger.error(f"Error in settings change callback: {e}")
    
    def _load_default_schema(self) -> None:
        """Load default settings schema"""
        # This would typically load from a schema file
        # For now, we'll define basic defaults
        self._defaults = {
            'api': {
                'openai': {'key': '', 'model': 'gpt-4'},
                'anthropic': {'key': '', 'model': 'claude-3-sonnet-20240229'},
                'google': {'key': '', 'model': 'gemini-pro'}
            },
            'ui': {
                'theme': 'auto',
                'font_size': 12,
                'window_opacity': 0.95
            },
            'hotkey': 'cmd+shift+p',
            'auto_save_settings': True,
            'check_for_updates': True
        }
    
    def _apply_migrations(self) -> None:
        """Apply any needed migrations"""
        # Migration logic would go here
        # For now, just log that migrations were checked
        self.logger.debug("Checked for settings migrations") 