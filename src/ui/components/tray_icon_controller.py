#!/usr/bin/env python3
"""
Tray Icon Controller
Service-integrated tray icon management
"""

import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
import threading

from .service_aware_component import ServiceAwareComponent
from services import (
    NotificationService, ThemeService, SettingsService, 
    HotkeyService, PermissionService
)

# Import original tray icon functionality
from ui.tray_icon import TrayIconManager

logger = logging.getLogger(__name__)


@dataclass
class TrayIconState:
    """Represents the current state of the tray icon"""
    is_processing: bool = False
    has_error: bool = False
    error_message: str = ""
    current_mode: str = "default"
    available_modes: List[str] = None
    notifications_enabled: bool = True
    permissions: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.available_modes is None:
            self.available_modes = []
        if self.permissions is None:
            self.permissions = {}


class TrayIconController(ServiceAwareComponent):
    """
    Service-integrated tray icon controller
    
    Integrates with:
    - NotificationService: For status notifications
    - ThemeService: For theme-aware icons
    - SettingsService: For configuration
    - HotkeyService: For hotkey updates
    - PermissionService: For permission status
    """
    
    def __init__(self, app_name: str = "Potter"):
        super().__init__(component_name="TrayIconController")
        
        self.app_name = app_name
        self._state = TrayIconState()
        self._state_lock = threading.Lock()
        
        # Original tray icon manager (for UI rendering)
        self._tray_manager: Optional[TrayIconManager] = None
        
        # Service references (will be initialized later)
        self._notification_service = None
        self._theme_service = None
        self._settings_service = None
        self._hotkey_service = None
        self._permission_service = None
        
        # Event callbacks (for backward compatibility)
        self._mode_change_callback: Optional[Callable] = None
        self._preferences_callback: Optional[Callable] = None
        self._process_callback: Optional[Callable] = None
        self._quit_callback: Optional[Callable] = None
    
    def _initialize_services(self):
        """Initialize required services"""
        try:
            # Get services
            self._notification_service = self.get_service_safely(NotificationService)
            self._theme_service = self.get_service_safely(ThemeService)
            self._settings_service = self.get_service_safely(SettingsService)
            self._hotkey_service = self.get_service_safely(HotkeyService)
            self._permission_service = self.get_service_safely(PermissionService)
            
            # Subscribe to service events
            if self._theme_service:
                self.subscribe_to_service(ThemeService, 'theme_changed', self._on_theme_changed)
            
            if self._settings_service:
                self.subscribe_to_service(SettingsService, 'settings_changed', self._on_settings_changed)
            
            if self._permission_service:
                self.subscribe_to_service(PermissionService, 'permission_changed', self._on_permission_changed)
            
            if self._hotkey_service:
                self.subscribe_to_service(HotkeyService, 'hotkey_changed', self._on_hotkey_changed)
            
            self.logger.info("Tray icon services initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            raise
    
    def _on_initialize(self):
        """Custom initialization logic"""
        # Create the actual tray icon manager
        self._tray_manager = TrayIconManager(
            app_name=self.app_name,
            on_mode_change=self._handle_mode_change,
            on_preferences=self._handle_preferences,
            on_notifications_toggle=self._handle_notifications_toggle,
            on_process_click=self._handle_process_click,
            on_quit=self._handle_quit
        )
        
        # Load initial state from services
        self._load_initial_state()
        
        # Update tray icon to reflect current state
        self._update_tray_icon()
    
    def _load_initial_state(self):
        """Load initial state from services"""
        with self._state_lock:
            # Load settings
            if self._settings_service:
                try:
                    # Get current mode and available modes
                    prompts = self._settings_service.get('prompts', [])
                    self._state.available_modes = [p.get('name', '') for p in prompts if p.get('name')]
                    if self._state.available_modes:
                        self._state.current_mode = self._state.available_modes[0]
                    
                    # Get notification settings
                    self._state.notifications_enabled = self._settings_service.get('notifications', True)
                    
                except Exception as e:
                    self.logger.error(f"Failed to load settings: {e}")
            
            # Load permissions
            if self._permission_service:
                try:
                    permissions = self._permission_service.get_all_permissions()
                    self._state.permissions = {
                        perm_type.value: status.value == "granted" 
                        for perm_type, status in permissions.items()
                    }
                except Exception as e:
                    self.logger.error(f"Failed to load permissions: {e}")
    
    def set_callbacks(self, 
                     on_mode_change: Callable = None,
                     on_preferences: Callable = None,
                     on_process_click: Callable = None,
                     on_quit: Callable = None):
        """
        Set callback functions for backward compatibility
        
        Args:
            on_mode_change: Callback for mode changes
            on_preferences: Callback for preferences
            on_process_click: Callback for process button
            on_quit: Callback for quit action
        """
        self._mode_change_callback = on_mode_change
        self._preferences_callback = on_preferences
        self._process_callback = on_process_click
        self._quit_callback = on_quit
    
    def set_processing_state(self, processing: bool):
        """
        Set processing state
        
        Args:
            processing: True if processing, False otherwise
        """
        with self._state_lock:
            if self._state.is_processing != processing:
                self._state.is_processing = processing
                self._state.has_error = False  # Clear error when processing state changes
                self._state.error_message = ""
                
                self.logger.debug(f"Processing state changed: {processing}")
                self._update_tray_icon()
                
                # Notify via notification service
                if self._notification_service and self._state.notifications_enabled:
                    if processing:
                        self._notification_service.show_info(
                            "Processing started", 
                            "Text processing in progress..."
                        )
                    else:
                        self._notification_service.show_success(
                            "Processing complete", 
                            "Text processing finished"
                        )
    
    def set_error_state(self, has_error: bool, error_message: str = ""):
        """
        Set error state
        
        Args:
            has_error: True if there's an error
            error_message: Error message to display
        """
        with self._state_lock:
            if self._state.has_error != has_error or self._state.error_message != error_message:
                self._state.has_error = has_error
                self._state.error_message = error_message
                
                if has_error:
                    self._state.is_processing = False  # Stop processing on error
                
                self.logger.debug(f"Error state changed: {has_error}, message: {error_message}")
                self._update_tray_icon()
                
                # Notify via notification service
                if self._notification_service and has_error and self._state.notifications_enabled:
                    self._notification_service.show_error(
                        "Processing Error", 
                        error_message or "An error occurred during processing"
                    )
    
    def clear_error(self):
        """Clear error state"""
        self.set_error_state(False, "")
    
    def set_current_mode(self, mode: str):
        """
        Set current processing mode
        
        Args:
            mode: Mode name
        """
        with self._state_lock:
            if mode in self._state.available_modes and self._state.current_mode != mode:
                self._state.current_mode = mode
                self.logger.debug(f"Mode changed: {mode}")
                self._update_tray_icon()
    
    def get_state(self) -> TrayIconState:
        """Get current tray icon state (copy)"""
        with self._state_lock:
            return TrayIconState(
                is_processing=self._state.is_processing,
                has_error=self._state.has_error,
                error_message=self._state.error_message,
                current_mode=self._state.current_mode,
                available_modes=self._state.available_modes.copy(),
                notifications_enabled=self._state.notifications_enabled,
                permissions=self._state.permissions.copy()
            )
    
    def _update_tray_icon(self):
        """Update the actual tray icon based on current state"""
        if not self._tray_manager:
            return
        
        try:
            with self._state_lock:
                # Update tray icon state
                self._tray_manager.set_processing_state(self._state.is_processing)
                self._tray_manager.set_error_state(self._state.has_error, self._state.error_message)
                
                # Update menu
                self._tray_manager.update_menu(
                    current_mode=self._state.current_mode,
                    available_modes=self._state.available_modes,
                    permissions=self._state.permissions,
                    notifications_enabled=self._state.notifications_enabled
                )
                
        except Exception as e:
            self.logger.error(f"Failed to update tray icon: {e}")
    
    def _on_theme_changed(self, theme_info: Dict):
        """Handle theme changes"""
        self.logger.debug(f"Theme changed: {theme_info}")
        
        if self._tray_manager:
            # Refresh icons for new theme
            self._tray_manager.refresh_logo_for_appearance()
            self._tray_manager.update_icon_for_appearance()
    
    def _on_settings_changed(self, settings: Dict):
        """Handle settings changes"""
        self.logger.debug("Settings changed, updating tray icon")
        
        with self._state_lock:
            # Update prompts/modes
            prompts = settings.get('prompts', [])
            old_modes = self._state.available_modes.copy()
            self._state.available_modes = [p.get('name', '') for p in prompts if p.get('name')]
            
            # Update current mode if it's no longer available
            if self._state.current_mode not in self._state.available_modes and self._state.available_modes:
                self._state.current_mode = self._state.available_modes[0]
            
            # Update notifications setting
            self._state.notifications_enabled = settings.get('notifications', True)
            
            # Log changes
            if old_modes != self._state.available_modes:
                self.logger.info(f"Available modes updated: {self._state.available_modes}")
        
        self._update_tray_icon()
    
    def _on_permission_changed(self, permission_info: Dict):
        """Handle permission changes"""
        self.logger.debug(f"Permission changed: {permission_info}")
        
        with self._state_lock:
            # Update permission status
            perm_type = permission_info.get('type')
            status = permission_info.get('status')
            if perm_type and status:
                self._state.permissions[perm_type] = (status == "granted")
        
        self._update_tray_icon()
    
    def _on_hotkey_changed(self, hotkey_info: Dict):
        """Handle hotkey changes"""
        self.logger.debug(f"Hotkey changed: {hotkey_info}")
        # The tray icon might show hotkey info, so update it
        self._update_tray_icon()
    
    # Event handlers (bridge to callbacks for backward compatibility)
    def _handle_mode_change(self, mode: str):
        """Handle mode change from tray menu"""
        self.set_current_mode(mode)
        
        # Update settings service
        if self._settings_service:
            try:
                self._settings_service.set('current_mode', mode)
            except Exception as e:
                self.logger.error(f"Failed to save mode change: {e}")
        
        # Call callback if set
        if self._mode_change_callback:
            try:
                self._mode_change_callback(mode)
            except Exception as e:
                self.logger.error(f"Error in mode change callback: {e}")
    
    def _handle_preferences(self, *args):
        """Handle preferences action"""
        self.logger.debug("Preferences requested")
        
        if self._preferences_callback:
            try:
                self._preferences_callback()
            except Exception as e:
                self.logger.error(f"Error in preferences callback: {e}")
    
    def _handle_notifications_toggle(self, *args):
        """Handle notifications toggle"""
        with self._state_lock:
            self._state.notifications_enabled = not self._state.notifications_enabled
            
        # Update settings
        if self._settings_service:
            try:
                self._settings_service.set('notifications', self._state.notifications_enabled)
            except Exception as e:
                self.logger.error(f"Failed to save notification setting: {e}")
        
        # Show notification about the change
        if self._notification_service:
            status = "enabled" if self._state.notifications_enabled else "disabled"
            self._notification_service.show_info(
                "Notifications", 
                f"Notifications {status}"
            )
        
        self._update_tray_icon()
    
    def _handle_process_click(self, *args):
        """Handle process button click"""
        self.logger.debug("Process button clicked")
        
        if self._process_callback:
            try:
                self._process_callback()
            except Exception as e:
                self.logger.error(f"Error in process callback: {e}")
    
    def _handle_quit(self, *args):
        """Handle quit action"""
        self.logger.debug("Quit requested")
        
        if self._quit_callback:
            try:
                self._quit_callback()
            except Exception as e:
                self.logger.error(f"Error in quit callback: {e}")
    
    def run(self):
        """Start the tray icon"""
        if self._tray_manager:
            self.logger.info("Starting tray icon")
            self._tray_manager.run()
    
    def stop(self):
        """Stop the tray icon"""
        if self._tray_manager:
            self.logger.info("Stopping tray icon")
            self._tray_manager.stop()
    
    def _on_cleanup(self):
        """Custom cleanup logic"""
        if self._tray_manager:
            try:
                self._tray_manager.stop()
            except Exception as e:
                self.logger.error(f"Error stopping tray manager: {e}")
            finally:
                self._tray_manager = None 