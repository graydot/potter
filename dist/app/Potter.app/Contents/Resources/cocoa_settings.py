#!/usr/bin/env python3
"""
Native macOS Settings UI for Potter using PyObjC/Cocoa
Built from scratch for reliability
"""

import json
import os
import sys
import subprocess
from typing import Dict, Any, Optional
import objc
from Foundation import *
from AppKit import *
from UserNotifications import *


class SettingsManager:
    """Simple settings manager"""
    
    def __init__(self, settings_file=None):
        # Determine appropriate settings file location
        if settings_file is None:
            if getattr(sys, 'frozen', False):
                # Running as PyInstaller bundle - use user's Application Support directory
                settings_dir = os.path.expanduser('~/Library/Application Support/Potter')
                os.makedirs(settings_dir, exist_ok=True)
                self.settings_file = os.path.join(settings_dir, 'settings.json')
            else:
                # Running as script - use config directory
                self.settings_file = "config/settings.json"
        else:
            self.settings_file = settings_file
        self.default_settings = {
            "prompts": [
                {
                    "name": "rephrase",
                    "text": "Please rephrase the following text to make it clearer and more professional:",
                    "output_format": "text"
                },
                {
                    "name": "summarize", 
                    "text": "Please provide a concise summary of the following text:",
                    "output_format": "text"
                },
                {
                    "name": "expand",
                    "text": "Please expand on the following text with more detail and examples:",
                    "output_format": "text"
                },
                {
                    "name": "casual",
                    "text": "Please rewrite the following text in a more casual, friendly tone:",
                    "output_format": "text"
                },
                {
                    "name": "formal",
                    "text": "Please rewrite the following text in a more formal, professional tone:",
                    "output_format": "text"
                }
            ],
            "hotkey": "cmd+shift+r",
            "model": "gpt-3.5-turbo",
            "max_tokens": 1000,
            "temperature": 0.7,
            "show_notifications": True,
            "launch_at_startup": False,
            "openai_api_key": ""
        }
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    settings = self.default_settings.copy()
                    
                    # Handle prompts separately to ensure proper structure
                    if "prompts" in loaded:
                        if isinstance(loaded["prompts"], dict):
                            # Migrate old format
                            print("🔄 Migrating prompts from old format to new format...")
                            old_prompts = loaded["prompts"]
                            new_prompts = []
                            
                            for name, text in old_prompts.items():
                                new_prompts.append({
                                    "name": name,
                                    "text": text,
                                    "output_format": "text"
                                })
                            
                            settings["prompts"] = new_prompts
                            print("✅ Successfully migrated prompts to new format")
                        elif isinstance(loaded["prompts"], list):
                            # Check if it's the correct new format
                            if loaded["prompts"] and isinstance(loaded["prompts"][0], dict):
                                settings["prompts"] = loaded["prompts"]
                            else:
                                # It's a list of strings or wrong format, use defaults
                                print("⚠️ Invalid prompts format, using defaults")
                                settings["prompts"] = self.default_settings["prompts"]
                        else:
                            # Unknown format, use defaults
                            settings["prompts"] = self.default_settings["prompts"]
                    
                    # Update other settings normally
                    for key, value in loaded.items():
                        if key != "prompts":  # We handled prompts above
                            settings[key] = value
                    
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
    
    def is_first_launch(self) -> bool:
        """Check if this is the first launch (no settings file exists or no API key)"""
        # Check if settings file exists
        if not os.path.exists(self.settings_file):
            return True
        
        # Check if OpenAI API key is configured (in settings or environment)
        api_key_in_settings = self.get("openai_api_key", "").strip()
        api_key_in_env = os.getenv('OPENAI_API_KEY', "").strip()
        
        if not api_key_in_settings and not api_key_in_env:
            return True
        
        return False
    
    def show_notification(self, title, message, is_error=False):
        """Show a macOS notification"""
        try:
            notification = NSUserNotification.alloc().init()
            notification.setTitle_(title)
            notification.setInformativeText_(message)
            
            if is_error:
                notification.setSoundName_("Funk")  # Error sound
            else:
                notification.setSoundName_("Glass")  # Success sound
            
            center = NSUserNotificationCenter.defaultUserNotificationCenter()
            center.deliverNotification_(notification)
            
        except Exception as e:
            print(f"Failed to show notification: {e}")
    
    def show_success(self, message="Operation completed successfully"):
        """Show success notification if enabled"""
        if self.get("show_notifications", False):
            self.show_notification("Potter", message, is_error=False)
    
    def show_error(self, error_message):
        """Show error notification if enabled"""
        if self.get("show_notifications", False):
            self.show_notification("Potter Error", error_message, is_error=True)


class HotkeyField(NSTextField):
    """Simple hotkey input field"""
    
    def initWithFrame_manager_(self, frame, settings_manager):
        self = objc.super(HotkeyField, self).initWithFrame_(frame)
        if self is None:
            return None
        
        self.settings_manager = settings_manager
        self.reset_callback = None
        
        # Configure appearance and behavior
        self.setBezeled_(True)
        self.setBezelStyle_(NSTextFieldRoundedBezel)
        self.setEditable_(True)
        self.setSelectable_(True)
        self.setEnabled_(True)
        self.setUsesSingleLineMode_(True)
        
        # Allow field to become first responder
        self.setRefusesFirstResponder_(False)
        
        # Set font
        self.setFont_(NSFont.systemFontOfSize_(13))
        
        return self
    
    def acceptsFirstResponder(self):
        """Allow this field to become first responder"""
        return True
    
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


class PasteableTextField(NSTextField):
    """NSTextField that explicitly supports paste operations"""
    
    def initWithFrame_(self, frame):
        self = objc.super(PasteableTextField, self).initWithFrame_(frame)
        if self is None:
            return None
        
        # Configure as single-line text field
        self.setBezeled_(True)
        self.setBezelStyle_(NSTextFieldRoundedBezel)  # Modern rounded appearance
        self.setEditable_(True)
        self.setSelectable_(True)
        self.setEnabled_(True)
        self.setUsesSingleLineMode_(True)  # Force single line
        self.setLineBreakMode_(NSLineBreakByClipping)  # Clip overflow
        
        # Allow field to become first responder
        self.setRefusesFirstResponder_(False)
        
        # Set font to match system
        self.setFont_(NSFont.systemFontOfSize_(13))
        
        return self
    
    def becomeFirstResponder(self):
        """Handle becoming first responder"""
        print("Debug - API key field becoming first responder")
        result = objc.super(PasteableTextField, self).becomeFirstResponder()
        if result:
            print("Debug - API key field successfully became first responder")
        else:
            print("Debug - API key field failed to become first responder")
        return result
    
    def performKeyEquivalent_(self, event):
        """Handle key equivalents like Cmd+V"""
        # Check for Cmd+V (paste)
        if (event.modifierFlags() & NSEventModifierFlagCommand and 
            event.charactersIgnoringModifiers().lower() == 'v'):
            self.paste_(None)
            return True
        
        # Check for Cmd+C (copy)
        if (event.modifierFlags() & NSEventModifierFlagCommand and 
            event.charactersIgnoringModifiers().lower() == 'c'):
            self.copy_(None)
            return True
        
        # Check for Cmd+X (cut)
        if (event.modifierFlags() & NSEventModifierFlagCommand and 
            event.charactersIgnoringModifiers().lower() == 'x'):
            self.cut_(None)
            return True
        
        # Check for Cmd+A (select all)
        if (event.modifierFlags() & NSEventModifierFlagCommand and 
            event.charactersIgnoringModifiers().lower() == 'a'):
            self.selectAll_(None)
            return True
        
        return objc.super(PasteableTextField, self).performKeyEquivalent_(event)
    
    def paste_(self, sender):
        """Handle paste operation"""
        try:
            pasteboard = NSPasteboard.generalPasteboard()
            string = pasteboard.stringForType_(NSPasteboardTypeString)
            if string:
                # Get current selection or cursor position
                field_editor = self.currentEditor()
                if field_editor:
                    field_editor.insertText_(string)
                else:
                    # Fallback: replace entire content
                    self.setStringValue_(string)
                print(f"Debug - Pasted text: {len(string)} characters")
                return True
        except Exception as e:
            print(f"Debug - Paste error: {e}")
        return False
    
    def copy_(self, sender):
        """Handle copy operation"""
        try:
            # Get selected text or all text
            field_editor = self.currentEditor()
            if field_editor and field_editor.selectedRange().length > 0:
                selected_text = field_editor.string().substringWithRange_(field_editor.selectedRange())
            else:
                selected_text = self.stringValue()
            
            if selected_text:
                pasteboard = NSPasteboard.generalPasteboard()
                pasteboard.clearContents()
                pasteboard.setString_forType_(selected_text, NSPasteboardTypeString)
                print(f"Debug - Copied text: {len(selected_text)} characters")
                return True
        except Exception as e:
            print(f"Debug - Copy error: {e}")
        return False
    
    def cut_(self, sender):
        """Handle cut operation"""
        try:
            if self.copy_(sender):
                # Get selected text range or select all
                field_editor = self.currentEditor()
                if field_editor:
                    if field_editor.selectedRange().length > 0:
                        field_editor.insertText_("")
                    else:
                        self.setStringValue_("")
                else:
                    self.setStringValue_("")
                print("Debug - Cut operation completed")
                return True
        except Exception as e:
            print(f"Debug - Cut error: {e}")
        return False
    
    def selectAll_(self, sender):
        """Handle select all operation"""
        try:
            field_editor = self.currentEditor()
            if field_editor:
                field_editor.selectAll_(sender)
            else:
                # Make this field first responder and then select all
                self.window().makeFirstResponder_(self)
                field_editor = self.currentEditor()
                if field_editor:
                    field_editor.selectAll_(sender)
            print("Debug - Select all completed")
            return True
        except Exception as e:
            print(f"Debug - Select all error: {e}")
        return False


class PromptDialog(NSWindowController):
    """Dialog for adding/editing prompts"""
    
    def initWithPrompt_isEdit_(self, prompt=None, is_edit=False):
        self = objc.super(PromptDialog, self).init()
        if self is None:
            return None
        
        self.prompt = prompt or {"name": "", "text": "", "output_format": "text"}
        self.is_edit = is_edit
        self.result = None
        self.callback = None
        
        self.createDialog()
        return self
    
    def createDialog(self):
        """Create the dialog window"""
        # Create window
        frame = NSMakeRect(100, 100, 500, 300)
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
            NSBackingStoreBuffered,
            False
        )
        
        title = "Edit Prompt" if self.is_edit else "Add New Prompt"
        window.setTitle_(title)
        window.setLevel_(NSModalPanelWindowLevel)
        content_view = window.contentView()
        
        # Name field (max 10 chars)
        name_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 240, 100, 20))
        name_label.setStringValue_("Name (max 10):")
        name_label.setBezeled_(False)
        name_label.setDrawsBackground_(False)
        name_label.setEditable_(False)
        content_view.addSubview_(name_label)
        
        self.name_field = NSTextField.alloc().initWithFrame_(NSMakeRect(130, 240, 200, 25))
        self.name_field.setStringValue_(self.prompt.get("name", ""))
        self.name_field.setTarget_(self)
        self.name_field.setAction_("validateName:")
        content_view.addSubview_(self.name_field)
        
        # Character count label
        self.char_count_label = NSTextField.alloc().initWithFrame_(NSMakeRect(340, 240, 100, 20))
        self.char_count_label.setBezeled_(False)
        self.char_count_label.setDrawsBackground_(False)
        self.char_count_label.setEditable_(False)
        self.char_count_label.setFont_(NSFont.systemFontOfSize_(10))
        self.char_count_label.setTextColor_(NSColor.secondaryLabelColor())
        content_view.addSubview_(self.char_count_label)
        
        # Prompt text field
        prompt_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 200, 100, 20))
        prompt_label.setStringValue_("Prompt Text:")
        prompt_label.setBezeled_(False)
        prompt_label.setDrawsBackground_(False)
        prompt_label.setEditable_(False)
        content_view.addSubview_(prompt_label)
        
        # Scrollable text view for prompt
        scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(20, 100, 460, 90))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setHasHorizontalScroller_(False)
        scroll_view.setBorderType_(NSBezelBorder)
        
        self.prompt_text_view = NSTextView.alloc().initWithFrame_(scroll_view.contentView().bounds())
        self.prompt_text_view.setString_(self.prompt.get("text", ""))
        self.prompt_text_view.setFont_(NSFont.systemFontOfSize_(12))
        scroll_view.setDocumentView_(self.prompt_text_view)
        content_view.addSubview_(scroll_view)
        
        # Output format dropdown
        format_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 60, 100, 20))
        format_label.setStringValue_("Output Format:")
        format_label.setBezeled_(False)
        format_label.setDrawsBackground_(False)
        format_label.setEditable_(False)
        content_view.addSubview_(format_label)
        
        self.format_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(130, 60, 150, 25))
        self.format_popup.addItemsWithTitles_(["text", "images", "pdf"])
        current_format = self.prompt.get("output_format", "text")
        self.format_popup.selectItemWithTitle_(current_format)
        content_view.addSubview_(self.format_popup)
        
        # Buttons
        cancel_btn = NSButton.alloc().initWithFrame_(NSMakeRect(320, 20, 80, 30))
        cancel_btn.setTitle_("Cancel")
        cancel_btn.setTarget_(self)
        cancel_btn.setAction_("cancel:")
        cancel_btn.setKeyEquivalent_("\x1b")
        content_view.addSubview_(cancel_btn)
        
        save_btn = NSButton.alloc().initWithFrame_(NSMakeRect(410, 20, 80, 30))
        save_btn.setTitle_("Save")
        save_btn.setTarget_(self)
        save_btn.setAction_("save:")
        save_btn.setKeyEquivalent_("\r")
        content_view.addSubview_(save_btn)
        
        window.setDefaultButtonCell_(save_btn.cell())
        self.setWindow_(window)
        
        # Update character count
        self.updateCharCount()
    
    def validateName_(self, sender):
        """Validate name length as user types"""
        name = str(self.name_field.stringValue())
        if len(name) > 10:
            # Truncate to 10 characters
            truncated = name[:10]
            self.name_field.setStringValue_(truncated)
        self.updateCharCount()
    
    def updateCharCount(self):
        """Update character count label"""
        name = str(self.name_field.stringValue())
        count = len(name)
        self.char_count_label.setStringValue_(f"{count}/10")
        
        if count > 8:
            self.char_count_label.setTextColor_(NSColor.systemRedColor())
        elif count > 6:
            self.char_count_label.setTextColor_(NSColor.systemOrangeColor())
        else:
            self.char_count_label.setTextColor_(NSColor.secondaryLabelColor())
    
    def save_(self, sender):
        """Save the prompt"""
        name = str(self.name_field.stringValue()).strip()
        text = str(self.prompt_text_view.string()).strip()
        output_format = str(self.format_popup.titleOfSelectedItem())
        
        # Validation
        if not name:
            self.showAlertWithTitle_message_("Name Required", "Please enter a name for this prompt.")
            return
        
        if len(name) > 10:
            self.showAlertWithTitle_message_("Name Too Long", "Name must be 10 characters or less.")
            return
        
        if not text:
            self.showAlertWithTitle_message_("Prompt Required", "Please enter the prompt text.")
            return
        
        # Create result
        self.result = {
            "name": name,
            "text": text,
            "output_format": output_format
        }
        
        # Call callback if set
        if self.callback:
            self.callback(self.result)
        
        self.window().close()
    
    def cancel_(self, sender):
        """Cancel the dialog"""
        self.result = None
        if self.callback:
            self.callback(None)
        self.window().close()
    
    def showAlertWithTitle_message_(self, title, message):
        """Show an alert dialog"""
        alert = NSAlert.alloc().init()
        alert.setMessageText_(title)
        alert.setInformativeText_(message)
        alert.setAlertStyle_(NSAlertStyleWarning)
        alert.runModal()
    
    def runModal(self):
        """Run the dialog modally"""
        return NSApp.runModalForWindow_(self.window())


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
        self.prompts_data = []  # Initialize prompts data
        
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
        
        window.setTitle_("Potter Settings")
        window.setLevel_(NSNormalWindowLevel)
        
        # Set delegate to handle window events including ESC key
        window.setDelegate_(self)
        
        content_view = window.contentView()
        
        # Navigation buttons at top
        self.general_btn = NSButton.alloc().initWithFrame_(NSMakeRect(20, 550, 100, 30))
        self.general_btn.setTitle_("General")
        self.general_btn.setTag_(0)
        self.general_btn.setTarget_(self)
        self.general_btn.setAction_("switchSection:")
        self.general_btn.setButtonType_(NSButtonTypePushOnPushOff)
        self.general_btn.setBezelStyle_(NSBezelStyleRounded)
        content_view.addSubview_(self.general_btn)
        
        self.prompts_btn = NSButton.alloc().initWithFrame_(NSMakeRect(130, 550, 100, 30))
        self.prompts_btn.setTitle_("Prompts") 
        self.prompts_btn.setTag_(1)
        self.prompts_btn.setTarget_(self)
        self.prompts_btn.setAction_("switchSection:")
        self.prompts_btn.setButtonType_(NSButtonTypePushOnPushOff)
        self.prompts_btn.setBezelStyle_(NSBezelStyleRounded)
        content_view.addSubview_(self.prompts_btn)
        
        self.advanced_btn = NSButton.alloc().initWithFrame_(NSMakeRect(240, 550, 100, 30))
        self.advanced_btn.setTitle_("Advanced")
        self.advanced_btn.setTag_(2)
        self.advanced_btn.setTarget_(self)
        self.advanced_btn.setAction_("switchSection:")
        self.advanced_btn.setButtonType_(NSButtonTypePushOnPushOff)
        self.advanced_btn.setBezelStyle_(NSBezelStyleRounded)
        content_view.addSubview_(self.advanced_btn)
        
        # Store buttons for easy access
        self.section_buttons = [self.general_btn, self.prompts_btn, self.advanced_btn]
        
        # Content area
        self.content_container = NSView.alloc().initWithFrame_(NSMakeRect(20, 80, 660, 460))
        content_view.addSubview_(self.content_container)
        
        # Create content views
        self.content_views = [
            self.createGeneralView(),
            self.createPromptsView(),
            self.createAdvancedView()
        ]
        
        # Show general view initially and set button states
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
        
        # Update button states to show which is active
        for i, button in enumerate(self.section_buttons):
            if i == section:
                # Active button styling
                button.setState_(1)  # Pressed/selected state
                button.setBezelStyle_(NSBezelStyleRounded)
            else:
                # Inactive button styling  
                button.setState_(0)  # Normal state
                button.setBezelStyle_(NSBezelStyleRounded)
        
        # Remove current content
        for subview in self.content_container.subviews():
            subview.removeFromSuperview()
        
        # Add new content
        view = self.content_views[section]
        view.setFrame_(NSMakeRect(0, 0, 660, 460))
        self.content_container.addSubview_(view)
        
        self.current_section = section
        
        # Set focus to appropriate field based on section
        if section == 0 and hasattr(self, 'api_key_field'):  # General section
            # Delay focus setting to ensure view is fully displayed
            def set_focus():
                print("Debug - Setting focus to API key field")
                self.window().makeFirstResponder_(self.api_key_field)
            
            # Use performSelector to delay the focus setting
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.1, self, "setApiKeyFocus:", None, False
            )
    
    def setApiKeyFocus_(self, timer):
        """Set focus to API key field (called by timer)"""
        if hasattr(self, 'api_key_field') and self.current_section == 0:
            print("Debug - Timer: Setting focus to API key field")
            success = self.window().makeFirstResponder_(self.api_key_field)
            print(f"Debug - Focus set result: {success}")
    
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
        
        # API Key section (most important for first-time users)
        api_key_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 380, 120, 25))
        api_key_label.setStringValue_("OpenAI API Key:")
        api_key_label.setBezeled_(False)
        api_key_label.setDrawsBackground_(False)
        api_key_label.setEditable_(False)
        view.addSubview_(api_key_label)
        
        # Use custom PasteableTextField to explicitly support paste operations
        self.api_key_field = PasteableTextField.alloc().initWithFrame_(NSMakeRect(150, 380, 400, 25))
        self.api_key_field.setStringValue_(self.settings_manager.get("openai_api_key", ""))
        self.api_key_field.setPlaceholderString_("sk-...")
        # Ensure it can become first responder
        self.api_key_field.setEnabled_(True)
        self.api_key_field.setEditable_(True)
        view.addSubview_(self.api_key_field)
        
        # API key help text
        api_help = NSTextField.alloc().initWithFrame_(NSMakeRect(150, 355, 400, 20))
        api_help.setStringValue_("Get your API key from https://platform.openai.com/api-keys")
        api_help.setBezeled_(False)
        api_help.setDrawsBackground_(False)
        api_help.setEditable_(False)
        api_help.setTextColor_(NSColor.secondaryLabelColor())
        api_help.setFont_(NSFont.systemFontOfSize_(11))
        view.addSubview_(api_help)
        
        # Hotkey section
        hotkey_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 320, 120, 25))
        hotkey_label.setStringValue_("Global Hotkey:")
        hotkey_label.setBezeled_(False)
        hotkey_label.setDrawsBackground_(False)
        hotkey_label.setEditable_(False)
        view.addSubview_(hotkey_label)
        
        # Hotkey field
        self.hotkey_field = HotkeyField.alloc().initWithFrame_manager_(
            NSMakeRect(150, 320, 200, 25), self.settings_manager
        )
        self.hotkey_field.setStringValue_(self.settings_manager.get("hotkey", "cmd+shift+r"))
        self.hotkey_field.reset_callback = self.updateResetButton
        view.addSubview_(self.hotkey_field)
        
        # Reset button - always create it, visibility controlled by updateResetButton
        self.reset_button = NSButton.alloc().initWithFrame_(NSMakeRect(360, 320, 60, 25))
        self.reset_button.setTitle_("Reset")
        self.reset_button.setTarget_(self)
        self.reset_button.setAction_("resetHotkey:")
        self.reset_button.setButtonType_(NSButtonTypeMomentaryPushIn)
        view.addSubview_(self.reset_button)
        
        # Conflict warning
        self.conflict_label = NSTextField.alloc().initWithFrame_(NSMakeRect(150, 295, 400, 20))
        self.conflict_label.setBezeled_(False)
        self.conflict_label.setDrawsBackground_(False)
        self.conflict_label.setEditable_(False)
        self.conflict_label.setTextColor_(NSColor.systemRedColor())
        self.conflict_label.setFont_(NSFont.systemFontOfSize_(11))
        view.addSubview_(self.conflict_label)
        
        # Options
        self.notifications_checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(20, 250, 400, 25))
        self.notifications_checkbox.setButtonType_(NSButtonTypeSwitch)
        self.notifications_checkbox.setTitle_("Show success/error notifications")
        self.notifications_checkbox.setState_(1 if self.settings_manager.get("show_notifications", False) else 0)
        view.addSubview_(self.notifications_checkbox)
        
        self.startup_checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(20, 220, 400, 25))
        self.startup_checkbox.setButtonType_(NSButtonTypeSwitch)
        self.startup_checkbox.setTitle_("Launch Potter at startup")
        self.startup_checkbox.setState_(1 if self.settings_manager.get("launch_at_startup", False) else 0)
        view.addSubview_(self.startup_checkbox)
        
        # Permissions section
        permissions_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 150, 620, 25))
        permissions_label.setStringValue_("System Permissions:")
        permissions_label.setFont_(NSFont.boldSystemFontOfSize_(14))
        permissions_label.setBezeled_(False)
        permissions_label.setDrawsBackground_(False)
        permissions_label.setEditable_(False)
        view.addSubview_(permissions_label)
        
        # Check permissions from the main app if available
        permissions_status = self.get_permissions_status()
        
        # Determine what entity has permission (Python vs Potter app)
        import sys
        permission_entity = "Potter.app" if getattr(sys, 'frozen', False) else "Python"
        
        # Accessibility permission status
        self.accessibility_status = NSTextField.alloc().initWithFrame_(NSMakeRect(40, 125, 480, 20))
        if permissions_status.get('accessibility', False):
            accessibility_text = f"Accessibility (Global Hotkeys): ✅ Granted to {permission_entity}"
        else:
            accessibility_text = f"Accessibility (Global Hotkeys): ❌ Required for {permission_entity}"
        self.accessibility_status.setStringValue_(accessibility_text)
        self.accessibility_status.setBezeled_(False)
        self.accessibility_status.setDrawsBackground_(False)
        self.accessibility_status.setEditable_(False)
        if not permissions_status.get('accessibility', False):
            self.accessibility_status.setTextColor_(NSColor.systemRedColor())
        else:
            self.accessibility_status.setTextColor_(NSColor.systemGreenColor())
        view.addSubview_(self.accessibility_status)
        
        # Accessibility permission button
        self.accessibility_btn = NSButton.alloc().initWithFrame_(NSMakeRect(530, 125, 120, 20))
        if not permissions_status.get('accessibility', False):
            self.accessibility_btn.setTitle_("Grant Permission")
            self.accessibility_btn.setTarget_(self)
            self.accessibility_btn.setAction_("openAccessibilitySettings:")
        else:
            self.accessibility_btn.setTitle_("✅ Granted")
            self.accessibility_btn.setEnabled_(False)
        self.accessibility_btn.setBezelStyle_(NSBezelStyleRounded)
        self.accessibility_btn.setFont_(NSFont.systemFontOfSize_(11))
        view.addSubview_(self.accessibility_btn)
        
        # General refresh permissions button
        self.refresh_permissions_btn = NSButton.alloc().initWithFrame_(NSMakeRect(40, 100, 120, 25))
        self.refresh_permissions_btn.setTitle_("Refresh Status")
        self.refresh_permissions_btn.setTarget_(self)
        self.refresh_permissions_btn.setAction_("refreshPermissions:")
        self.refresh_permissions_btn.setBezelStyle_(NSBezelStyleRounded)
        view.addSubview_(self.refresh_permissions_btn)
        
        # Update UI - this will set initial reset button visibility and check conflicts
        self.updateResetButton()
        
        return view
    
    def createPromptsView(self):
        """Create Prompts view with dynamic table"""
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
        
        # Instructions
        instructions = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 390, 620, 20))
        instructions.setStringValue_("Customize your AI prompts and output formats:")
        instructions.setFont_(NSFont.systemFontOfSize_(12))
        instructions.setBezeled_(False)
        instructions.setDrawsBackground_(False)
        instructions.setEditable_(False)
        instructions.setTextColor_(NSColor.secondaryLabelColor())
        view.addSubview_(instructions)
        
        # Create scroll view for table
        scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(20, 80, 620, 300))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setHasHorizontalScroller_(False)
        scroll_view.setBorderType_(NSBezelBorder)
        
        # Create table view
        self.prompts_table = NSTableView.alloc().initWithFrame_(scroll_view.contentView().bounds())
        self.prompts_table.setUsesAlternatingRowBackgroundColors_(True)
        self.prompts_table.setRowSizeStyle_(NSTableViewRowSizeStyleMedium)
        self.prompts_table.setGridStyleMask_(NSTableViewSolidHorizontalGridLineMask)
        
        # Create columns
        # Name column
        name_column = NSTableColumn.alloc().initWithIdentifier_("name")
        name_column.headerCell().setStringValue_("Name")
        name_column.setWidth_(120)
        name_column.setMinWidth_(80)
        name_column.setMaxWidth_(150)
        name_column.setEditable_(True)
        self.prompts_table.addTableColumn_(name_column)
        
        # Prompt text column
        text_column = NSTableColumn.alloc().initWithIdentifier_("text")
        text_column.headerCell().setStringValue_("Prompt Text")
        text_column.setWidth_(380)
        text_column.setMinWidth_(200)
        text_column.setEditable_(True)
        self.prompts_table.addTableColumn_(text_column)
        
        # Output format column
        format_column = NSTableColumn.alloc().initWithIdentifier_("format")
        format_column.headerCell().setStringValue_("Format")
        format_column.setWidth_(100)
        format_column.setMinWidth_(80)
        format_column.setMaxWidth_(120)
        format_column.setEditable_(True)
        self.prompts_table.addTableColumn_(format_column)
        
        # Get prompts and ensure correct format
        prompts = self.settings_manager.get("prompts", [])
        print(f"Debug - prompts in table: {prompts}")
        
        # Store prompts data - make a copy to avoid reference issues
        self.prompts_data = list(prompts) if prompts else []
        
        # Set up table data source
        self.prompts_table.setDataSource_(self)
        self.prompts_table.setDelegate_(self)
        
        # Force reload to show data
        self.prompts_table.reloadData()
        
        scroll_view.setDocumentView_(self.prompts_table)
        view.addSubview_(scroll_view)
        
        # Add button
        add_btn = NSButton.alloc().initWithFrame_(NSMakeRect(20, 40, 80, 30))
        add_btn.setTitle_("Add")
        add_btn.setTarget_(self)
        add_btn.setAction_("addPrompt:")
        add_btn.setBezelStyle_(NSBezelStyleRounded)
        view.addSubview_(add_btn)
        
        # Remove button
        remove_btn = NSButton.alloc().initWithFrame_(NSMakeRect(110, 40, 80, 30))
        remove_btn.setTitle_("Remove")
        remove_btn.setTarget_(self)
        remove_btn.setAction_("removePrompt:")
        remove_btn.setBezelStyle_(NSBezelStyleRounded)
        view.addSubview_(remove_btn)
        
        # Edit button
        edit_btn = NSButton.alloc().initWithFrame_(NSMakeRect(200, 40, 80, 30))
        edit_btn.setTitle_("Edit")
        edit_btn.setTarget_(self)
        edit_btn.setAction_("editPrompt:")
        edit_btn.setBezelStyle_(NSBezelStyleRounded)
        view.addSubview_(edit_btn)
        
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
    
    def get_permissions_status(self):
        """Get current permissions status from the main app"""
        try:
            # Try to import from potter module to check permissions
            potter_module = sys.modules.get('__main__')
            if potter_module and hasattr(potter_module, 'service'):
                return potter_module.service.get_permission_status()
            
            # Fallback: try to check permissions directly using the same improved method as main app
            try:
                # Use the proper accessibility API to check permissions (same as main app)
                from ApplicationServices import AXIsProcessTrusted
                from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
                
                # Check accessibility using the same robust method as main app
                accessibility = False
                try:
                    is_trusted = AXIsProcessTrusted()
                    print(f"Debug - AXIsProcessTrusted() returned: {is_trusted}")
                    
                    # Force a more aggressive check - try to actually use accessibility features
                    if is_trusted:
                        try:
                            # Additional verification - try to access window list which requires accessibility permission
                            window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
                            if window_list and len(window_list) > 0:
                                # Extra verification: try to access detailed window information
                                # This is more likely to fail if accessibility permission is not actually granted
                                try:
                                    # Try to access window owner information - this typically requires accessibility permission
                                    accessible_count = 0
                                    for window in window_list[:3]:  # Check first 3 windows
                                        owner_name = window.get('kCGWindowOwnerName', '')
                                        window_name = window.get('kCGWindowName', '')
                                        if owner_name or window_name:
                                            print(f"Debug - Window access verified: owner={owner_name}, name={window_name}")
                                            accessible_count += 1
                                    
                                    if accessible_count > 0:
                                        print(f"Debug - Window list verification successful: {len(window_list)} windows, {accessible_count} accessible")
                                        accessibility = True
                                    else:
                                        print("Debug - Could not access window details despite window list being available")
                                        accessibility = False
                                except Exception as e:
                                    print(f"Debug - Failed to access window details: {e}")
                                    accessibility = False
                            else:
                                print("Debug - AXIsProcessTrusted=True but window list is empty - permission might not be fully granted yet")
                                accessibility = False
                        except Exception as e:
                            print(f"Debug - Window list verification failed despite AXIsProcessTrusted=True: {e}")
                            accessibility = False
                    else:
                        print("Debug - AXIsProcessTrusted() returned False - no accessibility permission")
                        accessibility = False
                except Exception as e:
                    print(f"Debug - Accessibility permission check failed: {e}")
                    accessibility = False
                
                return {
                    "accessibility": accessibility,
                    "macos_available": True
                }
            except ImportError as e:
                print(f"Debug - ApplicationServices not available, falling back to window list only: {e}")
                # Fallback method - try to get window list directly (but be more strict)
                try:
                    from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
                    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
                    if window_list and len(window_list) > 5:  # Require more windows to reduce false positives
                        # Try to access window details to verify real accessibility
                        accessible_windows = 0
                        for window in window_list[:5]:
                            owner_name = window.get('kCGWindowOwnerName', '')
                            if owner_name:
                                accessible_windows += 1
                        
                        accessibility = accessible_windows >= 2  # Require at least 2 accessible windows
                        print(f"Debug - Fallback window list check: {accessibility} (accessible windows: {accessible_windows})")
                        return {
                            "accessibility": accessibility,
                            "macos_available": True
                        }
                    else:
                        print("Debug - Fallback window list check: insufficient windows")
                        return {
                            "accessibility": False,
                            "macos_available": True
                        }
                except Exception as e2:
                    print(f"Debug - Fallback window list check failed: {e2}")
                    pass
        except Exception as e:
            print(f"Debug - Error checking permissions: {e}")
        
        # Default fallback
        return {
            "accessibility": False,
            "macos_available": False
        }
    
    def openAccessibilitySettings_(self, sender):
        """Open System Settings to Accessibility"""
        try:
            # For macOS 13+ (Ventura and later), it's System Settings
            subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'], check=False)
        except Exception as e:
            print(f"Debug - Failed to open Accessibility Settings: {e}")
            # Fallback to general System Preferences
            try:
                subprocess.run(['open', '/System/Applications/System Preferences.app'], check=False)
            except Exception as e2:
                print(f"Debug - Failed to open System Preferences fallback: {e2}")
    
    def openSystemSettings_(self, sender):
        """Open System Settings to Privacy & Security (general)"""
        try:
            # For macOS 13+ (Ventura and later), it's System Settings
            subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'], check=False)
        except Exception as e:
            print(f"Debug - Failed to open System Settings: {e}")
            # Fallback to general System Preferences
            try:
                subprocess.run(['open', '/System/Applications/System Preferences.app'], check=False)
            except Exception as e2:
                print(f"Debug - Failed to open System Preferences fallback: {e2}")
    
    def refreshPermissions_(self, sender):
        """Refresh permission status display"""
        print("Debug - Refreshing permissions...")
        
        # Get updated permissions
        permissions_status = self.get_permissions_status()
        
        # Determine what entity has permission (Python vs Potter app)
        import sys
        permission_entity = "Potter.app" if getattr(sys, 'frozen', False) else "Python"
        
        # Update accessibility status
        if permissions_status.get('accessibility', False):
            accessibility_text = f"Accessibility (Global Hotkeys): ✅ Granted to {permission_entity}"
        else:
            accessibility_text = f"Accessibility (Global Hotkeys): ❌ Required for {permission_entity}"
        self.accessibility_status.setStringValue_(accessibility_text)
        if not permissions_status.get('accessibility', False):
            self.accessibility_status.setTextColor_(NSColor.systemRedColor())
            self.accessibility_btn.setTitle_("Grant Permission")
            self.accessibility_btn.setEnabled_(True)
            self.accessibility_btn.setTarget_(self)
            self.accessibility_btn.setAction_("openAccessibilitySettings:")
        else:
            self.accessibility_status.setTextColor_(NSColor.systemGreenColor())
            self.accessibility_btn.setTitle_("✅ Granted")
            self.accessibility_btn.setEnabled_(False)
        
        # Also refresh the main app's tray icon if available
        try:
            potter_module = sys.modules.get('__main__')
            if potter_module and hasattr(potter_module, 'service') and hasattr(potter_module.service, 'refresh_tray_icon'):
                potter_module.service.refresh_tray_icon()
                print("Debug - Triggered tray icon refresh")
        except Exception as e:
            print(f"Debug - Could not refresh tray icon: {e}")
        
        print("Debug - Permissions status refreshed")
    
    # NSTableViewDataSource methods for prompts table
    def numberOfRowsInTableView_(self, table_view):
        """Return number of rows"""
        if hasattr(self, 'prompts_table') and table_view == self.prompts_table:
            count = len(self.prompts_data) if hasattr(self, 'prompts_data') and self.prompts_data else 0
            print(f"Debug - numberOfRows returning: {count}")
            return count
        return 0
    
    def tableView_objectValueForTableColumn_row_(self, table_view, column, row):
        """Return value for cell"""
        if not hasattr(self, 'prompts_table') or table_view != self.prompts_table:
            return ""
        
        if not hasattr(self, 'prompts_data') or not self.prompts_data:
            return ""
        
        if row >= len(self.prompts_data):
            print(f"Debug - row {row} >= len {len(self.prompts_data)}")
            return ""
        
        prompt = self.prompts_data[row]
        identifier = str(column.identifier())
        
        print(f"Debug - getting value for row {row}, col {identifier}, prompt: {prompt}")
        
        if identifier == "name":
            return prompt.get("name", "")
        elif identifier == "text":
            return prompt.get("text", "")
        elif identifier == "format":
            return prompt.get("output_format", "text")
        
        return ""
    
    def tableView_setObjectValue_forTableColumn_row_(self, table_view, value, column, row):
        """Set value for cell"""
        if not hasattr(self, 'prompts_table') or table_view != self.prompts_table:
            return
        
        if not hasattr(self, 'prompts_data') or not self.prompts_data:
            return
        
        if row >= len(self.prompts_data):
            return
        
        prompt = self.prompts_data[row]
        identifier = str(column.identifier())
        
        print(f"Debug - setting value for row {row}, col {identifier}, value: {value}")
        
        if identifier == "name":
            prompt["name"] = str(value)
        elif identifier == "text":
            prompt["text"] = str(value)
        elif identifier == "format":
            # Validate format
            format_val = str(value)
            if format_val in ["text", "images", "pdf"]:  # video disabled
                prompt["output_format"] = format_val
    
    def save_(self, sender):
        """Save settings"""
        print("Debug - Save button clicked")
        
        try:
            settings = self.settings_manager.settings.copy()
            print("Debug - Copied existing settings")
            
            # General settings with validation
            if hasattr(self, 'api_key_field') and self.api_key_field:
                api_key = str(self.api_key_field.stringValue()).strip()
                settings["openai_api_key"] = api_key
                print(f"Debug - API key saved: {'sk-...' if api_key.startswith('sk-') else f'Invalid format: {api_key[:10]}...'}")
            
            if hasattr(self, 'hotkey_field') and self.hotkey_field:
                hotkey = str(self.hotkey_field.stringValue()).strip()
                if hotkey:  # Only save if not empty
                    settings["hotkey"] = hotkey
                    print(f"Debug - Hotkey saved: {hotkey}")
            
            if hasattr(self, 'notifications_checkbox') and self.notifications_checkbox:
                settings["show_notifications"] = bool(self.notifications_checkbox.state())
                print(f"Debug - Notifications: {settings['show_notifications']}")
            
            if hasattr(self, 'startup_checkbox') and self.startup_checkbox:
                settings["launch_at_startup"] = bool(self.startup_checkbox.state())
                print(f"Debug - Launch at startup: {settings['launch_at_startup']}")
            
            # Prompts - get from table data
            if hasattr(self, 'prompts_data') and self.prompts_data:
                settings["prompts"] = self.prompts_data
                print(f"Debug - Prompts saved: {len(self.prompts_data)} items")
            
            # Advanced settings with validation
            if hasattr(self, 'model_popup') and self.model_popup:
                model = str(self.model_popup.titleOfSelectedItem())
                if model:  # Only save if not empty
                    settings["model"] = model
                    print(f"Debug - Model saved: {model}")
            
            if hasattr(self, 'tokens_field') and self.tokens_field:
                try:
                    tokens = int(self.tokens_field.stringValue())
                    if tokens > 0:  # Validate positive number
                        settings["max_tokens"] = tokens
                        print(f"Debug - Max tokens: {tokens}")
                except (ValueError, TypeError):
                    settings["max_tokens"] = 1000  # Default fallback
                    print("Debug - Invalid max_tokens, using default 1000")
            
            if hasattr(self, 'temp_field') and self.temp_field:
                try:
                    temp = float(self.temp_field.stringValue())
                    if 0.0 <= temp <= 2.0:  # Validate range
                        settings["temperature"] = temp
                        print(f"Debug - Temperature: {temp}")
                except (ValueError, TypeError):
                    settings["temperature"] = 0.7  # Default fallback
                    print("Debug - Invalid temperature, using default 0.7")
            
            # Attempt to save
            print("Debug - Attempting to save settings...")
            save_success = self.settings_manager.save_settings(settings)
            print(f"Debug - Save result: {save_success}")
            
            if save_success:
                print("Debug - Settings saved successfully")
                
                # Call callback if provided
                callback_success = True
                if hasattr(self, 'on_settings_changed') and self.on_settings_changed:
                    try:
                        print("Debug - Calling settings change callback...")
                        self.on_settings_changed(settings)
                        print("Debug - Settings change callback executed successfully")
                    except Exception as e:
                        print(f"Debug - Callback error (non-critical): {e}")
                        callback_success = False
                
                # Close the window - force close regardless of callback success
                try:
                    print("Debug - Attempting to close settings window...")
                    window = self.window()
                    if window:
                        print("Debug - Window exists, about to call close()...")
                        
                        # Before closing, make sure NSApplication won't terminate
                        try:
                            from AppKit import NSApplication
                            app = NSApplication.sharedApplication()
                            print(f"Debug - NSApp activation policy before close: {app.activationPolicy()}")
                            print(f"Debug - NSApp delegate before close: {app.delegate()}")
                            
                            # Ensure delegate is still set and working
                            if app.delegate():
                                print("Debug - NSApplication delegate is set")
                            else:
                                print("Debug - WARNING: NSApplication delegate is None!")
                                
                        except Exception as e:
                            print(f"Debug - Error checking NSApplication state: {e}")
                        
                        print("Debug - Calling window.close()...")
                        window.close()
                        print("Debug - Window.close() called successfully")
                    else:
                        print("Debug - Warning: Window is None")
                except Exception as e:
                    print(f"Debug - Error closing window: {e}")
                    # Force close by attempting alternative methods
                    try:
                        if hasattr(self, 'window'):
                            self.close()
                        print("Debug - Alternative close method attempted")
                    except Exception as e2:
                        print(f"Debug - Alternative close failed: {e2}")
                
                print("Debug - Save process completed")
            else:
                print("Debug - Save failed, showing error dialog")
                self.show_save_error("Failed to save settings to file. Please check file permissions.")
                
        except Exception as e:
            print(f"Debug - Critical save error: {e}")
            import traceback
            traceback.print_exc()
            self.show_save_error(f"Unexpected error saving settings: {str(e)}")
    
    def show_save_error(self, message):
        """Show save error dialog"""
        print(f"Debug - Showing save error: {message}")
        try:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Save Failed")
            alert.setInformativeText_(message)
            alert.setAlertStyle_(NSAlertStyleCritical)
            alert.runModal()
        except Exception as e:
            print(f"Debug - Error showing alert: {e}")
    
    def cancel_(self, sender):
        """Cancel changes"""
        self.window().close()
    
    def windowShouldClose_(self, window):
        """Handle window close events"""
        print("Debug - Settings window should close called")
        return True
    
    def windowWillClose_(self, notification):
        """Handle window will close notification"""
        print("Debug - Settings window will close")
        # Make sure this doesn't trigger app termination
        try:
            from AppKit import NSApplication
            app = NSApplication.sharedApplication()
            # Ensure the app doesn't quit when this window closes
            if hasattr(app, 'setActivationPolicy_'):
                app.setActivationPolicy_(2)  # Keep as accessory app
        except Exception as e:
            print(f"Debug - Error in windowWillClose: {e}")
    
    def cancelOperation_(self, sender):
        """Handle ESC key press to close dialog"""
        print("Debug - ESC key pressed, closing dialog")
        self.window().close()
    
    def keyDown_(self, event):
        """Handle key events for the window"""
        if event.keyCode() == 53:  # ESC key
            print("Debug - ESC key detected")
            self.window().close()
        else:
            # Pass other keys to superclass
            objc.super(SettingsWindow, self).keyDown_(event)

    def addPrompt_(self, sender):
        """Add a new prompt using dialog"""
        def on_result(result):
            if result:  # User didn't cancel
                # Check for duplicate names
                existing_names = [p.get("name", "") for p in self.prompts_data]
                if result["name"] in existing_names:
                    alert = NSAlert.alloc().init()
                    alert.setMessageText_("Duplicate Name")
                    alert.setInformativeText_(f"A prompt named '{result['name']}' already exists.")
                    alert.setAlertStyle_(NSAlertStyleWarning)
                    alert.runModal()
                    return
                
                # Add the new prompt
                self.prompts_data.append(result)
                self.prompts_table.reloadData()
                
                # Select the new row
                new_index = len(self.prompts_data) - 1
                self.prompts_table.selectRowIndexes_byExtendingSelection_(
                    NSIndexSet.indexSetWithIndex_(new_index), False
                )
                self.prompts_table.scrollRowToVisible_(new_index)
        
        # Create and show dialog
        dialog = PromptDialog.alloc().initWithPrompt_isEdit_(None, False)
        dialog.callback = on_result
        dialog.showWindow_(self)
    
    def removePrompt_(self, sender):
        """Remove selected prompt"""
        if not hasattr(self, 'prompts_data') or not self.prompts_data:
            return
        
        selected_row = self.prompts_table.selectedRow()
        if selected_row < 0:
            # No selection, show alert
            alert = NSAlert.alloc().init()
            alert.setMessageText_("No Selection")
            alert.setInformativeText_("Please select a prompt to remove.")
            alert.setAlertStyle_(NSAlertStyleInformational)
            alert.runModal()
            return
        
        # Get prompt name for confirmation
        prompt_name = self.prompts_data[selected_row].get("name", "this prompt")
        
        # Confirm deletion
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Delete Prompt")
        alert.setInformativeText_(f"Are you sure you want to delete '{prompt_name}'?")
        alert.setAlertStyle_(NSAlertStyleWarning)
        alert.addButtonWithTitle_("Delete")
        alert.addButtonWithTitle_("Cancel")
        
        response = alert.runModal()
        if response == NSAlertFirstButtonReturn:  # Delete
            self.prompts_data.pop(selected_row)
            self.prompts_table.reloadData()
    
    def editPrompt_(self, sender):
        """Edit selected prompt using dialog"""
        if not hasattr(self, 'prompts_data') or not self.prompts_data:
            return
        
        selected_row = self.prompts_table.selectedRow()
        if selected_row < 0:
            # No selection, show alert
            alert = NSAlert.alloc().init()
            alert.setMessageText_("No Selection")
            alert.setInformativeText_("Please select a prompt to edit.")
            alert.setAlertStyle_(NSAlertStyleInformational)
            alert.runModal()
            return
        
        # Get current prompt
        current_prompt = self.prompts_data[selected_row]
        original_name = current_prompt["name"]
        
        def on_result(result):
            if result:  # User didn't cancel
                # Check for duplicate names (excluding current name)
                existing_names = [p.get("name", "") for i, p in enumerate(self.prompts_data) if i != selected_row]
                if result["name"] in existing_names:
                    alert = NSAlert.alloc().init()
                    alert.setMessageText_("Duplicate Name")
                    alert.setInformativeText_(f"A prompt named '{result['name']}' already exists.")
                    alert.setAlertStyle_(NSAlertStyleWarning)
                    alert.runModal()
                    return
                
                # Update the prompt
                self.prompts_data[selected_row] = result
                self.prompts_table.reloadData()
                
                # Keep selection
                self.prompts_table.selectRowIndexes_byExtendingSelection_(
                    NSIndexSet.indexSetWithIndex_(selected_row), False
                )
        
        # Create and show dialog
        dialog = PromptDialog.alloc().initWithPrompt_isEdit_(current_prompt, True)
        dialog.callback = on_result
        dialog.showWindow_(self)


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