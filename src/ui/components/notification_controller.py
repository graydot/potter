#!/usr/bin/env python3
"""
Notification Controller
Service-integrated notification management
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass

from .service_aware_component import ServiceAwareComponent
from services import NotificationService, SettingsService, PermissionService

logger = logging.getLogger(__name__)


class NotificationLevel(Enum):
    """Notification importance levels"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class NotificationRequest:
    """Represents a notification request"""
    title: str
    message: str
    level: NotificationLevel = NotificationLevel.INFO
    action_url: Optional[str] = None
    show_in_ui: bool = True
    persist: bool = False


class NotificationController(ServiceAwareComponent):
    """
    Service-integrated notification controller
    
    Features:
    - Uses NotificationService for actual delivery
    - Respects user notification preferences from SettingsService
    - Checks permissions via PermissionService
    - Provides backward compatibility with old notification API
    - Handles notification templates and formatting
    """
    
    def __init__(self):
        super().__init__(component_name="NotificationController")
        
        # Service references
        self._notification_service = None
        self._settings_service = None
        self._permission_service = None
        
        # State
        self._notifications_enabled = True
        self._notification_history: List[NotificationRequest] = []
        self._max_history = 50
        
        # Template messages
        self._templates = {
            'processing_started': NotificationRequest(
                "Processing Started",
                "Text processing has begun...",
                NotificationLevel.INFO
            ),
            'processing_complete': NotificationRequest(
                "Processing Complete",
                "Text processing finished successfully",
                NotificationLevel.SUCCESS
            ),
            'processing_error': NotificationRequest(
                "Processing Error",
                "An error occurred during text processing",
                NotificationLevel.ERROR
            ),
            'hotkey_registered': NotificationRequest(
                "Hotkey Updated",
                "Global hotkey has been registered",
                NotificationLevel.INFO
            ),
            'permissions_required': NotificationRequest(
                "Permissions Required",
                "Please grant required permissions in System Preferences",
                NotificationLevel.WARNING,
                action_url="x-apple.systempreferences:com.apple.preference.security"
            )
        }
    
    def _initialize_services(self):
        """Initialize required services"""
        try:
            # Get services
            self._notification_service = self.get_service_safely(NotificationService)
            self._settings_service = self.get_service_safely(SettingsService)
            self._permission_service = self.get_service_safely(PermissionService)
            
            # Subscribe to settings changes
            if self._settings_service:
                self.subscribe_to_service(SettingsService, 'settings_changed', self._on_settings_changed)
            
            self.logger.info("Notification services initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            raise
    
    def _on_initialize(self):
        """Custom initialization logic"""
        # Load notification preferences from settings
        self._load_notification_preferences()
        
        # Check notification permissions
        self._check_notification_permissions()
    
    def _load_notification_preferences(self):
        """Load notification preferences from settings"""
        if self._settings_service:
            try:
                self._notifications_enabled = self._settings_service.get('notifications', True)
                self.logger.debug(f"Notifications enabled: {self._notifications_enabled}")
            except Exception as e:
                self.logger.error(f"Failed to load notification preferences: {e}")
    
    def _check_notification_permissions(self):
        """Check if notification permissions are granted"""
        if self._permission_service:
            try:
                from services.permission_service import PermissionType
                # Check if method exists before calling
                if hasattr(self._permission_service, 'get_all_permissions'):
                    permissions = self._permission_service.get_all_permissions()
                    notifications_granted = permissions.get(PermissionType.NOTIFICATIONS)
                    
                    if notifications_granted and notifications_granted.value != "granted":
                        self.logger.warning("Notification permissions not granted")
                        # Could show a permission request notification
                else:
                    self.logger.debug("Permission service doesn't support get_all_permissions yet")
                    
            except Exception as e:
                self.logger.error(f"Failed to check notification permissions: {e}")
    
    def show_notification(self, request: NotificationRequest) -> bool:
        """
        Show a notification
        
        Args:
            request: NotificationRequest object
            
        Returns:
            True if notification was shown successfully
        """
        if not self._notifications_enabled:
            self.logger.debug("Notifications disabled, skipping")
            return False
        
        if not self._notification_service:
            self.logger.warning("Notification service not available")
            return False
        
        try:
            # Add to history
            self._add_to_history(request)
            
            # Map our levels to service levels
            from services.notification_service import NotificationType
            level_mapping = {
                NotificationLevel.INFO: NotificationType.INFO,
                NotificationLevel.SUCCESS: NotificationType.SUCCESS,
                NotificationLevel.WARNING: NotificationType.WARNING,
                NotificationLevel.ERROR: NotificationType.ERROR
            }
            
            service_level = level_mapping.get(request.level, NotificationType.INFO)
            
            # Send notification via service
            success = self._notification_service.send_notification(
                title=request.title,
                message=request.message,
                notification_type=service_level,
                action_url=request.action_url,
                persist=request.persist
            )
            
            if success:
                self.logger.debug(f"Notification sent: {request.title}")
            else:
                self.logger.warning(f"Failed to send notification: {request.title}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error showing notification: {e}")
            return False
    
    def _add_to_history(self, request: NotificationRequest):
        """Add notification to history"""
        self._notification_history.append(request)
        
        # Trim history if too long
        if len(self._notification_history) > self._max_history:
            self._notification_history = self._notification_history[-self._max_history:]
    
    # Convenience methods for different notification types
    def show_info(self, title: str, message: str, action_url: str = None) -> bool:
        """Show info notification"""
        request = NotificationRequest(title, message, NotificationLevel.INFO, action_url)
        return self.show_notification(request)
    
    def show_success(self, title: str, message: str, action_url: str = None) -> bool:
        """Show success notification"""
        request = NotificationRequest(title, message, NotificationLevel.SUCCESS, action_url)
        return self.show_notification(request)
    
    def show_warning(self, title: str, message: str, action_url: str = None) -> bool:
        """Show warning notification"""
        request = NotificationRequest(title, message, NotificationLevel.WARNING, action_url)
        return self.show_notification(request)
    
    def show_error(self, title: str, message: str, action_url: str = None) -> bool:
        """Show error notification"""
        request = NotificationRequest(title, message, NotificationLevel.ERROR, action_url)
        return self.show_notification(request)
    
    # Template-based notifications
    def show_template_notification(self, template_name: str, **kwargs) -> bool:
        """
        Show a templated notification
        
        Args:
            template_name: Name of the template to use
            **kwargs: Template parameters for formatting
            
        Returns:
            True if notification was shown successfully
        """
        if template_name not in self._templates:
            self.logger.error(f"Unknown notification template: {template_name}")
            return False
        
        template = self._templates[template_name]
        
        # Create a copy with formatted content
        request = NotificationRequest(
            title=template.title.format(**kwargs) if kwargs else template.title,
            message=template.message.format(**kwargs) if kwargs else template.message,
            level=template.level,
            action_url=template.action_url,
            show_in_ui=template.show_in_ui,
            persist=template.persist
        )
        
        return self.show_notification(request)
    
    # Backward compatibility methods (matching old NotificationManager API)
    def set_notifications_enabled(self, enabled: bool):
        """Set notifications enabled/disabled"""
        self._notifications_enabled = enabled
        
        # Update settings if available
        if self._settings_service:
            try:
                self._settings_service.set('notifications', enabled)
            except Exception as e:
                self.logger.error(f"Failed to save notification setting: {e}")
        
        self.logger.info(f"Notifications {'enabled' if enabled else 'disabled'}")
    
    def is_notifications_enabled(self) -> bool:
        """Check if notifications are enabled"""
        return self._notifications_enabled
    
    def get_notification_history(self) -> List[NotificationRequest]:
        """Get notification history"""
        return self._notification_history.copy()
    
    def clear_notification_history(self):
        """Clear notification history"""
        self._notification_history.clear()
        self.logger.debug("Notification history cleared")
    
    def add_custom_template(self, name: str, template: NotificationRequest):
        """
        Add a custom notification template
        
        Args:
            name: Template name
            template: NotificationRequest template
        """
        self._templates[name] = template
        self.logger.debug(f"Added custom notification template: {name}")
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template names"""
        return list(self._templates.keys())
    
    # Event handlers
    def _on_settings_changed(self, settings: Dict):
        """Handle settings changes"""
        notifications_enabled = settings.get('notifications', True)
        if notifications_enabled != self._notifications_enabled:
            self._notifications_enabled = notifications_enabled
            self.logger.debug(f"Notification setting updated: {notifications_enabled}")
    
    # Processing-specific notification methods (for backward compatibility)
    def notify_processing_started(self):
        """Notify that processing has started"""
        return self.show_template_notification('processing_started')
    
    def notify_processing_complete(self, result: str = ""):
        """Notify that processing is complete"""
        if result:
            return self.show_success("Processing Complete", f"Result: {result}")
        else:
            return self.show_template_notification('processing_complete')
    
    def notify_processing_error(self, error: str):
        """Notify about a processing error"""
        return self.show_error("Processing Error", error)
    
    def notify_hotkey_updated(self, hotkey: str):
        """Notify that hotkey was updated"""
        return self.show_info("Hotkey Updated", f"New hotkey: {hotkey}")
    
    def notify_permissions_required(self):
        """Notify that permissions are required"""
        return self.show_template_notification('permissions_required')
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get notification controller status
        
        Returns:
            Status information dictionary
        """
        return {
            'notifications_enabled': self._notifications_enabled,
            'notification_service_available': self._notification_service is not None,
            'settings_service_available': self._settings_service is not None,
            'permission_service_available': self._permission_service is not None,
            'history_count': len(self._notification_history),
            'available_templates': len(self._templates)
        } 