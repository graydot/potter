#!/usr/bin/env python3
"""
Theme-Aware Icon Handler
Handles loading and displaying icons based on system theme
"""

import os
import logging
from typing import Optional
from AppKit import NSImage, NSAppearance, NSApp

logger = logging.getLogger(__name__)


class ThemeAwareIcon:
    """Handles theme-aware icon loading and display"""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize theme-aware icon handler
        
        Args:
            base_path: Base path for icon files (defaults to project assets)
        """
        if base_path is None:
            # Default to project assets directory
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )))
            self.base_path = os.path.join(project_root, 'assets')
        else:
            self.base_path = base_path
    
    def get_current_theme(self) -> str:
        """
        Get the current system theme
        
        Returns:
            'dark' or 'light'
        """
        try:
            # Try to get appearance from the app
            app = NSApp()
            if app and hasattr(app, 'effectiveAppearance'):
                appearance = app.effectiveAppearance()
            else:
                # Fallback to system appearance
                appearance = NSAppearance.currentAppearance()
            
            if appearance:
                appearance_name = appearance.name()
                # Check if it's a dark appearance
                if 'Dark' in appearance_name:
                    return 'dark'
            
            return 'light'
            
        except Exception as e:
            logger.warning(f"Could not determine theme, defaulting to light: {e}")
            return 'light'
    
    def get_icon_path(self, icon_name: str, theme: Optional[str] = None) -> str:
        """
        Get the path to an icon file based on theme
        
        Args:
            icon_name: Base name of the icon (without theme suffix)
            theme: 'dark' or 'light' (auto-detected if None)
            
        Returns:
            Full path to the icon file
        """
        if theme is None:
            theme = self.get_current_theme()
        
        # Try theme-specific icon first
        themed_name = f"{icon_name}_{theme}.png"
        themed_path = os.path.join(self.base_path, themed_name)
        
        if os.path.exists(themed_path):
            return themed_path
        
        # Fallback to generic icon
        generic_path = os.path.join(self.base_path, f"{icon_name}.png")
        if os.path.exists(generic_path):
            logger.debug(f"Theme-specific icon not found, using generic: {generic_path}")
            return generic_path
        
        # If nothing found, return the themed path (will fail when loading)
        logger.warning(f"Icon not found: {icon_name} (theme: {theme})")
        return themed_path
    
    def load_icon(self, icon_name: str, size: Optional[tuple] = None) -> Optional[NSImage]:
        """
        Load an icon as NSImage
        
        Args:
            icon_name: Base name of the icon
            size: Optional (width, height) tuple to resize the icon
            
        Returns:
            NSImage or None if loading fails
        """
        icon_path = self.get_icon_path(icon_name)
        
        if not os.path.exists(icon_path):
            logger.error(f"Icon file not found: {icon_path}")
            return None
        
        try:
            image = NSImage.alloc().initWithContentsOfFile_(icon_path)
            
            if image and size:
                # Resize if size specified
                width, height = size
                image.setSize_((width, height))
            
            return image
            
        except Exception as e:
            logger.error(f"Failed to load icon {icon_path}: {e}")
            return None
    
    def set_window_icon(self, window, icon_name: str = "logo"):
        """
        Set the icon for a window based on current theme
        
        Args:
            window: NSWindow instance
            icon_name: Base name of the icon
        """
        try:
            icon = self.load_icon(icon_name, size=(128, 128))
            if icon and hasattr(window, 'setRepresentedURL_'):
                # This makes the icon appear in the title bar
                window.setRepresentedURL_(None)
                if hasattr(window, 'standardWindowButton_'):
                    # Try to set the document icon
                    doc_button = window.standardWindowButton_(0)  # NSWindowDocumentIconButton
                    if doc_button:
                        doc_button.setImage_(icon)
        except Exception as e:
            logger.debug(f"Could not set window icon: {e}")
    
    def set_dialog_icon(self, alert, icon_name: str = "logo"):
        """
        Set the icon for an NSAlert dialog based on current theme
        
        Args:
            alert: NSAlert instance
            icon_name: Base name of the icon
        """
        try:
            icon = self.load_icon(icon_name, size=(64, 64))
            if icon:
                alert.setIcon_(icon)
                logger.debug(f"Set dialog icon: {icon_name}")
        except Exception as e:
            logger.error(f"Failed to set dialog icon: {e}")
    
    def create_icon_view(self, icon_name: str, frame, size: Optional[tuple] = None):
        """
        Create an NSImageView with a theme-aware icon
        
        Args:
            icon_name: Base name of the icon
            frame: NSRect for the view frame
            size: Optional (width, height) tuple for the icon
            
        Returns:
            NSImageView instance
        """
        from AppKit import NSImageView
        
        image_view = NSImageView.alloc().initWithFrame_(frame)
        icon = self.load_icon(icon_name, size=size)
        
        if icon:
            image_view.setImage_(icon)
            image_view.setImageScaling_(1)  # NSImageScaleProportionallyUpOrDown
        
        return image_view
    
    def update_on_theme_change(self, callback):
        """
        Register a callback to be called when theme changes
        
        Args:
            callback: Function to call when theme changes
        """
        # This would require setting up an observer for appearance changes
        # For now, this is a placeholder for future implementation
        logger.debug("Theme change observer not yet implemented") 