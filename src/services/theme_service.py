#!/usr/bin/env python3
"""
Theme Service
Manages application theme and appearance settings
"""

import logging
import os
from typing import Dict, Any, Optional, Callable, List
from threading import Lock

from .base_service import BaseService
from core.exceptions import ServiceError

# Import AppKit for theme detection
try:
    from AppKit import NSApp, NSAppearance, NSNotificationCenter
    APPKIT_AVAILABLE = True
except ImportError:
    APPKIT_AVAILABLE = False
    logger.warning("AppKit not available - theme detection disabled")

logger = logging.getLogger(__name__)


class ThemeService(BaseService):
    """
    Service for managing application theme and appearance
    
    Features:
    - System theme detection (dark/light mode)
    - Custom theme management
    - Theme change notifications
    - Icon and asset management for themes
    - Automatic theme switching
    """
    
    def __init__(self, settings_manager=None):
        super().__init__("theme", {})
        
        self.settings_manager = settings_manager
        self._current_theme = "auto"  # auto, light, dark, custom
        self._system_theme = "light"
        self._theme_observers: List[Callable[[str], None]] = []
        self._observer_lock = Lock()
        
        # Theme assets cache
        self._icon_cache: Dict[str, Any] = {}
        
    def _start_service(self) -> None:
        """Start the theme service"""
        # Detect current system theme
        self._detect_system_theme()
        
        # Load theme settings
        if self.settings_manager:
            self._load_theme_settings()
        
        # Register for system theme changes
        if APPKIT_AVAILABLE:
            self._register_for_theme_changes()
        
        self.logger.info(f"🎨 Theme service started (current: {self._current_theme})")
    
    def _stop_service(self) -> None:
        """Stop the theme service"""
        # Unregister from system notifications
        if APPKIT_AVAILABLE:
            try:
                NSNotificationCenter.defaultCenter().removeObserver_(self)
            except Exception:
                pass
        
        # Clear caches
        self._icon_cache.clear()
        
        with self._observer_lock:
            self._theme_observers.clear()
        
        self.logger.info("🎨 Theme service stopped")
    
    def _get_service_status(self) -> Dict[str, Any]:
        """Get theme service specific status"""
        return {
            'current_theme': self._current_theme,
            'system_theme': self._system_theme,
            'effective_theme': self.get_effective_theme(),
            'observers_count': len(self._theme_observers),
            'icon_cache_size': len(self._icon_cache),
            'appkit_available': APPKIT_AVAILABLE
        }
    
    def _handle_config_update(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        """Handle configuration updates"""
        if 'theme' in new_config:
            theme = new_config['theme']
            if theme != self._current_theme:
                self.set_theme(theme)
    
    def get_current_theme(self) -> str:
        """Get the current theme setting"""
        return self._current_theme
    
    def get_system_theme(self) -> str:
        """Get the detected system theme"""
        return self._system_theme
    
    def get_effective_theme(self) -> str:
        """
        Get the effective theme (resolved from auto/system)
        
        Returns:
            'light' or 'dark'
        """
        if self._current_theme == "auto":
            return self._system_theme
        elif self._current_theme in ["light", "dark"]:
            return self._current_theme
        else:
            # Custom theme - default to light
            return "light"
    
    def set_theme(self, theme: str) -> None:
        """
        Set the application theme
        
        Args:
            theme: Theme name ('auto', 'light', 'dark', or custom theme name)
        """
        if theme == self._current_theme:
            return
        
        old_theme = self._current_theme
        old_effective = self.get_effective_theme()
        
        self._current_theme = theme
        
        # Save to settings if available
        if self.settings_manager:
            try:
                self.settings_manager.set("theme", theme)
            except Exception as e:
                self.logger.error(f"Failed to save theme setting: {e}")
        
        # Check if effective theme changed
        new_effective = self.get_effective_theme()
        if old_effective != new_effective:
            self._notify_theme_change(new_effective)
        
        self.logger.info(f"🎨 Theme changed from {old_theme} to {theme} (effective: {new_effective})")
    
    def add_theme_observer(self, callback: Callable[[str], None]) -> None:
        """
        Add a theme change observer
        
        Args:
            callback: Function to call when theme changes (receives effective theme)
        """
        with self._observer_lock:
            if callback not in self._theme_observers:
                self._theme_observers.append(callback)
                self.logger.debug(f"Added theme observer: {callback}")
    
    def remove_theme_observer(self, callback: Callable[[str], None]) -> None:
        """
        Remove a theme change observer
        
        Args:
            callback: Function to remove from observers
        """
        with self._observer_lock:
            if callback in self._theme_observers:
                self._theme_observers.remove(callback)
                self.logger.debug(f"Removed theme observer: {callback}")
    
    def get_themed_icon(self, icon_name: str, size: Optional[tuple] = None) -> Optional[Any]:
        """
        Get a themed icon (light/dark version)
        
        Args:
            icon_name: Base icon name (without light/dark suffix)
            size: Optional size tuple (width, height)
            
        Returns:
            Icon object or None if not found
        """
        effective_theme = self.get_effective_theme()
        cache_key = f"{icon_name}_{effective_theme}_{size}"
        
        # Check cache first
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]
        
        # Try to load themed icon
        icon = self._load_themed_icon(icon_name, effective_theme, size)
        
        # Cache the result
        self._icon_cache[cache_key] = icon
        
        return icon
    
    def clear_icon_cache(self) -> None:
        """Clear the icon cache"""
        self._icon_cache.clear()
        self.logger.info("🧹 Cleared icon cache")
    
    def get_theme_colors(self) -> Dict[str, str]:
        """
        Get theme-appropriate colors
        
        Returns:
            Dict mapping color names to hex values
        """
        effective_theme = self.get_effective_theme()
        
        if effective_theme == "dark":
            return {
                'background': '#1e1e1e',
                'surface': '#2d2d2d',
                'primary': '#007acc',
                'text': '#ffffff',
                'text_secondary': '#cccccc',
                'border': '#454545',
                'accent': '#ff6b35'
            }
        else:  # light theme
            return {
                'background': '#ffffff',
                'surface': '#f5f5f5',
                'primary': '#007acc',
                'text': '#000000',
                'text_secondary': '#666666',
                'border': '#d0d0d0',
                'accent': '#ff6b35'
            }
    
    def _detect_system_theme(self) -> None:
        """Detect the current system theme"""
        if not APPKIT_AVAILABLE:
            self._system_theme = "light"
            return
        
        try:
            # Get system appearance
            app = NSApp
            if app and hasattr(app, 'effectiveAppearance'):
                appearance = app.effectiveAppearance()
                if appearance:
                    appearance_name = appearance.name()
                    if 'Dark' in str(appearance_name):
                        self._system_theme = "dark"
                    else:
                        self._system_theme = "light"
                else:
                    self._system_theme = "light"
            else:
                self._system_theme = "light"
                
        except Exception as e:
            self.logger.warning(f"Failed to detect system theme: {e}")
            self._system_theme = "light"
        
        self.logger.debug(f"Detected system theme: {self._system_theme}")
    
    def _load_theme_settings(self) -> None:
        """Load theme settings from configuration"""
        if not self.settings_manager:
            return
        
        try:
            saved_theme = self.settings_manager.get("theme", "auto")
            self._current_theme = saved_theme
            self.logger.info(f"Loaded theme setting: {saved_theme}")
            
        except Exception as e:
            self.logger.error(f"Failed to load theme settings: {e}")
            self._current_theme = "auto"
    
    def _register_for_theme_changes(self) -> None:
        """Register for system theme change notifications"""
        if not APPKIT_AVAILABLE:
            return
        
        try:
            # Register for appearance changes
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                self, 
                'appearanceDidChange:', 
                'NSSystemColorsDidChangeNotification',
                None
            )
            self.logger.debug("Registered for system theme change notifications")
            
        except Exception as e:
            self.logger.warning(f"Failed to register for theme changes: {e}")
    
    def appearanceDidChange_(self, notification):
        """Handle system appearance change notification"""
        old_system_theme = self._system_theme
        self._detect_system_theme()
        
        if old_system_theme != self._system_theme:
            self.logger.info(f"System theme changed from {old_system_theme} to {self._system_theme}")
            
            # If using auto theme, notify observers
            if self._current_theme == "auto":
                self._notify_theme_change(self._system_theme)
    
    def _notify_theme_change(self, effective_theme: str) -> None:
        """Notify all observers of theme change"""
        with self._observer_lock:
            observers = self._theme_observers.copy()
        
        for observer in observers:
            try:
                observer(effective_theme)
            except Exception as e:
                self.logger.error(f"Error notifying theme observer {observer}: {e}")
        
        # Clear icon cache when theme changes
        self.clear_icon_cache()
    
    def _load_themed_icon(self, icon_name: str, theme: str, size: Optional[tuple]) -> Optional[Any]:
        """
        Load a themed icon from file system
        
        Args:
            icon_name: Base icon name
            theme: Theme name (light/dark)
            size: Optional size
            
        Returns:
            Icon object or None
        """
        if not APPKIT_AVAILABLE:
            return None
        
        try:
            from AppKit import NSImage, NSMakeSize
            
            # Try themed version first (icon_name_dark.png, icon_name_light.png)
            themed_name = f"{icon_name}_{theme}"
            icon_path = self._find_icon_file(themed_name)
            
            # Fallback to base name
            if not icon_path:
                icon_path = self._find_icon_file(icon_name)
            
            if not icon_path:
                return None
            
            # Load the icon
            icon = NSImage.alloc().initWithContentsOfFile_(icon_path)
            
            # Resize if size specified
            if icon and size:
                icon.setSize_(NSMakeSize(size[0], size[1]))
            
            return icon
            
        except Exception as e:
            self.logger.error(f"Failed to load themed icon {icon_name}: {e}")
            return None
    
    def _find_icon_file(self, icon_name: str) -> Optional[str]:
        """Find icon file in common locations"""
        # Common icon locations
        icon_dirs = [
            "icons",
            "assets/icons", 
            "resources/icons",
            "images",
            "assets/images"
        ]
        
        # Common icon extensions
        extensions = [".png", ".jpg", ".jpeg", ".tiff", ".icns"]
        
        for icon_dir in icon_dirs:
            for ext in extensions:
                icon_path = os.path.join(icon_dir, f"{icon_name}{ext}")
                if os.path.exists(icon_path):
                    return icon_path
        
        return None 