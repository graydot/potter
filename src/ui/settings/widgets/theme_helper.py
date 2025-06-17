#!/usr/bin/env python3
"""
Theme Helper
Provides theme detection and themed dialog icon functionality
"""

import os
import sys
import subprocess
import logging
from AppKit import NSImage, NSMakeSize, NSApplication

logger = logging.getLogger(__name__)


class ThemeHelper:
    """Helper class for theme detection and themed UI elements"""
    
    @staticmethod
    def get_current_appearance() -> str:
        """
        Get current macOS appearance (light/dark)
        
        Returns:
            str: 'dark' for dark mode, 'light' for light mode
        """
        try:
            # Method 1: Try NSApplication effective appearance
            app = NSApplication.sharedApplication()
            if hasattr(app, 'effectiveAppearance'):
                app_appearance = app.effectiveAppearance()
                if app_appearance:
                    appearance_name = str(app_appearance.name())
                    if "Dark" in appearance_name:
                        return 'dark'
                    else:
                        return 'light'
            
            # Method 2: Check system defaults
            result = subprocess.run(
                ['defaults', 'read', '-g', 'AppleInterfaceStyle'], 
                capture_output=True, 
                text=True,
                timeout=2  # Add timeout for safety
            )
            if result.returncode == 0:
                interface_style = result.stdout.strip()
                return 'dark' if interface_style == "Dark" else 'light'
            
        except Exception as e:
            logger.debug(f"Error detecting appearance: {e}")
        
        # Default to light mode if detection fails
        return 'light'
    
    @staticmethod
    def get_themed_icon_path(appearance: str = None) -> str:
        """
        Get path to themed icon based on current appearance
        
        Args:
            appearance: Optional appearance override ('light' or 'dark')
            
        Returns:
            str: Path to appropriate icon file
        """
        if appearance is None:
            appearance = ThemeHelper.get_current_appearance()
        
        # Use opposite icon for contrast
        # Dark theme -> light icon, Light theme -> dark icon
        icon_filename = 'light.png' if appearance == 'dark' else 'dark.png'
        
        # Build path based on runtime environment
        if getattr(sys, 'frozen', False):
            # Running as app bundle
            app_bundle_path = os.path.dirname(sys.executable)
            icon_path = os.path.join(app_bundle_path, '..', 'Resources', 'assets', icon_filename)
        else:
            # Running in development
            # Navigate from src/ui/settings/widgets/ to project root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
            icon_path = os.path.join(project_root, 'assets', icon_filename)
        
        return icon_path
    
    @staticmethod
    def set_dialog_icon(alert_object, appearance: str = None):
        """
        Set themed icon on NSAlert dialog
        
        Args:
            alert_object: NSAlert object to set icon on
            appearance: Optional appearance override
        """
        try:
            icon_path = ThemeHelper.get_themed_icon_path(appearance)
            
            if os.path.exists(icon_path):
                # Load and configure icon
                logo_image = NSImage.alloc().initWithContentsOfFile_(icon_path)
                if logo_image:
                    # Resize to appropriate dialog icon size
                    logo_image.setSize_(NSMakeSize(64, 64))
                    
                    # Set the icon on the alert
                    if hasattr(alert_object, 'setIcon_'):
                        alert_object.setIcon_(logo_image)
                        logger.debug(f"Dialog icon set using {os.path.basename(icon_path)}")
                    else:
                        logger.warning("Alert object does not have setIcon_ method")
                else:
                    logger.warning(f"Could not load icon image from {icon_path}")
            else:
                logger.warning(f"Icon file not found at {icon_path}")
                
        except Exception as e:
            logger.error(f"Error setting dialog icon: {e}") 