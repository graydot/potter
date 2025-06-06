#!/usr/bin/env python3
"""
Permission Service
Manages system permissions (accessibility, notifications, etc.)
"""

import logging
import subprocess
import time
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from threading import Lock, Timer

from .base_service import BaseService
from core.exceptions import ServiceError, PermissionDeniedException

# Import system frameworks
try:
    from UserNotifications import UNUserNotificationCenter
    from Foundation import NSBundle
    USERNOTIFICATIONS_AVAILABLE = True
except ImportError:
    USERNOTIFICATIONS_AVAILABLE = False

logger = logging.getLogger(__name__)


class PermissionType(Enum):
    """Types of system permissions"""
    ACCESSIBILITY = "accessibility"
    NOTIFICATIONS = "notifications"
    SCREEN_RECORDING = "screen_recording"
    MICROPHONE = "microphone"
    CAMERA = "camera"


class PermissionStatus(Enum):
    """Permission status values"""
    GRANTED = "granted"
    DENIED = "denied"
    NOT_DETERMINED = "not_determined"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"


class PermissionService(BaseService):
    """
    Service for managing system permissions
    
    Features:
    - Permission status checking
    - Permission request handling
    - Periodic permission monitoring
    - Permission change notifications
    - System settings integration
    - User guidance for permission setup
    """
    
    def __init__(self, settings_manager=None):
        super().__init__("permission", {})
        
        self.settings_manager = settings_manager
        
        # Permission tracking
        self._permission_status: Dict[PermissionType, PermissionStatus] = {}
        self._permission_callbacks: Dict[PermissionType, List[Callable[[PermissionStatus], None]]] = {
            ptype: [] for ptype in PermissionType
        }
        self._status_lock = Lock()
        
        # Monitoring
        self._monitoring_timer: Optional[Timer] = None
        self._monitoring_interval = 30.0  # Check every 30 seconds
        
        # App bundle info
        self._bundle_id = self._get_bundle_id()
        
    def _start_service(self) -> None:
        """Start the permission service"""
        # Initial permission check
        self._check_all_permissions()
        
        # Start periodic monitoring
        self._start_permission_monitoring()
        
        self.logger.info("🔐 Permission service started")
    
    def _stop_service(self) -> None:
        """Stop the permission service"""
        # Stop monitoring
        if self._monitoring_timer:
            self._monitoring_timer.cancel()
            self._monitoring_timer = None
        
        # Clear callbacks
        with self._status_lock:
            for callbacks in self._permission_callbacks.values():
                callbacks.clear()
        
        self.logger.info("🔐 Permission service stopped")
    
    def _get_service_status(self) -> Dict[str, Any]:
        """Get permission service specific status"""
        with self._status_lock:
            return {
                'bundle_id': self._bundle_id,
                'usernotifications_available': USERNOTIFICATIONS_AVAILABLE,
                'monitoring_active': self._monitoring_timer is not None,
                'monitoring_interval': self._monitoring_interval,
                'permission_status': {
                    ptype.value: status.value 
                    for ptype, status in self._permission_status.items()
                },
                'callback_counts': {
                    ptype.value: len(callbacks)
                    for ptype, callbacks in self._permission_callbacks.items()
                }
            }
    
    def _handle_config_update(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        """Handle configuration updates"""
        if 'permission_monitoring_interval' in new_config:
            self._monitoring_interval = new_config['permission_monitoring_interval']
            # Restart monitoring with new interval
            if self._monitoring_timer:
                self._start_permission_monitoring()
    
    def get_permission_status(self, permission_type: PermissionType) -> PermissionStatus:
        """
        Get the current status of a permission
        
        Args:
            permission_type: Type of permission to check
            
        Returns:
            Current permission status
        """
        with self._status_lock:
            return self._permission_status.get(permission_type, PermissionStatus.UNKNOWN)
    
    def get_all_permission_status(self) -> Dict[PermissionType, PermissionStatus]:
        """
        Get status of all permissions
        
        Returns:
            Dict mapping permission types to their status
        """
        with self._status_lock:
            return self._permission_status.copy()
    
    def request_permission(self, permission_type: PermissionType) -> bool:
        """
        Request a system permission
        
        Args:
            permission_type: Type of permission to request
            
        Returns:
            bool: True if request was initiated successfully
        """
        try:
            if permission_type == PermissionType.ACCESSIBILITY:
                return self._request_accessibility_permission()
            elif permission_type == PermissionType.NOTIFICATIONS:
                return self._request_notification_permission()
            elif permission_type == PermissionType.SCREEN_RECORDING:
                return self._request_screen_recording_permission()
            else:
                self.logger.warning(f"Permission request not implemented for {permission_type.value}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error requesting {permission_type.value} permission: {e}")
            return False
    
    def open_system_settings(self, permission_type: PermissionType) -> bool:
        """
        Open system settings for a specific permission
        
        Args:
            permission_type: Type of permission settings to open
            
        Returns:
            bool: True if settings opened successfully
        """
        try:
            if permission_type == PermissionType.ACCESSIBILITY:
                url = "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
            elif permission_type == PermissionType.NOTIFICATIONS:
                url = "x-apple.systempreferences:com.apple.preference.notifications"
            elif permission_type == PermissionType.SCREEN_RECORDING:
                url = "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"
            else:
                self.logger.warning(f"System settings URL not defined for {permission_type.value}")
                return False
            
            result = subprocess.run(['open', url], capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info(f"Opened system settings for {permission_type.value}")
                return True
            else:
                self.logger.error(f"Failed to open system settings: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error opening system settings for {permission_type.value}: {e}")
            return False
    
    def add_permission_callback(self, permission_type: PermissionType, 
                               callback: Callable[[PermissionStatus], None]) -> None:
        """
        Add a callback for permission status changes
        
        Args:
            permission_type: Type of permission to monitor
            callback: Function to call when permission status changes
        """
        with self._status_lock:
            if callback not in self._permission_callbacks[permission_type]:
                self._permission_callbacks[permission_type].append(callback)
                self.logger.debug(f"Added callback for {permission_type.value} permission")
    
    def remove_permission_callback(self, permission_type: PermissionType,
                                  callback: Callable[[PermissionStatus], None]) -> None:
        """
        Remove a permission status callback
        
        Args:
            permission_type: Type of permission
            callback: Callback function to remove
        """
        with self._status_lock:
            if callback in self._permission_callbacks[permission_type]:
                self._permission_callbacks[permission_type].remove(callback)
                self.logger.debug(f"Removed callback for {permission_type.value} permission")
    
    def is_permission_granted(self, permission_type: PermissionType) -> bool:
        """
        Check if a permission is granted
        
        Args:
            permission_type: Type of permission to check
            
        Returns:
            bool: True if permission is granted
        """
        return self.get_permission_status(permission_type) == PermissionStatus.GRANTED
    
    def are_required_permissions_granted(self) -> bool:
        """
        Check if all required permissions are granted
        
        Returns:
            bool: True if all required permissions are granted
        """
        required_permissions = [PermissionType.ACCESSIBILITY]
        
        for permission_type in required_permissions:
            if not self.is_permission_granted(permission_type):
                return False
        
        return True
    
    def _check_all_permissions(self) -> None:
        """Check status of all permissions"""
        for permission_type in PermissionType:
            old_status = self._permission_status.get(permission_type)
            new_status = self._check_permission_status(permission_type)
            
            with self._status_lock:
                self._permission_status[permission_type] = new_status
            
            # Notify callbacks if status changed
            if old_status != new_status:
                self._notify_permission_callbacks(permission_type, new_status)
    
    def _check_permission_status(self, permission_type: PermissionType) -> PermissionStatus:
        """Check the status of a specific permission"""
        try:
            if permission_type == PermissionType.ACCESSIBILITY:
                return self._check_accessibility_permission()
            elif permission_type == PermissionType.NOTIFICATIONS:
                return self._check_notification_permission()
            elif permission_type == PermissionType.SCREEN_RECORDING:
                return self._check_screen_recording_permission()
            else:
                return PermissionStatus.UNKNOWN
                
        except Exception as e:
            self.logger.error(f"Error checking {permission_type.value} permission: {e}")
            return PermissionStatus.UNKNOWN
    
    def _check_accessibility_permission(self) -> PermissionStatus:
        """Check accessibility permission status"""
        try:
            # Use AXIsProcessTrusted to check accessibility permission
            result = subprocess.run([
                'osascript', '-e',
                'tell application "System Events" to return "ok"'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                return PermissionStatus.GRANTED
            else:
                return PermissionStatus.DENIED
                
        except subprocess.TimeoutExpired:
            return PermissionStatus.DENIED
        except Exception as e:
            self.logger.error(f"Error checking accessibility permission: {e}")
            return PermissionStatus.UNKNOWN
    
    def _check_notification_permission(self) -> PermissionStatus:
        """Check notification permission status"""
        if not USERNOTIFICATIONS_AVAILABLE:
            return PermissionStatus.UNKNOWN
        
        try:
            center = UNUserNotificationCenter.currentNotificationCenter()
            
            # This is a bit tricky - we need to check settings asynchronously
            # For now, we'll return a basic check
            return PermissionStatus.NOT_DETERMINED  # Would need async implementation
            
        except Exception as e:
            self.logger.error(f"Error checking notification permission: {e}")
            return PermissionStatus.UNKNOWN
    
    def _check_screen_recording_permission(self) -> PermissionStatus:
        """Check screen recording permission status"""
        try:
            # Check if we can capture screen (basic test)
            result = subprocess.run([
                'screencapture', '-x', '/tmp/test_screen_capture.png'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Clean up test file
                subprocess.run(['rm', '-f', '/tmp/test_screen_capture.png'])
                return PermissionStatus.GRANTED
            else:
                return PermissionStatus.DENIED
                
        except Exception as e:
            self.logger.error(f"Error checking screen recording permission: {e}")
            return PermissionStatus.UNKNOWN
    
    def _request_accessibility_permission(self) -> bool:
        """Request accessibility permission"""
        try:
            # Open accessibility settings
            return self.open_system_settings(PermissionType.ACCESSIBILITY)
            
        except Exception as e:
            self.logger.error(f"Error requesting accessibility permission: {e}")
            return False
    
    def _request_notification_permission(self) -> bool:
        """Request notification permission"""
        if not USERNOTIFICATIONS_AVAILABLE:
            return False
        
        try:
            center = UNUserNotificationCenter.currentNotificationCenter()
            
            # Request authorization
            from UserNotifications import UNAuthorizationOptionAlert, UNAuthorizationOptionSound, UNAuthorizationOptionBadge
            
            options = UNAuthorizationOptionAlert | UNAuthorizationOptionSound | UNAuthorizationOptionBadge
            
            def completion_handler(granted, error):
                if granted:
                    self.logger.info("✅ Notification permission granted")
                    with self._status_lock:
                        self._permission_status[PermissionType.NOTIFICATIONS] = PermissionStatus.GRANTED
                else:
                    self.logger.warning("❌ Notification permission denied")
                    with self._status_lock:
                        self._permission_status[PermissionType.NOTIFICATIONS] = PermissionStatus.DENIED
            
            center.requestAuthorizationWithOptions_completionHandler_(options, completion_handler)
            return True
            
        except Exception as e:
            self.logger.error(f"Error requesting notification permission: {e}")
            return False
    
    def _request_screen_recording_permission(self) -> bool:
        """Request screen recording permission"""
        try:
            # Open screen recording settings
            return self.open_system_settings(PermissionType.SCREEN_RECORDING)
            
        except Exception as e:
            self.logger.error(f"Error requesting screen recording permission: {e}")
            return False
    
    def _start_permission_monitoring(self) -> None:
        """Start periodic permission monitoring"""
        def monitor_permissions():
            if self.is_running:
                self._check_all_permissions()
                # Schedule next check
                self._monitoring_timer = Timer(self._monitoring_interval, monitor_permissions)
                self._monitoring_timer.start()
        
        # Cancel existing timer
        if self._monitoring_timer:
            self._monitoring_timer.cancel()
        
        # Start monitoring
        self._monitoring_timer = Timer(self._monitoring_interval, monitor_permissions)
        self._monitoring_timer.start()
        
        self.logger.debug(f"Started permission monitoring (interval: {self._monitoring_interval}s)")
    
    def _notify_permission_callbacks(self, permission_type: PermissionType, status: PermissionStatus) -> None:
        """Notify callbacks of permission status change"""
        with self._status_lock:
            callbacks = self._permission_callbacks[permission_type].copy()
        
        for callback in callbacks:
            try:
                callback(status)
            except Exception as e:
                self.logger.error(f"Error in permission callback for {permission_type.value}: {e}")
        
        self.logger.info(f"🔐 Permission {permission_type.value} status changed to {status.value}")
    
    def _get_bundle_id(self) -> str:
        """Get the application bundle ID"""
        try:
            if USERNOTIFICATIONS_AVAILABLE:
                bundle = NSBundle.mainBundle()
                if bundle:
                    bundle_id = bundle.bundleIdentifier()
                    if bundle_id:
                        return str(bundle_id)
            
            return "com.potter.app"  # Fallback
            
        except Exception:
            return "com.potter.app"  # Fallback 