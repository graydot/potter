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
from UserNotifications import *


class SettingsManager:
    """Simple settings manager"""
    
    def __init__(self, settings_file="settings.json"):
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
            "auto_paste": True,
            "show_notifications": False,
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
            self.show_notification("Rephrasely", message, is_error=False)
    
    def show_error(self, error_message):
        """Show error notification if enabled"""
        if self.get("show_notifications", False):
            self.show_notification("Rephrasely Error", error_message, is_error=True)


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
        
        window.setTitle_("Rephrasely Settings")
        window.setLevel_(NSNormalWindowLevel)
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
        self.notifications_checkbox.setState_(1 if self.settings_manager.get("show_notifications", False) else 0)
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
        
        # Prompts - get from table data
        if hasattr(self, 'prompts_data') and self.prompts_data:
            settings["prompts"] = self.prompts_data
        
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