#!/usr/bin/env python3
"""
UI Components Package
Service-aware UI components for Potter application
"""

from .service_aware_component import ServiceAwareComponent
from .ui_service_manager import UIServiceManager
# from .service_aware_window import ServiceAwareWindow  # Temporarily disabled
from .tray_icon_controller import TrayIconController, TrayIconState
from .notification_controller import NotificationController, NotificationLevel, NotificationRequest
from .settings_controller import SettingsController, ValidationResult, SettingsState

__all__ = [
    'ServiceAwareComponent',
    'UIServiceManager',
    # 'ServiceAwareWindow',  # Temporarily disabled
    'TrayIconController',
    'TrayIconState',
    'NotificationController',
    'NotificationLevel',
    'NotificationRequest',
    'SettingsController',
    'ValidationResult',
    'SettingsState'
] 