#!/usr/bin/env python3
"""
Notification Manager Module
Handles system notifications and user feedback
"""

import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages system notifications and user feedback"""
    
    def __init__(self, show_notifications: bool = True):
        self.show_notifications = show_notifications
        self.app_name = "Potter"
    
    def set_notifications_enabled(self, enabled: bool):
        """Enable or disable notifications"""
        self.show_notifications = enabled
        logger.info(f"Notifications {'enabled' if enabled else 'disabled'}")
    
    def is_notifications_enabled(self) -> bool:
        """Check if notifications are enabled"""
        return self.show_notifications
    
    def show_notification(self, title: str, message: str, is_error: bool = False):
        """Show notification if enabled"""
        # Always log notifications for debugging
        log_level = logging.ERROR if is_error else logging.INFO
        logger.log(log_level, f"📢 Notification: {title} - {message}")
        
        # Show notification if enabled
        if self.show_notifications:
            self._show_system_notification(title, message, is_error)
    
    def _show_system_notification(self, title: str, message: str, is_error: bool = False):
        """Show native system notification"""
        try:
            # Escape quotes in message and title for shell safety
            safe_title = title.replace('"', '\\"').replace("'", "\\'")
            safe_message = message.replace('"', '\\"').replace("'", "\\'")
            
            # Try macOS notification using osascript
            script = f'display notification "{safe_message}" with title "{safe_title}"'
            result = subprocess.run(['osascript', '-e', script], 
                                  check=False, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.debug("Successfully showed osascript notification")
                return
            else:
                logger.debug(f"osascript notification failed: {result.stderr}")
        
        except Exception as e:
            logger.debug(f"Could not show osascript notification: {e}")
        
        # Fallback to alert dialog for important messages
        if is_error:
            try:
                script = f'display alert "{safe_title}" message "{safe_message}"'
                subprocess.run(['osascript', '-e', script], check=False)
                logger.debug("Showed fallback alert dialog")
            except Exception as e2:
                logger.debug(f"Could not show alert either: {e2}")
    
    def show_success(self, message: str):
        """Show a success notification"""
        self.show_notification("Potter", f"✅ {message}", is_error=False)
    
    def show_error(self, message: str):
        """Show an error notification"""
        self.show_notification("Potter Error", f"❌ {message}", is_error=True)
    
    def show_warning(self, message: str):
        """Show a warning notification"""
        self.show_notification("Potter Warning", f"⚠️  {message}", is_error=False)
    
    def show_info(self, message: str):
        """Show an info notification"""
        self.show_notification("Potter", f"ℹ️  {message}", is_error=False)
    
    def show_processing(self, message: str = "Processing text..."):
        """Show a processing notification"""
        self.show_notification("Potter", f"🔄 {message}", is_error=False)
    
    def show_text_processed(self, mode: str):
        """Show text processing completion notification"""
        message = f"Text {mode}d and copied to clipboard! Press Cmd+V to paste."
        self.show_success(message)
    
    def show_hotkey_detected(self):
        """Show immediate feedback that hotkey was detected"""
        self.show_processing("Hotkey detected! Processing...")
    
    def show_first_launch_welcome(self):
        """Show first launch welcome notification"""
        self.show_info("Welcome to Potter! Please configure your settings.")
    
    def show_permissions_granted(self):
        """Show notification when permissions are granted"""
        self.show_success("Permissions granted! Potter is now fully functional.")
    
    def show_api_key_needed(self):
        """Show notification when API key is needed"""
        self.show_warning("OpenAI API key required. Please check Settings.")


def create_notification_manager(enabled: bool = True) -> NotificationManager:
    """Factory function to create a notification manager"""
    return NotificationManager(show_notifications=enabled) 