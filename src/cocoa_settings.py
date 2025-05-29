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
                    "name": "summarize", 
                    "text": "Please provide a concise summary of the following text. Focus on the key points and main ideas. Keep it brief but comprehensive, capturing the essential information in a clear and organized way."
                },
                {
                    "name": "formal",
                    "text": "Please rewrite the following text in a formal, professional tone. Use proper business language and structure. Ensure the tone is respectful, authoritative, and appropriate for professional communication."
                },
                {
                    "name": "casual",
                    "text": "Please rewrite the following text in a casual, relaxed tone. Make it sound conversational and approachable. Use everyday language while maintaining clarity and keeping the core message intact."
                },
                {
                    "name": "friendly",
                    "text": "Please rewrite the following text in a warm, friendly tone. Make it sound welcoming and personable. Add warmth and approachability while keeping the message clear and engaging."
                },
                {
                    "name": "polish",
                    "text": "Please polish the following text by fixing any grammatical issues, typos, or awkward phrasing. Make it sound natural and human while keeping it direct and clear. Double-check that the tone is appropriate and not offensive, but maintain the original intent and directness."
                }
            ],
            "hotkey": "cmd+shift+a",
            "model": "gpt-3.5-turbo",
            "max_tokens": 1000,
            "temperature": 0.7,
            "show_notifications": True,
            "launch_at_startup": False,
            "openai_api_key": ""
        }
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file, create default if not exists"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    settings = self.default_settings.copy()
                    
                    # Update settings with loaded values
                    for key, value in loaded.items():
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
        
        self.prompt = prompt or {"name": "", "text": ""}
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
        try:
            name = str(self.name_field.stringValue()).strip()
            text = str(self.prompt_text_view.string()).strip()
            
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
                "text": text
            }
            
            # Call callback if set, but ensure window closes even if callback fails
            if self.callback:
                try:
                    self.callback(self.result)
                except Exception as e:
                    print(f"Debug - Callback error in save: {e}")
            
        except Exception as e:
            print(f"Debug - Error in save_: {e}")
        finally:
            # Always close the window
            try:
                self.window().close()
            except Exception as e:
                print(f"Debug - Error closing window in save: {e}")
    
    def cancel_(self, sender):
        """Cancel the dialog"""
        try:
            self.result = None
            if self.callback:
                try:
                    self.callback(None)
                except Exception as e:
                    print(f"Debug - Callback error in cancel: {e}")
        except Exception as e:
            print(f"Debug - Error in cancel_: {e}")
        finally:
            # Always close the window
            try:
                self.window().close()
            except Exception as e:
                print(f"Debug - Error closing window in cancel: {e}")
    
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


# Helper functions for creating UI elements (outside class to avoid PyObjC conflicts)
def create_section_header(title, y_position):
    """Create a modern section header"""
    header = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_position, 620, 35))
    header.setStringValue_(title)
    header.setFont_(NSFont.boldSystemFontOfSize_(24))
    header.setBezeled_(False)
    header.setDrawsBackground_(False)
    header.setEditable_(False)
    header.setTextColor_(NSColor.labelColor())
    return header

def create_section_separator(y_position):
    """Create a visual separator"""
    separator = NSView.alloc().initWithFrame_(NSMakeRect(40, y_position, 620, 1))
    separator.setWantsLayer_(True)
    separator.layer().setBackgroundColor_(NSColor.separatorColor().CGColor())
    return separator

def create_modern_switch(frame, title, initial_state=False):
    """Create a modern switch control - returns (container, switch)"""
    container = NSView.alloc().initWithFrame_(frame)
    
    # Label
    label = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 5, frame.size.width - 60, 20))
    label.setStringValue_(title)
    label.setBezeled_(False)
    label.setDrawsBackground_(False)
    label.setEditable_(False)
    label.setFont_(NSFont.systemFontOfSize_(14))
    label.setTextColor_(NSColor.labelColor())
    container.addSubview_(label)
    
    # Switch (try NSSwitch first, fallback to checkbox)
    try:
        switch = NSSwitch.alloc().initWithFrame_(NSMakeRect(frame.size.width - 50, 0, 50, 30))
        switch.setState_(1 if initial_state else 0)
    except Exception:
        # Fallback for older macOS
        switch = NSButton.alloc().initWithFrame_(NSMakeRect(frame.size.width - 50, 0, 50, 30))
        switch.setButtonType_(NSButtonTypeSwitch)
        switch.setState_(1 if initial_state else 0)
    
    container.addSubview_(switch)
    
    # Return both container and switch
    return container, switch

def create_sidebar_button(item, y_position):
    """Create a modern sidebar button with icon"""
    button = NSButton.alloc().initWithFrame_(NSMakeRect(10, y_position, 180, 40))
    button.setTitle_(item["title"])
    button.setTag_(item["tag"])
    button.setButtonType_(NSButtonTypePushOnPushOff)
    button.setBordered_(False)
    button.setAlignment_(NSTextAlignmentLeft)
    
    # Set font and styling
    button.setFont_(NSFont.systemFontOfSize_(14))
    
    # Try to set SF Symbol icon (fallback gracefully if not available)
    try:
        if hasattr(NSImage, 'imageWithSystemSymbolName_accessibilityDescription_'):
            icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
                item["icon"], item["title"]
            )
            button.setImage_(icon)
            button.setImagePosition_(NSImageLeft)
    except:
        # Fallback for older macOS versions
        pass
    
    return button


class SettingsWindow(NSWindowController):
    """Modern settings window with sidebar navigation"""
    
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
        self.prompts_data = []
        self.sidebar_items = []
        self.split_view = None
        self.sidebar_table = None
        self.content_container = None
        
        self.createWindow()
        return self
    
    def createWindow(self):
        """Create the modern window with sidebar"""
        # Create larger window for modern layout
        frame = NSMakeRect(100, 100, 900, 650)
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable,
            NSBackingStoreBuffered,
            False
        )
        
        window.setTitle_("Potter Settings")
        window.setLevel_(NSNormalWindowLevel)
        window.setMinSize_(NSMakeSize(800, 600))
        window.setDelegate_(self)
        
        # Create split view
        self.split_view = NSSplitView.alloc().initWithFrame_(window.contentView().bounds())
        self.split_view.setVertical_(True)
        self.split_view.setDividerStyle_(NSSplitViewDividerStyleThin)
        self.split_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        
        # Create sidebar
        self.createSidebar()
        
        # Create content area
        self.createContentArea()
        
        # Add to split view
        self.split_view.addSubview_(self.sidebar_container)
        self.split_view.addSubview_(self.content_scroll_view)
        
        # Set split view positions
        self.split_view.setPosition_ofDividerAtIndex_(200, 0)
        
        window.contentView().addSubview_(self.split_view)
        
        # Create content views
        self.content_views = [
            self.createGeneralView(),
            self.createPromptsView(), 
            self.createAdvancedView(),
            self.createLogsView()
        ]
        
        # Show initial section
        self.showSection_(0)
        
        self.setWindow_(window)
        
        # Set default button now that window is available
        if hasattr(self, 'save_button'):
            try:
                self.window().setDefaultButtonCell_(self.save_button.cell())
            except Exception as e:
                print(f"Warning: Could not set default button: {e}")
    
    def createSidebar(self):
        """Create modern sidebar with icons"""
        # Sidebar container
        self.sidebar_container = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 200, 650))
        self.sidebar_container.setAutoresizingMask_(NSViewHeightSizable)
        
        # Sidebar background
        self.sidebar_container.setWantsLayer_(True)
        if hasattr(NSColor, 'controlBackgroundColor'):
            self.sidebar_container.layer().setBackgroundColor_(NSColor.controlBackgroundColor().CGColor())
        else:
            self.sidebar_container.layer().setBackgroundColor_(NSColor.windowBackgroundColor().CGColor())
        
        # Title
        title_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 600, 160, 30))
        title_label.setStringValue_("Settings")
        title_label.setFont_(NSFont.boldSystemFontOfSize_(20))
        title_label.setBezeled_(False)
        title_label.setDrawsBackground_(False)
        title_label.setEditable_(False)
        title_label.setTextColor_(NSColor.labelColor())
        self.sidebar_container.addSubview_(title_label)
        
        # Sidebar items data
        self.sidebar_items = [
            {"title": "General", "icon": "gear", "tag": 0},
            {"title": "Prompts", "icon": "text.bubble", "tag": 1}, 
            {"title": "Advanced", "icon": "slider.horizontal.3", "tag": 2},
            {"title": "Logs", "icon": "doc.text", "tag": 3}
        ]
        
        # Create sidebar buttons
        self.sidebar_buttons = []
        y_position = 540
        
        for item in self.sidebar_items:
            button = create_sidebar_button(item, y_position)
            button.setTarget_(self)
            button.setAction_("switchSection:")
            self.sidebar_buttons.append(button)
            self.sidebar_container.addSubview_(button)
            y_position -= 50
        
        # Footer with save/cancel buttons
        self.createSidebarFooter()
    
    def createSidebarFooter(self):
        """Create footer with save/cancel buttons"""
        # Separator line
        separator = NSView.alloc().initWithFrame_(NSMakeRect(20, 70, 160, 1))
        separator.setWantsLayer_(True)
        separator.layer().setBackgroundColor_(NSColor.separatorColor().CGColor())
        self.sidebar_container.addSubview_(separator)
        
        # Cancel button
        cancel_btn = NSButton.alloc().initWithFrame_(NSMakeRect(20, 20, 70, 32))
        cancel_btn.setTitle_("Cancel")
        cancel_btn.setTarget_(self)
        cancel_btn.setAction_("cancel:")
        cancel_btn.setKeyEquivalent_("\x1b")
        cancel_btn.setBezelStyle_(NSBezelStyleRounded)
        self.sidebar_container.addSubview_(cancel_btn)
        
        # Save button
        save_btn = NSButton.alloc().initWithFrame_(NSMakeRect(100, 20, 70, 32))
        save_btn.setTitle_("Save")
        save_btn.setTarget_(self)
        save_btn.setAction_("save:")
        save_btn.setKeyEquivalent_("\r")
        save_btn.setBezelStyle_(NSBezelStyleRounded)
        save_btn.setButtonType_(NSButtonTypeMomentaryPushIn)
        
        # Make save button blue (primary)
        try:
            save_btn.setControlTint_(NSBlueControlTint)
        except:
            pass
        
        self.sidebar_container.addSubview_(save_btn)
        
        # Store reference to save button for later default button setup
        self.save_button = save_btn
    
    def createContentArea(self):
        """Create scrollable content area"""
        # Scroll view for content
        self.content_scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(200, 0, 700, 650))
        self.content_scroll_view.setHasVerticalScroller_(True)
        self.content_scroll_view.setAutohidesScrollers_(True)
        self.content_scroll_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        self.content_scroll_view.setBorderType_(NSNoBorder)
        
        # Content container
        self.content_container = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 700, 650))
        self.content_scroll_view.setDocumentView_(self.content_container)
    
    def switchSection_(self, sender):
        """Switch to a different section with animation"""
        section = sender.tag()
        self.showSection_(section)
    
    def showSection_(self, section):
        """Show the specified section with modern styling"""
        if section < 0 or section >= len(self.content_views):
            return
        
        # Update sidebar button states
        for i, button in enumerate(self.sidebar_buttons):
            if i == section:
                button.setState_(1)
                try:
                    button.setControlTint_(NSBlueControlTint)
                except:
                    pass
            else:
                button.setState_(0)
                try:
                    button.setControlTint_(NSDefaultControlTint)
                except:
                    pass
        
        # Remove current content
        for subview in list(self.content_container.subviews()):
            subview.removeFromSuperview()
        
        # Add new content with proper sizing
        view = self.content_views[section]
        content_rect = self.content_container.bounds()
        view.setFrame_(content_rect)
        self.content_container.addSubview_(view)
        
        self.current_section = section
        
        # Set focus appropriately
        if section == 0 and hasattr(self, 'api_key_field'):
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.1, self, "setApiKeyFocus:", None, False
            )
    
    def setApiKeyFocus_(self, timer):
        """Set focus to API key field"""
        if hasattr(self, 'api_key_field') and self.current_section == 0:
            self.window().makeFirstResponder_(self.api_key_field)
    
    def createGeneralView(self):
        """Create modern General settings view"""
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 700, 650))
        
        y_pos = 580
        
        # Section header
        header = create_section_header("General Settings", y_pos)
        view.addSubview_(header)
        y_pos -= 50
        
        # Separator
        separator = create_section_separator(y_pos)
        view.addSubview_(separator)
        y_pos -= 40
        
        # API Key section
        api_section_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 620, 20))
        api_section_label.setStringValue_("OpenAI Configuration")
        api_section_label.setFont_(NSFont.boldSystemFontOfSize_(16))
        api_section_label.setBezeled_(False)
        api_section_label.setDrawsBackground_(False)
        api_section_label.setEditable_(False)
        api_section_label.setTextColor_(NSColor.labelColor())
        view.addSubview_(api_section_label)
        y_pos -= 35
        
        # API Key field
        api_key_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 120, 22))
        api_key_label.setStringValue_("API Key:")
        api_key_label.setBezeled_(False)
        api_key_label.setDrawsBackground_(False)
        api_key_label.setEditable_(False)
        api_key_label.setFont_(NSFont.systemFontOfSize_(14))
        view.addSubview_(api_key_label)
        
        self.api_key_field = PasteableTextField.alloc().initWithFrame_(NSMakeRect(160, y_pos, 450, 22))
        self.api_key_field.setStringValue_(self.settings_manager.get("openai_api_key", ""))
        self.api_key_field.setPlaceholderString_("sk-...")
        self.api_key_field.setFont_(NSFont.monospacedSystemFontOfSize_weight_(12, 0))
        view.addSubview_(self.api_key_field)
        y_pos -= 30
        
        # API help text
        api_help = NSTextField.alloc().initWithFrame_(NSMakeRect(160, y_pos, 450, 17))
        api_help.setStringValue_("Get your API key from https://platform.openai.com/api-keys")
        api_help.setBezeled_(False)
        api_help.setDrawsBackground_(False)
        api_help.setEditable_(False)
        api_help.setFont_(NSFont.systemFontOfSize_(11))
        api_help.setTextColor_(NSColor.secondaryLabelColor())
        view.addSubview_(api_help)
        y_pos -= 50
        
        # Hotkey section
        hotkey_section_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 620, 20))
        hotkey_section_label.setStringValue_("Hotkey Configuration")
        hotkey_section_label.setFont_(NSFont.boldSystemFontOfSize_(16))
        hotkey_section_label.setBezeled_(False)
        hotkey_section_label.setDrawsBackground_(False)
        hotkey_section_label.setEditable_(False)
        hotkey_section_label.setTextColor_(NSColor.labelColor())
        view.addSubview_(hotkey_section_label)
        y_pos -= 35
        
        # Hotkey field
        hotkey_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 120, 22))
        hotkey_label.setStringValue_("Hotkey:")
        hotkey_label.setBezeled_(False)
        hotkey_label.setDrawsBackground_(False)
        hotkey_label.setEditable_(False)
        hotkey_label.setFont_(NSFont.systemFontOfSize_(14))
        view.addSubview_(hotkey_label)
        
        self.hotkey_field = HotkeyField.alloc().initWithFrame_manager_(
            NSMakeRect(160, y_pos, 200, 22), self.settings_manager
        )
        self.hotkey_field.setStringValue_(self.settings_manager.get("hotkey", "cmd+shift+a"))
        view.addSubview_(self.hotkey_field)
        
        # Reset button
        self.reset_button = NSButton.alloc().initWithFrame_(NSMakeRect(370, y_pos, 80, 22))
        self.reset_button.setTitle_("Reset")
        self.reset_button.setTarget_(self)
        self.reset_button.setAction_("resetHotkey:")
        self.reset_button.setBezelStyle_(NSBezelStyleRounded)
        self.reset_button.setFont_(NSFont.systemFontOfSize_(12))
        view.addSubview_(self.reset_button)
        y_pos -= 25
        
        # Conflict warning
        self.conflict_label = NSTextField.alloc().initWithFrame_(NSMakeRect(160, y_pos, 450, 17))
        self.conflict_label.setStringValue_("")
        self.conflict_label.setBezeled_(False)
        self.conflict_label.setDrawsBackground_(False)
        self.conflict_label.setEditable_(False)
        self.conflict_label.setFont_(NSFont.systemFontOfSize_(11))
        self.conflict_label.setTextColor_(NSColor.systemRedColor())
        view.addSubview_(self.conflict_label)
        y_pos -= 40
        
        # Preferences section
        pref_section_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 620, 20))
        pref_section_label.setStringValue_("Preferences")
        pref_section_label.setFont_(NSFont.boldSystemFontOfSize_(16))
        pref_section_label.setBezeled_(False)
        pref_section_label.setDrawsBackground_(False)
        pref_section_label.setEditable_(False)
        pref_section_label.setTextColor_(NSColor.labelColor())
        view.addSubview_(pref_section_label)
        y_pos -= 40
        
        # Modern switches
        notifications_switch = create_modern_switch(
            NSMakeRect(40, y_pos, 620, 30),
            "Show notifications",
            self.settings_manager.get("show_notifications", True)
        )
        view.addSubview_(notifications_switch[0])
        self.notifications_switch = notifications_switch[1]
        y_pos -= 50
        
        startup_switch = create_modern_switch(
            NSMakeRect(40, y_pos, 620, 30),
            "Launch at startup",
            self.settings_manager.get("launch_at_startup", False)
        )
        view.addSubview_(startup_switch[0])
        self.startup_switch = startup_switch[1]
        
        # Set up callbacks
        self.hotkey_field.reset_callback = self.updateResetButton
        self.updateResetButton()
        self.checkConflicts()
        
        return view
    
    def createPromptsView(self):
        """Create modern Prompts settings view"""
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 700, 650))
        
        y_pos = 580
        
        # Section header
        header = create_section_header("Prompts", y_pos)
        view.addSubview_(header)
        y_pos -= 50
        
        # Separator
        separator = create_section_separator(y_pos)
        view.addSubview_(separator)
        y_pos -= 30
        
        # Description
        desc_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 620, 17))
        desc_label.setStringValue_("Customize the AI prompts used for text processing")
        desc_label.setBezeled_(False)
        desc_label.setDrawsBackground_(False)
        desc_label.setEditable_(False)
        desc_label.setFont_(NSFont.systemFontOfSize_(13))
        desc_label.setTextColor_(NSColor.secondaryLabelColor())
        view.addSubview_(desc_label)
        y_pos -= 40
        
        # Toolbar with buttons
        toolbar_container = NSView.alloc().initWithFrame_(NSMakeRect(40, y_pos, 620, 30))
        
        # Add button
        add_btn = NSButton.alloc().initWithFrame_(NSMakeRect(0, 0, 80, 30))
        add_btn.setTitle_("Add")
        add_btn.setTarget_(self)
        add_btn.setAction_("addPrompt:")
        add_btn.setBezelStyle_(NSBezelStyleRounded)
        add_btn.setFont_(NSFont.systemFontOfSize_(13))
        toolbar_container.addSubview_(add_btn)
        
        # Edit button
        edit_btn = NSButton.alloc().initWithFrame_(NSMakeRect(90, 0, 80, 30))
        edit_btn.setTitle_("Edit")
        edit_btn.setTarget_(self)
        edit_btn.setAction_("editPrompt:")
        edit_btn.setBezelStyle_(NSBezelStyleRounded)
        edit_btn.setFont_(NSFont.systemFontOfSize_(13))
        toolbar_container.addSubview_(edit_btn)
        
        # Remove button
        remove_btn = NSButton.alloc().initWithFrame_(NSMakeRect(180, 0, 80, 30))
        remove_btn.setTitle_("Remove")
        remove_btn.setTarget_(self)
        remove_btn.setAction_("removePrompt:")
        remove_btn.setBezelStyle_(NSBezelStyleRounded)
        remove_btn.setFont_(NSFont.systemFontOfSize_(13))
        toolbar_container.addSubview_(remove_btn)
        
        view.addSubview_(toolbar_container)
        y_pos -= 40
        
        # Table view container
        table_container = NSScrollView.alloc().initWithFrame_(NSMakeRect(40, 60, 620, y_pos - 60))
        table_container.setHasVerticalScroller_(True)
        table_container.setAutohidesScrollers_(True)
        table_container.setBorderType_(NSBezelBorder)
        table_container.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        
        # Create table view
        self.prompts_table = NSTableView.alloc().initWithFrame_(table_container.bounds())
        self.prompts_table.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        self.prompts_table.setDataSource_(self)
        self.prompts_table.setDelegate_(self)
        self.prompts_table.setRowHeight_(24)
        self.prompts_table.setIntercellSpacing_(NSMakeSize(3, 2))
        self.prompts_table.setUsesAlternatingRowBackgroundColors_(True)
        self.prompts_table.setSelectionHighlightStyle_(NSTableViewSelectionHighlightStyleRegular)
        
        # Add columns
        name_column = NSTableColumn.alloc().initWithIdentifier_("name")
        name_column.headerCell().setStringValue_("Name")
        name_column.setWidth_(120)
        name_column.setMinWidth_(80)
        name_column.setMaxWidth_(200)
        name_column.setResizingMask_(NSTableColumnUserResizingMask)
        self.prompts_table.addTableColumn_(name_column)
        
        text_column = NSTableColumn.alloc().initWithIdentifier_("text")
        text_column.headerCell().setStringValue_("Prompt Text")
        text_column.setWidth_(480)
        text_column.setMinWidth_(200)
        text_column.setResizingMask_(NSTableColumnAutoresizingMask | NSTableColumnUserResizingMask)
        self.prompts_table.addTableColumn_(text_column)
        
        table_container.setDocumentView_(self.prompts_table)
        view.addSubview_(table_container)
        
        # Load prompts data
        self.prompts_data = list(self.settings_manager.get("prompts", []))
        
        return view
    
    def createAdvancedView(self):
        """Create modern Advanced settings view"""
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 700, 650))
        
        y_pos = 580
        
        # Section header
        header = create_section_header("Advanced Settings", y_pos)
        view.addSubview_(header)
        y_pos -= 50
        
        # Separator
        separator = create_section_separator(y_pos)
        view.addSubview_(separator)
        y_pos -= 40
        
        # AI Model section
        model_section_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 620, 20))
        model_section_label.setStringValue_("AI Model Configuration")
        model_section_label.setFont_(NSFont.boldSystemFontOfSize_(16))
        model_section_label.setBezeled_(False)
        model_section_label.setDrawsBackground_(False)
        model_section_label.setEditable_(False)
        model_section_label.setTextColor_(NSColor.labelColor())
        view.addSubview_(model_section_label)
        y_pos -= 35
        
        # Model selection
        model_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 120, 22))
        model_label.setStringValue_("Model:")
        model_label.setBezeled_(False)
        model_label.setDrawsBackground_(False)
        model_label.setEditable_(False)
        model_label.setFont_(NSFont.systemFontOfSize_(14))
        view.addSubview_(model_label)
        
        self.model_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(160, y_pos, 200, 22))
        self.model_popup.addItemWithTitle_("gpt-3.5-turbo")
        self.model_popup.addItemWithTitle_("gpt-4")
        self.model_popup.addItemWithTitle_("gpt-4-turbo")
        self.model_popup.selectItemWithTitle_(self.settings_manager.get("model", "gpt-3.5-turbo"))
        view.addSubview_(self.model_popup)
        y_pos -= 35
        
        # Max tokens
        tokens_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 120, 22))
        tokens_label.setStringValue_("Max Tokens:")
        tokens_label.setBezeled_(False)
        tokens_label.setDrawsBackground_(False)
        tokens_label.setEditable_(False)
        tokens_label.setFont_(NSFont.systemFontOfSize_(14))
        view.addSubview_(tokens_label)
        
        self.tokens_field = NSTextField.alloc().initWithFrame_(NSMakeRect(160, y_pos, 100, 22))
        self.tokens_field.setStringValue_(str(self.settings_manager.get("max_tokens", 1000)))
        self.tokens_field.setPlaceholderString_("1000")
        view.addSubview_(self.tokens_field)
        
        tokens_help = NSTextField.alloc().initWithFrame_(NSMakeRect(270, y_pos, 300, 22))
        tokens_help.setStringValue_("Maximum response length (1-4000)")
        tokens_help.setBezeled_(False)
        tokens_help.setDrawsBackground_(False)
        tokens_help.setEditable_(False)
        tokens_help.setFont_(NSFont.systemFontOfSize_(11))
        tokens_help.setTextColor_(NSColor.secondaryLabelColor())
        view.addSubview_(tokens_help)
        y_pos -= 35
        
        # Temperature
        temp_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 120, 22))
        temp_label.setStringValue_("Temperature:")
        temp_label.setBezeled_(False)
        temp_label.setDrawsBackground_(False)
        temp_label.setEditable_(False)
        temp_label.setFont_(NSFont.systemFontOfSize_(14))
        view.addSubview_(temp_label)
        
        self.temp_field = NSTextField.alloc().initWithFrame_(NSMakeRect(160, y_pos, 100, 22))
        self.temp_field.setStringValue_(str(self.settings_manager.get("temperature", 0.7)))
        self.temp_field.setPlaceholderString_("0.7")
        view.addSubview_(self.temp_field)
        
        temp_help = NSTextField.alloc().initWithFrame_(NSMakeRect(270, y_pos, 300, 22))
        temp_help.setStringValue_("Creativity level (0.0 = focused, 1.0 = creative)")
        temp_help.setBezeled_(False)
        temp_help.setDrawsBackground_(False)
        temp_help.setEditable_(False)
        temp_help.setFont_(NSFont.systemFontOfSize_(11))
        temp_help.setTextColor_(NSColor.secondaryLabelColor())
        view.addSubview_(temp_help)
        y_pos -= 50
        
        # System Permissions section
        permissions_section_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 620, 20))
        permissions_section_label.setStringValue_("System Permissions")
        permissions_section_label.setFont_(NSFont.boldSystemFontOfSize_(16))
        permissions_section_label.setBezeled_(False)
        permissions_section_label.setDrawsBackground_(False)
        permissions_section_label.setEditable_(False)
        permissions_section_label.setTextColor_(NSColor.labelColor())
        view.addSubview_(permissions_section_label)
        y_pos -= 35
        
        # Permission status
        permissions_status = self.get_permissions_status()
        permission_entity = "Potter.app" if getattr(sys, 'frozen', False) else "Development Session"
        
        # Accessibility permission
        self.accessibility_status = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 400, 22))
        if permissions_status.get('accessibility', False):
            accessibility_text = f"✅ Accessibility: Granted to {permission_entity}"
            color = NSColor.systemGreenColor()
        else:
            accessibility_text = f"❌ Accessibility: Required for {permission_entity}"
            color = NSColor.systemRedColor()
        
        self.accessibility_status.setStringValue_(accessibility_text)
        self.accessibility_status.setBezeled_(False)
        self.accessibility_status.setDrawsBackground_(False)
        self.accessibility_status.setEditable_(False)
        self.accessibility_status.setFont_(NSFont.systemFontOfSize_(14))
        self.accessibility_status.setTextColor_(color)
        view.addSubview_(self.accessibility_status)
        
        # Accessibility button
        self.accessibility_btn = NSButton.alloc().initWithFrame_(NSMakeRect(450, y_pos, 120, 22))
        if not permissions_status.get('accessibility', False):
            self.accessibility_btn.setTitle_("Open Settings")
            self.accessibility_btn.setTarget_(self)
            self.accessibility_btn.setAction_("openAccessibilitySettings:")
        else:
            self.accessibility_btn.setTitle_("Granted")
            self.accessibility_btn.setEnabled_(False)
        self.accessibility_btn.setBezelStyle_(NSBezelStyleRounded)
        self.accessibility_btn.setFont_(NSFont.systemFontOfSize_(12))
        view.addSubview_(self.accessibility_btn)
        y_pos -= 30
        
        # Notification permission
        self.notification_status = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 400, 22))
        notification_text, notification_color = self.get_notification_status()
        self.notification_status.setStringValue_(notification_text)
        self.notification_status.setBezeled_(False)
        self.notification_status.setDrawsBackground_(False)
        self.notification_status.setEditable_(False)
        self.notification_status.setFont_(NSFont.systemFontOfSize_(14))
        self.notification_status.setTextColor_(notification_color)
        view.addSubview_(self.notification_status)
        
        # Notification button
        self.notification_btn = NSButton.alloc().initWithFrame_(NSMakeRect(450, y_pos, 120, 22))
        if "❌" in notification_text:
            self.notification_btn.setTitle_("Open Settings")
            self.notification_btn.setTarget_(self)
            self.notification_btn.setAction_("openNotificationSettings:")
        else:
            self.notification_btn.setTitle_("Working")
            self.notification_btn.setEnabled_(False)
        self.notification_btn.setBezelStyle_(NSBezelStyleRounded)
        self.notification_btn.setFont_(NSFont.systemFontOfSize_(12))
        view.addSubview_(self.notification_btn)
        y_pos -= 40
        
        # Permission actions
        actions_container = NSView.alloc().initWithFrame_(NSMakeRect(40, y_pos, 620, 30))
        
        refresh_btn = NSButton.alloc().initWithFrame_(NSMakeRect(0, 0, 120, 30))
        refresh_btn.setTitle_("Refresh Status")
        refresh_btn.setTarget_(self)
        refresh_btn.setAction_("refreshPermissions:")
        refresh_btn.setBezelStyle_(NSBezelStyleRounded)
        refresh_btn.setFont_(NSFont.systemFontOfSize_(13))
        actions_container.addSubview_(refresh_btn)
        
        reset_btn = NSButton.alloc().initWithFrame_(NSMakeRect(130, 0, 140, 30))
        reset_btn.setTitle_("Reset Permissions")
        reset_btn.setTarget_(self)
        reset_btn.setAction_("resetPermissions:")
        reset_btn.setBezelStyle_(NSBezelStyleRounded)
        reset_btn.setFont_(NSFont.systemFontOfSize_(13))
        actions_container.addSubview_(reset_btn)
        
        view.addSubview_(actions_container)
        
        return view
    
    def createLogsView(self):
        """Create modern Logs view"""
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 700, 650))
        
        y_pos = 580
        
        # Section header
        header = create_section_header("Application Logs", y_pos)
        view.addSubview_(header)
        y_pos -= 50
        
        # Separator
        separator = create_section_separator(y_pos)
        view.addSubview_(separator)
        y_pos -= 30
        
        # Description
        desc_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 620, 17))
        desc_label.setStringValue_("View application logs for debugging and troubleshooting")
        desc_label.setBezeled_(False)
        desc_label.setDrawsBackground_(False)
        desc_label.setEditable_(False)
        desc_label.setFont_(NSFont.systemFontOfSize_(13))
        desc_label.setTextColor_(NSColor.secondaryLabelColor())
        view.addSubview_(desc_label)
        y_pos -= 30
        
        # Toolbar with controls
        toolbar_container = NSView.alloc().initWithFrame_(NSMakeRect(40, y_pos, 620, 30))
        
        # Filter popup
        filter_label = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 5, 50, 20))
        filter_label.setStringValue_("Filter:")
        filter_label.setBezeled_(False)
        filter_label.setDrawsBackground_(False)
        filter_label.setEditable_(False)
        filter_label.setFont_(NSFont.systemFontOfSize_(13))
        toolbar_container.addSubview_(filter_label)
        
        self.log_filter_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(55, 0, 120, 30))
        self.log_filter_popup.addItemWithTitle_("All")
        self.log_filter_popup.addItemWithTitle_("Error")
        self.log_filter_popup.addItemWithTitle_("Warning")
        self.log_filter_popup.addItemWithTitle_("Info")
        self.log_filter_popup.addItemWithTitle_("Debug")
        self.log_filter_popup.setTarget_(self)
        self.log_filter_popup.setAction_("filterLogs:")
        toolbar_container.addSubview_(self.log_filter_popup)
        
        # Refresh button
        refresh_btn = NSButton.alloc().initWithFrame_(NSMakeRect(185, 0, 80, 30))
        refresh_btn.setTitle_("Refresh")
        refresh_btn.setTarget_(self)
        refresh_btn.setAction_("refreshLogs:")
        refresh_btn.setBezelStyle_(NSBezelStyleRounded)
        refresh_btn.setFont_(NSFont.systemFontOfSize_(13))
        toolbar_container.addSubview_(refresh_btn)
        
        # Clear button
        clear_btn = NSButton.alloc().initWithFrame_(NSMakeRect(275, 0, 80, 30))
        clear_btn.setTitle_("Clear")
        clear_btn.setTarget_(self)
        clear_btn.setAction_("clearLogsView:")
        clear_btn.setBezelStyle_(NSBezelStyleRounded)
        clear_btn.setFont_(NSFont.systemFontOfSize_(13))
        toolbar_container.addSubview_(clear_btn)
        
        # Open log file button
        open_btn = NSButton.alloc().initWithFrame_(NSMakeRect(365, 0, 100, 30))
        open_btn.setTitle_("Open File")
        open_btn.setTarget_(self)
        open_btn.setAction_("openLogFile:")
        open_btn.setBezelStyle_(NSBezelStyleRounded)
        open_btn.setFont_(NSFont.systemFontOfSize_(13))
        toolbar_container.addSubview_(open_btn)
        
        view.addSubview_(toolbar_container)
        y_pos -= 40
        
        # Logs scroll view
        logs_container = NSScrollView.alloc().initWithFrame_(NSMakeRect(40, 60, 620, y_pos - 60))
        logs_container.setHasVerticalScroller_(True)
        logs_container.setAutohidesScrollers_(True)
        logs_container.setBorderType_(NSBezelBorder)
        logs_container.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        
        # Create text view for logs
        self.logs_text = NSTextView.alloc().initWithFrame_(logs_container.contentView().bounds())
        self.logs_text.setEditable_(False)
        self.logs_text.setSelectable_(True)
        self.logs_text.setFont_(NSFont.monospacedSystemFontOfSize_weight_(11, 0))
        self.logs_text.setTextColor_(NSColor.labelColor())
        self.logs_text.setBackgroundColor_(NSColor.textBackgroundColor())
        self.logs_text.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        
        logs_container.setDocumentView_(self.logs_text)
        view.addSubview_(logs_container)
        
        # Status label
        self.log_status_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, 30, 620, 17))
        self.log_status_label.setStringValue_("Loading logs...")
        self.log_status_label.setBezeled_(False)
        self.log_status_label.setDrawsBackground_(False)
        self.log_status_label.setEditable_(False)
        self.log_status_label.setFont_(NSFont.systemFontOfSize_(11))
        self.log_status_label.setTextColor_(NSColor.secondaryLabelColor())
        view.addSubview_(self.log_status_label)
        
        # Initialize log monitoring variables
        self.log_timer = None
        self.full_log_content = ""
        self.last_log_size = 0
        
        # Load initial logs
        self.loadLogs()
        self.startLogMonitoring()
        
        return view
    
    def getLogFilePath(self):
        """Get the path to the log file"""
        import sys
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller bundle
            return os.path.expanduser('~/Library/Logs/potter.log')
        else:
            # Running as script
            return 'potter.log'
    
    def loadLogs(self):
        """Load logs from file"""
        try:
            log_file_path = self.getLogFilePath()
            
            if not os.path.exists(log_file_path):
                self.logs_text.setString_("Log file not found at: " + log_file_path)
                self.log_status_label.setStringValue_("Log file not found")
                return
            
            # Get file size to track changes
            file_size = os.path.getsize(log_file_path)
            
            # Read the file
            with open(log_file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            self.full_log_content = content
            self.last_log_size = file_size
            
            # Apply current filter
            self.filterLogsContent()
            
            # Update status
            line_count = len(content.splitlines()) if content else 0
            self.log_status_label.setStringValue_(f"Loaded {line_count} log entries from {log_file_path}")
            
            # Auto-scroll to bottom if enabled
            if hasattr(self, 'auto_scroll_checkbox') and self.auto_scroll_checkbox.state():
                self.scrollToBottom()
                
        except Exception as e:
            error_msg = f"Error loading logs: {str(e)}"
            self.logs_text.setString_(error_msg)
            self.log_status_label.setStringValue_(error_msg)
    
    def filterLogsContent(self):
        """Filter log content based on selected level"""
        if not hasattr(self, 'log_filter_popup'):
            return
        
        selected_level = str(self.log_filter_popup.titleOfSelectedItem())
        
        if selected_level == "All":
            filtered_content = self.full_log_content
        else:
            # Filter lines containing the selected level
            lines = self.full_log_content.splitlines()
            filtered_lines = [line for line in lines if selected_level in line]
            filtered_content = '\n'.join(filtered_lines)
        
        self.logs_text.setString_(filtered_content)
        
        # Auto-scroll to bottom if enabled
        if hasattr(self, 'auto_scroll_checkbox') and self.auto_scroll_checkbox.state():
            self.scrollToBottom()
    
    def scrollToBottom(self):
        """Scroll the log view to the bottom"""
        try:
            # Get the text view's content
            text_length = len(self.logs_text.string())
            if text_length > 0:
                # Scroll to the end
                end_range = NSMakeRange(text_length, 0)
                self.logs_text.scrollRangeToVisible_(end_range)
        except Exception as e:
            print(f"Error scrolling to bottom: {e}")
    
    def startLogMonitoring(self):
        """Start the log monitoring timer"""
        if self.log_timer:
            self.log_timer.invalidate()
        
        # Check for log updates every 2 seconds
        self.log_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            2.0, self, "checkLogUpdates:", None, True
        )
    
    def stopLogMonitoring(self):
        """Stop the log monitoring timer"""
        if self.log_timer:
            self.log_timer.invalidate()
            self.log_timer = None
    
    def checkLogUpdates_(self, timer):
        """Check if log file has been updated"""
        try:
            log_file_path = self.getLogFilePath()
            
            if not os.path.exists(log_file_path):
                return
            
            # Check if file size changed
            current_size = os.path.getsize(log_file_path)
            
            if current_size != self.last_log_size:
                # File has been updated, reload logs
                self.loadLogs()
                
        except Exception as e:
            print(f"Error checking log updates: {e}")
    
    def refreshLogs_(self, sender):
        """Refresh logs manually"""
        self.loadLogs()
    
    def clearLogsView_(self, sender):
        """Clear the logs view (not the actual log file)"""
        self.logs_text.setString_("")
        self.log_status_label.setStringValue_("Log view cleared")
    
    def openLogFile_(self, sender):
        """Open the log file in the default text editor"""
        try:
            log_file_path = self.getLogFilePath()
            if os.path.exists(log_file_path):
                import subprocess
                subprocess.run(['open', log_file_path])
            else:
                alert = NSAlert.alloc().init()
                alert.setMessageText_("Log File Not Found")
                alert.setInformativeText_(f"Log file not found at: {log_file_path}")
                alert.setAlertStyle_(NSAlertStyleWarning)
                alert.runModal()
        except Exception as e:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Error Opening Log File")
            alert.setInformativeText_(f"Could not open log file: {str(e)}")
            alert.setAlertStyle_(NSAlertStyleCritical)
            alert.runModal()
    
    def filterLogs_(self, sender):
        """Filter logs based on selected level"""
        self.filterLogsContent()
    
    def windowWillClose_(self, notification):
        """Handle window will close notification"""
        print("Debug - Settings window will close")
        
        # Stop log monitoring when window closes
        self.stopLogMonitoring()
        
        # Make sure this doesn't trigger app termination
        try:
            from AppKit import NSApplication
            app = NSApplication.sharedApplication()
            # Ensure the app doesn't quit when this window closes
            if hasattr(app, 'setActivationPolicy_'):
                app.setActivationPolicy_(2)  # Keep as accessory app
        except Exception as e:
            print(f"Debug - Error in windowWillClose: {e}")
    
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
        
        # Determine what entity has permission (only check for Potter.app)
        permission_entity = "Potter.app" if getattr(sys, 'frozen', False) else "this development session"
        
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
        
        # Update notification status if the UI elements exist
        if hasattr(self, 'notification_status') and hasattr(self, 'notification_btn'):
            notification_text, notification_color = self.get_notification_status()
            self.notification_status.setStringValue_(notification_text)
            self.notification_status.setTextColor_(notification_color)
            
            if "❌" in notification_text or "⚠️" in notification_text:
                self.notification_btn.setTitle_("Open Settings")
                self.notification_btn.setEnabled_(True)
                self.notification_btn.setTarget_(self)
                self.notification_btn.setAction_("openNotificationSettings:")
            else:
                self.notification_btn.setTitle_("✅ Working")
                self.notification_btn.setEnabled_(False)
        
        # Also refresh the main app's tray icon if available
        try:
            potter_module = sys.modules.get('__main__')
            if potter_module and hasattr(potter_module, 'service') and hasattr(potter_module.service, 'refresh_tray_icon'):
                potter_module.service.refresh_tray_icon()
                print("Debug - Triggered tray icon refresh")
        except Exception as e:
            print(f"Debug - Could not refresh tray icon: {e}")
        
        print("Debug - Permissions status refreshed")
    
    def resetPermissions_(self, sender):
        """Reset all permissions for the Potter app"""
        try:
            # Show confirmation dialog first
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Reset All Permissions")
            alert.setInformativeText_("This will reset ALL system permissions for Potter, including:\n\n• Accessibility (required for global hotkeys)\n• Notifications\n• Any other granted permissions\n\nYou will need to re-grant permissions and restart the app. Continue?")
            alert.setAlertStyle_(NSAlertStyleCritical)
            alert.addButtonWithTitle_("Reset Permissions")
            alert.addButtonWithTitle_("Cancel")
            
            response = alert.runModal()
            if response != NSAlertFirstButtonReturn:  # User clicked Cancel
                return
            
            # Run the tccutil reset command for our app bundle ID
            import subprocess
            bundle_id = "com.potter.app"
            
            try:
                # Reset all permissions for our bundle ID
                result = subprocess.run(['tccutil', 'reset', 'All', bundle_id], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    # Success - show confirmation and offer to restart
                    success_alert = NSAlert.alloc().init()
                    success_alert.setMessageText_("Permissions Reset Successfully")
                    success_alert.setInformativeText_("All permissions for Potter have been reset.\n\nPotter needs to be restarted for changes to take effect. Would you like to restart now?")
                    success_alert.setAlertStyle_(NSAlertStyleInformational)
                    success_alert.addButtonWithTitle_("Restart Potter")
                    success_alert.addButtonWithTitle_("Later")
                    
                    restart_response = success_alert.runModal()
                    if restart_response == NSAlertFirstButtonReturn:  # Restart
                        self.restartApp()
                    else:
                        # Just refresh the permissions display
                        self.refreshPermissions_(None)
                        
                else:
                    # Command failed
                    error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                    self.show_permission_reset_error(f"Failed to reset permissions: {error_msg}")
                    
            except subprocess.TimeoutExpired:
                self.show_permission_reset_error("Permission reset timed out. Please try again.")
            except FileNotFoundError:
                self.show_permission_reset_error("tccutil command not found. This feature requires macOS 10.11 or later.")
            except Exception as e:
                self.show_permission_reset_error(f"Unexpected error: {str(e)}")
                
        except Exception as e:
            print(f"Debug - Error in resetPermissions: {e}")
            self.show_permission_reset_error(f"Failed to reset permissions: {str(e)}")
    
    def show_permission_reset_error(self, message):
        """Show permission reset error dialog"""
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Permission Reset Failed")
        alert.setInformativeText_(message)
        alert.setAlertStyle_(NSAlertStyleCritical)
        alert.runModal()
    
    def restartApp(self):
        """Restart the Potter application"""
        try:
            import subprocess
            import sys
            import os
            
            # Get the path to the current executable
            if getattr(sys, 'frozen', False):
                # Running as app bundle
                app_path = sys.executable
                # Find the .app bundle root
                while app_path and not app_path.endswith('.app'):
                    app_path = os.path.dirname(app_path)
                
                if app_path and app_path.endswith('.app'):
                    # Launch the app bundle
                    subprocess.Popen(['open', app_path])
                    
                    # Quit current app after a short delay
                    def quit_app():
                        try:
                            from AppKit import NSApplication
                            app = NSApplication.sharedApplication()
                            app.terminate_(None)
                        except:
                            import os
                            os._exit(0)
                    
                    # Use a timer to quit after launching new instance
                    NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                        1.0, self, "quitApp:", None, False
                    )
                else:
                    self.show_permission_reset_error("Could not find app bundle path for restart.")
            else:
                # Running as script - just show message
                alert = NSAlert.alloc().init()
                alert.setMessageText_("Manual Restart Required")
                alert.setInformativeText_("Please manually restart Potter for the permission changes to take effect.")
                alert.setAlertStyle_(NSAlertStyleInformational)
                alert.runModal()
                
        except Exception as e:
            print(f"Debug - Error restarting app: {e}")
            # Fallback - just show message
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Manual Restart Required")
            alert.setInformativeText_("Please manually restart Potter for the permission changes to take effect.")
            alert.setAlertStyle_(NSAlertStyleInformational)
            alert.runModal()
    
    def quitApp_(self, timer):
        """Quit the app (called by timer after restart)"""
        try:
            from AppKit import NSApplication
            app = NSApplication.sharedApplication()
            app.terminate_(None)
        except:
            import os
            os._exit(0)
    
    def get_notification_status(self):
        """Get notification permission and Do Not Disturb status"""
        try:
            import subprocess
            
            # Check if Do Not Disturb is enabled
            try:
                result = subprocess.run(['defaults', 'read', 'com.apple.controlcenter', 'NSStatusItem Visible FocusModes'], 
                                      capture_output=True, text=True, timeout=5)
                focus_modes_visible = result.stdout.strip() == "1"
                
                # Check current Focus mode status
                result = subprocess.run(['shortcuts', 'run', 'Get Current Focus'], 
                                      capture_output=True, text=True, timeout=5)
                focus_mode = result.stdout.strip()
                
                if focus_mode and focus_mode != "None":
                    return (f"Notifications: ❌ Blocked by Focus mode ({focus_mode})", NSColor.systemOrangeColor())
                
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
                # If we can't check Focus mode, continue with other checks
                pass
            
            # Test if notifications work by checking app registration
            try:
                from UserNotifications import UNUserNotificationCenter
                center = UNUserNotificationCenter.currentNotificationCenter()
                
                def check_settings(settings):
                    if settings:
                        if settings.authorizationStatus() == 2:  # UNAuthorizationStatusAuthorized
                            return (f"Notifications: ✅ Enabled and working", NSColor.systemGreenColor())
                        elif settings.authorizationStatus() == 1:  # UNAuthorizationStatusDenied
                            return (f"Notifications: ❌ Permission denied", NSColor.systemRedColor())
                        else:
                            return (f"Notifications: ⚠️ Permission not determined", NSColor.systemOrangeColor())
                    return (f"Notifications: ❌ Could not check permissions", NSColor.systemRedColor())
                
                # This is async, so we'll just assume enabled for now if we get here
                return (f"Notifications: ✅ Enabled (app has permission)", NSColor.systemGreenColor())
                
            except ImportError:
                # Fallback: assume notifications are enabled if the checkbox is checked
                if self.settings_manager.get("show_notifications", False):
                    return (f"Notifications: ✅ Enabled in settings", NSColor.systemGreenColor())
                else:
                    return (f"Notifications: ❌ Disabled in settings", NSColor.systemRedColor())
                
        except Exception as e:
            print(f"Debug - get_notification_status error: {e}")
            return (f"Notifications: ⚠️ Status unknown", NSColor.systemOrangeColor())
    
    def openNotificationSettings_(self, sender):
        """Open System Settings to Notifications"""
        try:
            subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.notifications'], check=False)
        except Exception as e:
            print(f"Debug - Failed to open Notification Settings: {e}")
    
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
    
    def save_(self, sender):
        """Save settings to file"""
        print("Debug - Save button clicked")
        
        try:
            # Create new settings dict
            new_settings = self.settings_manager.settings.copy()
            
            # Get values from UI controls
            if hasattr(self, 'api_key_field'):
                new_settings["openai_api_key"] = str(self.api_key_field.stringValue()).strip()
                print(f"Debug - API key field value: {new_settings['openai_api_key'][:10] if new_settings['openai_api_key'] else 'None'}...")
            
            if hasattr(self, 'hotkey_field'):
                new_settings["hotkey"] = str(self.hotkey_field.stringValue()).strip()
                print(f"Debug - Hotkey: {new_settings['hotkey']}")
            
            if hasattr(self, 'model_popup'):
                new_settings["model"] = str(self.model_popup.titleOfSelectedItem())
                print(f"Debug - Model: {new_settings['model']}")
            
            if hasattr(self, 'tokens_field'):
                try:
                    tokens_str = str(self.tokens_field.stringValue()).strip()
                    new_settings["max_tokens"] = int(tokens_str) if tokens_str else 1000
                except ValueError:
                    new_settings["max_tokens"] = 1000
                print(f"Debug - Max tokens: {new_settings['max_tokens']}")
            
            if hasattr(self, 'temp_field'):
                try:
                    temp_str = str(self.temp_field.stringValue()).strip()
                    new_settings["temperature"] = float(temp_str) if temp_str else 0.7
                except ValueError:
                    new_settings["temperature"] = 0.7
                print(f"Debug - Temperature: {new_settings['temperature']}")
            
            # Handle modern switches
            if hasattr(self, 'notifications_switch'):
                new_settings["show_notifications"] = bool(self.notifications_switch.state())
                print(f"Debug - Notifications: {new_settings['show_notifications']}")
            
            if hasattr(self, 'startup_switch'):
                new_settings["launch_at_startup"] = bool(self.startup_switch.state())
                print(f"Debug - Launch at startup: {new_settings['launch_at_startup']}")
            
            # Handle prompts data
            if hasattr(self, 'prompts_data') and self.prompts_data:
                new_settings["prompts"] = list(self.prompts_data)
                print(f"Debug - Prompts count: {len(new_settings['prompts'])}")
            
            print(f"Debug - About to save settings: {list(new_settings.keys())}")
            
            # Save settings
            success = self.settings_manager.save_settings(new_settings)
            
            if success:
                print("Debug - Settings saved successfully")
                
                # Call the callback if provided
                if hasattr(self, 'on_settings_changed') and self.on_settings_changed:
                    print("Debug - Calling on_settings_changed callback")
                    self.on_settings_changed(new_settings)
                
                # Show success notification
                self.settings_manager.show_success("Settings saved successfully")
                
                # Close the window
                print("Debug - Attempting to close window")
                try:
                    if hasattr(self, 'window') and self.window():
                        print("Debug - Closing window via self.window()")
                        self.window().close()
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