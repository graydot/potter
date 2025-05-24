#!/usr/bin/env python3
"""
Native macOS Settings UI for Rephrasely using PyObjC/Cocoa
Built from scratch for reliability
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


class HotkeyField(NSTextField):
    """Simple hotkey input field"""
    
    def initWithFrame_manager_(self, frame, settings_manager):
        self = objc.super(HotkeyField, self).initWithFrame_(frame)
        if self is None:
            return None
        
        self.settings_manager = settings_manager
        self.original_value = ""
        self.reset_callback = None
        
        # Configure appearance
        self.setBezeled_(True)
        self.setBezelStyle_(NSTextFieldSquareBezel)
        
        return self
    
    def becomeFirstResponder(self):
        """Clear field when focused"""
        self.original_value = str(self.stringValue())
        self.setStringValue_("")
        self.setPlaceholderString_("Press hotkey combination...")
        return objc.super(HotkeyField, self).becomeFirstResponder()
    
    def resignFirstResponder(self):
        """Restore original if empty"""
        if not self.stringValue():
            self.setStringValue_(self.original_value)
        self.setPlaceholderString_("")
        
        # Trigger reset button update and conflict check
        if self.reset_callback:
            self.reset_callback()
        
        return objc.super(HotkeyField, self).resignFirstResponder()
    
    def keyDown_(self, event):
        """Capture hotkey combinations"""
        if not self.currentEditor():
            return
        
        # Get modifiers
        modifiers = []
        flags = event.modifierFlags()
        
        if flags & NSEventModifierFlagCommand:
            modifiers.append("cmd")
        if flags & NSEventModifierFlagOption:
            modifiers.append("alt")
        if flags & NSEventModifierFlagControl:
            modifiers.append("ctrl")
        if flags & NSEventModifierFlagShift:
            modifiers.append("shift")
        
        # Get key
        key = event.charactersIgnoringModifiers().lower()
        
        # Build hotkey string
        if modifiers and key and key.isalnum():
            hotkey = "+".join(modifiers + [key])
            self.setStringValue_(hotkey)
            
            # Trigger updates
            if self.reset_callback:
                self.reset_callback()
            
            self.window().makeFirstResponder_(None)  # End editing


class SettingsWindow(NSWindowController):
    """Main settings window"""
    
    def initWithSettingsManager_(self, settings_manager):
        self = objc.super(SettingsWindow, self).init()
        if self is None:
            return None
        
        self.settings_manager = settings_manager
        self.on_settings_changed = None
        self.current_section = 0
        
        # UI elements
        self.hotkey_field = None
        self.reset_button = None
        self.conflict_label = None
        self.content_views = []
        self.text_views = {}
        
        self.createWindow()
        return self
    
    def createWindow(self):
        """Create the main window"""
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
        content_view = window.contentView()
        
        # Navigation buttons at top
        general_btn = NSButton.alloc().initWithFrame_(NSMakeRect(20, 550, 100, 30))
        general_btn.setTitle_("General")
        general_btn.setTag_(0)
        general_btn.setTarget_(self)
        general_btn.setAction_("switchSection:")
        content_view.addSubview_(general_btn)
        
        prompts_btn = NSButton.alloc().initWithFrame_(NSMakeRect(130, 550, 100, 30))
        prompts_btn.setTitle_("Prompts") 
        prompts_btn.setTag_(1)
        prompts_btn.setTarget_(self)
        prompts_btn.setAction_("switchSection:")
        content_view.addSubview_(prompts_btn)
        
        advanced_btn = NSButton.alloc().initWithFrame_(NSMakeRect(240, 550, 100, 30))
        advanced_btn.setTitle_("Advanced")
        advanced_btn.setTag_(2)
        advanced_btn.setTarget_(self)
        advanced_btn.setAction_("switchSection:")
        content_view.addSubview_(advanced_btn)
        
        # Content area
        self.content_container = NSView.alloc().initWithFrame_(NSMakeRect(20, 80, 660, 460))
        content_view.addSubview_(self.content_container)
        
        # Create content views
        self.content_views = [
            self.createGeneralView(),
            self.createPromptsView(),
            self.createAdvancedView()
        ]
        
        # Show general view initially
        self.showSection_(0)
        
        # Bottom buttons
        cancel_btn = NSButton.alloc().initWithFrame_(NSMakeRect(500, 20, 80, 30))
        cancel_btn.setTitle_("Cancel")
        cancel_btn.setTarget_(self)
        cancel_btn.setAction_("cancel:")
        cancel_btn.setKeyEquivalent_("\x1b")
        content_view.addSubview_(cancel_btn)
        
        save_btn = NSButton.alloc().initWithFrame_(NSMakeRect(600, 20, 80, 30))
        save_btn.setTitle_("Save")
        save_btn.setTarget_(self)
        save_btn.setAction_("save:")
        save_btn.setKeyEquivalent_("\r")
        content_view.addSubview_(save_btn)
        
        window.setDefaultButtonCell_(save_btn.cell())
        self.setWindow_(window)
    
    def switchSection_(self, sender):
        """Switch to a different section"""
        section = sender.tag()
        self.showSection_(section)
    
    def showSection_(self, section):
        """Show the specified section"""
        if section < 0 or section >= len(self.content_views):
            return
        
        # Remove current content
        for subview in self.content_container.subviews():
            subview.removeFromSuperview()
        
        # Add new content
        view = self.content_views[section]
        view.setFrame_(NSMakeRect(0, 0, 660, 460))
        self.content_container.addSubview_(view)
        
        self.current_section = section
    
    def createGeneralView(self):
        """Create General settings view"""
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 660, 460))
        
        # Title
        title = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 420, 660, 30))
        title.setStringValue_("General Settings")
        title.setFont_(NSFont.boldSystemFontOfSize_(18))
        title.setBezeled_(False)
        title.setDrawsBackground_(False)
        title.setEditable_(False)
        title.setAlignment_(NSTextAlignmentCenter)
        view.addSubview_(title)
        
        # Hotkey section
        hotkey_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 370, 120, 25))
        hotkey_label.setStringValue_("Global Hotkey:")
        hotkey_label.setBezeled_(False)
        hotkey_label.setDrawsBackground_(False)
        hotkey_label.setEditable_(False)
        view.addSubview_(hotkey_label)
        
        # Hotkey field
        self.hotkey_field = HotkeyField.alloc().initWithFrame_manager_(
            NSMakeRect(150, 370, 200, 25), self.settings_manager
        )
        self.hotkey_field.setStringValue_(self.settings_manager.get("hotkey", "cmd+shift+r"))
        self.hotkey_field.reset_callback = self.updateResetButton
        view.addSubview_(self.hotkey_field)
        
        # Reset button - always create it, visibility controlled by updateResetButton
        self.reset_button = NSButton.alloc().initWithFrame_(NSMakeRect(360, 370, 60, 25))
        self.reset_button.setTitle_("Reset")
        self.reset_button.setTarget_(self)
        self.reset_button.setAction_("resetHotkey:")
        self.reset_button.setButtonType_(NSButtonTypeMomentaryPushIn)
        view.addSubview_(self.reset_button)
        
        # Conflict warning
        self.conflict_label = NSTextField.alloc().initWithFrame_(NSMakeRect(150, 345, 400, 20))
        self.conflict_label.setBezeled_(False)
        self.conflict_label.setDrawsBackground_(False)
        self.conflict_label.setEditable_(False)
        self.conflict_label.setTextColor_(NSColor.systemRedColor())
        self.conflict_label.setFont_(NSFont.systemFontOfSize_(11))
        view.addSubview_(self.conflict_label)
        
        # Options
        self.auto_paste_checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(20, 300, 400, 25))
        self.auto_paste_checkbox.setButtonType_(NSButtonTypeSwitch)
        self.auto_paste_checkbox.setTitle_("Automatically paste processed text")
        self.auto_paste_checkbox.setState_(1 if self.settings_manager.get("auto_paste", True) else 0)
        view.addSubview_(self.auto_paste_checkbox)
        
        self.notifications_checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(20, 270, 400, 25))
        self.notifications_checkbox.setButtonType_(NSButtonTypeSwitch)
        self.notifications_checkbox.setTitle_("Show success/error notifications")
        self.notifications_checkbox.setState_(1 if self.settings_manager.get("show_notifications", True) else 0)
        view.addSubview_(self.notifications_checkbox)
        
        self.startup_checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(20, 240, 400, 25))
        self.startup_checkbox.setButtonType_(NSButtonTypeSwitch)
        self.startup_checkbox.setTitle_("Launch Rephrasely at startup")
        self.startup_checkbox.setState_(1 if self.settings_manager.get("launch_at_startup", False) else 0)
        view.addSubview_(self.startup_checkbox)
        
        # Update UI - this will set initial reset button visibility and check conflicts
        self.updateResetButton()
        
        return view
    
    def createPromptsView(self):
        """Create Prompts view"""
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 660, 460))
        
        # Title
        title = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 420, 660, 30))
        title.setStringValue_("AI Prompts")
        title.setFont_(NSFont.boldSystemFontOfSize_(18))
        title.setBezeled_(False)
        title.setDrawsBackground_(False)
        title.setEditable_(False)
        title.setAlignment_(NSTextAlignmentCenter)
        view.addSubview_(title)
        
        # Prompt editors
        prompts = self.settings_manager.get("prompts", {})
        y_pos = 380
        
        for mode in ['rephrase', 'summarize', 'expand', 'casual', 'formal']:
            # Label
            label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y_pos, 620, 20))
            label.setStringValue_(f"{mode.title()} Mode:")
            label.setFont_(NSFont.boldSystemFontOfSize_(13))
            label.setBezeled_(False)
            label.setDrawsBackground_(False)
            label.setEditable_(False)
            view.addSubview_(label)
            
            # Text field
            text_field = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y_pos - 25, 620, 25))
            text_field.setStringValue_(prompts.get(mode, ''))
            view.addSubview_(text_field)
            
            self.text_views[mode] = text_field
            y_pos -= 60
        
        return view
    
    def createAdvancedView(self):
        """Create Advanced view"""
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 660, 460))
        
        # Title
        title = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 420, 660, 30))
        title.setStringValue_("Advanced Settings")
        title.setFont_(NSFont.boldSystemFontOfSize_(18))
        title.setBezeled_(False)
        title.setDrawsBackground_(False)
        title.setEditable_(False)
        title.setAlignment_(NSTextAlignmentCenter)
        view.addSubview_(title)
        
        # AI Model
        model_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 370, 100, 25))
        model_label.setStringValue_("AI Model:")
        model_label.setBezeled_(False)
        model_label.setDrawsBackground_(False)
        model_label.setEditable_(False)
        view.addSubview_(model_label)
        
        self.model_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(130, 370, 200, 25))
        self.model_popup.addItemsWithTitles_(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
        current_model = self.settings_manager.get("model", "gpt-3.5-turbo")
        self.model_popup.selectItemWithTitle_(current_model)
        view.addSubview_(self.model_popup)
        
        # Max Tokens
        tokens_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 330, 100, 25))
        tokens_label.setStringValue_("Max Tokens:")
        tokens_label.setBezeled_(False)
        tokens_label.setDrawsBackground_(False)
        tokens_label.setEditable_(False)
        view.addSubview_(tokens_label)
        
        self.tokens_field = NSTextField.alloc().initWithFrame_(NSMakeRect(130, 330, 100, 25))
        self.tokens_field.setStringValue_(str(self.settings_manager.get("max_tokens", 1000)))
        view.addSubview_(self.tokens_field)
        
        # Temperature
        temp_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 290, 100, 25))
        temp_label.setStringValue_("Temperature:")
        temp_label.setBezeled_(False)
        temp_label.setDrawsBackground_(False)
        temp_label.setEditable_(False)
        view.addSubview_(temp_label)
        
        self.temp_field = NSTextField.alloc().initWithFrame_(NSMakeRect(130, 290, 100, 25))
        self.temp_field.setStringValue_(str(self.settings_manager.get("temperature", 0.7)))
        view.addSubview_(self.temp_field)
        
        return view
    
    def updateResetButton(self):
        """Update reset button visibility and check conflicts"""
        if not self.hotkey_field or not self.reset_button:
            return
        
        current = str(self.hotkey_field.stringValue())
        default = self.settings_manager.default_settings["hotkey"]
        
        # Show reset button if different from default
        self.reset_button.setHidden_(current == default)
        
        # Also check for conflicts
        self.checkConflicts()
    
    def checkConflicts(self):
        """Check for hotkey conflicts"""
        if not self.hotkey_field or not self.conflict_label:
            return
        
        hotkey = str(self.hotkey_field.stringValue()).lower()
        conflicts = {
            "cmd+space": "Spotlight",
            "cmd+tab": "App switching", 
            "cmd+shift+3": "Screenshot",
            "cmd+shift+4": "Screenshot selection",
            "cmd+shift+5": "Screenshot options",
            "cmd+ctrl+space": "Character viewer",
            "cmd+shift+a": "Applications folder",
            "cmd+shift+g": "Go to folder",
            "cmd+shift+h": "Home folder",
            "cmd+shift+u": "Utilities folder",
            "cmd+shift+n": "New folder",
            "cmd+shift+delete": "Empty trash",
            "cmd+alt+esc": "Force quit",
            "cmd+ctrl+q": "Lock screen",
            "cmd+shift+q": "Log out",
            "cmd+alt+d": "Show/hide dock"
        }
        
        if hotkey in conflicts:
            self.conflict_label.setStringValue_(f"⚠️ Conflicts with {conflicts[hotkey]}")
        else:
            self.conflict_label.setStringValue_("")
    
    def resetHotkey_(self, sender):
        """Reset hotkey to default"""
        default = self.settings_manager.default_settings["hotkey"]
        self.hotkey_field.setStringValue_(default)
        self.updateResetButton()
    
    def save_(self, sender):
        """Save settings"""
        settings = self.settings_manager.settings.copy()
        
        # General settings
        if self.hotkey_field:
            settings["hotkey"] = str(self.hotkey_field.stringValue())
        if self.auto_paste_checkbox:
            settings["auto_paste"] = bool(self.auto_paste_checkbox.state())
        if self.notifications_checkbox:
            settings["show_notifications"] = bool(self.notifications_checkbox.state())
        if self.startup_checkbox:
            settings["launch_at_startup"] = bool(self.startup_checkbox.state())
        
        # Prompts
        prompts = settings.get("prompts", {})
        for mode, field in self.text_views.items():
            prompts[mode] = str(field.stringValue())
        settings["prompts"] = prompts
        
        # Advanced
        if hasattr(self, 'model_popup'):
            settings["model"] = str(self.model_popup.titleOfSelectedItem())
        if hasattr(self, 'tokens_field'):
            try:
                settings["max_tokens"] = int(self.tokens_field.stringValue())
            except ValueError:
                settings["max_tokens"] = 1000
        if hasattr(self, 'temp_field'):
            try:
                settings["temperature"] = float(self.temp_field.stringValue())
            except ValueError:
                settings["temperature"] = 0.7
        
        # Save
        if self.settings_manager.save_settings(settings):
            if self.on_settings_changed:
                self.on_settings_changed(settings)
            self.window().close()
        else:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Save Failed")
            alert.setInformativeText_("Failed to save settings.")
            alert.setAlertStyle_(NSAlertStyleCritical)
            alert.runModal()
    
    def cancel_(self, sender):
        """Cancel changes"""
        self.window().close()


def show_settings(settings_manager, on_settings_changed=None):
    """Show settings window"""
    controller = SettingsWindow.alloc().initWithSettingsManager_(settings_manager)
    controller.on_settings_changed = on_settings_changed
    
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