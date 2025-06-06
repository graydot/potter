#!/usr/bin/env python3
"""
Settings Controller
Service-integrated settings management with real-time validation
"""

import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from threading import Lock

from .service_aware_component import ServiceAwareComponent
from services import (
    SettingsService, ValidationService, ThemeService, 
    NotificationService, WindowService
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation operation"""
    is_valid: bool
    message: str = ""
    field: str = ""
    
    def __bool__(self):
        return self.is_valid


@dataclass
class SettingsState:
    """Current state of settings"""
    settings: Dict[str, Any]
    validation_results: Dict[str, ValidationResult]
    is_modified: bool = False
    is_saving: bool = False
    last_error: str = ""
    
    def __post_init__(self):
        if not hasattr(self, 'settings'):
            self.settings = {}
        if not hasattr(self, 'validation_results'):
            self.validation_results = {}


class SettingsController(ServiceAwareComponent):
    """
    Service-integrated settings controller
    
    Features:
    - Real-time validation using ValidationService
    - Settings persistence via SettingsService
    - Theme-aware UI via ThemeService
    - Window state management via WindowService
    - Error notifications via NotificationService
    - Automatic backup and recovery
    """
    
    def __init__(self):
        super().__init__(component_name="SettingsController")
        
        # Service references
        self._settings_service = None
        self._validation_service = None
        self._theme_service = None
        self._notification_service = None
        self._window_service = None
        
        # State management
        self._state = SettingsState(settings={}, validation_results={})
        self._state_lock = Lock()
        
        # UI callbacks
        self._validation_callbacks: Dict[str, List[Callable]] = {}
        self._change_callbacks: List[Callable] = []
        self._save_callbacks: List[Callable] = []
        
        # Auto-save settings
        self._auto_save_enabled = True
        self._auto_save_delay = 2.0  # seconds
        self._auto_save_timer = None
    
    def _initialize_services(self):
        """Initialize required services"""
        try:
            # Get services
            self._settings_service = self.get_service_safely(SettingsService)
            self._validation_service = self.get_service_safely(ValidationService)
            self._theme_service = self.get_service_safely(ThemeService)
            self._notification_service = self.get_service_safely(NotificationService)
            self._window_service = self.get_service_safely(WindowService)
            
            # Subscribe to service events
            if self._settings_service:
                self.subscribe_to_service(SettingsService, 'settings_changed', self._on_settings_changed)
                self.subscribe_to_service(SettingsService, 'settings_saved', self._on_settings_saved)
                self.subscribe_to_service(SettingsService, 'settings_error', self._on_settings_error)
            
            if self._theme_service:
                self.subscribe_to_service(ThemeService, 'theme_changed', self._on_theme_changed)
            
            self.logger.info("Settings services initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            raise
    
    def _on_initialize(self):
        """Custom initialization logic"""
        # Load current settings
        self._load_settings()
        
        # Validate all current settings
        self._validate_all_settings()
    
    def _load_settings(self):
        """Load settings from SettingsService"""
        if not self._settings_service:
            self.logger.warning("Settings service not available")
            return
        
        try:
            with self._state_lock:
                self._state.settings = self._settings_service.get_all()
                self._state.is_modified = False
                self._state.last_error = ""
            
            self.logger.debug(f"Loaded {len(self._state.settings)} settings")
            
            # Notify callbacks
            self._notify_change_callbacks()
            
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
            self._state.last_error = str(e)
    
    def get_setting(self, key: str, default=None):
        """
        Get a setting value
        
        Args:
            key: Setting key (supports dot notation)
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        with self._state_lock:
            if self._settings_service:
                return self._settings_service.get(key, default)
            else:
                # Fallback to local state
                return self._get_nested_value(self._state.settings, key, default)
    
    def set_setting(self, key: str, value: Any, validate: bool = True) -> ValidationResult:
        """
        Set a setting value with validation
        
        Args:
            key: Setting key (supports dot notation)
            value: New value
            validate: Whether to validate the value
            
        Returns:
            ValidationResult
        """
        # Validate first if requested
        if validate and self._validation_service:
            validation_result = self._validate_setting(key, value)
            if not validation_result.is_valid:
                self.logger.warning(f"Validation failed for {key}: {validation_result.message}")
                return validation_result
        else:
            validation_result = ValidationResult(True)
        
        # Set the value
        try:
            with self._state_lock:
                if self._settings_service:
                    # Use service to set value
                    self._settings_service.set(key, value)
                    # Update local state
                    self._set_nested_value(self._state.settings, key, value)
                else:
                    # Fallback to local state only
                    self._set_nested_value(self._state.settings, key, value)
                
                self._state.is_modified = True
                
                # Store validation result
                self._state.validation_results[key] = validation_result
            
            self.logger.debug(f"Setting updated: {key} = {value}")
            
            # Notify callbacks
            self._notify_validation_callbacks(key, validation_result)
            self._notify_change_callbacks()
            
            # Schedule auto-save
            if self._auto_save_enabled:
                self._schedule_auto_save()
            
            return validation_result
            
        except Exception as e:
            error_msg = f"Failed to set {key}: {e}"
            self.logger.error(error_msg)
            return ValidationResult(False, error_msg, key)
    
    def _validate_setting(self, key: str, value: Any) -> ValidationResult:
        """Validate a setting value"""
        if not self._validation_service:
            return ValidationResult(True)
        
        try:
            # Use validation service
            is_valid, message = self._validation_service.validate_setting(key, value)
            return ValidationResult(is_valid, message, key)
            
        except Exception as e:
            self.logger.error(f"Validation error for {key}: {e}")
            return ValidationResult(False, f"Validation error: {e}", key)
    
    def _validate_all_settings(self):
        """Validate all current settings"""
        if not self._validation_service:
            return
        
        with self._state_lock:
            for key, value in self._state.settings.items():
                if isinstance(value, dict):
                    # Skip nested dictionaries for now
                    continue
                
                validation_result = self._validate_setting(key, value)
                self._state.validation_results[key] = validation_result
                
                if not validation_result.is_valid:
                    self.logger.warning(f"Invalid setting {key}: {validation_result.message}")
    
    def get_validation_result(self, key: str) -> Optional[ValidationResult]:
        """Get validation result for a setting"""
        with self._state_lock:
            return self._state.validation_results.get(key)
    
    def get_all_validation_results(self) -> Dict[str, ValidationResult]:
        """Get all validation results"""
        with self._state_lock:
            return self._state.validation_results.copy()
    
    def is_valid(self) -> bool:
        """Check if all settings are valid"""
        with self._state_lock:
            return all(result.is_valid for result in self._state.validation_results.values())
    
    def get_invalid_settings(self) -> Dict[str, ValidationResult]:
        """Get all invalid settings"""
        with self._state_lock:
            return {
                key: result for key, result in self._state.validation_results.items()
                if not result.is_valid
            }
    
    def save_settings(self) -> bool:
        """
        Save settings to disk
        
        Returns:
            True if saved successfully
        """
        if not self._settings_service:
            self.logger.error("Settings service not available")
            return False
        
        # Check if all settings are valid
        if not self.is_valid():
            invalid_settings = self.get_invalid_settings()
            self.logger.error(f"Cannot save invalid settings: {list(invalid_settings.keys())}")
            
            if self._notification_service:
                self._notification_service.show_error(
                    "Invalid Settings",
                    f"Please fix validation errors in: {', '.join(invalid_settings.keys())}"
                )
            return False
        
        try:
            with self._state_lock:
                self._state.is_saving = True
            
            # Save via service
            success = self._settings_service.save()
            
            with self._state_lock:
                self._state.is_saving = False
                if success:
                    self._state.is_modified = False
                    self._state.last_error = ""
            
            if success:
                self.logger.info("Settings saved successfully")
                if self._notification_service:
                    self._notification_service.show_success("Settings Saved", "Your preferences have been saved")
                
                # Notify callbacks
                self._notify_save_callbacks(True)
            else:
                self.logger.error("Failed to save settings")
                if self._notification_service:
                    self._notification_service.show_error("Save Failed", "Could not save settings")
                
                self._notify_save_callbacks(False)
            
            return success
            
        except Exception as e:
            with self._state_lock:
                self._state.is_saving = False
                self._state.last_error = str(e)
            
            self.logger.error(f"Error saving settings: {e}")
            if self._notification_service:
                self._notification_service.show_error("Save Error", f"Error saving settings: {e}")
            
            self._notify_save_callbacks(False)
            return False
    
    def reset_settings(self) -> bool:
        """Reset settings to defaults"""
        if not self._settings_service:
            return False
        
        try:
            # Reset via service
            self._settings_service.reset_to_defaults()
            
            # Reload settings
            self._load_settings()
            
            # Revalidate all
            self._validate_all_settings()
            
            self.logger.info("Settings reset to defaults")
            if self._notification_service:
                self._notification_service.show_info("Settings Reset", "Settings have been reset to defaults")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reset settings: {e}")
            if self._notification_service:
                self._notification_service.show_error("Reset Failed", f"Could not reset settings: {e}")
            return False
    
    def _schedule_auto_save(self):
        """Schedule auto-save after delay"""
        if self._auto_save_timer:
            self._auto_save_timer.cancel()
        
        import threading
        self._auto_save_timer = threading.Timer(self._auto_save_delay, self._auto_save)
        self._auto_save_timer.start()
    
    def _auto_save(self):
        """Perform auto-save"""
        if self._state.is_modified and not self._state.is_saving:
            self.logger.debug("Auto-saving settings")
            self.save_settings()
    
    # Callback management
    def add_validation_callback(self, key: str, callback: Callable[[str, ValidationResult], None]):
        """Add callback for validation events"""
        if key not in self._validation_callbacks:
            self._validation_callbacks[key] = []
        self._validation_callbacks[key].append(callback)
    
    def add_change_callback(self, callback: Callable[[], None]):
        """Add callback for settings changes"""
        self._change_callbacks.append(callback)
    
    def add_save_callback(self, callback: Callable[[bool], None]):
        """Add callback for save events"""
        self._save_callbacks.append(callback)
    
    def _notify_validation_callbacks(self, key: str, result: ValidationResult):
        """Notify validation callbacks"""
        callbacks = self._validation_callbacks.get(key, [])
        for callback in callbacks:
            try:
                callback(key, result)
            except Exception as e:
                self.logger.error(f"Error in validation callback: {e}")
    
    def _notify_change_callbacks(self):
        """Notify change callbacks"""
        for callback in self._change_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in change callback: {e}")
    
    def _notify_save_callbacks(self, success: bool):
        """Notify save callbacks"""
        for callback in self._save_callbacks:
            try:
                callback(success)
            except Exception as e:
                self.logger.error(f"Error in save callback: {e}")
    
    # Service event handlers
    def _on_settings_changed(self, settings: Dict):
        """Handle settings changed event from service"""
        self.logger.debug("Settings changed externally")
        with self._state_lock:
            self._state.settings.update(settings)
        self._notify_change_callbacks()
    
    def _on_settings_saved(self, success: bool):
        """Handle settings saved event from service"""
        self.logger.debug(f"Settings save event: {success}")
        with self._state_lock:
            if success:
                self._state.is_modified = False
        self._notify_save_callbacks(success)
    
    def _on_settings_error(self, error: str):
        """Handle settings error event from service"""
        self.logger.error(f"Settings service error: {error}")
        with self._state_lock:
            self._state.last_error = error
        
        if self._notification_service:
            self._notification_service.show_error("Settings Error", error)
    
    def _on_theme_changed(self, theme_info: Dict):
        """Handle theme change events"""
        self.logger.debug("Theme changed, may need to update UI")
        # UI components can override this to update their appearance
    
    # Utility methods
    def _get_nested_value(self, data: Dict, key: str, default=None):
        """Get nested value using dot notation"""
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def _set_nested_value(self, data: Dict, key: str, value: Any):
        """Set nested value using dot notation"""
        keys = key.split('.')
        current = data
        
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def get_state(self) -> SettingsState:
        """Get current settings state (copy)"""
        with self._state_lock:
            return SettingsState(
                settings=self._state.settings.copy(),
                validation_results=self._state.validation_results.copy(),
                is_modified=self._state.is_modified,
                is_saving=self._state.is_saving,
                last_error=self._state.last_error
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Get controller status"""
        with self._state_lock:
            invalid_count = len([r for r in self._state.validation_results.values() if not r.is_valid])
            
            return {
                'settings_count': len(self._state.settings),
                'is_modified': self._state.is_modified,
                'is_saving': self._state.is_saving,
                'is_valid': self.is_valid(),
                'validation_count': len(self._state.validation_results),
                'invalid_count': invalid_count,
                'last_error': self._state.last_error,
                'auto_save_enabled': self._auto_save_enabled,
                'services_available': {
                    'settings': self._settings_service is not None,
                    'validation': self._validation_service is not None,
                    'theme': self._theme_service is not None,
                    'notification': self._notification_service is not None,
                    'window': self._window_service is not None
                }
            }
    
    def _on_cleanup(self):
        """Custom cleanup logic"""
        # Cancel auto-save timer
        if self._auto_save_timer:
            self._auto_save_timer.cancel()
            self._auto_save_timer = None
        
        # Save if modified
        if self._state.is_modified and not self._state.is_saving:
            try:
                self.save_settings()
            except Exception as e:
                self.logger.error(f"Error saving on cleanup: {e}")
        
        # Clear callbacks
        self._validation_callbacks.clear()
        self._change_callbacks.clear()
        self._save_callbacks.clear() 