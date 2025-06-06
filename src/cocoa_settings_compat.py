#!/usr/bin/env python3
"""
Cocoa Settings Compatibility Module
Provides backward compatibility for code using the old cocoa_settings imports
"""

# Import all the refactored components
from settings.settings_manager import SettingsManager
from ui.settings import (
    show_settings_dialog,
    show_settings_at_section,
    show_api_key_settings,
    get_settings_window,
    close_settings,
    SettingsWindow
)
from ui.settings.dialogs.prompt_dialog import PromptDialog
from ui.settings.widgets.hotkey_capture import HotkeyCapture
from ui.settings.widgets.pasteable_text_field import PasteableTextField

# Import AppKit components that were used
from AppKit import (
    NSAlert, NSImage, NSMakeSize, NSWindowController,
    NSView, NSTextField, NSObject
)

# Legacy function for showing settings
def show_settings(service=None):
    """Legacy compatibility function"""
    return show_settings_dialog(service)

# Export all components for backward compatibility
__all__ = [
    # Settings components
    'SettingsManager',
    'SettingsWindow',
    'show_settings',
    'show_settings_dialog',
    'show_settings_at_section',
    'show_api_key_settings',
    'get_settings_window',
    'close_settings',
    
    # Dialog components
    'PromptDialog',
    
    # Widget components
    'HotkeyCapture',
    'PasteableTextField',
    
    # AppKit re-exports
    'NSAlert',
    'NSImage', 
    'NSMakeSize',
    'NSWindowController',
    'NSView',
    'NSTextField',
    'NSObject'
] 