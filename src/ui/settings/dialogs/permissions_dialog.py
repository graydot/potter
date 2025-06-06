#!/usr/bin/env python3
"""
Permissions Dialog
Dialog for managing app permissions
"""

import logging
from AppKit import (
    NSAlert, NSAlertFirstButtonReturn,
    NSInformationalAlertStyle, NSWarningAlertStyle,
    NSWorkspace, NSURL
)

from ..widgets.theme_aware_icon import ThemeAwareIcon

logger = logging.getLogger(__name__)


class PermissionsDialog:
    """Handles permission-related dialogs"""
    
    def __init__(self):
        """Initialize permissions dialog"""
        self.theme_icon = ThemeAwareIcon()
        
    def show_accessibility_permission_dialog(self) -> bool:
        """
        Show dialog for accessibility permission
        
        Returns:
            True if user wants to open settings, False otherwise
        """
        logger.debug("Showing accessibility permission dialog")
        
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Accessibility Permission Required")
        alert.setInformativeText_(
            "Potter needs accessibility permission to monitor global hotkeys.\n\n"
            "Please grant permission in:\n"
            "System Settings > Privacy & Security > Accessibility\n\n"
            "The app will continue running and check for permissions periodically."
        )
        alert.setAlertStyle_(NSInformationalAlertStyle)
        
        # Set icon
        self.theme_icon.set_dialog_icon(alert)
        
        # Add buttons
        alert.addButtonWithTitle_("Open System Settings")
        alert.addButtonWithTitle_("Later")
        
        # Show dialog
        response = alert.runModal()
        
        if response == NSAlertFirstButtonReturn:
            logger.info("User chose to open system settings")
            self._open_accessibility_settings()
            return True
        else:
            logger.info("User chose to skip accessibility permission")
            return False
            
    def show_notification_permission_dialog(self) -> bool:
        """
        Show dialog for notification permission
        
        Returns:
            True if user wants to enable, False otherwise
        """
        logger.debug("Showing notification permission dialog")
        
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Enable Notifications?")
        alert.setInformativeText_(
            "Potter can show notifications when text processing is complete.\n\n"
            "This is optional but recommended for a better experience."
        )
        alert.setAlertStyle_(NSInformationalAlertStyle)
        
        # Set icon
        self.theme_icon.set_dialog_icon(alert)
        
        # Add buttons
        alert.addButtonWithTitle_("Enable Notifications")
        alert.addButtonWithTitle_("Not Now")
        
        # Show dialog
        response = alert.runModal()
        
        return response == NSAlertFirstButtonReturn
        
    def show_permission_error(self, permission_type: str, error_message: str):
        """
        Show error dialog for permission issues
        
        Args:
            permission_type: Type of permission (e.g., "Accessibility", "Notifications")
            error_message: Error message to display
        """
        logger.error(f"Permission error for {permission_type}: {error_message}")
        
        alert = NSAlert.alloc().init()
        alert.setMessageText_(f"{permission_type} Permission Error")
        alert.setInformativeText_(error_message)
        alert.setAlertStyle_(NSWarningAlertStyle)
        
        # Set icon
        self.theme_icon.set_dialog_icon(alert)
        
        # Add button
        alert.addButtonWithTitle_("OK")
        
        # Show dialog
        alert.runModal()
        
    def show_first_launch_permissions(self) -> dict:
        """
        Show first launch permissions overview
        
        Returns:
            Dictionary with user choices for each permission
        """
        logger.debug("Showing first launch permissions dialog")
        
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Welcome to Potter!")
        alert.setInformativeText_(
            "Potter needs a few permissions to work properly:\n\n"
            "• Accessibility - Required for global hotkey monitoring\n"
            "• Notifications - Optional for completion alerts\n\n"
            "You can change these settings anytime in the app preferences."
        )
        alert.setAlertStyle_(NSInformationalAlertStyle)
        
        # Set icon
        self.theme_icon.set_dialog_icon(alert)
        
        # Add buttons
        alert.addButtonWithTitle_("Set Up Permissions")
        alert.addButtonWithTitle_("Skip for Now")
        
        # Show dialog
        response = alert.runModal()
        
        return {
            "setup_permissions": response == NSAlertFirstButtonReturn
        }
        
    def _open_accessibility_settings(self):
        """Open system accessibility settings"""
        try:
            # URL for accessibility settings
            url = NSURL.URLWithString_(
                "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
            )
            NSWorkspace.sharedWorkspace().openURL_(url)
            logger.info("Opened accessibility settings")
        except Exception as e:
            logger.error(f"Error opening accessibility settings: {e}")
            # Fallback to general privacy settings
            try:
                url = NSURL.URLWithString_(
                    "x-apple.systempreferences:com.apple.preference.security?Privacy"
                )
                NSWorkspace.sharedWorkspace().openURL_(url)
            except Exception as e2:
                logger.error(f"Error opening privacy settings: {e2}") 