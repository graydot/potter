#!/usr/bin/env python3
"""
Simple Native macOS Settings UI for Rephrasely using PyObjC/Cocoa
Starting fresh with minimal complexity
"""

import json
import os
import subprocess
from typing import Dict, Any, Optional
import objc
from Foundation import *
from AppKit import *


class SettingsManager:
    """Simple settings manager"""
    
    def __init__(self, settings_file="settings.json"):
        self.settings_file = settings_file
        self.default_settings = {
            "prompts": {
                'rephrase': 'Please rephrase the following text to make it clearer and more professional:',
                'summarize': 'Please provide a concise summary of the following text:',
                'expand': 'Please expand on the following text with more detail and examples:',
                'casual': 'Please rewrite the following text in a more casual, friendly tone:',
                'formal': 'Please rewrite the following text in a more formal, professional tone:'
            },
            "hotkey": "cmd+shift+r",
            "model": "gpt-3.5-turbo",
            "max_tokens": 1000,
            "temperature": 0.7,
            "auto_paste": True,
            "show_notifications": True,
            "launch_at_startup": False
        }
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    settings = self.default_settings.copy()
                    settings.update(loaded)
                    return settings
            else:
                return self.default_settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to file"""
        try:
            self.settings = settings
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get(self, key: str, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)


class SimpleSettingsWindow(NSWindowController):
    """Simple settings window controller"""
    
    def initWithSettingsManager_(self, settings_manager):
        self = objc.super(SimpleSettingsWindow, self).init()
        if self is None:
            return None
        
        self.settings_manager = settings_manager
        self.on_settings_changed = None
        self.text_views = {}
        
        # Create window
        self.createWindow()
        return self
    
    def createWindow(self):
        """Create a simple settings window with three tabs"""
        # Create window
        frame = NSMakeRect(100, 100, 700, 600)
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False
        )
        
        window.setTitle_("Rephrasely Settings")
        window.setLevel_(NSNormalWindowLevel)
        
        # Create main content view
        content_view = window.contentView()
        
        # Create tab view
        tab_view = NSTabView.alloc().initWithFrame_(NSMakeRect(20, 60, 660, 520))
        
        # Create the three tabs
        self.createGeneralTab_(tab_view)
        self.createPromptsTab_(tab_view)
        self.createAdvancedTab_(tab_view)
        
        content_view.addSubview_(tab_view)
        
        # Bottom buttons (outside tabs)
        cancel_btn = NSButton.alloc().initWithFrame_(NSMakeRect(500, 20, 80, 30))
        cancel_btn.setTitle_("Cancel")
        cancel_btn.setTarget_(self)
        cancel_btn.setAction_("cancel:")
        cancel_btn.setKeyEquivalent_("\x1b")  # ESC key
        content_view.addSubview_(cancel_btn)
        
        save_btn = NSButton.alloc().initWithFrame_(NSMakeRect(600, 20, 80, 30))
        save_btn.setTitle_("Save")
        save_btn.setTarget_(self)
        save_btn.setAction_("save:")
        save_btn.setKeyEquivalent_("\r")  # Return key
        content_view.addSubview_(save_btn)
        
        # Set as default button
        window.setDefaultButtonCell_(save_btn.cell())
        
        self.setWindow_(window)
    
    def createGeneralTab_(self, tab_view):
        """Create the General tab"""
        tab_item = NSTabViewItem.alloc().initWithIdentifier_("general")
        tab_item.setLabel_("General")
        
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 640, 480))
        
        # Title
        title = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 440, 600, 25))
        title.setStringValue_("General Settings")
        title.setFont_(NSFont.boldSystemFontOfSize_(16))
        title.setBezeled_(False)
        title.setDrawsBackground_(False)
        title.setEditable_(False)
        view.addSubview_(title)
        
        # Hotkey setting
        hotkey_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 390, 120, 25))
        hotkey_label.setStringValue_("Global Hotkey:")
        hotkey_label.setBezeled_(False)
        hotkey_label.setDrawsBackground_(False)
        hotkey_label.setEditable_(False)
        view.addSubview_(hotkey_label)
        
        self.hotkey_field = NSTextField.alloc().initWithFrame_(NSMakeRect(150, 390, 200, 25))
        self.hotkey_field.setStringValue_(self.settings_manager.get("hotkey", "cmd+shift+r"))
        view.addSubview_(self.hotkey_field)
        
        # Auto-paste checkbox
        self.auto_paste_checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(20, 340, 400, 25))
        self.auto_paste_checkbox.setButtonType_(NSButtonTypeSwitch)
        self.auto_paste_checkbox.setTitle_("Automatically paste processed text")
        self.auto_paste_checkbox.setState_(1 if self.settings_manager.get("auto_paste", True) else 0)
        view.addSubview_(self.auto_paste_checkbox)
        
        # Notifications checkbox
        self.notifications_checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(20, 310, 400, 25))
        self.notifications_checkbox.setButtonType_(NSButtonTypeSwitch)
        self.notifications_checkbox.setTitle_("Show success/error notifications")
        self.notifications_checkbox.setState_(1 if self.settings_manager.get("show_notifications", True) else 0)
        view.addSubview_(self.notifications_checkbox)
        
        # Startup checkbox
        self.startup_checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(20, 280, 400, 25))
        self.startup_checkbox.setButtonType_(NSButtonTypeSwitch)
        self.startup_checkbox.setTitle_("Launch Rephrasely at startup")
        self.startup_checkbox.setState_(1 if self.settings_manager.get("launch_at_startup", False) else 0)
        view.addSubview_(self.startup_checkbox)
        
        tab_item.setView_(view)
        tab_view.addTabViewItem_(tab_item)
    
    def createPromptsTab_(self, tab_view):
        """Create the Prompts tab"""
        tab_item = NSTabViewItem.alloc().initWithIdentifier_("prompts")
        tab_item.setLabel_("Prompts")
        
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 640, 480))
        
        # Title
        title = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 440, 600, 25))
        title.setStringValue_("AI Prompts")
        title.setFont_(NSFont.boldSystemFontOfSize_(16))
        title.setBezeled_(False)
        title.setDrawsBackground_(False)
        title.setEditable_(False)
        view.addSubview_(title)
        
        # Create prompt editors for each mode
        prompts = self.settings_manager.get("prompts", {})
        y_pos = 400
        
        for mode in ['rephrase', 'summarize', 'expand', 'casual', 'formal']:
            # Mode label
            mode_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y_pos, 600, 20))
            mode_label.setStringValue_(f"{mode.title()} Mode:")
            mode_label.setFont_(NSFont.boldSystemFontOfSize_(13))
            mode_label.setBezeled_(False)
            mode_label.setDrawsBackground_(False)
            mode_label.setEditable_(False)
            view.addSubview_(mode_label)
            
            # Text view for this prompt
            scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(20, y_pos - 60, 600, 50))
            scroll_view.setHasVerticalScroller_(True)
            scroll_view.setAutohidesScrollers_(True)
            
            text_view = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 580, 50))
            prompt_text = prompts.get(mode, '')
            text_view.setString_(prompt_text)
            text_view.setFont_(NSFont.systemFontOfSize_(11))
            
            scroll_view.setDocumentView_(text_view)
            view.addSubview_(scroll_view)
            
            self.text_views[mode] = text_view
            
            y_pos -= 80
        
        tab_item.setView_(view)
        tab_view.addTabViewItem_(tab_item)
    
    def createAdvancedTab_(self, tab_view):
        """Create the Advanced tab"""
        tab_item = NSTabViewItem.alloc().initWithIdentifier_("advanced")
        tab_item.setLabel_("Advanced")
        
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 640, 480))
        
        # Title
        title = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 440, 600, 25))
        title.setStringValue_("Advanced Settings")
        title.setFont_(NSFont.boldSystemFontOfSize_(16))
        title.setBezeled_(False)
        title.setDrawsBackground_(False)
        title.setEditable_(False)
        view.addSubview_(title)
        
        # Model setting
        model_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 390, 100, 25))
        model_label.setStringValue_("AI Model:")
        model_label.setBezeled_(False)
        model_label.setDrawsBackground_(False)
        model_label.setEditable_(False)
        view.addSubview_(model_label)
        
        self.model_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(130, 390, 200, 25))
        self.model_popup.addItemsWithTitles_(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
        current_model = self.settings_manager.get("model", "gpt-3.5-turbo")
        self.model_popup.selectItemWithTitle_(current_model)
        view.addSubview_(self.model_popup)
        
        # Max tokens
        tokens_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 350, 100, 25))
        tokens_label.setStringValue_("Max Tokens:")
        tokens_label.setBezeled_(False)
        tokens_label.setDrawsBackground_(False)
        tokens_label.setEditable_(False)
        view.addSubview_(tokens_label)
        
        self.tokens_field = NSTextField.alloc().initWithFrame_(NSMakeRect(130, 350, 100, 25))
        self.tokens_field.setStringValue_(str(self.settings_manager.get("max_tokens", 1000)))
        view.addSubview_(self.tokens_field)
        
        # Temperature
        temp_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 310, 100, 25))
        temp_label.setStringValue_("Temperature:")
        temp_label.setBezeled_(False)
        temp_label.setDrawsBackground_(False)
        temp_label.setEditable_(False)
        view.addSubview_(temp_label)
        
        self.temp_field = NSTextField.alloc().initWithFrame_(NSMakeRect(130, 310, 100, 25))
        self.temp_field.setStringValue_(str(self.settings_manager.get("temperature", 0.7)))
        view.addSubview_(self.temp_field)
        
        tab_item.setView_(view)
        tab_view.addTabViewItem_(tab_item)
    
    def collectSettings(self):
        """Collect settings from UI"""
        settings = self.settings_manager.settings.copy()
        
        # Update basic settings from General tab
        settings["hotkey"] = str(self.hotkey_field.stringValue())
        settings["auto_paste"] = bool(self.auto_paste_checkbox.state())
        settings["show_notifications"] = bool(self.notifications_checkbox.state())
        settings["launch_at_startup"] = bool(self.startup_checkbox.state())
        
        # Update prompts from Prompts tab
        prompts = settings.get("prompts", {})
        for mode, text_view in self.text_views.items():
            prompts[mode] = str(text_view.string())
        settings["prompts"] = prompts
        
        # Update advanced settings from Advanced tab
        settings["model"] = str(self.model_popup.titleOfSelectedItem())
        
        try:
            settings["max_tokens"] = int(self.tokens_field.stringValue())
        except ValueError:
            settings["max_tokens"] = 1000  # Default fallback
        
        try:
            settings["temperature"] = float(self.temp_field.stringValue())
        except ValueError:
            settings["temperature"] = 0.7  # Default fallback
        
        return settings
    
    def save_(self, sender):
        """Save settings"""
        settings = self.collectSettings()
        
        if self.settings_manager.save_settings(settings):
            if self.on_settings_changed:
                self.on_settings_changed(settings)
            
            # Close window immediately without success dialog
            self.window().close()
        else:
            # Only show error alert
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Save Failed")
            alert.setInformativeText_("Failed to save settings.")
            alert.setAlertStyle_(NSAlertStyleCritical)
            alert.runModal()
    
    def cancel_(self, sender):
        """Cancel and close"""
        self.window().close()


def show_settings(settings_manager, on_settings_changed=None):
    """Show the simple settings window"""
    controller = SimpleSettingsWindow.alloc().initWithSettingsManager_(settings_manager)
    controller.on_settings_changed = on_settings_changed
    
    # Show window
    controller.showWindow_(None)
    controller.window().makeKeyAndOrderFront_(None)
    
    return controller


# Test if run directly
if __name__ == "__main__":
    app = NSApplication.sharedApplication()
    
    settings_manager = SettingsManager()
    controller = show_settings(settings_manager)
    
    if controller:
        app.run()
    else:
        print("Failed to create settings window") 