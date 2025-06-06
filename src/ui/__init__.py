#!/usr/bin/env python3
"""
UI Package
User interface components for Potter
"""

from .tray_icon import TrayIconManager
from .notifications import NotificationManager

# Service-integrated components
from .components import (
    ServiceAwareComponent, UIServiceManager,  # ServiceAwareWindow temporarily disabled
    TrayIconController, NotificationController, SettingsController
)

__all__ = [
    # Legacy components
    'TrayIconManager', 
    'NotificationManager',
    
    # Service-integrated components
    'ServiceAwareComponent',
    'UIServiceManager',
    # 'ServiceAwareWindow',  # Temporarily disabled
    'TrayIconController',
    'NotificationController',
    'SettingsController'
] 