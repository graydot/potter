#!/usr/bin/env python3
"""
Native macOS Settings UI for Rephrasely using PyObjC/Cocoa
"""

import json
import os
import subprocess
from typing import Dict, Any, Optional
import objc
from Foundation import *
from AppKit import *


class SettingsManager:
    """Manages saving and loading of user settings"""
    
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
        """Load settings from file, create default if not exists"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
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
    
    def set(self, key: str, value: Any):
        """Set a setting value"""
        self.settings[key] = value


class HotkeyRecorder(NSView):
    """Custom view for recording hotkey combinations"""
    
    def initWithFrame_target_action_(self, frame, target, action):
        self = objc.super(HotkeyRecorder, self).initWithFrame_(frame)
        if self is None:
            return None
        
        self.target = target
        self.action = action
        self.recording = False
        self.hotkey_string = ""
        self.background_color = NSColor.controlBackgroundColor()
        self.text_color = NSColor.controlTextColor()
        
        return self
    
    def acceptsFirstResponder(self):
        return True
    
    def becomeFirstResponder(self):
        self.recording = True
        self.setNeedsDisplay_(True)
        return True
    
    def resignFirstResponder(self):
        self.recording = False
        self.setNeedsDisplay_(True)
        return True
    
    def drawRect_(self, rect):
        """Draw the hotkey recorder view"""
        # Draw background
        self.background_color.set()
        NSRectFill(rect)
        
        # Draw border
        if self.recording:
            NSColor.keyboardFocusIndicatorColor().set()
        else:
            NSColor.tertiaryLabelColor().set()
        NSFrameRect(rect)
        
        # Draw text
        text = self.hotkey_string if self.hotkey_string else ("Press keys..." if self.recording else "Click to set hotkey")
        
        attributes = {
            NSFontAttributeName: NSFont.systemFontOfSize_(13),
            NSForegroundColorAttributeName: self.text_color
        }
        
        text_size = NSString.sizeWithAttributes_(text, attributes)
        text_rect = NSMakeRect(
            (rect.size.width - text_size.width) / 2,
            (rect.size.height - text_size.height) / 2,
            text_size.width,
            text_size.height
        )
        
        NSString.drawInRect_withAttributes_(text, text_rect, attributes)
    
    def mouseDown_(self, event):
        """Handle mouse clicks to start recording"""
        if not self.recording:
            self.window().makeFirstResponder_(self)
    
    def keyDown_(self, event):
        """Record key combinations"""
        if not self.recording:
            return
        
        # Get modifier flags
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
        
        # Get key character
        key_char = event.charactersIgnoringModifiers().lower()
        
        # Build hotkey string
        if modifiers and key_char and key_char.isalnum():
            self.hotkey_string = "+".join(modifiers + [key_char])
            self.setNeedsDisplay_(True)
            
            # Notify target
            if self.target and self.action:
                objc.objc_msgSend(self.target, self.action, self.hotkey_string)
            
            # Stop recording
            self.window().makeFirstResponder_(None)
    
    def setHotkeyString_(self, hotkey_string):
        """Set the hotkey string"""
        self.hotkey_string = hotkey_string
        self.setNeedsDisplay_(True)


class SettingsWindowController(NSWindowController):
    """Native macOS settings window controller"""
    
    def initWithSettingsManager_(self, settings_manager):
        self = objc.super(SettingsWindowController, self).init()
        if self is None:
            return None
        
        self.settings_manager = settings_manager
        self.on_settings_changed = None
        self.prompt_text_views = {}
        self.hotkey_recorder = None
        
        # Create window
        self.createWindow()
        return self
    
    def createWindow(self):
        """Create the main settings window"""
        # Window frame
        frame = NSMakeRect(100, 100, 800, 650)
        
        # Create window
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable,
            NSBackingStoreBuffered,
            False
        )
        
        window.setTitle_("Rephrasely Preferences")
        window.setLevel_(NSFloatingWindowLevel)
        
        # Create tab view
        tab_view = NSTabView.alloc().initWithFrame_(NSMakeRect(20, 60, 760, 570))
        
        # Create tabs in the new order: General, Prompts, Advanced
        self.createGeneralTab_(tab_view)
        self.createPromptsTab_(tab_view)
        self.createAdvancedTab_(tab_view)
        
        # Add tab view to window
        window.contentView().addSubview_(tab_view)
        
        # Create buttons
        self.createButtons_(window)
        
        self.setWindow_(window)
    
    def createGeneralTab_(self, tab_view):
        """Create the general settings tab with permissions, startup, and hotkey"""
        tab_item = NSTabViewItem.alloc().initWithIdentifier_("general")
        tab_item.setLabel_("General")
        
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 740, 550))
        
        # Title
        title = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 500, 680, 30))
        title.setStringValue_("General Settings")
        title.setFont_(NSFont.boldSystemFontOfSize_(16))
        title.setBezeled_(False)
        title.setDrawsBackground_(False)
        title.setEditable_(False)
        view.addSubview_(title)
        
        # Permissions section
        perms_title = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 460, 680, 20))
        perms_title.setStringValue_("Permissions")
        perms_title.setFont_(NSFont.boldSystemFontOfSize_(14))
        perms_title.setBezeled_(False)
        perms_title.setDrawsBackground_(False)
        perms_title.setEditable_(False)
        view.addSubview_(perms_title)
        
        # Accessibility permission status
        self.accessibility_status = NSTextField.alloc().initWithFrame_(NSMakeRect(40, 430, 500, 20))
        self.accessibility_status.setBezeled_(False)
        self.accessibility_status.setDrawsBackground_(False)
        self.accessibility_status.setEditable_(False)
        view.addSubview_(self.accessibility_status)
        
        accessibility_btn = NSButton.alloc().initWithFrame_(NSMakeRect(550, 430, 150, 25))
        accessibility_btn.setTitle_("Open Accessibility")
        accessibility_btn.setTarget_(self)
        accessibility_btn.setAction_("openAccessibilitySettings:")
        view.addSubview_(accessibility_btn)
        
        # Screen recording permission status
        self.screen_recording_status = NSTextField.alloc().initWithFrame_(NSMakeRect(40, 400, 500, 20))
        self.screen_recording_status.setBezeled_(False)
        self.screen_recording_status.setDrawsBackground_(False)
        self.screen_recording_status.setEditable_(False)
        view.addSubview_(self.screen_recording_status)
        
        screen_recording_btn = NSButton.alloc().initWithFrame_(NSMakeRect(550, 400, 150, 25))
        screen_recording_btn.setTitle_("Open Privacy Settings")
        screen_recording_btn.setTarget_(self)
        screen_recording_btn.setAction_("openScreenRecordingSettings:")
        view.addSubview_(screen_recording_btn)
        
        # Startup section
        startup_title = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 350, 680, 20))
        startup_title.setStringValue_("Startup")
        startup_title.setFont_(NSFont.boldSystemFontOfSize_(14))
        startup_title.setBezeled_(False)
        startup_title.setDrawsBackground_(False)
        startup_title.setEditable_(False)
        view.addSubview_(startup_title)
        
        self.startup_checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(40, 320, 400, 25))
        self.startup_checkbox.setButtonType_(NSButtonTypeSwitch)
        self.startup_checkbox.setTitle_("Launch Rephrasely at startup")
        self.startup_checkbox.setState_(1 if self.settings_manager.get("launch_at_startup", False) else 0)
        self.startup_checkbox.setTarget_(self)
        self.startup_checkbox.setAction_("startupCheckboxChanged:")
        view.addSubview_(self.startup_checkbox)
        
        # Hotkey section
        hotkey_title = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 270, 680, 20))
        hotkey_title.setStringValue_("Global Hotkey")
        hotkey_title.setFont_(NSFont.boldSystemFontOfSize_(14))
        hotkey_title.setBezeled_(False)
        hotkey_title.setDrawsBackground_(False)
        hotkey_title.setEditable_(False)
        view.addSubview_(hotkey_title)
        
        # Hotkey recorder
        self.hotkey_recorder = HotkeyRecorder.alloc().initWithFrame_target_action_(
            NSMakeRect(40, 240, 300, 25), self, "hotkeyChanged:"
        )
        self.hotkey_recorder.setHotkeyString_(self.settings_manager.get("hotkey", "cmd+shift+r"))
        view.addSubview_(self.hotkey_recorder)
        
        # Reset hotkey button
        reset_hotkey_btn = NSButton.alloc().initWithFrame_(NSMakeRect(350, 240, 100, 25))
        reset_hotkey_btn.setTitle_("Reset")
        reset_hotkey_btn.setTarget_(self)
        reset_hotkey_btn.setAction_("resetHotkey:")
        view.addSubview_(reset_hotkey_btn)
        
        # Hotkey conflict warning
        self.hotkey_warning = NSTextField.alloc().initWithFrame_(NSMakeRect(40, 210, 600, 20))
        self.hotkey_warning.setBezeled_(False)
        self.hotkey_warning.setDrawsBackground_(False)
        self.hotkey_warning.setEditable_(False)
        self.hotkey_warning.setTextColor_(NSColor.systemRedColor())
        self.hotkey_warning.setStringValue_("")
        view.addSubview_(self.hotkey_warning)
        
        # Options section
        options_title = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 160, 680, 20))
        options_title.setStringValue_("Options")
        options_title.setFont_(NSFont.boldSystemFontOfSize_(14))
        options_title.setBezeled_(False)
        options_title.setDrawsBackground_(False)
        options_title.setEditable_(False)
        view.addSubview_(options_title)
        
        # Auto-paste checkbox
        self.auto_paste_checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(40, 130, 400, 25))
        self.auto_paste_checkbox.setButtonType_(NSButtonTypeSwitch)
        self.auto_paste_checkbox.setTitle_("Automatically paste processed text")
        self.auto_paste_checkbox.setState_(1 if self.settings_manager.get("auto_paste", True) else 0)
        view.addSubview_(self.auto_paste_checkbox)
        
        # Notifications checkbox
        self.notifications_checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(40, 100, 400, 25))
        self.notifications_checkbox.setButtonType_(NSButtonTypeSwitch)
        self.notifications_checkbox.setTitle_("Show success/error notifications")
        self.notifications_checkbox.setState_(1 if self.settings_manager.get("show_notifications", True) else 0)
        view.addSubview_(self.notifications_checkbox)
        
        # Update permission status
        self.updatePermissionStatus()
        
        tab_item.setView_(view)
        tab_view.addTabViewItem_(tab_item)
    
    def createPromptsTab_(self, tab_view):
        """Create the prompts tab"""
        tab_item = NSTabViewItem.alloc().initWithIdentifier_("prompts")
        tab_item.setLabel_("Prompts")
        
        # Create scroll view
        scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(10, 10, 740, 530))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setAutohidesScrollers_(True)
        
        # Create document view
        doc_view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 720, 1000))
        
        # Title
        title = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 950, 680, 30))
        title.setStringValue_("Customize AI Prompts")
        title.setFont_(NSFont.boldSystemFontOfSize_(16))
        title.setBezeled_(False)
        title.setDrawsBackground_(False)
        title.setEditable_(False)
        doc_view.addSubview_(title)
        
        # Create prompt editors
        prompts = self.settings_manager.get("prompts", {})
        y_pos = 900
        
        for mode, prompt in prompts.items():
            y_pos = self.createPromptEditorForMode_atY_inView_(mode, y_pos, doc_view)
        
        scroll_view.setDocumentView_(doc_view)
        tab_item.setView_(scroll_view)
        tab_view.addTabViewItem_(tab_item)
    
    def createPromptEditorForMode_atY_inView_(self, mode, y_pos, parent_view):
        """Create a prompt editor for a specific mode"""
        # Mode label
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y_pos, 680, 20))
        label.setStringValue_(f"{mode.title()} Mode")
        label.setFont_(NSFont.boldSystemFontOfSize_(14))
        label.setBezeled_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        parent_view.addSubview_(label)
        
        # Text view for prompt editing
        text_scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(20, y_pos - 100, 680, 80))
        text_scroll.setHasVerticalScroller_(True)
        text_scroll.setAutohidesScrollers_(True)
        
        text_view = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 660, 80))
        prompts = self.settings_manager.get("prompts", {})
        prompt = prompts.get(mode, "")
        text_view.setString_(prompt)
        # Use Monaco or Menlo as fallback monospace fonts
        font = NSFont.fontWithName_size_("Monaco", 11) or NSFont.fontWithName_size_("Menlo", 11) or NSFont.systemFontOfSize_(11)
        text_view.setFont_(font)
        
        text_scroll.setDocumentView_(text_view)
        parent_view.addSubview_(text_scroll)
        
        # Store reference
        self.prompt_text_views[mode] = text_view
        
        # Reset button
        reset_btn = NSButton.alloc().initWithFrame_(NSMakeRect(600, y_pos - 130, 100, 25))
        reset_btn.setTitle_("Reset Default")
        reset_btn.setTarget_(self)
        reset_btn.setAction_("resetPrompt:")
        reset_btn.setTag_(hash(mode))  # Use hash as identifier
        parent_view.addSubview_(reset_btn)
        
        return y_pos - 150
    
    def createAdvancedTab_(self, tab_view):
        """Create the advanced settings tab"""
        tab_item = NSTabViewItem.alloc().initWithIdentifier_("advanced")
        tab_item.setLabel_("Advanced")
        
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 740, 550))
        
        # Title
        title = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 500, 680, 30))
        title.setStringValue_("Advanced Settings")
        title.setFont_(NSFont.boldSystemFontOfSize_(16))
        title.setBezeled_(False)
        title.setDrawsBackground_(False)
        title.setEditable_(False)
        view.addSubview_(title)
        
        # Model selection
        model_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 450, 100, 20))
        model_label.setStringValue_("AI Model:")
        model_label.setBezeled_(False)
        model_label.setDrawsBackground_(False)
        model_label.setEditable_(False)
        view.addSubview_(model_label)
        
        self.model_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(130, 450, 200, 25))
        self.model_popup.addItemsWithTitles_(["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"])
        current_model = self.settings_manager.get("model", "gpt-3.5-turbo")
        self.model_popup.selectItemWithTitle_(current_model)
        view.addSubview_(self.model_popup)
        
        # Max tokens
        tokens_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 400, 100, 20))
        tokens_label.setStringValue_("Max Tokens:")
        tokens_label.setBezeled_(False)
        tokens_label.setDrawsBackground_(False)
        tokens_label.setEditable_(False)
        view.addSubview_(tokens_label)
        
        self.tokens_field = NSTextField.alloc().initWithFrame_(NSMakeRect(130, 400, 100, 25))
        self.tokens_field.setStringValue_(str(self.settings_manager.get("max_tokens", 1000)))
        view.addSubview_(self.tokens_field)
        
        # Temperature
        temp_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 350, 100, 20))
        temp_label.setStringValue_("Temperature:")
        temp_label.setBezeled_(False)
        temp_label.setDrawsBackground_(False)
        temp_label.setEditable_(False)
        view.addSubview_(temp_label)
        
        self.temp_field = NSTextField.alloc().initWithFrame_(NSMakeRect(130, 350, 100, 25))
        self.temp_field.setStringValue_(str(self.settings_manager.get("temperature", 0.7)))
        view.addSubview_(self.temp_field)
        
        # Export/Import buttons
        export_btn = NSButton.alloc().initWithFrame_(NSMakeRect(20, 250, 100, 30))
        export_btn.setTitle_("Export Settings")
        export_btn.setTarget_(self)
        export_btn.setAction_("exportSettings:")
        view.addSubview_(export_btn)
        
        import_btn = NSButton.alloc().initWithFrame_(NSMakeRect(130, 250, 100, 30))
        import_btn.setTitle_("Import Settings")
        import_btn.setTarget_(self)
        import_btn.setAction_("importSettings:")
        view.addSubview_(import_btn)
        
        tab_item.setView_(view)
        tab_view.addTabViewItem_(tab_item)
    
    def createButtons_(self, window):
        """Create the bottom buttons"""
        # Cancel button
        cancel_btn = NSButton.alloc().initWithFrame_(NSMakeRect(600, 20, 80, 30))
        cancel_btn.setTitle_("Cancel")
        cancel_btn.setTarget_(self)
        cancel_btn.setAction_("cancel:")
        window.contentView().addSubview_(cancel_btn)
        
        # Apply button
        apply_btn = NSButton.alloc().initWithFrame_(NSMakeRect(510, 20, 80, 30))
        apply_btn.setTitle_("Apply")
        apply_btn.setTarget_(self)
        apply_btn.setAction_("apply:")
        window.contentView().addSubview_(apply_btn)
        
        # Save button
        save_btn = NSButton.alloc().initWithFrame_(NSMakeRect(690, 20, 80, 30))
        save_btn.setTitle_("Save")
        save_btn.setTarget_(self)
        save_btn.setAction_("save:")
        window.contentView().addSubview_(save_btn)
    
    # Permission checking methods
    def updatePermissionStatus(self):
        """Update the permission status indicators"""
        # Check accessibility permission
        accessibility_enabled = self.checkAccessibilityPermission()
        if accessibility_enabled:
            self.accessibility_status.setStringValue_("✅ Accessibility: Enabled")
            self.accessibility_status.setTextColor_(NSColor.systemGreenColor())
        else:
            self.accessibility_status.setStringValue_("❌ Accessibility: Required for hotkey monitoring")
            self.accessibility_status.setTextColor_(NSColor.systemRedColor())
        
        # Check screen recording permission (needed for clipboard operations)
        screen_recording_enabled = self.checkScreenRecordingPermission()
        if screen_recording_enabled:
            self.screen_recording_status.setStringValue_("✅ Screen Recording: Enabled")
            self.screen_recording_status.setTextColor_(NSColor.systemGreenColor())
        else:
            self.screen_recording_status.setStringValue_("❌ Screen Recording: Required for text capture")
            self.screen_recording_status.setTextColor_(NSColor.systemRedColor())
    
    def checkAccessibilityPermission(self):
        """Check if accessibility permission is granted"""
        try:
            # This will return True if accessibility is enabled
            from ApplicationServices import AXIsProcessTrusted
            return AXIsProcessTrusted()
        except:
            return False
    
    def checkScreenRecordingPermission(self):
        """Check if screen recording permission is granted"""
        try:
            # Try to access screen recording capability
            from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
            windows = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
            return windows is not None and len(windows) > 0
        except:
            return False
    
    # Action methods
    def openAccessibilitySettings_(self, sender):
        """Open System Preferences to Accessibility settings"""
        try:
            subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'])
        except:
            pass
    
    def openScreenRecordingSettings_(self, sender):
        """Open System Preferences to Screen Recording settings"""
        try:
            subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture'])
        except:
            pass
    
    def startupCheckboxChanged_(self, sender):
        """Handle startup checkbox changes"""
        enabled = bool(sender.state())
        if enabled:
            self.addToLoginItems()
        else:
            self.removeFromLoginItems()
    
    def addToLoginItems(self):
        """Add app to login items"""
        try:
            app_path = NSBundle.mainBundle().bundlePath()
            if not app_path:
                # Fallback for development
                app_path = os.path.abspath("dist/Rephrasely.app")
            
            script = f'''
            tell application "System Events"
                make login item at end with properties {{path:"{app_path}", hidden:false}}
            end tell
            '''
            subprocess.run(['osascript', '-e', script])
        except Exception as e:
            print(f"Failed to add to login items: {e}")
    
    def removeFromLoginItems(self):
        """Remove app from login items"""
        try:
            script = '''
            tell application "System Events"
                delete login item "Rephrasely"
            end tell
            '''
            subprocess.run(['osascript', '-e', script])
        except Exception as e:
            print(f"Failed to remove from login items: {e}")
    
    def hotkeyChanged_(self, hotkey_string):
        """Handle hotkey changes"""
        self.checkHotkeyConflicts(hotkey_string)
    
    def resetHotkey_(self, sender):
        """Reset hotkey to default"""
        default_hotkey = self.settings_manager.default_settings["hotkey"]
        self.hotkey_recorder.setHotkeyString_(default_hotkey)
        self.checkHotkeyConflicts(default_hotkey)
    
    def checkHotkeyConflicts(self, hotkey_string):
        """Check for potential hotkey conflicts"""
        # List of common system shortcuts that might conflict
        system_shortcuts = {
            "cmd+space": "Spotlight search",
            "cmd+tab": "Application switching",
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
            "cmd+opt+esc": "Force quit",
            "cmd+ctrl+q": "Lock screen"
        }
        
        if hotkey_string.lower() in system_shortcuts:
            conflict = system_shortcuts[hotkey_string.lower()]
            self.hotkey_warning.setStringValue_(f"⚠️ May conflict with system shortcut: {conflict}")
        else:
            self.hotkey_warning.setStringValue_("")
    
    def resetPrompt_(self, sender):
        """Reset a prompt to default"""
        # Find the mode from button tag
        tag = sender.tag()
        for mode in self.settings_manager.default_settings["prompts"]:
            if hash(mode) == tag:
                default_prompt = self.settings_manager.default_settings["prompts"][mode]
                if mode in self.prompt_text_views:
                    self.prompt_text_views[mode].setString_(default_prompt)
                break
    
    def collectSettings(self):
        """Collect all settings from the UI"""
        settings = self.settings_manager.settings.copy()
        
        # Collect prompts
        prompts = {}
        for mode, text_view in self.prompt_text_views.items():
            prompts[mode] = str(text_view.string())
        settings["prompts"] = prompts
        
        # Collect general settings
        settings["hotkey"] = str(self.hotkey_recorder.hotkey_string)
        settings["auto_paste"] = bool(self.auto_paste_checkbox.state())
        settings["show_notifications"] = bool(self.notifications_checkbox.state())
        settings["launch_at_startup"] = bool(self.startup_checkbox.state())
        
        # Collect advanced settings
        settings["model"] = str(self.model_popup.titleOfSelectedItem())
        
        try:
            settings["max_tokens"] = int(self.tokens_field.stringValue())
        except ValueError:
            settings["max_tokens"] = 1000
        
        try:
            settings["temperature"] = float(self.temp_field.stringValue())
        except ValueError:
            settings["temperature"] = 0.7
        
        return settings
    
    def apply_(self, sender):
        """Apply settings without saving"""
        settings = self.collectSettings()
        self.settings_manager.settings = settings
        
        if self.on_settings_changed:
            self.on_settings_changed(settings)
        
        # Show confirmation
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Settings Applied")
        alert.setInformativeText_("Settings have been applied successfully.")
        alert.setAlertStyle_(NSAlertStyleInformational)
        alert.runModal()
    
    def save_(self, sender):
        """Save settings to file"""
        settings = self.collectSettings()
        
        if self.settings_manager.save_settings(settings):
            if self.on_settings_changed:
                self.on_settings_changed(settings)
            
            # Show confirmation
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Settings Saved")
            alert.setInformativeText_("Settings have been saved successfully.")
            alert.setAlertStyle_(NSAlertStyleInformational)
            alert.runModal()
            
            # Close window
            self.window().close()
        else:
            # Show error
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Save Failed")
            alert.setInformativeText_("Failed to save settings to file.")
            alert.setAlertStyle_(NSAlertStyleCritical)
            alert.runModal()
    
    def cancel_(self, sender):
        """Cancel and close window without saving"""
        self.window().close()
    
    def exportSettings_(self, sender):
        """Export settings to a file"""
        panel = NSSavePanel.alloc().init()
        panel.setTitle_("Export Settings")
        panel.setNameFieldStringValue_("rephrasely_settings.json")
        panel.setAllowedFileTypes_(["json"])
        
        if panel.runModal() == NSModalResponseOK:
            url = panel.URL()
            path = url.path()
            
            settings = self.collectSettings()
            try:
                with open(path, 'w') as f:
                    json.dump(settings, f, indent=2)
                
                alert = NSAlert.alloc().init()
                alert.setMessageText_("Export Successful")
                alert.setInformativeText_(f"Settings exported to {path}")
                alert.setAlertStyle_(NSAlertStyleInformational)
                alert.runModal()
            except Exception as e:
                alert = NSAlert.alloc().init()
                alert.setMessageText_("Export Failed")
                alert.setInformativeText_(f"Failed to export settings: {str(e)}")
                alert.setAlertStyle_(NSAlertStyleCritical)
                alert.runModal()
    
    def importSettings_(self, sender):
        """Import settings from a file"""
        panel = NSOpenPanel.alloc().init()
        panel.setTitle_("Import Settings")
        panel.setAllowedFileTypes_(["json"])
        panel.setCanChooseFiles_(True)
        panel.setCanChooseDirectories_(False)
        
        if panel.runModal() == NSModalResponseOK:
            url = panel.URL()
            path = url.path()
            
            try:
                with open(path, 'r') as f:
                    imported_settings = json.load(f)
                
                # Load settings into UI
                self.loadSettingsToUI_(imported_settings)
                
                alert = NSAlert.alloc().init()
                alert.setMessageText_("Import Successful")
                alert.setInformativeText_(f"Settings imported from {path}")
                alert.setAlertStyle_(NSAlertStyleInformational)
                alert.runModal()
            except Exception as e:
                alert = NSAlert.alloc().init()
                alert.setMessageText_("Import Failed")
                alert.setInformativeText_(f"Failed to import settings: {str(e)}")
                alert.setAlertStyle_(NSAlertStyleCritical)
                alert.runModal()
    
    def loadSettingsToUI_(self, settings):
        """Load settings into the UI controls"""
        # Load prompts
        prompts = settings.get("prompts", {})
        for mode, text_view in self.prompt_text_views.items():
            if mode in prompts:
                text_view.setString_(prompts[mode])
        
        # Load general settings
        self.hotkey_recorder.setHotkeyString_(settings.get("hotkey", "cmd+shift+r"))
        self.auto_paste_checkbox.setState_(1 if settings.get("auto_paste", True) else 0)
        self.notifications_checkbox.setState_(1 if settings.get("show_notifications", True) else 0)
        self.startup_checkbox.setState_(1 if settings.get("launch_at_startup", False) else 0)
        
        # Load advanced settings
        model = settings.get("model", "gpt-3.5-turbo")
        self.model_popup.selectItemWithTitle_(model)
        self.tokens_field.setStringValue_(str(settings.get("max_tokens", 1000)))
        self.temp_field.setStringValue_(str(settings.get("temperature", 0.7)))
    
    def close(self):
        """Close the settings window"""
        if self.window():
            self.window().close()

def show_settings(settings_manager, on_settings_changed=None):
    """Show the settings window"""
    controller = SettingsWindowController.alloc().initWithSettingsManager_(settings_manager)
    controller.on_settings_changed = on_settings_changed
    
    # Show window
    controller.showWindow_(None)
    controller.window().makeKeyAndOrderFront_(None)
    
    return controller


# Test the UI if run directly
if __name__ == "__main__":
    app = NSApplication.sharedApplication()
    
    settings_manager = SettingsManager()
    controller = show_settings(settings_manager)
    
    if controller:
        app.run()
    else:
        print("Failed to create settings window") 