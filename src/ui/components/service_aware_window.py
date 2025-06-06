#!/usr/bin/env python3
"""
Service-Aware Window Base Class
Extension of BaseSettingsWindow with service integration
"""

import logging
from typing import Dict, Any, Optional, Callable

from .service_aware_component import ServiceAwareComponent
from ..settings.base_settings_window import BaseSettingsWindow
# Import services with try/except for flexibility
try:
    from services.settings_service import SettingsService
    from services.theme_service import ThemeService
    from services.window_service import WindowService
    from services.validation_service import ValidationService
    from services.notification_service import NotificationService
except ImportError:
    # Fallback for test environment
    SettingsService = None
    ThemeService = None
    WindowService = None
    ValidationService = None
    NotificationService = None

logger = logging.getLogger(__name__)


class ServiceAwareWindow(BaseSettingsWindow, ServiceAwareComponent):
    """
    Service-integrated window base class
    
    Combines BaseSettingsWindow functionality with service integration:
    - Automatic window state persistence via WindowService
    - Theme updates via ThemeService
    - Settings integration via SettingsService
    - Real-time validation via ValidationService
    - Error notifications via NotificationService
    """
    
    def __init__(self, window_id: str = None):
        """
        Initialize service-aware window
        
        Args:
            window_id: Unique identifier for window state persistence
        """
        # Initialize both parent classes
        BaseSettingsWindow.__init__(self)
        ServiceAwareComponent.__init__(self, component_name=f"Window_{window_id or 'Unknown'}")
        
        self.window_id = window_id or self.__class__.__name__
        
        # Service references
        self._settings_service = None
        self._theme_service = None
        self._window_service = None
        self._validation_service = None
        self._notification_service = None
        
        # Window state
        self._is_visible = False
        self._last_position = None
        self._last_size = None
        
        self.logger.info(f"Service-aware window created: {self.window_id}")
    
    def _initialize_services(self):
        """Initialize required services"""
        try:
            # Get services (only if available)
            if SettingsService:
                self._settings_service = self.get_service_safely(SettingsService)
            if ThemeService:
                self._theme_service = self.get_service_safely(ThemeService)
            if WindowService:
                self._window_service = self.get_service_safely(WindowService)
            if ValidationService:
                self._validation_service = self.get_service_safely(ValidationService)
            if NotificationService:
                self._notification_service = self.get_service_safely(NotificationService)
            
            # Subscribe to service events
            if self._theme_service:
                self.subscribe_to_service(ThemeService, 'theme_changed', self._on_theme_changed)
            
            if self._settings_service:
                self.subscribe_to_service(SettingsService, 'settings_changed', self._on_settings_changed)
            
            self.logger.info("Window services initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            raise
    
    def _on_initialize(self):
        """Custom initialization logic"""
        # Apply current theme
        self._apply_current_theme()
        
        # Restore window state if available
        self._restore_window_state()
    
    def createWindow(self, title: str = "Settings", 
                     width: int = 900, height: int = 650,
                     min_width: int = 800, min_height: int = 600):
        """
        Create window with service integration
        
        Args:
            title: Window title
            width: Window width
            height: Window height
            min_width: Minimum window width
            min_height: Minimum window height
        """
        # Call parent createWindow
        super().createWindow(title, width, height, min_width, min_height)
        
        # Initialize services after window creation
        self.initialize()
        
        self.logger.debug(f"Service-aware window created: {title}")
    
    def _apply_current_theme(self):
        """Apply current theme to window"""
        if not self._theme_service:
            return
        
        try:
            theme_info = self._theme_service.get_current_theme()
            self._apply_theme(theme_info)
        except Exception as e:
            self.logger.error(f"Failed to apply theme: {e}")
    
    def _apply_theme(self, theme_info: Dict[str, Any]):
        """
        Apply theme to window components
        Override in subclasses for custom theming
        
        Args:
            theme_info: Theme information from ThemeService
        """
        self.logger.debug(f"Applying theme: {theme_info.get('name', 'unknown')}")
        
        # Update window appearance based on theme
        try:
            from AppKit import NSColor
            
            # Get theme colors
            is_dark = theme_info.get('is_dark', False)
            
            # Update window background
            if self.window():
                if hasattr(NSColor, 'controlBackgroundColor'):
                    bg_color = NSColor.controlBackgroundColor()
                else:
                    bg_color = NSColor.windowBackgroundColor()
                
                if self.sidebar_container:
                    self.sidebar_container.setWantsLayer_(True)
                    self.sidebar_container.layer().setBackgroundColor_(bg_color.CGColor())
            
            # Update content area
            if self.content_container:
                self.content_container.setNeedsDisplay_(True)
            
            # Notify subclasses
            self._on_theme_applied(theme_info)
            
        except Exception as e:
            self.logger.error(f"Error applying theme: {e}")
    
    def _on_theme_applied(self, theme_info: Dict[str, Any]):
        """
        Called after theme is applied
        Override in subclasses for custom theme handling
        
        Args:
            theme_info: Applied theme information
        """
        pass
    
    def _restore_window_state(self):
        """Restore window state from WindowService"""
        if not self._window_service or not self.window():
            return
        
        try:
            window_state = self._window_service.get_window_state(self.window_id)
            if window_state:
                # Restore position and size
                from AppKit import NSMakeRect
                
                frame = NSMakeRect(
                    window_state.x,
                    window_state.y,
                    window_state.width,
                    window_state.height
                )
                
                self.window().setFrame_display_(frame, True)
                
                # Restore window state
                if hasattr(window_state, 'is_visible') and window_state.is_visible:
                    self._is_visible = True
                
                self.logger.debug(f"Restored window state for {self.window_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to restore window state: {e}")
    
    def _save_window_state(self):
        """Save window state to WindowService"""
        if not self._window_service or not self.window():
            return
        
        try:
            # Get current window frame
            frame = self.window().frame()
            
            # Create window state
            from services import WindowState
            window_state = WindowState(
                x=frame.origin.x,
                y=frame.origin.y,
                width=frame.size.width,
                height=frame.size.height,
                is_visible=self._is_visible,
                screen_index=0  # TODO: Detect current screen
            )
            
            # Save state
            self._window_service.save_window_state(self.window_id, window_state)
            
            self.logger.debug(f"Saved window state for {self.window_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to save window state: {e}")
    
    def show_validation_error(self, field: str, message: str):
        """
        Show validation error for a specific field
        
        Args:
            field: Field name
            message: Error message
        """
        if self._notification_service:
            self._notification_service.show_error(
                f"Validation Error: {field}",
                message
            )
        
        # Also log the error
        self.logger.warning(f"Validation error in {field}: {message}")
    
    def validate_field(self, field: str, value: Any) -> bool:
        """
        Validate a field value
        
        Args:
            field: Field name
            value: Value to validate
            
        Returns:
            True if valid
        """
        if not self._validation_service:
            return True
        
        try:
            is_valid, message = self._validation_service.validate_setting(field, value)
            
            if not is_valid:
                self.show_validation_error(field, message)
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Validation error for {field}: {e}")
            return False
    
    # Service event handlers
    def _on_theme_changed(self, theme_info: Dict[str, Any]):
        """Handle theme change events"""
        self.logger.debug("Theme changed, updating window")
        self._apply_theme(theme_info)
    
    def _on_settings_changed(self, settings: Dict[str, Any]):
        """
        Handle settings change events
        Override in subclasses for custom settings handling
        
        Args:
            settings: Changed settings
        """
        self.logger.debug("Settings changed")
    
    # Window event overrides
    def windowWillClose_(self, notification):
        """Handle window close event"""
        self.logger.debug(f"Window {self.window_id} will close")
        
        # Save window state
        self._save_window_state()
        
        # Mark as not visible
        self._is_visible = False
        
        # Call parent implementation
        super().windowWillClose_(notification)
    
    def windowDidBecomeKey_(self, notification):
        """Handle window becoming key"""
        self._is_visible = True
        self.logger.debug(f"Window {self.window_id} became key")
    
    def windowDidResignKey_(self, notification):
        """Handle window resigning key"""
        # Save state when losing focus
        self._save_window_state()
        self.logger.debug(f"Window {self.window_id} resigned key")
    
    def windowDidResize_(self, notification):
        """Handle window resize"""
        # Save state after resize
        self._save_window_state()
        self.logger.debug(f"Window {self.window_id} resized")
    
    def windowDidMove_(self, notification):
        """Handle window move"""
        # Save state after move
        self._save_window_state()
        self.logger.debug(f"Window {self.window_id} moved")
    
    # Convenience methods
    def get_setting(self, key: str, default=None):
        """Get setting value from SettingsService"""
        if self._settings_service:
            return self._settings_service.get(key, default)
        return default
    
    def set_setting(self, key: str, value: Any, validate: bool = True) -> bool:
        """
        Set setting value with optional validation
        
        Args:
            key: Setting key
            value: New value
            validate: Whether to validate
            
        Returns:
            True if successful
        """
        if validate and not self.validate_field(key, value):
            return False
        
        if self._settings_service:
            try:
                self._settings_service.set(key, value)
                return True
            except Exception as e:
                self.logger.error(f"Failed to set {key}: {e}")
                if self._notification_service:
                    self._notification_service.show_error(
                        "Settings Error",
                        f"Failed to save {key}: {e}"
                    )
                return False
        
        return False
    
    def show_error(self, title: str, message: str):
        """Show error notification"""
        if self._notification_service:
            self._notification_service.show_error(title, message)
        self.logger.error(f"{title}: {message}")
    
    def show_success(self, title: str, message: str):
        """Show success notification"""
        if self._notification_service:
            self._notification_service.show_success(title, message)
        self.logger.info(f"{title}: {message}")
    
    def show_info(self, title: str, message: str):
        """Show info notification"""
        if self._notification_service:
            self._notification_service.show_info(title, message)
        self.logger.info(f"{title}: {message}")
    
    def _on_cleanup(self):
        """Custom cleanup logic"""
        # Save final window state
        self._save_window_state()
        
        # Mark as not visible
        self._is_visible = False
        
        self.logger.info(f"Service-aware window cleaned up: {self.window_id}")
    
    # Status and debugging
    def get_window_status(self) -> Dict[str, Any]:
        """
        Get window status information
        
        Returns:
            Status dictionary
        """
        status = {
            'window_id': self.window_id,
            'is_visible': self._is_visible,
            'is_initialized': getattr(self, '_is_initialized', False),
            'has_window': self.window() is not None,
            'services_available': {
                'settings': self._settings_service is not None,
                'theme': self._theme_service is not None,
                'window': self._window_service is not None,
                'validation': self._validation_service is not None,
                'notification': self._notification_service is not None
            }
        }
        
        # Add window frame info if available
        if self.window():
            frame = self.window().frame()
            status['frame'] = {
                'x': frame.origin.x,
                'y': frame.origin.y,
                'width': frame.size.width,
                'height': frame.size.height
            }
        
        return status 