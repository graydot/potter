#!/usr/bin/env python3
"""
Common Dialogs
Common dialog utilities for the application
"""

import logging
from typing import Optional
from AppKit import (
    NSAlert, NSAlertFirstButtonReturn,
    NSInformationalAlertStyle, NSWarningAlertStyle, NSCriticalAlertStyle
)

from ..widgets.theme_aware_icon import ThemeAwareIcon

logger = logging.getLogger(__name__)


class CommonDialogs:
    """Common dialog utilities"""
    
    def __init__(self):
        """Initialize common dialogs"""
        self.theme_icon = ThemeAwareIcon()
        
    def show_error(self, title: str, message: str, details: Optional[str] = None):
        """
        Show error dialog
        
        Args:
            title: Error title
            message: Error message
            details: Optional detailed error information
        """
        logger.error(f"Showing error dialog: {title} - {message}")
        
        alert = NSAlert.alloc().init()
        alert.setMessageText_(title)
        
        if details:
            alert.setInformativeText_(f"{message}\n\nDetails:\n{details}")
        else:
            alert.setInformativeText_(message)
            
        alert.setAlertStyle_(NSCriticalAlertStyle)
        
        # Set icon
        self.theme_icon.set_dialog_icon(alert)
        
        # Add button
        alert.addButtonWithTitle_("OK")
        
        # Show dialog
        alert.runModal()
        
    def show_warning(self, title: str, message: str) -> bool:
        """
        Show warning dialog with OK/Cancel
        
        Args:
            title: Warning title
            message: Warning message
            
        Returns:
            True if user clicked OK, False if cancelled
        """
        logger.warning(f"Showing warning dialog: {title}")
        
        alert = NSAlert.alloc().init()
        alert.setMessageText_(title)
        alert.setInformativeText_(message)
        alert.setAlertStyle_(NSWarningAlertStyle)
        
        # Set icon
        self.theme_icon.set_dialog_icon(alert)
        
        # Add buttons
        alert.addButtonWithTitle_("OK")
        alert.addButtonWithTitle_("Cancel")
        
        # Show dialog
        response = alert.runModal()
        
        return response == NSAlertFirstButtonReturn
        
    def show_info(self, title: str, message: str):
        """
        Show information dialog
        
        Args:
            title: Info title
            message: Info message
        """
        logger.info(f"Showing info dialog: {title}")
        
        alert = NSAlert.alloc().init()
        alert.setMessageText_(title)
        alert.setInformativeText_(message)
        alert.setAlertStyle_(NSInformationalAlertStyle)
        
        # Set icon
        self.theme_icon.set_dialog_icon(alert)
        
        # Add button
        alert.addButtonWithTitle_("OK")
        
        # Show dialog
        alert.runModal()
        
    def show_confirmation(self, title: str, message: str,
                          ok_button: str = "OK",
                          cancel_button: str = "Cancel") -> bool:
        """
        Show confirmation dialog
        
        Args:
            title: Confirmation title
            message: Confirmation message
            ok_button: Text for OK button
            cancel_button: Text for Cancel button
            
        Returns:
            True if user confirmed, False if cancelled
        """
        logger.debug(f"Showing confirmation dialog: {title}")
        
        alert = NSAlert.alloc().init()
        alert.setMessageText_(title)
        alert.setInformativeText_(message)
        alert.setAlertStyle_(NSInformationalAlertStyle)
        
        # Set icon
        self.theme_icon.set_dialog_icon(alert)
        
        # Add buttons
        alert.addButtonWithTitle_(ok_button)
        alert.addButtonWithTitle_(cancel_button)
        
        # Show dialog
        response = alert.runModal()
        
        return response == NSAlertFirstButtonReturn
        
    def show_api_key_missing(self, provider: str):
        """
        Show dialog for missing API key
        
        Args:
            provider: Provider name (e.g., "OpenAI", "Anthropic")
        """
        self.show_error(
            f"{provider} API Key Missing",
            f"Please configure your {provider} API key in Settings > Advanced.",
            "The API key is required to use AI-powered text processing."
        )
        
    def show_processing_error(self, error_message: str):
        """
        Show dialog for text processing error
        
        Args:
            error_message: Error message from processing
        """
        self.show_error(
            "Text Processing Error",
            "Failed to process the text.",
            error_message
        )
        
    def show_clipboard_empty(self):
        """Show dialog for empty clipboard"""
        self.show_info(
            "Clipboard Empty",
            "No text found in clipboard.\n\n"
            "Copy some text first, then press the hotkey."
        )
        
    def show_first_launch_welcome(self) -> bool:
        """
        Show first launch welcome dialog
        
        Returns:
            True if user wants to configure settings
        """
        return self.show_confirmation(
            "Welcome to Potter!",
            "Potter is a powerful text transformation tool.\n\n"
            "Would you like to configure your settings now?",
            ok_button="Configure Settings",
            cancel_button="Use Defaults"
        )
        
    def show_update_available(self, current_version: str, new_version: str) -> bool:
        """
        Show update available dialog
        
        Args:
            current_version: Current app version
            new_version: Available new version
            
        Returns:
            True if user wants to update
        """
        return self.show_confirmation(
            "Update Available",
            f"A new version of Potter is available!\n\n"
            f"Current version: {current_version}\n"
            f"New version: {new_version}\n\n"
            f"Would you like to download the update?",
            ok_button="Download Update",
            cancel_button="Later"
        ) 