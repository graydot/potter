#!/usr/bin/env python3
"""
Notification Service
Manages user notifications and alerts
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass
from threading import Lock
import time

from .base_service import BaseService
from core.exceptions import ServiceError

# Import notification framework
try:
    from UserNotifications import UNUserNotificationCenter, UNMutableNotificationContent, UNNotificationRequest
    from Foundation import NSString
    USERNOTIFICATIONS_AVAILABLE = True
except ImportError:
    USERNOTIFICATIONS_AVAILABLE = False

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Notification:
    """Notification data structure"""
    id: str
    title: str
    message: str
    type: NotificationType
    timestamp: float
    delivered: bool = False
    clicked: bool = False


class NotificationService(BaseService):
    """
    Service for managing user notifications
    
    Features:
    - System notifications (macOS Notification Center)
    - In-app notifications
    - Notification history and tracking
    - Permission management
    - Custom notification handlers
    """
    
    def __init__(self, settings_manager=None):
        super().__init__("notification", {})
        
        self.settings_manager = settings_manager
        self._notifications_enabled = True
        self._notification_history: List[Notification] = []
        self._custom_handlers: Dict[NotificationType, List[Callable]] = {
            NotificationType.INFO: [],
            NotificationType.SUCCESS: [],
            NotificationType.WARNING: [],
            NotificationType.ERROR: []
        }
        self._handlers_lock = Lock()
        self._history_lock = Lock()
        
        # Permission status
        self._permission_granted = False
        
    def _start_service(self) -> None:
        """Start the notification service"""
        # Load settings
        if self.settings_manager:
            self._load_notification_settings()
        
        # Check notification permissions
        if USERNOTIFICATIONS_AVAILABLE:
            self._check_notification_permission()
        
        self.logger.info(f"📢 Notification service started (enabled: {self._notifications_enabled})")
    
    def _stop_service(self) -> None:
        """Stop the notification service"""
        # Clear handlers
        with self._handlers_lock:
            for handlers in self._custom_handlers.values():
                handlers.clear()
        
        self.logger.info("📢 Notification service stopped")
    
    def _get_service_status(self) -> Dict[str, Any]:
        """Get notification service specific status"""
        with self._history_lock:
            total_notifications = len(self._notification_history)
            delivered_count = sum(1 for n in self._notification_history if n.delivered)
            clicked_count = sum(1 for n in self._notification_history if n.clicked)
        
        return {
            'enabled': self._notifications_enabled,
            'permission_granted': self._permission_granted,
            'usernotifications_available': USERNOTIFICATIONS_AVAILABLE,
            'total_notifications': total_notifications,
            'delivered_notifications': delivered_count,
            'clicked_notifications': clicked_count,
            'custom_handlers': {
                ntype.value: len(handlers) 
                for ntype, handlers in self._custom_handlers.items()
            }
        }
    
    def _handle_config_update(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        """Handle configuration updates"""
        if 'notifications_enabled' in new_config:
            self._notifications_enabled = new_config['notifications_enabled']
    
    def show_notification(self, 
                         title: str,
                         message: str,
                         notification_type: NotificationType = NotificationType.INFO,
                         use_system: bool = True) -> str:
        """
        Show a notification
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            use_system: Whether to use system notifications
            
        Returns:
            Notification ID
        """
        if not self._notifications_enabled:
            self.logger.debug(f"Notifications disabled, skipping: {title}")
            return ""
        
        # Generate notification ID
        notification_id = f"potter_{int(time.time() * 1000)}"
        
        # Create notification object
        notification = Notification(
            id=notification_id,
            title=title,
            message=message,
            type=notification_type,
            timestamp=time.time()
        )
        
        # Add to history
        with self._history_lock:
            self._notification_history.append(notification)
            # Keep only last 100 notifications
            if len(self._notification_history) > 100:
                self._notification_history = self._notification_history[-100:]
        
        # Show system notification if available and requested
        if use_system and USERNOTIFICATIONS_AVAILABLE and self._permission_granted:
            self._show_system_notification(notification)
        
        # Call custom handlers
        self._call_custom_handlers(notification)
        
        self.logger.info(f"📢 Showed {notification_type.value} notification: {title}")
        return notification_id
    
    def show_success(self, title: str, message: str, use_system: bool = True) -> str:
        """Show a success notification"""
        return self.show_notification(title, message, NotificationType.SUCCESS, use_system)
    
    def show_warning(self, title: str, message: str, use_system: bool = True) -> str:
        """Show a warning notification"""
        return self.show_notification(title, message, NotificationType.WARNING, use_system)
    
    def show_error(self, title: str, message: str, use_system: bool = True) -> str:
        """Show an error notification"""
        return self.show_notification(title, message, NotificationType.ERROR, use_system)
    
    def show_info(self, title: str, message: str, use_system: bool = True) -> str:
        """Show an info notification"""
        return self.show_notification(title, message, NotificationType.INFO, use_system)
    
    def add_custom_handler(self, notification_type: NotificationType, handler: Callable[[Notification], None]) -> None:
        """
        Add a custom notification handler
        
        Args:
            notification_type: Type of notifications to handle
            handler: Function to call when notification is shown
        """
        with self._handlers_lock:
            if handler not in self._custom_handlers[notification_type]:
                self._custom_handlers[notification_type].append(handler)
                self.logger.debug(f"Added custom handler for {notification_type.value} notifications")
    
    def remove_custom_handler(self, notification_type: NotificationType, handler: Callable[[Notification], None]) -> None:
        """
        Remove a custom notification handler
        
        Args:
            notification_type: Type of notifications
            handler: Handler function to remove
        """
        with self._handlers_lock:
            if handler in self._custom_handlers[notification_type]:
                self._custom_handlers[notification_type].remove(handler)
                self.logger.debug(f"Removed custom handler for {notification_type.value} notifications")
    
    def get_notification_history(self, limit: Optional[int] = None) -> List[Notification]:
        """
        Get notification history
        
        Args:
            limit: Maximum number of notifications to return
            
        Returns:
            List of notifications (most recent first)
        """
        with self._history_lock:
            history = list(reversed(self._notification_history))
            if limit:
                history = history[:limit]
            return history
    
    def clear_notification_history(self) -> None:
        """Clear the notification history"""
        with self._history_lock:
            self._notification_history.clear()
        self.logger.info("🧹 Cleared notification history")
    
    def mark_notification_clicked(self, notification_id: str) -> None:
        """Mark a notification as clicked"""
        with self._history_lock:
            for notification in self._notification_history:
                if notification.id == notification_id:
                    notification.clicked = True
                    break
    
    def is_notifications_enabled(self) -> bool:
        """Check if notifications are enabled"""
        return self._notifications_enabled
    
    def set_notifications_enabled(self, enabled: bool) -> None:
        """Enable or disable notifications"""
        if enabled != self._notifications_enabled:
            self._notifications_enabled = enabled
            
            # Save to settings
            if self.settings_manager:
                try:
                    self.settings_manager.set("notifications_enabled", enabled)
                except Exception as e:
                    self.logger.error(f"Failed to save notification setting: {e}")
            
            self.logger.info(f"📢 Notifications {'enabled' if enabled else 'disabled'}")
    
    def request_permission(self) -> bool:
        """
        Request notification permission from the user
        
        Returns:
            True if permission granted
        """
        if not USERNOTIFICATIONS_AVAILABLE:
            self.logger.warning("UserNotifications framework not available")
            return False
        
        try:
            center = UNUserNotificationCenter.currentNotificationCenter()
            
            # Request authorization (this is async, but we'll check status after)
            from UserNotifications import UNAuthorizationOptionAlert, UNAuthorizationOptionSound, UNAuthorizationOptionBadge
            
            options = UNAuthorizationOptionAlert | UNAuthorizationOptionSound | UNAuthorizationOptionBadge
            
            def completion_handler(granted, error):
                if granted:
                    self._permission_granted = True
                    self.logger.info("✅ Notification permission granted")
                else:
                    self._permission_granted = False
                    if error:
                        self.logger.warning(f"❌ Notification permission denied: {error}")
                    else:
                        self.logger.warning("❌ Notification permission denied")
            
            center.requestAuthorizationWithOptions_completionHandler_(options, completion_handler)
            
            # Check current status
            self._check_notification_permission()
            return self._permission_granted
            
        except Exception as e:
            self.logger.error(f"Failed to request notification permission: {e}")
            return False
    
    def _load_notification_settings(self) -> None:
        """Load notification settings from configuration"""
        if not self.settings_manager:
            return
        
        try:
            self._notifications_enabled = self.settings_manager.get("notifications_enabled", True)
            self.logger.info(f"Loaded notification settings: enabled={self._notifications_enabled}")
            
        except Exception as e:
            self.logger.error(f"Failed to load notification settings: {e}")
            self._notifications_enabled = True
    
    def _check_notification_permission(self) -> None:
        """Check current notification permission status"""
        if not USERNOTIFICATIONS_AVAILABLE:
            return
        
        try:
            center = UNUserNotificationCenter.currentNotificationCenter()
            
            def completion_handler(settings):
                from UserNotifications import UNAuthorizationStatusAuthorized, UNAuthorizationStatusProvisional
                
                if settings.authorizationStatus() in [UNAuthorizationStatusAuthorized, UNAuthorizationStatusProvisional]:
                    self._permission_granted = True
                    self.logger.debug("Notification permission is granted")
                else:
                    self._permission_granted = False
                    self.logger.debug("Notification permission not granted")
            
            center.getNotificationSettingsWithCompletionHandler_(completion_handler)
            
        except Exception as e:
            self.logger.error(f"Failed to check notification permission: {e}")
            self._permission_granted = False
    
    def _show_system_notification(self, notification: Notification) -> None:
        """Show a system notification using UserNotifications framework"""
        try:
            center = UNUserNotificationCenter.currentNotificationCenter()
            
            # Create notification content
            content = UNMutableNotificationContent.alloc().init()
            content.setTitle_(NSString.stringWithString_(notification.title))
            content.setBody_(NSString.stringWithString_(notification.message))
            
            # Set sound based on notification type
            if notification.type == NotificationType.ERROR:
                from UserNotifications import UNNotificationSound
                content.setSound_(UNNotificationSound.criticalSoundWithAudioVolumeLevel_(1.0))
            else:
                from UserNotifications import UNNotificationSound
                content.setSound_(UNNotificationSound.defaultSound())
            
            # Create request
            request = UNNotificationRequest.requestWithIdentifier_content_trigger_(
                NSString.stringWithString_(notification.id),
                content,
                None  # No trigger = immediate delivery
            )
            
            # Add to notification center
            def completion_handler(error):
                if error:
                    self.logger.error(f"Failed to deliver system notification: {error}")
                else:
                    notification.delivered = True
                    self.logger.debug(f"System notification delivered: {notification.id}")
            
            center.addNotificationRequest_withCompletionHandler_(request, completion_handler)
            
        except Exception as e:
            self.logger.error(f"Failed to show system notification: {e}")
    
    def _call_custom_handlers(self, notification: Notification) -> None:
        """Call custom handlers for a notification"""
        with self._handlers_lock:
            handlers = self._custom_handlers[notification.type].copy()
        
        for handler in handlers:
            try:
                handler(notification)
            except Exception as e:
                self.logger.error(f"Error in custom notification handler: {e}") 