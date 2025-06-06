#!/usr/bin/env python3
"""
Cocoa Settings - Modular Architecture
This file now imports from the refactored modular structure
"""

# Import the SettingsManager from its proper location
from settings.settings_manager import SettingsManager

# Import all UI components from the new modular structure
from ui.settings import (
    show_settings,
    show_settings_dialog,
    show_settings_at_section,
    show_api_key_settings,
    get_settings_window,
    close_settings,
    SettingsWindow
)

# Import specific UI components
from ui.settings.dialogs.prompt_dialog import PromptDialog
from ui.settings.widgets.hotkey_capture import HotkeyCapture
from ui.settings.widgets.pasteable_text_field import PasteableTextField

# Import AppKit components for backward compatibility
from AppKit import (
    NSAlert, NSImage, NSMakeSize, NSWindowController,
    NSView, NSTextField, NSObject, NSMakeRect, NSFont,
    NSColor, NSButton, NSBezelStyleRounded, NSControlSizeRegular,
    NSBlueControlTint, NSEventModifierFlagCommand, NSEventModifierFlagOption,
    NSEventModifierFlagControl, NSEventModifierFlagShift, NSString,
    NSFontAttributeName
)

# Import helper functions from the modular structure
from ui.settings.widgets.ui_helpers import (
    create_clickable_link,
    create_section_header,
    create_section_separator, 
    create_modern_switch,
    create_sidebar_button
)

# Export all components for backward compatibility
__all__ = [
    # Core settings
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
    
    # Helper functions
    'create_clickable_link',
    'create_section_header',
    'create_section_separator',
    'create_modern_switch',
    'create_sidebar_button',
    
    # AppKit re-exports
    'NSAlert',
    'NSImage',
    'NSMakeSize',
    'NSWindowController',
    'NSView',
    'NSTextField',
    'NSObject',
    'NSMakeRect',
    'NSFont',
    'NSColor',
    'NSButton',
    'NSBezelStyleRounded',
    'NSControlSizeRegular',
    'NSBlueControlTint',
    'NSEventModifierFlagCommand',
    'NSEventModifierFlagOption',
    'NSEventModifierFlagControl',
    'NSEventModifierFlagShift',
    'NSString',
    'NSFontAttributeName'
] 