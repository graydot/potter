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
import time

# Import the proper SettingsManager from the settings module
from settings.settings_manager import SettingsManager


# Removed duplicate SettingsManager class - now using proper import from settings.settings_manager


class HotkeyCapture(NSView):
    """Hotkey capture control that displays keys as pill buttons"""
    
    def initWithFrame_manager_(self, frame, settings_manager):
        self = objc.super(HotkeyCapture, self).initWithFrame_(frame)
        if self is None:
            return None
        
        self.settings_manager = settings_manager
        self.reset_callback = None
        self.hotkey_parts = []
        self.is_capturing = False
        
        # Create container for pills
        self.pill_container = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, frame.size.width - 100, frame.size.height))
        self.addSubview_(self.pill_container)
        
        # Create capture button
        self.capture_button = NSButton.alloc().initWithFrame_(NSMakeRect(frame.size.width - 90, 0, 90, frame.size.height))
        self.capture_button.setTitle_("Capture")
        self.capture_button.setTarget_(self)
        self.capture_button.setAction_("startCapture:")
        self.capture_button.setBezelStyle_(NSBezelStyleRounded)
        self.capture_button.setFont_(NSFont.systemFontOfSize_(12))
        self.addSubview_(self.capture_button)
        
        # Set initial hotkey
        self.setHotkeyString_(settings_manager.get("hotkey", "cmd+shift+a"))
        
        return self
    
    def acceptsFirstResponder(self):
        """Allow this view to become first responder for key capture"""
        return True
    
    def becomeFirstResponder(self):
        """Handle becoming first responder"""
        if self.is_capturing:
            return objc.super(HotkeyCapture, self).becomeFirstResponder()
        return False
    
    def setHotkeyString_(self, hotkey_string):
        """Set hotkey from string like 'cmd+shift+a'"""
        self.hotkey_parts = hotkey_string.split('+') if hotkey_string else []
        self.updatePillDisplay()
    
    def getHotkeyString(self):
        """Get hotkey as string"""
        return '+'.join(self.hotkey_parts) if self.hotkey_parts else ""
    
    def updatePillDisplay(self):
        """Update the pill button display"""
        # Clear existing pills
        for subview in list(self.pill_container.subviews()):
            subview.removeFromSuperview()
        
        if not self.hotkey_parts:
            # Show placeholder
            placeholder = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 5, 200, 15))
            placeholder.setStringValue_("Click Capture to set hotkey")
            placeholder.setBezeled_(False)
            placeholder.setDrawsBackground_(False)
            placeholder.setEditable_(False)
            placeholder.setFont_(NSFont.systemFontOfSize_(11))
            placeholder.setTextColor_(NSColor.placeholderTextColor())
            self.pill_container.addSubview_(placeholder)
            return
        
        # Create pills for each key part - better size calculation
        x_offset = 0
        for i, part in enumerate(self.hotkey_parts):
            # Better width calculation - use actual text measurement
            font = NSFont.boldSystemFontOfSize_(12)  # Larger, bold font
            
            # Convert Python string to NSString and measure its size with proper attributes
            ns_string = NSString.stringWithString_(part)
            attributes = {NSFontAttributeName: font}
            text_size = ns_string.sizeWithAttributes_(attributes)
            
            # Add generous padding to prevent cutoff - especially for shorter strings
            base_padding = 24  # Base padding
            extra_padding = max(8, int((4 - len(part)) * 4))  # Extra padding for shorter strings
            pill_width = int(text_size.width) + base_padding + extra_padding
            
            # Ensure minimum width for single characters
            if len(part) == 1:
                pill_width = max(pill_width, 40)
            
            pill_height = 24  # Taller pills
            
            # Create pill button
            pill = NSButton.alloc().initWithFrame_(NSMakeRect(x_offset, 0, pill_width, pill_height))
            pill.setTitle_(part)
            pill.setFont_(font)
            pill.setBezelStyle_(NSBezelStyleRounded)
            pill.setBordered_(True)
            pill.setEnabled_(False)  # Not clickable, just visual
            
            # Style as brighter pill with better colors
            try:
                pill.setControlSize_(NSControlSizeRegular)  # Use regular size for bigger appearance
                
                # Set a nice blue tint for better visibility
                if hasattr(pill, 'setControlTint_'):
                    pill.setControlTint_(NSBlueControlTint)
                
                # Try to set background color for better appearance
                cell = pill.cell()
                if hasattr(cell, 'setBackgroundColor_'):
                    cell.setBackgroundColor_(NSColor.systemBlueColor().colorWithAlphaComponent_(0.1))
                
            except Exception as e:
                print(f"Debug - Pill styling error: {e}")
                # Fallback styling
                pass
            
            self.pill_container.addSubview_(pill)
            x_offset += pill_width + 8  # More spacing between pills
            
            # Add "+" between pills with better styling
            if i < len(self.hotkey_parts) - 1:
                plus_label = NSTextField.alloc().initWithFrame_(NSMakeRect(x_offset, 6, 12, 15))
                plus_label.setStringValue_("+")
                plus_label.setBezeled_(False)
                plus_label.setDrawsBackground_(False)
                plus_label.setEditable_(False)
                plus_label.setFont_(NSFont.boldSystemFontOfSize_(12))  # Bolder "+" sign
                plus_label.setTextColor_(NSColor.secondaryLabelColor())
                self.pill_container.addSubview_(plus_label)
                x_offset += 18  # More space for the "+" sign
    
    def startCapture_(self, sender):
        """Start capturing hotkey"""
        self.is_capturing = True
        self.capture_button.setTitle_("Press keys...")
        self.capture_button.setEnabled_(False)
        self.window().makeFirstResponder_(self)
    
    def keyDown_(self, event):
        """Capture key combination"""
        if not self.is_capturing:
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
        
        # Build hotkey parts
        if modifiers and key and key.isalnum():
            self.hotkey_parts = modifiers + [key]
            self.updatePillDisplay()
            
            # Trigger callback
            if self.reset_callback:
                self.reset_callback()
            
            # End capture
            self.endCapture()
    
    def endCapture(self):
        """End key capture mode"""
        self.is_capturing = False
        self.capture_button.setTitle_("Capture")
        self.capture_button.setEnabled_(True)
        self.window().makeFirstResponder_(None)


class LinkTarget(NSObject):
    """Target class for clickable links"""
    
    def initWithURL_(self, url):
        self = objc.super(LinkTarget, self).init()
        if self is None:
            return None
        self.url = url
        return self
    
    def openURL_(self, sender):
        """Open the URL in the default browser"""
        import subprocess
        if self.url:
            subprocess.run(['open', self.url])


def create_clickable_link(frame, text, url):
    """Create a clickable button (gave up on blue links!)"""
    
    # Simple, clean button that actually works
    button = NSButton.alloc().initWithFrame_(frame)
    button.setTitle_(text)
    button.setButtonType_(NSButtonTypeMomentaryPushIn)
    button.setBezelStyle_(NSBezelStyleRounded)
    button.setFont_(NSFont.systemFontOfSize_(11))
    
    # Set up click handling
    target = LinkTarget.alloc().initWithURL_(url)
    button.setTarget_(target)
    button.setAction_("openURL:")
    button.setRepresentedObject_(target)
    
    return button


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
        self.response_code = None  # Track response for modal operation
        self.name_validator = None  # Callback to validate name for duplicates
        
        print(f"Debug - Creating prompt dialog, is_edit={is_edit}, prompt={self.prompt}")
        self.createDialog()
        return self
    
    def createDialog(self):
        """Create the dialog window"""
        # Create window with better modal setup
        frame = NSMakeRect(100, 100, 500, 350)  # Increased height for error labels
        style_mask = (NSWindowStyleMaskTitled | 
                     NSWindowStyleMaskClosable | 
                     NSWindowStyleMaskMiniaturizable)
        
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            style_mask,
            NSBackingStoreBuffered,
            False
        )
        
        title = "Edit Prompt" if self.is_edit else "Add New Prompt"
        window.setTitle_(title)
        window.setLevel_(NSModalPanelWindowLevel)
        window.setReleasedWhenClosed_(False)  # Keep window object alive
        window.setDelegate_(self)  # Set delegate to handle key events
        content_view = window.contentView()
        
        # Set window to accept key events
        window.setAcceptsMouseMovedEvents_(True)
        window.makeKeyWindow()
        
        # Set custom icon for the dialog window
        try:
            # Get the parent settings window controller to access the icon setting method
            # For prompt dialogs (which are windows, not alerts), we need different handling
            if hasattr(self, 'parent_window_controller'):
                # This is a window dialog, not an NSAlert, so we skip icon setting for now
                # TODO: Implement window icon setting if needed
                pass
        except Exception as e:
            print(f"Debug - Could not set prompt dialog icon: {e}")
        
        # Name field (max 10 chars)
        name_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 280, 100, 20))
        name_label.setStringValue_("Name (max 10):")
        name_label.setBezeled_(False)
        name_label.setDrawsBackground_(False)
        name_label.setEditable_(False)
        content_view.addSubview_(name_label)
        
        self.name_field = NSTextField.alloc().initWithFrame_(NSMakeRect(130, 280, 200, 25))
        self.name_field.setStringValue_(self.prompt.get("name", ""))
        self.name_field.setTarget_(self)
        self.name_field.setAction_("validateName:")
        content_view.addSubview_(self.name_field)
        
        # Character count label
        self.char_count_label = NSTextField.alloc().initWithFrame_(NSMakeRect(340, 280, 100, 20))
        self.char_count_label.setBezeled_(False)
        self.char_count_label.setDrawsBackground_(False)
        self.char_count_label.setEditable_(False)
        self.char_count_label.setFont_(NSFont.systemFontOfSize_(10))
        self.char_count_label.setTextColor_(NSColor.secondaryLabelColor())
        content_view.addSubview_(self.char_count_label)
        
        # Name error label (initially hidden)
        self.name_error_label = NSTextField.alloc().initWithFrame_(NSMakeRect(130, 255, 300, 20))
        self.name_error_label.setStringValue_("")
        self.name_error_label.setBezeled_(False)
        self.name_error_label.setDrawsBackground_(False)
        self.name_error_label.setEditable_(False)
        self.name_error_label.setFont_(NSFont.systemFontOfSize_(11))
        self.name_error_label.setTextColor_(NSColor.systemRedColor())
        self.name_error_label.setHidden_(True)
        content_view.addSubview_(self.name_error_label)
        
        # Prompt text field
        prompt_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 220, 100, 20))
        prompt_label.setStringValue_("Prompt Text:")
        prompt_label.setBezeled_(False)
        prompt_label.setDrawsBackground_(False)
        prompt_label.setEditable_(False)
        content_view.addSubview_(prompt_label)
        
        # Scrollable text view for prompt
        scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(20, 120, 460, 90))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setHasHorizontalScroller_(False)
        scroll_view.setBorderType_(NSBezelBorder)
        
        self.prompt_text_view = NSTextView.alloc().initWithFrame_(scroll_view.contentView().bounds())
        self.prompt_text_view.setString_(self.prompt.get("text", ""))
        self.prompt_text_view.setFont_(NSFont.systemFontOfSize_(12))
        self.prompt_text_view.setDelegate_(self)  # Set delegate to monitor text changes
        # Set the text view to forward key events to the window
        self.prompt_text_view.setImportsGraphics_(False)
        scroll_view.setDocumentView_(self.prompt_text_view)
        content_view.addSubview_(scroll_view)
        
        # Text error label (initially hidden)
        self.text_error_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, 95, 460, 20))
        self.text_error_label.setStringValue_("")
        self.text_error_label.setBezeled_(False)
        self.text_error_label.setDrawsBackground_(False)
        self.text_error_label.setEditable_(False)
        self.text_error_label.setFont_(NSFont.systemFontOfSize_(11))
        self.text_error_label.setTextColor_(NSColor.systemRedColor())
        self.text_error_label.setHidden_(True)
        content_view.addSubview_(self.text_error_label)
        
        # Buttons - Create with proper targets and actions
        self.cancel_btn = NSButton.alloc().initWithFrame_(NSMakeRect(320, 20, 80, 30))
        self.cancel_btn.setTitle_("Cancel")
        self.cancel_btn.setTarget_(self)
        self.cancel_btn.setAction_("cancel:")
        self.cancel_btn.setKeyEquivalent_("\x1b")  # ESC key
        self.cancel_btn.setBezelStyle_(NSBezelStyleRounded)
        content_view.addSubview_(self.cancel_btn)
        
        self.save_btn = NSButton.alloc().initWithFrame_(NSMakeRect(410, 20, 80, 30))
        self.save_btn.setTitle_("Save")
        self.save_btn.setTarget_(self)
        self.save_btn.setAction_("save:")
        self.save_btn.setKeyEquivalent_("\r")  # Return key
        self.save_btn.setBezelStyle_(NSBezelStyleRounded)
        content_view.addSubview_(self.save_btn)
        
        # Set default button
        window.setDefaultButtonCell_(self.save_btn.cell())
        
        # Set the window
        self.setWindow_(window)
        
        # Update character count
        self.updateCharCount()
        
        print("Debug - Prompt dialog window created successfully")
    
    def validateName_(self, sender):
        """Validate name length as user types"""
        print("Debug - validateName_ called")
        name = str(self.name_field.stringValue())
        if len(name) > 10:
            # Truncate to 10 characters
            truncated = name[:10]
            self.name_field.setStringValue_(truncated)
        self.updateCharCount()
        self.clearValidationErrors()  # Clear errors when user types
    
    def clearValidationErrors(self):
        """Clear all validation error labels"""
        if hasattr(self, 'name_error_label'):
            self.name_error_label.setStringValue_("")
            self.name_error_label.setHidden_(True)
        if hasattr(self, 'text_error_label'):
            self.text_error_label.setStringValue_("")
            self.text_error_label.setHidden_(True)
    
    def showNameError_(self, message):
        """Show name validation error"""
        self.name_error_label.setStringValue_(message)
        self.name_error_label.setHidden_(False)
    
    def showTextError_(self, message):
        """Show text validation error"""
        self.text_error_label.setStringValue_(message)
        self.text_error_label.setHidden_(False)
    
    def textDidChange_(self, notification):
        """Clear validation errors when user types in text view"""
        self.clearValidationErrors()
    
    def keyDown_(self, event):
        """Handle key events for the dialog"""
        # Check for Cmd+Enter (save)
        if (event.modifierFlags() & NSEventModifierFlagCommand and 
            event.keyCode() == 36):  # Enter key
            print("Debug - Cmd+Enter detected, saving")
            self.save_(None)
            return
        
        # Check for Esc (cancel)
        if event.keyCode() == 53:  # ESC key
            print("Debug - ESC key detected, cancelling")
            self.cancel_(None)
            return
        
        # Pass other keys to superclass
        objc.super(PromptDialog, self).keyDown_(event)
    
    def cancelOperation_(self, sender):
        """Handle ESC key press via responder chain"""
        print("Debug - cancelOperation_ called (ESC key)")
        self.cancel_(None)
    
    def performKeyEquivalent_(self, event):
        """Handle key equivalents for the window"""
        # Check for Cmd+Enter anywhere in the dialog
        if (event.modifierFlags() & NSEventModifierFlagCommand and 
            event.keyCode() == 36):  # Enter key
            print("Debug - performKeyEquivalent: Cmd+Enter detected")
            self.save_(None)
            return True
        
        # Check for Esc anywhere in the dialog
        if event.keyCode() == 53:  # ESC key
            print("Debug - performKeyEquivalent: ESC detected")
            self.cancel_(None)
            return True
        
        # Let superclass handle other key equivalents
        return objc.super(PromptDialog, self).performKeyEquivalent_(event)
    
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
        print("Debug - save_ method called")
        try:
            name = str(self.name_field.stringValue()).strip()
            text = str(self.prompt_text_view.string()).strip()
            
            print(f"Debug - Validating prompt: name='{name}', text_length={len(text)}")
            
            # Clear previous errors
            self.clearValidationErrors()
            
            # Validation with inline error display
            has_errors = False
            
            if not name:
                print("Debug - Validation failed: empty name")
                self.showNameError_("Please enter a name for this prompt")
                has_errors = True
            elif len(name) > 10:
                print("Debug - Validation failed: name too long")
                self.showNameError_("Name must be 10 characters or less")
                has_errors = True
            
            if not text:
                print("Debug - Validation failed: empty text")
                self.showTextError_("Please enter the prompt text")
                has_errors = True
            
            # Check for duplicate names if validator is provided
            if self.name_validator:
                duplicate_error = self.name_validator(name)
                if duplicate_error:
                    print(f"Debug - Validation failed: {duplicate_error}")
                    self.showNameError_(duplicate_error)
                    has_errors = True
            
            # If there are validation errors, don't proceed
            if has_errors:
                return
            
            # If we get here, validation passed
            self.result = {
                "name": name,
                "text": text
            }
            self.response_code = NSModalResponseOK
            
            print(f"Debug - Prompt validated successfully: {self.result}")
            
            # Call callback if set
            if self.callback:
                try:
                    print("Debug - Calling callback with result")
                    self.callback(self.result)
                except Exception as e:
                    print(f"Debug - Callback error in save: {e}")
            
            # Close the dialog
            self.endModalDialog()
            
        except Exception as e:
            print(f"Debug - Error in save_: {e}")
            import traceback
            traceback.print_exc()
    
    def cancel_(self, sender):
        """Cancel the dialog"""
        print("Debug - cancel_ method called")
        try:
            self.result = None
            self.response_code = NSModalResponseCancel
            
            if self.callback:
                try:
                    print("Debug - Calling callback with None (cancel)")
                    self.callback(None)
                except Exception as e:
                    print(f"Debug - Callback error in cancel: {e}")
            
            # Close the dialog
            self.endModalDialog()
            
        except Exception as e:
            print(f"Debug - Error in cancel_: {e}")
            import traceback
            traceback.print_exc()
    
    def endModalDialog(self):
        """End the modal dialog properly"""
        print("Debug - endModalDialog called")
        try:
            window = self.window()
            if window:
                print("Debug - Stopping modal for window")
                NSApp.stopModalWithCode_(self.response_code or NSModalResponseCancel)
                window.orderOut_(None)
            else:
                print("Debug - No window to close in endModalDialog")
        except Exception as e:
            print(f"Debug - Error in endModalDialog: {e}")
    
    def showAlertWithTitle_message_(self, title, message):
        """Show an alert dialog"""
        print(f"Debug - Showing alert: {title} - {message}")
        try:
            alert = NSAlert.alloc().init()
            alert.setMessageText_(title)
            alert.setInformativeText_(message)
            alert.setAlertStyle_(NSAlertStyleWarning)
            alert.runModal()
        except Exception as e:
            print(f"Debug - Error showing alert: {e}")
    
    def runModalDialog(self):
        """Run the dialog modally and return the result"""
        print("Debug - Running modal dialog")
        try:
            window = self.window()
            if not window:
                print("Debug - No window available for modal dialog")
                return None
            
            # Center the window on screen
            screen_frame = NSScreen.mainScreen().visibleFrame()
            window_frame = window.frame()
            x = (screen_frame.size.width - window_frame.size.width) / 2 + screen_frame.origin.x
            y = (screen_frame.size.height - window_frame.size.height) / 2 + screen_frame.origin.y
            window.setFrameOrigin_(NSMakePoint(x, y))
            
            # Make it key and order front
            window.makeKeyAndOrderFront_(None)
            
            # Run modal
            response = NSApp.runModalForWindow_(window)
            print(f"Debug - Modal dialog finished with response: {response}")
            
            return self.result
            
        except Exception as e:
            print(f"Debug - Error running modal dialog: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def windowShouldClose_(self, window):
        """Handle window close request"""
        print("Debug - Window close requested")
        self.cancel_(None)
        return False  # We handle closing ourselves
    
    def windowWillClose_(self, notification):
        """Handle window will close notification"""
        print("Debug - Window will close")
    
    def performKeyEquivalent_(self, event):
        """Handle key equivalents for the entire window"""
        print(f"Debug - performKeyEquivalent called with keyCode: {event.keyCode()}")
        
        # Check for Cmd+Enter anywhere in the dialog
        if (event.modifierFlags() & NSEventModifierFlagCommand and 
            event.keyCode() == 36):  # Enter key
            print("Debug - performKeyEquivalent: Cmd+Enter detected")
            self.save_(None)
            return True
        
        # Check for Esc anywhere in the dialog  
        if event.keyCode() == 53:  # ESC key
            print("Debug - performKeyEquivalent: ESC detected")
            self.cancel_(None)
            return True
        
        # Let superclass handle other key equivalents
        return objc.super(PromptDialog, self).performKeyEquivalent_(event)


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
    
    # Switch (try NSSwitch first, fallback to checkbox) - positioned at right edge
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
    """Create enhanced sidebar button with proper highlighting support"""
    button = NSButton.alloc().initWithFrame_(NSMakeRect(10, y_position, 180, 40))
    button.setButtonType_(NSButtonTypePushOnPushOff)  # Toggle button for highlighting
    button.setBordered_(False)
    button.setTag_(item["tag"])
    
    # Create custom attributed title with icon and text
    icon_name = item["icon"]
    title = item["title"]
    
    # Try to use SF Symbols if available
    if hasattr(NSImage, 'imageWithSystemSymbolName_accessibilityDescription_'):
        icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(icon_name, None)
        if icon:
            icon.setSize_(NSMakeSize(16, 16))
        else:
            icon = None
    else:
        icon = None
    
    # Set button title
    button.setTitle_(f"  {title}")  # Add space for icon
    button.setFont_(NSFont.systemFontOfSize_(14))
    
    # Configure button appearance
    button.setAlignment_(NSTextAlignmentLeft)
    
    # Set icon if available
    if icon:
        button.setImage_(icon)
        button.setImagePosition_(NSImageLeft)
        button.setImageScaling_(NSImageScaleProportionallyDown)
    
    # Configure button colors for highlighting
    def configure_button_appearance():
        # Normal state
        button.setBezelStyle_(NSBezelStyleRegularSquare)
        button.setBordered_(True)
        button.setShowsBorderOnlyWhileMouseInside_(False)
        
        # Create custom cell for better control
        cell = button.cell()
        if hasattr(cell, 'setHighlightsBy_'):
            cell.setHighlightsBy_(NSChangeGrayCellMask)
        if hasattr(cell, 'setShowsStateBy_'):
            cell.setShowsStateBy_(NSChangeBackgroundCellMask)
    
    configure_button_appearance()
    
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
        """Create and configure the settings window"""
        print("Debug - Creating settings window...")
        
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
        
        # Try to set window icon using logo.png
        self._set_window_icon(window)
        
        print("Debug - Creating sidebar and content area...")
        
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
        
        print("Debug - Creating content views...")
        
        # Create content views with safety checks
        content_views = []
        
        try:
            general_view = self.createGeneralView()
            if general_view is not None:
                content_views.append(general_view)
                print("Debug - General view created successfully")
            else:
                print("Debug - Failed to create General view")
                
        except Exception as e:
            print(f"Debug - Error creating General view: {e}")
        
        try:
            prompts_view = self.createPromptsView()
            if prompts_view is not None:
                content_views.append(prompts_view)
                print("Debug - Prompts view created successfully")
            else:
                print("Debug - Failed to create Prompts view")
                
        except Exception as e:
            print(f"Debug - Error creating Prompts view: {e}")
        
        try:
            advanced_view = self.createAdvancedView()
            if advanced_view is not None:
                content_views.append(advanced_view)
                print("Debug - Advanced view created successfully")
            else:
                print("Debug - Failed to create Advanced view")
                
        except Exception as e:
            print(f"Debug - Error creating Advanced view: {e}")
        
        try:
            logs_view = self.createLogsView()
            if logs_view is not None:
                content_views.append(logs_view)
                print("Debug - Logs view created successfully")
            else:
                print("Debug - Failed to create Logs view")
                
        except Exception as e:
            print(f"Debug - Error creating Logs view: {e}")
        
        # Only assign if we have at least one view
        if content_views:
            self.content_views = content_views
            print(f"Debug - Created {len(self.content_views)} content views successfully")
        else:
            print("Debug - Warning: No content views were created successfully")
            # Create a fallback empty view to prevent crashes
            self.content_views = [NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 700, 600))]
        
        # Show initial section
        self.showSection_(0)
        
        self.setWindow_(window)
        
        # Set default button now that window is available
        if hasattr(self, 'save_button'):
            try:
                self.window().setDefaultButtonCell_(self.save_button.cell())
                print("Debug - Set default button successfully")
            except Exception as e:
                print(f"Warning: Could not set default button: {e}")
        
        # Register for appearance change notifications
        self._register_for_appearance_changes()
    
    def _register_for_appearance_changes(self):
        """Register for system appearance change notifications"""
        try:
            # Register for system appearance changes
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                self, "appearanceDidChange:", "NSSystemColorsDidChangeNotification", None
            )
            print("Debug - Registered for appearance change notifications")
        except Exception as e:
            print(f"Debug - Error registering for appearance changes: {e}")
    
    def appearanceDidChange_(self, notification):
        """Handle system appearance changes"""
        print("Debug - System appearance changed, updating icons")
        try:
            # Update dock icon
            self._update_dock_icon()
            
            # Update tray icon if available
            try:
                potter_module = sys.modules.get('__main__')
                if potter_module and hasattr(potter_module, 'service') and hasattr(potter_module.service, 'tray_icon'):
                    print("Debug - Updating tray icon for appearance change")
                    potter_module.service.tray_icon.update_icon_for_appearance()
            except Exception as e:
                print(f"Debug - Error updating tray icon: {e}")
                
        except Exception as e:
            print(f"Debug - Error updating icons for appearance change: {e}")
    
    def _update_dock_icon(self):
        """Update dock icon for current appearance"""
        try:
            # Try to find logo files in assets folder
            base_paths = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets'),
                'assets',
                '.'
            ]
            
            logo_light_path = None
            logo_dark_path = None
            fallback_logo_path = None
            
            # Look for light/dark specific logos and fallback
            for base_path in base_paths:
                light_path = os.path.join(base_path, 'light.png')
                dark_path = os.path.join(base_path, 'dark.png')
                fallback_path = os.path.join(base_path, 'logo.png')
                
                if os.path.exists(light_path) and not logo_light_path:
                    logo_light_path = light_path
                if os.path.exists(dark_path) and not logo_dark_path:
                    logo_dark_path = dark_path
                if os.path.exists(fallback_path) and not fallback_logo_path:
                    fallback_logo_path = fallback_path
            
            # Determine current appearance
            current_appearance = self._get_current_appearance()
            
            # Choose appropriate icon
            if current_appearance == "dark" and logo_dark_path:
                icon_path = logo_dark_path
                print(f"Debug - Using dark icon: {icon_path}")
            elif current_appearance == "light" and logo_light_path:
                icon_path = logo_light_path
                print(f"Debug - Using light icon: {icon_path}")
            elif fallback_logo_path:
                icon_path = fallback_logo_path
                print(f"Debug - Using fallback icon: {icon_path}")
            else:
                print("Debug - No suitable icon found for dock")
                return
            
            # Load and set the icon
            ns_image = NSImage.alloc().initWithContentsOfFile_(icon_path)
            if ns_image:
                ns_image.setSize_(NSMakeSize(128, 128))
                # Set dock icon for the entire application
                app = NSApplication.sharedApplication()
                app.setApplicationIconImage_(ns_image)
                print(f"Debug - Updated dock icon for {current_appearance} mode")
            else:
                print(f"Debug - Failed to load icon from {icon_path}")
                
        except Exception as e:
            print(f"Debug - Error updating dock icon: {e}")
    
    def _get_current_appearance(self):
        """Get the current system appearance (light/dark)"""
        try:
            # Check the effective appearance of the current window or app
            if hasattr(self, 'window') and self.window():
                appearance = self.window().effectiveAppearance()
            else:
                appearance = NSApplication.sharedApplication().effectiveAppearance()
            
            if appearance:
                appearance_name = appearance.name()
                if "Dark" in str(appearance_name):
                    return "dark"
                else:
                    return "light"
            else:
                # Fallback: check system preferences
                import subprocess
                result = subprocess.run(['defaults', 'read', '-g', 'AppleInterfaceStyle'], 
                                      capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip() == "Dark":
                    return "dark"
                else:
                    return "light"
        except Exception as e:
            print(f"Debug - Error getting appearance: {e}")
            return "light"  # Default to light
    
    def _set_window_icon(self, window):
        """Set window icon using logo.png from assets folder with light/dark mode support"""
        try:
            # Update dock icon based on current appearance
            self._update_dock_icon()
        except Exception as e:
            print(f"Debug - Error setting window icon: {e}")
    
    def _set_dialog_icon(self, alert_object):
        """Set dialog icon based on current theme for NSAlert objects"""
        try:
            import os
            current_appearance = self._get_current_appearance()
            
            # Determine the correct logo path based on appearance
            if current_appearance == 'dark':
                logo_filename = 'dark.png'  # Use dark logo for dark theme
            else:
                logo_filename = 'light.png'   # Use light logo for light theme
            
            # Build the path to the logo
            if getattr(sys, 'frozen', False):
                # Running as app bundle
                app_bundle_path = os.path.dirname(sys.executable)
                logo_path = os.path.join(app_bundle_path, '..', 'Resources', 'assets', logo_filename)
            else:
                # Running in development
                script_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(script_dir)
                logo_path = os.path.join(project_root, 'assets', logo_filename)
            
            if os.path.exists(logo_path):
                # Load and set the icon
                logo_image = NSImage.alloc().initWithContentsOfFile_(logo_path)
                if logo_image:
                    # Resize to appropriate dialog icon size
                    logo_image.setSize_(NSMakeSize(64, 64))
                    
                    # Set the icon directly on the NSAlert object
                    if hasattr(alert_object, 'setIcon_'):
                        alert_object.setIcon_(logo_image)
                        print(f"Debug - Dialog icon set using {logo_filename}")
                    else:
                        print(f"Debug - Alert object does not have setIcon_ method")
                else:
                    print(f"Debug - Could not load logo image from {logo_path}")
            else:
                print(f"Debug - Logo file not found at {logo_path}")
                
        except Exception as e:
            print(f"Debug - Error setting dialog icon: {e}")
    
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
        
        # Title at the top
        title_y = 600
        title_label = NSTextField.alloc().initWithFrame_(NSMakeRect(20, title_y, 160, 30))
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
        
        # Create sidebar buttons (positioned after title)
        self.sidebar_buttons = []
        y_position = title_y - 40
        
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
        """Create footer area with buttons"""
        # Footer background
        footer = NSView.alloc().initWithFrame_(NSMakeRect(0, 20, 200, 100))
        footer.setAutoresizingMask_(NSViewMaxYMargin | NSViewWidthSizable)
        
        # Separator line
        separator = NSView.alloc().initWithFrame_(NSMakeRect(20, 80, 160, 1))
        separator.setWantsLayer_(True)
        separator.layer().setBackgroundColor_(NSColor.separatorColor().CGColor())
        footer.addSubview_(separator)
        
        # Cancel button
        cancel_button = NSButton.alloc().initWithFrame_(NSMakeRect(20, 40, 70, 32))
        cancel_button.setTitle_("Cancel")
        cancel_button.setTarget_(self)
        cancel_button.setAction_("cancel:")
        cancel_button.setBezelStyle_(NSBezelStyleRounded)
        cancel_button.setKeyEquivalent_("\033")  # Escape key
        footer.addSubview_(cancel_button)
        
        # Quit button - positioned next to Cancel
        quit_button = NSButton.alloc().initWithFrame_(NSMakeRect(100, 40, 80, 32))
        quit_button.setTitle_("Quit Potter")
        quit_button.setTarget_(self)
        quit_button.setAction_("quitApplication:")
        quit_button.setBezelStyle_(NSBezelStyleRounded)
        quit_button.setFont_(NSFont.systemFontOfSize_(13))
        footer.addSubview_(quit_button)
        
        # Add footer to sidebar container
        self.sidebar_container.addSubview_(footer)
        
        return footer
    
    def createContentArea(self):
        """Create scrollable content area"""
        # Scroll view for content
        self.content_scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(200, 0, 700, 650))
        self.content_scroll_view.setHasVerticalScroller_(True)
        self.content_scroll_view.setAutohidesScrollers_(True)
        self.content_scroll_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        self.content_scroll_view.setBorderType_(NSNoBorder)
        
        # Content container - properly sized for content
        self.content_container = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 700, 900))  # Reasonable height
        self.content_scroll_view.setDocumentView_(self.content_container)
    
    def switchSection_(self, sender):
        """Switch to a different section with animation"""
        section = sender.tag()
        self.showSection_(section)
    
    def showSection_(self, section):
        """Show the specified section with enhanced sidebar highlighting"""
        if section < 0 or section >= len(self.content_views):
            print(f"Debug - Invalid section index: {section}")
            return
        
        # Check if the content view exists and is valid
        if not self.content_views or section >= len(self.content_views):
            print(f"Debug - Content views not ready or invalid section: {section}")
            return
            
        view = self.content_views[section]
        if view is None:
            print(f"Debug - Content view at section {section} is None")
            return

        # Update sidebar button states with proper highlighting
        for i, button in enumerate(self.sidebar_buttons):
            if i == section:
                # Selected state
                button.setState_(NSControlStateValueOn)
                
                # Set selection appearance
                button.setBezelStyle_(NSBezelStyleTexturedRounded)
                button.setBordered_(True)
                
                # Change background color for selection
                if hasattr(NSColor, 'selectedControlColor'):
                    try:
                        # Try to set background color for selection
                        cell = button.cell()
                        if hasattr(cell, 'setBackgroundColor_'):
                            cell.setBackgroundColor_(NSColor.selectedControlColor())
                    except:
                        pass
                
                # Make text bold
                button.setFont_(NSFont.boldSystemFontOfSize_(14))
            else:
                # Unselected state
                button.setState_(NSControlStateValueOff)
                
                # Reset appearance
                button.setBezelStyle_(NSBezelStyleRegularSquare)
                button.setBordered_(False)
                
                # Reset background
                try:
                    cell = button.cell()
                    if hasattr(cell, 'setBackgroundColor_'):
                        cell.setBackgroundColor_(NSColor.clearColor())
                except:
                    pass
                
                # Reset text to normal
                button.setFont_(NSFont.systemFontOfSize_(14))
        
        # Remove current content
        if hasattr(self, 'content_container') and self.content_container:
            for subview in list(self.content_container.subviews()):
                subview.removeFromSuperview()
        else:
            print("Debug - Content container not available")
            return
        
        # Add new content with proper sizing to fit container bounds
        # Additional safety check for view frame
        try:
            view_frame = view.frame()
            if view_frame is None:
                print(f"Debug - View frame is None for section {section}")
                return
            view_height = view_frame.size.height
        except Exception as e:
            print(f"Debug - Error getting view frame for section {section}: {e}")
            # Fallback to a reasonable default height
            view_height = 800
        
        # Get container bounds safely
        try:
            container_bounds = self.content_container.bounds()
            if container_bounds is None:
                print("Debug - Container bounds is None")
                return
        except Exception as e:
            print(f"Debug - Error getting container bounds: {e}")
            return
        
        # Position view at the TOP of the container (not bottom)
        # The y-coordinate should be calculated so content starts at the top
        container_height = max(view_height, 650)  # Minimum scrollable height
        
        try:
            view.setFrame_(NSMakeRect(0, container_height - view_height, container_bounds.size.width, view_height))
            
            # Update container size for proper scrolling
            self.content_container.setFrame_(NSMakeRect(0, 0, container_bounds.size.width, container_height))
            self.content_container.addSubview_(view)
            
            # Scroll to the TOP instead of bottom
            if hasattr(self, 'content_scroll_view') and self.content_scroll_view:
                document_view = self.content_scroll_view.documentView()
                if document_view and hasattr(self.content_scroll_view, 'contentView'):
                    content_view = self.content_scroll_view.contentView()
                    if content_view:
                        content_bounds = content_view.bounds()
                        scroll_point = NSMakePoint(0, container_height - content_bounds.size.height)
                        document_view.scrollPoint_(scroll_point)
        except Exception as e:
            print(f"Debug - Error setting up view for section {section}: {e}")
            return
        
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
        """Create enhanced General settings view with LLM provider selection"""
        # Make content view properly sized to fit content without excessive height
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 700, 900))  # Reduced from 1200
        
        y_pos = 850  # Start much lower to reduce empty space
        
        # Section header
        header = create_section_header("General Settings", y_pos)
        view.addSubview_(header)
        y_pos -= 50
        
        # Separator
        separator = create_section_separator(y_pos)
        view.addSubview_(separator)
        y_pos -= 40
        
        # LLM Provider section
        llm_section_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 620, 20))
        llm_section_label.setStringValue_("AI Provider Configuration")
        llm_section_label.setFont_(NSFont.boldSystemFontOfSize_(16))
        llm_section_label.setBezeled_(False)
        llm_section_label.setDrawsBackground_(False)
        llm_section_label.setEditable_(False)
        llm_section_label.setTextColor_(NSColor.labelColor())
        view.addSubview_(llm_section_label)
        y_pos -= 35
        
        # LLM Provider selection
        provider_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 120, 22))
        provider_label.setStringValue_("Provider:")
        provider_label.setBezeled_(False)
        provider_label.setDrawsBackground_(False)
        provider_label.setEditable_(False)
        provider_label.setFont_(NSFont.systemFontOfSize_(14))
        view.addSubview_(provider_label)
        
        self.provider_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(160, y_pos, 200, 22))
        for provider_id, provider_info in self.settings_manager.llm_providers.items():
            self.provider_popup.addItemWithTitle_(provider_info["name"])
            item = self.provider_popup.itemAtIndex_(self.provider_popup.numberOfItems() - 1)
            item.setRepresentedObject_(provider_id)
        
        # Select current provider
        current_provider = self.settings_manager.get_current_provider()
        for i in range(self.provider_popup.numberOfItems()):
            item = self.provider_popup.itemAtIndex_(i)
            if item.representedObject() == current_provider:
                self.provider_popup.selectItemAtIndex_(i)
                break
        
        self.provider_popup.setTarget_(self)
        self.provider_popup.setAction_("providerChanged:")
        view.addSubview_(self.provider_popup)
        y_pos -= 30
        
        # API Key field with validation - aligned right edge at 580px
        api_key_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 120, 22))
        api_key_label.setStringValue_("API Key:")
        api_key_label.setBezeled_(False)
        api_key_label.setDrawsBackground_(False)
        api_key_label.setEditable_(False)
        api_key_label.setFont_(NSFont.systemFontOfSize_(14))
        view.addSubview_(api_key_label)
        
        self.api_key_field = PasteableTextField.alloc().initWithFrame_(NSMakeRect(160, y_pos, 300, 22))
        self.api_key_field.setFont_(NSFont.monospacedSystemFontOfSize_weight_(12, 0))
        self.api_key_field.setDelegate_(self)  # Set delegate for text change notifications
        # Add text change notification observer
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self, "apiKeyTextChanged:", "NSControlTextDidChangeNotification", self.api_key_field
        )
        view.addSubview_(self.api_key_field)
        
        # Verify & Save button - right edge aligned at 620px
        self.verify_api_button = NSButton.alloc().initWithFrame_(NSMakeRect(510, y_pos, 110, 22))  # x=510, width=110, right edge=620
        self.verify_api_button.setTitle_("Verify & Save")
        self.verify_api_button.setTarget_(self)
        self.verify_api_button.setAction_("verifyAndSaveApiKey:")
        self.verify_api_button.setBezelStyle_(NSBezelStyleRounded)
        self.verify_api_button.setFont_(NSFont.systemFontOfSize_(11))
        view.addSubview_(self.verify_api_button)
        
        # API Key validation status (moved down)
        self.api_validation_label = NSTextField.alloc().initWithFrame_(NSMakeRect(160, y_pos - 25, 400, 20))
        self.api_validation_label.setBezeled_(False)
        self.api_validation_label.setDrawsBackground_(False)
        self.api_validation_label.setEditable_(False)
        self.api_validation_label.setFont_(NSFont.systemFontOfSize_(11))
        self.api_validation_label.setStringValue_("")
        view.addSubview_(self.api_validation_label)
        
        # Spinner for verification (initially hidden)
        self.verification_spinner = None
        y_pos -= 50  # Extra space for validation label
        
        # API help text with clickable link
        help_text_label = NSTextField.alloc().initWithFrame_(NSMakeRect(160, y_pos, 120, 17))
        help_text_label.setStringValue_("Get your API key from")
        help_text_label.setBezeled_(False)
        help_text_label.setDrawsBackground_(False)
        help_text_label.setEditable_(False)
        help_text_label.setFont_(NSFont.systemFontOfSize_(11))
        help_text_label.setTextColor_(NSColor.secondaryLabelColor())
        view.addSubview_(help_text_label)
        
        # Clickable link (will be updated based on provider)
        self.api_help_link = create_clickable_link(
            NSMakeRect(280, y_pos, 200, 17),
            "provider website",
            "https://platform.openai.com/api-keys"
        )
        view.addSubview_(self.api_help_link)
        y_pos -= 35
        
        # Model selection (below provider)
        model_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 120, 22))
        model_label.setStringValue_("Model:")
        model_label.setBezeled_(False)
        model_label.setDrawsBackground_(False)
        model_label.setEditable_(False)
        model_label.setFont_(NSFont.systemFontOfSize_(14))
        view.addSubview_(model_label)
        
        self.model_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(160, y_pos, 250, 22))
        self.model_popup.setTarget_(self)
        self.model_popup.setAction_("modelChanged:")
        
        # Configure immediate tooltip display for model dropdown
        try:
            # Set tooltip delay to 0 for immediate display on this popup
            if hasattr(self.model_popup, 'cell') and self.model_popup.cell():
                cell = self.model_popup.cell()
                if hasattr(cell, 'setShowsFirstResponder_'):
                    cell.setShowsFirstResponder_(True)
            # Also configure general tooltip behavior for faster display
            if hasattr(NSToolTipManager, 'sharedToolTipManager'):
                tooltip_manager = NSToolTipManager.sharedToolTipManager()
                if hasattr(tooltip_manager, 'setInitialToolTipDelay_'):
                    tooltip_manager.setInitialToolTipDelay_(0.1)  # Very fast display (100ms)
                if hasattr(tooltip_manager, 'setReshowToolTipDelay_'):
                    tooltip_manager.setReshowToolTipDelay_(0.0)  # Immediate re-display
            print("Debug - Configured fast tooltip display for model dropdown")
        except Exception as e:
            print(f"Debug - Error configuring tooltip: {e}")
        
        view.addSubview_(self.model_popup)
        y_pos -= 50
        
        # Hotkey section
        hotkey_section_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 620, 20))
        hotkey_section_label.setStringValue_("Global Hotkey")
        hotkey_section_label.setFont_(NSFont.boldSystemFontOfSize_(16))
        hotkey_section_label.setBezeled_(False)
        hotkey_section_label.setDrawsBackground_(False)
        hotkey_section_label.setEditable_(False)
        hotkey_section_label.setTextColor_(NSColor.labelColor())
        view.addSubview_(hotkey_section_label)
        y_pos -= 35
        
        # Hotkey field - right edge aligned at 580px
        hotkey_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 120, 22))
        hotkey_label.setStringValue_("Hotkey:")
        hotkey_label.setBezeled_(False)
        hotkey_label.setDrawsBackground_(False)
        hotkey_label.setEditable_(False)
        hotkey_label.setFont_(NSFont.systemFontOfSize_(14))
        view.addSubview_(hotkey_label)
        
        # Create hotkey capture control
        self.hotkey_field = HotkeyCapture.alloc().initWithFrame_manager_(
            NSMakeRect(160, y_pos, 350, 30),
            self.settings_manager
        )
        self.hotkey_field.reset_callback = self.hotkeyChanged
        view.addSubview_(self.hotkey_field)
        
        # Reset button - right edge aligned at 620px
        self.reset_button = NSButton.alloc().initWithFrame_(NSMakeRect(540, y_pos, 80, 22))  # x=540, width=80, right edge=620
        self.reset_button.setTitle_("Reset")
        self.reset_button.setTarget_(self)
        self.reset_button.setAction_("resetHotkey:")
        self.reset_button.setBezelStyle_(NSBezelStyleRounded)
        self.reset_button.setFont_(NSFont.systemFontOfSize_(11))
        view.addSubview_(self.reset_button)
        y_pos -= 30
        
        # Conflict warning label
        self.conflict_label = NSTextField.alloc().initWithFrame_(NSMakeRect(160, y_pos, 350, 17))
        self.conflict_label.setBezeled_(False)
        self.conflict_label.setDrawsBackground_(False)
        self.conflict_label.setEditable_(False)
        self.conflict_label.setFont_(NSFont.systemFontOfSize_(11))
        self.conflict_label.setTextColor_(NSColor.systemOrangeColor())
        self.conflict_label.setStringValue_("")
        self.conflict_label.setHidden_(True)
        view.addSubview_(self.conflict_label)
        y_pos -= 50
        
        # Permissions section
        permissions_section_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 620, 20))
        permissions_section_label.setStringValue_("Permissions")
        permissions_section_label.setFont_(NSFont.boldSystemFontOfSize_(16))
        permissions_section_label.setBezeled_(False)
        permissions_section_label.setDrawsBackground_(False)
        permissions_section_label.setEditable_(False)
        permissions_section_label.setTextColor_(NSColor.labelColor())
        view.addSubview_(permissions_section_label)
        y_pos -= 35
        
        # Get permissions status
        permissions = self.get_permissions_status()
        
        # Accessibility permission
        accessibility_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 160, 22))
        accessibility_label.setStringValue_("Accessibility Permission:")
        accessibility_label.setBezeled_(False)
        accessibility_label.setDrawsBackground_(False)
        accessibility_label.setEditable_(False)
        accessibility_label.setFont_(NSFont.systemFontOfSize_(14))
        view.addSubview_(accessibility_label)
        
        # Accessibility status
        self.accessibility_status = NSTextField.alloc().initWithFrame_(NSMakeRect(210, y_pos, 80, 22))
        accessibility_granted = permissions.get("accessibility", False)
        self.accessibility_status.setStringValue_("✓ Granted" if accessibility_granted else "✗ Denied")
        self.accessibility_status.setBezeled_(False)
        self.accessibility_status.setDrawsBackground_(False)
        self.accessibility_status.setEditable_(False)
        self.accessibility_status.setFont_(NSFont.systemFontOfSize_(14))
        self.accessibility_status.setTextColor_(NSColor.systemGreenColor() if accessibility_granted else NSColor.systemRedColor())
        view.addSubview_(self.accessibility_status)
        
        # Accessibility button - right edge aligned at 620px
        self.accessibility_button = NSButton.alloc().initWithFrame_(NSMakeRect(500, y_pos, 120, 22))  # x=500, width=120, right edge=620
        self.accessibility_button.setTitle_("Open Settings")
        self.accessibility_button.setTarget_(self)
        self.accessibility_button.setAction_("openAccessibilitySettings:")
        self.accessibility_button.setBezelStyle_(NSBezelStyleRounded)
        self.accessibility_button.setFont_(NSFont.systemFontOfSize_(11))
        view.addSubview_(self.accessibility_button)
        y_pos -= 35
        
        # System Events permission
        system_events_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 160, 22))
        system_events_label.setStringValue_("System Events Permission:")
        system_events_label.setBezeled_(False)
        system_events_label.setDrawsBackground_(False)
        system_events_label.setEditable_(False)
        system_events_label.setFont_(NSFont.systemFontOfSize_(14))
        view.addSubview_(system_events_label)
        
        # System Events status
        self.system_events_status = NSTextField.alloc().initWithFrame_(NSMakeRect(210, y_pos, 80, 22))
        system_events_granted = permissions.get("system_events", False)
        self.system_events_status.setStringValue_("✓ Granted" if system_events_granted else "✗ Denied")
        self.system_events_status.setBezeled_(False)
        self.system_events_status.setDrawsBackground_(False)
        self.system_events_status.setEditable_(False)
        self.system_events_status.setFont_(NSFont.systemFontOfSize_(14))
        self.system_events_status.setTextColor_(NSColor.systemGreenColor() if system_events_granted else NSColor.systemRedColor())
        view.addSubview_(self.system_events_status)
        
        # System Events button - right edge aligned at 620px
        self.system_events_button = NSButton.alloc().initWithFrame_(NSMakeRect(500, y_pos, 120, 22))  # x=500, width=120, right edge=620
        self.system_events_button.setTitle_("Open Settings")
        self.system_events_button.setTarget_(self)
        self.system_events_button.setAction_("openSystemSettings:")
        self.system_events_button.setBezelStyle_(NSBezelStyleRounded)
        self.system_events_button.setFont_(NSFont.systemFontOfSize_(11))
        view.addSubview_(self.system_events_button)
        y_pos -= 35
        
        # Refresh permissions button - right edge aligned at 620px
        self.refresh_permissions_button = NSButton.alloc().initWithFrame_(NSMakeRect(480, y_pos, 140, 22))  # x=480, width=140, right edge=620
        self.refresh_permissions_button.setTitle_("Refresh Status")
        self.refresh_permissions_button.setTarget_(self)
        self.refresh_permissions_button.setAction_("refreshPermissions:")
        self.refresh_permissions_button.setBezelStyle_(NSBezelStyleRounded)
        self.refresh_permissions_button.setFont_(NSFont.systemFontOfSize_(11))
        view.addSubview_(self.refresh_permissions_button)
        y_pos -= 50
        
        # Application Preferences section (moved to bottom)
        prefs_section_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 620, 20))
        prefs_section_label.setStringValue_("Application Preferences")
        prefs_section_label.setFont_(NSFont.boldSystemFontOfSize_(16))
        prefs_section_label.setBezeled_(False)
        prefs_section_label.setDrawsBackground_(False)
        prefs_section_label.setEditable_(False)
        prefs_section_label.setTextColor_(NSColor.labelColor())
        view.addSubview_(prefs_section_label)
        y_pos -= 35
        
        # Notifications toggle - align right edge at 620
        notifications_container, self.notifications_switch = create_modern_switch(
            NSMakeRect(40, y_pos, 580, 30),  # Extended width to align right edge at 620
            "Show notifications",
            self.settings_manager.get("show_notifications", False)
        )
        self.notifications_switch.setTarget_(self)
        self.notifications_switch.setAction_("notificationsSwitchChanged:")
        view.addSubview_(notifications_container)
        y_pos -= 40
        
        # Launch at startup toggle - align right edge at 620
        startup_container, self.startup_switch = create_modern_switch(
            NSMakeRect(40, y_pos, 580, 30),  # Extended width to align right edge at 620
            "Launch at startup",
            self.settings_manager.get("launch_at_startup", False)
        )
        self.startup_switch.setTarget_(self)
        self.startup_switch.setAction_("startupSwitchChanged:")
        view.addSubview_(startup_container)
        
        # Load current values
        self.updateProviderUI()
        self.updateResetButton()
        
        return view
    
    def providerChanged_(self, sender):
        """Handle LLM provider change"""
        selected_item = sender.selectedItem()
        if selected_item:
            provider_id = selected_item.representedObject()
            self.settings_manager.settings["llm_provider"] = provider_id
            self.updateProviderUI()
            
            # Auto-save change
            self.autoSaveCurrentSettings()
            print(f"Debug - Auto-saved provider change to: {provider_id}")

    def modelChanged_(self, sender):
        """Handle model selection change"""
        # Auto-save change
        self.autoSaveCurrentSettings()
        print(f"Debug - Auto-saved model change")

    def notificationsSwitchChanged_(self, sender):
        """Handle notifications switch change"""
        notification_enabled = bool(sender.state())
        
        # Handle OS permissions when enabling notifications
        if notification_enabled:
            if not self.settings_manager.get_os_notification_status():
                self.requestNotificationPermission_(None)
        
        # Auto-save change
        self.autoSaveCurrentSettings()
        print(f"Debug - Auto-saved notifications change to: {notification_enabled}")

    def startupSwitchChanged_(self, sender):
        """Handle startup switch change"""
        startup_enabled = bool(sender.state())
        
        # Update OS startup setting
        self.updateStartupSetting_(startup_enabled)
        
        # Auto-save change
        self.autoSaveCurrentSettings()
        print(f"Debug - Auto-saved startup change to: {startup_enabled}")

    def hotkeyChanged(self):
        """Handle hotkey change and auto-save"""
        if hasattr(self, 'hotkey_field'):
            # Auto-save hotkey change
            current_settings = self.settings_manager.get_all_settings()
            current_settings["hotkey"] = self.hotkey_field.getHotkeyString()
            success = self.settings_manager.save_settings(current_settings)
            print(f"Debug - Auto-saved hotkey change: {success}")
            
            # Update reset button state
            self.updateResetButton()

    def apiKeyTextChanged_(self, notification):
        """Handle API key text changes for real-time validation"""
        try:
            if not hasattr(self, 'api_key_field'):
                return
                
            api_key = str(self.api_key_field.stringValue()).strip()
            current_provider = self.get_current_provider()
            
            # Clear red background and text color on text change
            self.api_key_field.setBackgroundColor_(NSColor.controlBackgroundColor())
            self.api_key_field.setTextColor_(NSColor.labelColor())
            
            if not api_key:
                self._update_api_validation_display("", None)
                return
            
            # Use the LLM client's validation instead of inline logic
            from utils.llm_client import LLMClientManager
            llm_manager = LLMClientManager()
            
            is_valid, error_msg = llm_manager.validate_api_key(current_provider, api_key)
            
            if is_valid:
                self._update_api_validation_display("✓ Format looks valid - click 'Verify & Save' to test", None)
                self.api_key_field.setBackgroundColor_(NSColor.controlBackgroundColor())
                self.api_key_field.setTextColor_(NSColor.labelColor())
            else:
                self._update_api_validation_display(f"⚠️ {error_msg}", False)
                self.api_key_field.setBackgroundColor_(NSColor.systemYellowColor().colorWithAlphaComponent_(0.2))
                self.api_key_field.setTextColor_(NSColor.systemOrangeColor())
                
            # Auto-save as user types (delayed)
            if hasattr(self, 'api_key_save_timer'):
                self.api_key_save_timer.invalidate()
            
            # Save after 1 second of no typing
            self.api_key_save_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                1.0, self, "delayedApiKeySave:", None, False
            )
            
        except Exception as e:
            print(f"Error in apiKeyTextChanged: {e}")
    
    def delayedApiKeySave_(self, timer):
        """Save API key after delay"""
        try:
            if not hasattr(self, 'api_key_field'):
                return
                
            api_key = str(self.api_key_field.stringValue()).strip()
            current_provider = self.get_current_provider()
            
            # Auto-save the key
            settings = self.settings_manager.get_all_settings()
            settings[f"{current_provider}_api_key"] = api_key
            self.settings_manager.save_settings(settings)
            
        except Exception as e:
            print(f"Error in delayed API key save: {e}")

    def verifyAndSaveApiKey_(self, sender):
        """Verify API key with real API call and save if valid"""
        api_key = str(self.api_key_field.stringValue()).strip()
        if not api_key:
            self._update_api_validation_display("Please enter an API key", False)
            self.api_key_field.setBackgroundColor_(NSColor.systemRedColor().colorWithAlphaComponent_(0.2))
            return
        
        # Get current provider
        current_provider = self.settings_manager.get("llm_provider", "openai")
        
        # Clear any background color and show verifying state
        self.api_key_field.setBackgroundColor_(NSColor.controlBackgroundColor())
        self.verify_api_button.setEnabled_(False)
        self.verify_api_button.setTitle_("Verifying...")
        self._update_api_validation_display("🔄 Verifying API key...", None)
        
        # Start verification in background
        self._start_api_verification(api_key, current_provider)

    def _update_api_validation_display(self, message, is_valid):
        """Show API validation message with appropriate styling"""
        self.api_validation_label.setStringValue_(message)
        
        if is_valid is None:  # Neutral/loading state
            self.api_validation_label.setTextColor_(NSColor.secondaryLabelColor())
        elif is_valid:  # Success
            self.api_validation_label.setTextColor_(NSColor.systemGreenColor())
        else:  # Error
            self.api_validation_label.setTextColor_(NSColor.systemRedColor())

    def _start_api_verification(self, api_key, provider):
        """Start API verification in background thread"""
        import threading
        
        def verify_in_background():
            try:
                # Use LLM client's test method
                from utils.llm_client import LLMClientManager
                llm_manager = LLMClientManager()
                
                success, error_msg = llm_manager.test_api_key(provider, api_key)
                
                # Update UI on main thread
                def update_ui():
                    self._handle_api_verification_result(success, provider, api_key, error_msg)
                
                # Schedule UI update on main thread
                self.performSelectorOnMainThread_withObject_waitUntilDone_("_updateUIFromVerification:", update_ui, False)
                
            except Exception as e:
                print(f"Debug - API verification error: {e}")
                # Update UI with error on main thread  
                def update_ui_error():
                    self._handle_api_verification_result(False, provider, api_key, str(e))
                
                self.performSelectorOnMainThread_withObject_waitUntilDone_("_updateUIFromVerification:", update_ui_error, False)
        
        # Start background thread
        thread = threading.Thread(target=verify_in_background)
        thread.daemon = True
        thread.start()

    def _update_ui_from_verification(self, update_func):
        """Helper to update UI from background thread"""
        if update_func:
            update_func()
    
    def _updateUIFromVerification_(self, update_func):
        """Objective-C compatible selector for main thread updates"""
        self._update_ui_from_verification(update_func)

    def _handle_api_verification_result(self, success, provider, api_key, error_msg=None):
        """Handle API verification result and update UI"""
        # Reset button state
        self.verify_api_button.setEnabled_(True)
        self.verify_api_button.setTitle_("Verify & Save")
        
        if success:
            # Save the API key
            current_settings = self.settings_manager.get_all_settings()
            current_settings[f"{provider}_api_key"] = api_key
            save_success = self.settings_manager.save_settings(current_settings)
            
            if save_success:
                self._update_api_validation_display("✅ API key verified and saved!", True)
                # Reset field styling to normal
                self.api_key_field.setBackgroundColor_(NSColor.controlBackgroundColor())
                self.api_key_field.setTextColor_(NSColor.labelColor())
                # Clear the temporary green message after 3 seconds
                self._schedule_validation_clear()
            else:
                self._update_api_validation_display("❌ Verification passed but failed to save", False)
                self.api_key_field.setBackgroundColor_(NSColor.systemRedColor().colorWithAlphaComponent_(0.2))
                self.api_key_field.setTextColor_(NSColor.systemRedColor())
        else:
            error_msg = error_msg or "Invalid API key"
            self._update_api_validation_display(f"❌ {error_msg}", False)
            # Make field red on error
            self.api_key_field.setBackgroundColor_(NSColor.systemRedColor().colorWithAlphaComponent_(0.2))
            self.api_key_field.setTextColor_(NSColor.systemRedColor())

    def _schedule_validation_clear(self):
        """Clear validation message after delay"""
        def clear_message():
            if hasattr(self, 'api_validation_label'):
                self.api_validation_label.setStringValue_("")
        
        # Schedule clearing after 3 seconds
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            3.0, self, "clearValidationMessage:", None, False
        )

    def clearValidationMessage_(self, timer):
        """Clear the validation message"""
        if hasattr(self, 'api_validation_label'):
            self.api_validation_label.setStringValue_("")
    
    def updateProviderUI(self):
        """Update UI elements based on selected provider"""
        current_provider = self.settings_manager.get_current_provider()
        provider_info = self.settings_manager.llm_providers.get(current_provider, {})
        
        # Update API key field
        api_key = self.settings_manager.get(f"{current_provider}_api_key", "")
        self.api_key_field.setStringValue_(api_key)
        
        # Update field styling based on API key presence
        if not api_key.strip():
            self.api_key_field.setTextColor_(NSColor.systemRedColor())
            self.api_key_field.setBackgroundColor_(NSColor.systemRedColor().colorWithAlphaComponent_(0.1))
            self.api_key_field.setPlaceholderString_(f"API key required for {provider_info.get('name', 'provider')}")
        else:
            self.api_key_field.setTextColor_(NSColor.labelColor())
            self.api_key_field.setBackgroundColor_(NSColor.controlBackgroundColor())
            # Update placeholder
            prefix = provider_info.get("api_key_prefix", "")
            self.api_key_field.setPlaceholderString_(f"{prefix}...")
        
        # Update clickable link
        help_url = provider_info.get("help_url", "")
        provider_name = provider_info.get("name", "provider")
        self.api_help_link.setTitle_(f"{provider_name} website")
        
        # Update the URL in the link target
        target = self.api_help_link.representedObject()
        if target and hasattr(target, 'url'):
            target.url = help_url
        
        # Update validation status
        validation = self.settings_manager.get_api_key_validation(current_provider)
        self.updateApiValidationDisplay_(validation)
        
        # Update model list
        self.updateModelList()
    
    def updateModelList(self):
        """Update model dropdown based on current provider with descriptions"""
        current_provider = self.settings_manager.get_current_provider()
        provider_info = self.settings_manager.llm_providers.get(current_provider, {})
        models = provider_info.get("models", [])
        
        # Clear current items
        self.model_popup.removeAllItems()
        
        # Add models for current provider with descriptions
        for model in models:
            if isinstance(model, dict):
                # New format with id, name, and description
                model_id = model.get("id", "")
                model_name = model.get("name", model_id)
                model_description = model.get("description", "")
                detailed_description = model.get("detailed_description", model_description)
                
                # Create display text with name and description
                display_text = f"{model_name} - {model_description}"
                self.model_popup.addItemWithTitle_(display_text)
                
                # Store the model ID in the represented object for saving
                item = self.model_popup.itemAtIndex_(self.model_popup.numberOfItems() - 1)
                item.setRepresentedObject_(model_id)
                
                # Set tooltip with detailed description for immediate display
                try:
                    item.setToolTip_(detailed_description)
                except Exception as e:
                    print(f"Debug - Could not set tooltip: {e}")
                    
            else:
                # Backward compatibility - old string format
                self.model_popup.addItemWithTitle_(model)
                item = self.model_popup.itemAtIndex_(self.model_popup.numberOfItems() - 1)
                item.setRepresentedObject_(model)
        
        # Select current model by matching the stored model ID
        current_model = self.settings_manager.get("model", "")
        model_selected = False
        
        for i in range(self.model_popup.numberOfItems()):
            item = self.model_popup.itemAtIndex_(i)
            stored_id = item.representedObject()
            if stored_id == current_model:
                self.model_popup.selectItemAtIndex_(i)
                model_selected = True
                break
        
        # If no match found and we have models, select the first one
        if not model_selected and self.model_popup.numberOfItems() > 0:
            self.model_popup.selectItemAtIndex_(0)
            
        # Enable tooltips on the popup button itself
        try:
            self.model_popup.setToolTip_("Hover over dropdown items for detailed model information")
        except Exception as e:
            print(f"Debug - Could not set popup tooltip: {e}")
    
    def updateApiValidationDisplay_(self, validation):
        """Update API key validation display"""
        if validation["valid"] is None:
            self.api_validation_label.setStringValue_("")
        elif validation["valid"]:
            self.api_validation_label.setStringValue_("✅ Valid")
            self.api_validation_label.setTextColor_(NSColor.systemGreenColor())
        else:
            error_msg = validation.get("error", "Invalid key")
            self.api_validation_label.setStringValue_(f"❌ {error_msg}")
            self.api_validation_label.setTextColor_(NSColor.systemRedColor())
    
    def createPromptsView(self):
        """Create modern Prompts settings view"""
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 700, 600))  # Proper height
        
        y_pos = 550  # Start higher to reduce empty space
        
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
        
        # Toolbar with buttons - ensure they're visible
        toolbar_container = NSView.alloc().initWithFrame_(NSMakeRect(40, y_pos, y_pos-40, 30))
        
        # Info label instead of action buttons at top
        info_label = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 5, 400, 20))
        info_label.setStringValue_("Double-click to edit. Use + and - buttons to add/remove.")
        info_label.setBezeled_(False)
        info_label.setDrawsBackground_(False)
        info_label.setEditable_(False)
        info_label.setFont_(NSFont.systemFontOfSize_(11))
        info_label.setTextColor_(NSColor.secondaryLabelColor())
        toolbar_container.addSubview_(info_label)
        
        view.addSubview_(toolbar_container)
        y_pos -= 20
        
        # Table view container - made even smaller
        table_container = NSScrollView.alloc().initWithFrame_(NSMakeRect(40, y_pos - 200, 620, 200))  # Much smaller table
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
        self.prompts_table.setTarget_(self)
        self.prompts_table.setDoubleAction_("editPrompt:")  # Double-click to edit
        
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
        
        # OSX-style controls at bottom of table - adjusted for smaller table
        controls_container = NSView.alloc().initWithFrame_(NSMakeRect(40, y_pos - 250, 620, 30))
        
        # + button (add)
        add_btn = NSButton.alloc().initWithFrame_(NSMakeRect(0, 5, 30, 20))
        add_btn.setTitle_("+")
        add_btn.setTarget_(self)
        add_btn.setAction_("addPrompt:")
        add_btn.setBezelStyle_(NSBezelStyleRoundRect)
        add_btn.setFont_(NSFont.boldSystemFontOfSize_(14))
        add_btn.setBordered_(True)
        controls_container.addSubview_(add_btn)
        
        # - button (remove)
        remove_btn = NSButton.alloc().initWithFrame_(NSMakeRect(35, 5, 30, 20))
        remove_btn.setTitle_("-")
        remove_btn.setTarget_(self)
        remove_btn.setAction_("removePrompt:")
        remove_btn.setBezelStyle_(NSBezelStyleRoundRect)
        remove_btn.setFont_(NSFont.boldSystemFontOfSize_(14))
        remove_btn.setBordered_(True)
        controls_container.addSubview_(remove_btn)
        
        # Status/count label
        self.prompts_count_label = NSTextField.alloc().initWithFrame_(NSMakeRect(80, 8, 200, 15))
        self.prompts_count_label.setBezeled_(False)
        self.prompts_count_label.setDrawsBackground_(False)
        self.prompts_count_label.setEditable_(False)
        self.prompts_count_label.setFont_(NSFont.systemFontOfSize_(11))
        self.prompts_count_label.setTextColor_(NSColor.secondaryLabelColor())
        controls_container.addSubview_(self.prompts_count_label)
        
        view.addSubview_(controls_container)
        
        # Load prompts data
        self.prompts_data = list(self.settings_manager.get("prompts", []))
        print(f"Debug - Loaded {len(self.prompts_data)} prompts for table view")
        
        # Log each prompt loaded
        for i, prompt in enumerate(self.prompts_data):
            print(f"Debug - Loaded prompt {i+1}: name='{prompt.get('name')}', text_length={len(prompt.get('text', ''))}")
        
        # Reload table data and update count
        if hasattr(self, 'prompts_table'):
            self.prompts_table.reloadData()
            print("Debug - Prompts table reloaded with data")
        
        self.updatePromptsCount()
        
        return view
    
    def createAdvancedView(self):
        """Create Advanced settings view focused on build version information"""
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 700, 700))  # Proper height
        
        y_pos = 650  # Start higher to reduce empty space
        
        # Section header
        header = create_section_header("Advanced Settings", y_pos)
        view.addSubview_(header)
        y_pos -= 50
        
        # Separator
        separator = create_section_separator(y_pos)
        view.addSubview_(separator)
        y_pos -= 40
        
        # Build Information section
        build_section_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 620, 20))
        build_section_label.setStringValue_("Build Information")
        build_section_label.setFont_(NSFont.boldSystemFontOfSize_(16))
        build_section_label.setBezeled_(False)
        build_section_label.setDrawsBackground_(False)
        build_section_label.setEditable_(False)
        build_section_label.setTextColor_(NSColor.labelColor())
        view.addSubview_(build_section_label)
        y_pos -= 35
        
        # Load build information
        try:
            from utils.instance_checker import load_build_id
            build_info = load_build_id()
        except Exception as e:
            print(f"Could not load build info: {e}")
            build_info = {
                "build_id": "unknown",
                "version": "unknown",
                "timestamp": "unknown"
            }
        
        # Build ID
        build_id_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 120, 22))
        build_id_label.setStringValue_("Build ID:")
        build_id_label.setBezeled_(False)
        build_id_label.setDrawsBackground_(False)
        build_id_label.setEditable_(False)
        build_id_label.setFont_(NSFont.systemFontOfSize_(14))
        view.addSubview_(build_id_label)
        
        build_id_value = NSTextField.alloc().initWithFrame_(NSMakeRect(160, y_pos, 400, 22))
        build_id_value.setStringValue_(str(build_info.get("build_id", "unknown")))
        build_id_value.setBezeled_(False)
        build_id_value.setDrawsBackground_(False)
        build_id_value.setEditable_(False)
        build_id_value.setFont_(NSFont.monospacedSystemFontOfSize_weight_(12, 0))
        build_id_value.setTextColor_(NSColor.labelColor())
        view.addSubview_(build_id_value)
        y_pos -= 30
        
        # Version
        version_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 120, 22))
        version_label.setStringValue_("Version:")
        version_label.setBezeled_(False)
        version_label.setDrawsBackground_(False)
        version_label.setEditable_(False)
        version_label.setFont_(NSFont.systemFontOfSize_(14))
        view.addSubview_(version_label)
        
        version_value = NSTextField.alloc().initWithFrame_(NSMakeRect(160, y_pos, 400, 22))
        version_value.setStringValue_(str(build_info.get("version", "unknown")))
        version_value.setBezeled_(False)
        version_value.setDrawsBackground_(False)
        version_value.setEditable_(False)
        version_value.setFont_(NSFont.monospacedSystemFontOfSize_weight_(12, 0))
        version_value.setTextColor_(NSColor.labelColor())
        view.addSubview_(version_value)
        y_pos -= 30
        
        # Build Timestamp
        timestamp_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 120, 22))
        timestamp_label.setStringValue_("Built:")
        timestamp_label.setBezeled_(False)
        timestamp_label.setDrawsBackground_(False)
        timestamp_label.setEditable_(False)
        timestamp_label.setFont_(NSFont.systemFontOfSize_(14))
        view.addSubview_(timestamp_label)
        
        timestamp_value = NSTextField.alloc().initWithFrame_(NSMakeRect(160, y_pos, 400, 22))
        build_timestamp = build_info.get("timestamp", "unknown")
        if build_timestamp != "unknown":
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(build_timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%B %d, %Y at %I:%M %p")
                timestamp_value.setStringValue_(formatted_time)
            except:
                timestamp_value.setStringValue_(str(build_timestamp))
        else:
            timestamp_value.setStringValue_("unknown")
        timestamp_value.setBezeled_(False)
        timestamp_value.setDrawsBackground_(False)
        timestamp_value.setEditable_(False)
        timestamp_value.setFont_(NSFont.monospacedSystemFontOfSize_weight_(12, 0))
        timestamp_value.setTextColor_(NSColor.labelColor())
        view.addSubview_(timestamp_value)
        y_pos -= 50
        
        # Environment Information
        env_section_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 620, 20))
        env_section_label.setStringValue_("Environment Information")
        env_section_label.setFont_(NSFont.boldSystemFontOfSize_(16))
        env_section_label.setBezeled_(False)
        env_section_label.setDrawsBackground_(False)
        env_section_label.setEditable_(False)
        env_section_label.setTextColor_(NSColor.labelColor())
        view.addSubview_(env_section_label)
        y_pos -= 35
        
        # Execution mode
        import sys
        exec_mode_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 120, 22))
        exec_mode_label.setStringValue_("Mode:")
        exec_mode_label.setBezeled_(False)
        exec_mode_label.setDrawsBackground_(False)
        exec_mode_label.setEditable_(False)
        exec_mode_label.setFont_(NSFont.systemFontOfSize_(14))
        view.addSubview_(exec_mode_label)
        
        exec_mode_value = NSTextField.alloc().initWithFrame_(NSMakeRect(160, y_pos, 400, 22))
        mode = "App Bundle" if getattr(sys, 'frozen', False) else "Development"
        exec_mode_value.setStringValue_(mode)
        exec_mode_value.setBezeled_(False)
        exec_mode_value.setDrawsBackground_(False)
        exec_mode_value.setEditable_(False)
        exec_mode_value.setFont_(NSFont.monospacedSystemFontOfSize_weight_(12, 0))
        exec_mode_value.setTextColor_(NSColor.labelColor())
        view.addSubview_(exec_mode_value)
        y_pos -= 30
        
        # Python version
        python_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 120, 22))
        python_label.setStringValue_("Python:")
        python_label.setBezeled_(False)
        python_label.setDrawsBackground_(False)
        python_label.setEditable_(False)
        python_label.setFont_(NSFont.systemFontOfSize_(14))
        view.addSubview_(python_label)
        
        python_value = NSTextField.alloc().initWithFrame_(NSMakeRect(160, y_pos, 400, 22))
        python_value.setStringValue_(f"{sys.version.split()[0]}")
        python_value.setBezeled_(False)
        python_value.setDrawsBackground_(False)
        python_value.setEditable_(False)
        python_value.setFont_(NSFont.monospacedSystemFontOfSize_weight_(12, 0))
        python_value.setTextColor_(NSColor.labelColor())
        view.addSubview_(python_value)
        y_pos -= 30
        
        # macOS version
        import platform
        macos_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_pos, 120, 22))
        macos_label.setStringValue_("macOS:")
        macos_label.setBezeled_(False)
        macos_label.setDrawsBackground_(False)
        macos_label.setEditable_(False)
        macos_label.setFont_(NSFont.systemFontOfSize_(14))
        view.addSubview_(macos_label)
        
        macos_value = NSTextField.alloc().initWithFrame_(NSMakeRect(160, y_pos, 400, 22))
        macos_value.setStringValue_(platform.mac_ver()[0])
        macos_value.setBezeled_(False)
        macos_value.setDrawsBackground_(False)
        macos_value.setEditable_(False)
        macos_value.setFont_(NSFont.monospacedSystemFontOfSize_weight_(12, 0))
        macos_value.setTextColor_(NSColor.labelColor())
        view.addSubview_(macos_value)
        
        return view
    
    def createLogsView(self):
        """Create modern Logs view"""
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 700, 800))  # Proper height
        
        y_pos = 750  # Start higher to reduce empty space
        
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
        
        # Toolbar with controls - ensure they're visible
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
        
        # Logs scroll view - moved up to reduce gap
        logs_container = NSScrollView.alloc().initWithFrame_(NSMakeRect(40, 160, 620, y_pos - 140))  # Moved table up from y=80 to y=120
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
        
        # Status label - moved up to match the new table position
        self.log_status_label = NSTextField.alloc().initWithFrame_(NSMakeRect(40, 130, 620, 17))  # Moved up from y=50 to y=90
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
        from pathlib import Path
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller bundle - log to user's home directory
            return str(Path.home() / 'Library' / 'Logs' / 'potter.log')
        else:
            # Running from source - log to project directory (src/potter.log)
            # Get the src directory path
            src_path = Path(__file__).parent
            return str(src_path / 'potter.log')
    
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
            
            # Read the file efficiently - only keep last 200 lines for performance
            with open(log_file_path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
            
            # Keep only the last 200 lines for performance
            MAX_LINES = 200
            total_lines_in_file = len(all_lines)
            
            if total_lines_in_file > MAX_LINES:
                lines = all_lines[-MAX_LINES:]
                truncated = True
            else:
                lines = all_lines
                truncated = False
            
            content = ''.join(lines)
            self.full_log_content = content
            self.last_log_size = file_size
            
            # Apply current filter
            self.filterLogsContent()
            
            # Update status
            displayed_lines = len(lines)
            
            if truncated:
                self.log_status_label.setStringValue_(f"Showing last {displayed_lines} of {total_lines_in_file} log entries (performance limited)")
            else:
                self.log_status_label.setStringValue_(f"Loaded {displayed_lines} log entries from {log_file_path}")
            
            # Auto-scroll to bottom (enabled by default for logs)
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
            lines = self.full_log_content.splitlines()
            filtered_lines_count = len(lines)
        else:
            # Better filtering logic - look for log level patterns
            lines = self.full_log_content.splitlines()
            filtered_lines = []
            
            # Define log level patterns to search for
            level_patterns = {
                "Error": ["ERROR", "Error", "error", "CRITICAL", "Critical"],
                "Warning": ["WARNING", "Warning", "warning", "WARN", "Warn"],
                "Info": ["INFO", "Info", "info"],
                "Debug": ["DEBUG", "Debug", "debug"]
            }
            
            patterns = level_patterns.get(selected_level, [selected_level])
            
            for line in lines:
                # Check if any pattern matches in the line
                if any(pattern in line for pattern in patterns):
                    filtered_lines.append(line)
            
            # Apply same 200-line limit to filtered content for performance
            MAX_LINES = 200
            if len(filtered_lines) > MAX_LINES:
                filtered_lines = filtered_lines[-MAX_LINES:]
                
            filtered_content = '\n'.join(filtered_lines)
            filtered_lines_count = len(filtered_lines)
            
            # Update status to show filter results
            if hasattr(self, 'log_status_label'):
                total_lines = len(lines) if lines else 0
                if len(filtered_lines) >= MAX_LINES:
                    self.log_status_label.setStringValue_(f"Showing last {filtered_lines_count} of {filtered_lines_count}+ entries (filtered by {selected_level}, performance limited)")
                else:
                    self.log_status_label.setStringValue_(f"Showing {filtered_lines_count} of {total_lines} log entries (filtered by {selected_level})")
        
        self.logs_text.setString_(filtered_content)
        
        # Auto-scroll to bottom (always enabled for real-time log viewing)
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
        """Clear the actual log file with confirmation"""
        try:
            # Show confirmation dialog
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Clear Log File")
            alert.setInformativeText_("This will permanently delete all log entries from the log file. This cannot be undone.\n\nAre you sure you want to clear the log file?")
            alert.setAlertStyle_(NSAlertStyleWarning)
            alert.addButtonWithTitle_("Clear Logs")
            alert.addButtonWithTitle_("Cancel")
            
            # Set custom icon based on theme
            try:
                self._set_dialog_icon(alert)
            except Exception as e:
                print(f"Debug - Could not set clear logs dialog icon: {e}")
            
            response = alert.runModal()
            if response != NSAlertFirstButtonReturn:  # User clicked Cancel
                return
            
            # Clear the actual log file
            log_file_path = self.getLogFilePath()
            
            if os.path.exists(log_file_path):
                # Clear the file by truncating it
                with open(log_file_path, 'w') as f:
                    f.truncate(0)
                
                # Clear the UI
                self.logs_text.setString_("")
                self.full_log_content = ""
                self.last_log_size = 0
                
                self.log_status_label.setStringValue_("Log file cleared successfully")
                
                print("Debug - Log file cleared successfully")
            else:
                # File doesn't exist, just clear the UI
                self.logs_text.setString_("")
                self.full_log_content = ""
                self.last_log_size = 0
                self.log_status_label.setStringValue_("No log file found to clear")
                
        except Exception as e:
            error_msg = f"Error clearing log file: {str(e)}"
            self.logs_text.setString_(error_msg)
            self.log_status_label.setStringValue_(error_msg)
            print(f"Debug - {error_msg}")
    
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
        
        # Stop periodic permission checking
        if hasattr(self, 'permission_timer') and self.permission_timer:
            self.permission_timer.invalidate()
            self.permission_timer = None
            print("Debug - Stopped periodic permission checking")
        
        # Unregister from appearance change notifications
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
            print("Debug - Unregistered from appearance change notifications")
        except Exception as e:
            print(f"Debug - Error unregistering from notifications: {e}")
        
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
        """Update reset button based on hotkey field state"""
        if hasattr(self, 'reset_button') and hasattr(self, 'hotkey_field'):
            try:
                current = self.hotkey_field.getHotkeyString()
                default = self.settings_manager.default_settings["hotkey"]
                is_default = (current == default)
                self.reset_button.setEnabled_(not is_default)
                
                # Update conflict checking
                self.checkConflicts()
            except Exception as e:
                print(f"Error updating reset button: {e}")
    
    def checkConflicts(self):
        """Check for hotkey conflicts with system shortcuts"""
        if not hasattr(self, 'conflict_label') or not hasattr(self, 'hotkey_field'):
            return
        
        try:
            hotkey = self.hotkey_field.getHotkeyString()
            
            # Known problematic hotkeys
            conflicts = {
                "cmd+space": "Spotlight",
                "cmd+tab": "App Switcher", 
                "cmd+`": "Window Switcher",
                "cmd+shift+3": "Screenshot",
                "cmd+shift+4": "Screenshot",
                "cmd+shift+5": "Screenshot",
                "cmd+c": "Copy",
                "cmd+v": "Paste",
                "cmd+x": "Cut",
                "cmd+z": "Undo",
            }
            
            if hotkey.lower() in conflicts:
                self.conflict_label.setStringValue_(f"⚠️ {conflicts[hotkey.lower()]}")
                self.conflict_label.setHidden_(False)
            else:
                self.conflict_label.setStringValue_("")
                self.conflict_label.setHidden_(True)
                
        except Exception as e:
            print(f"Error checking conflicts: {e}")
            self.conflict_label.setStringValue_("")
    
    def resetHotkey_(self, sender):
        """Reset hotkey to default"""
        default = self.settings_manager.default_settings["hotkey"]
        self.hotkey_field.setHotkeyString_(default)
        self.updateResetButton()
    
    def get_permissions_status(self):
        """Get current permissions status from the main app"""
        print("Debug - Checking system permissions...")
        
        try:
            # Try to import from potter module to check permissions
            potter_module = sys.modules.get('__main__')
            if potter_module and hasattr(potter_module, 'service'):
                permissions = potter_module.service.get_permission_status()
                print(f"Debug - Permissions from main app: {permissions}")
                return permissions
            
            # Fallback: try to check permissions directly using the same improved method as main app
            try:
                # Use the proper accessibility API to check permissions (same as main app)
                from ApplicationServices import AXIsProcessTrusted
                from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
                
                print("Debug - Checking accessibility permission directly...")
                
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
                
                # Check System Events permission
                system_events = self.check_system_events_permission()
                
                permissions = {
                    "accessibility": accessibility,
                    "system_events": system_events,
                    "macos_available": True
                }
                print(f"Debug - Direct permission check result: {permissions}")
                return permissions
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
                            "system_events": False,
                            "macos_available": True
                        }
                    else:
                        print("Debug - Fallback window list check: insufficient windows")
                        return {
                            "accessibility": False,
                            "system_events": False,
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
            "system_events": False,
            "macos_available": False
        }
    
    def check_system_events_permission(self):
        """Check if we have System Events permission (for login items, etc.)"""
        try:
            # Try to run a simple System Events command
            result = subprocess.run([
                'osascript', '-e',
                'tell application "System Events" to get name of first process'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print("Debug - System Events permission: granted")
                return True
            else:
                print(f"Debug - System Events permission denied: {result.stderr}")
                return False
        except Exception as e:
            print(f"Debug - System Events permission check failed: {e}")
            return False
    
    def openAccessibilitySettings_(self, sender):
        """Open System Settings to Privacy & Security > Accessibility"""
        try:
            print("Debug - Opening Accessibility settings...")
            # Try to open the specific Accessibility privacy settings pane
            # For macOS 13+ (Ventura and later), use the new System Settings URLs
            result = subprocess.run([
                'open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'
            ], check=False)
            
            if result.returncode != 0:
                print("Debug - Primary URL failed, trying alternative...")
                # Alternative URL format for newer macOS versions
                result = subprocess.run([
                    'open', 'x-apple.systempreferences:com.apple.Settings.PrivacySecurity.extension'
                ], check=False)
                
                if result.returncode != 0:
                    print("Debug - Alternative URL failed, opening general Security settings...")
                    # Fallback to general Security & Privacy
                    subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.security'], check=False)
            
        except Exception as e:
            print(f"Debug - Failed to open Accessibility Settings: {e}")
            # Final fallback to general System Preferences/Settings
            try:
                subprocess.run(['open', '/System/Applications/System Preferences.app'], check=False)
            except Exception as e2:
                print(f"Debug - Failed to open System Preferences fallback: {e2}")
                # Ultimate fallback - try the newer System Settings app
                subprocess.run(['open', '/System/Applications/System Settings.app'], check=False)
    
    def openSystemSettings_(self, sender):
        """Open System Settings to General > Login Items"""
        try:
            print("Debug - Opening Login Items settings...")
            # Try to open the specific Login Items settings pane
            # For macOS 13+ (Ventura and later), Login Items are in General settings
            result = subprocess.run([
                'open', 'x-apple.systempreferences:com.apple.LoginItems-Settings.extension'
            ], check=False)
            
            if result.returncode != 0:
                print("Debug - Login Items URL failed, trying General settings...")
                # Alternative: open General settings where Login Items are located
                result = subprocess.run([
                    'open', 'x-apple.systempreferences:com.apple.preference.general'
                ], check=False)
                
                if result.returncode != 0:
                    print("Debug - General settings failed, trying older Users & Groups...")
                    # Fallback for older macOS versions (Users & Groups > Login Items)
                    subprocess.run([
                        'open', 'x-apple.systempreferences:com.apple.preferences.users'
                    ], check=False)
            
        except Exception as e:
            print(f"Debug - Failed to open Login Items Settings: {e}")
            # Final fallback to general System Preferences/Settings
            try:
                subprocess.run(['open', '/System/Applications/System Preferences.app'], check=False)
            except Exception as e2:
                print(f"Debug - Failed to open System Preferences fallback: {e2}")
                # Ultimate fallback - try the newer System Settings app
                subprocess.run(['open', '/System/Applications/System Settings.app'], check=False)
    
    def refreshPermissions_(self, sender):
        """Refresh permission status display"""
        print("Debug - Refreshing permissions...")
        
        # Store current permissions before refresh
        old_permissions = getattr(self, 'last_permissions_status', self.get_permissions_status())
        
        # Get updated permissions
        permissions_status = self.get_permissions_status()
        
        # Update displays
        self.updatePermissionDisplays_(permissions_status)
        
        # Update notification status
        if hasattr(self, 'notification_status') and hasattr(self, 'notification_btn'):
            notification_text, notification_color = self.get_notification_status()
            if "✅" in notification_text or "✓" in notification_text:
                self.notification_status.setStringValue_("✓")
                self.notification_status.setTextColor_(NSColor.systemGreenColor())
                self.notification_btn.setTitle_("Manage")  # Keep enabled for management
                self.notification_btn.setEnabled_(True)
            else:
                self.notification_status.setStringValue_("✗")
                self.notification_status.setTextColor_(NSColor.systemRedColor())
                self.notification_btn.setTitle_("Grant Access")
                self.notification_btn.setEnabled_(True)
        
        # Only prompt for restart if permissions were NEWLY granted (changed from False to True)
        restart_needed = False
        for key in ['accessibility', 'system_events']:
            old_value = old_permissions.get(key, False)
            new_value = permissions_status.get(key, False)
            if not old_value and new_value:  # Changed from False to True
                restart_needed = True
                break
        
        if restart_needed:
            self.promptForRestart()
        
        # Update stored permissions
        self.last_permissions_status = permissions_status
        
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
            
            # Set custom icon based on theme
            try:
                self._set_dialog_icon(alert)
            except Exception as e:
                print(f"Debug - Could not set reset permissions dialog icon: {e}")
            
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
                    
                    # Set custom icon based on theme
                    try:
                        self._set_dialog_icon(success_alert)
                    except Exception as e:
                        print(f"Debug - Could not set success dialog icon: {e}")
                    
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
            # Use the centralized and safer restart mechanism
            from utils.common_dialogs import RestartHelper
            success = RestartHelper.restart_application()
            if not success:
                self.show_permission_reset_error("Failed to restart Potter. Please restart manually.")
        except Exception as e:
            print(f"Debug - Error restarting app: {e}")
            self.show_permission_reset_error(f"Failed to restart Potter: {str(e)}. Please restart manually.")
    
    def quitApplication_(self, sender):
        """Quit the Potter application"""
        try:
            print("Debug - quitApplication_ called, attempting to quit...")
            
            # First close the settings window
            if hasattr(self, 'window') and self.window():
                print("Debug - Closing settings window...")
                self.window().close()
            
            # Try to quit the main application
            try:
                from AppKit import NSApplication
                app = NSApplication.sharedApplication()
                print("Debug - Terminating NSApplication...")
                app.terminate_(None)
            except Exception as app_error:
                print(f"Debug - NSApplication.terminate failed: {app_error}")
                # Fallback to sys.exit
                import sys
                print("Debug - Calling sys.exit(0) as fallback...")
                sys.exit(0)
                
        except Exception as e:
            print(f"Debug - Error quitting app: {e}")
            # Remove unsafe fallback - just let the exception bubble up if sys.exit fails
    
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
            print("Debug - Opening Notifications settings...")
            # Try to open the specific Notifications settings pane
            result = subprocess.run([
                'open', 'x-apple.systempreferences:com.apple.preference.notifications'
            ], check=False)
            
            if result.returncode != 0:
                print("Debug - Notifications URL failed, trying alternative...")
                # Alternative URL format for newer macOS versions
                result = subprocess.run([
                    'open', 'x-apple.systempreferences:com.apple.Settings.Notifications.extension'
                ], check=False)
                
                if result.returncode != 0:
                    print("Debug - Alternative failed, opening general settings...")
                    # Final fallback to general System Preferences/Settings
                    subprocess.run(['open', '/System/Applications/System Settings.app'], check=False)
            
        except Exception as e:
            print(f"Debug - Failed to open Notification Settings: {e}")
            # Ultimate fallback
            try:
                subprocess.run(['open', '/System/Applications/System Settings.app'], check=False)
            except Exception as e2:
                print(f"Debug - All notification settings attempts failed: {e2}")
    
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
        """Save all settings with enhanced validation and LLM provider support"""
        try:
            # Collect settings from all views
            settings = self.settings_manager.settings.copy()
            
            # General settings
            if hasattr(self, 'provider_popup'):
                selected_item = self.provider_popup.selectedItem()
                if selected_item:
                    settings["llm_provider"] = selected_item.representedObject()
            
            # Save API key for current provider
            if hasattr(self, 'api_key_field'):
                current_provider = settings.get("llm_provider", "openai")
                api_key = str(self.api_key_field.stringValue()).strip()
                settings[f"{current_provider}_api_key"] = api_key
                
                # Validate API key if provided
                if api_key:
                    self.validateApiKey_withProvider_(api_key, current_provider)
            
            # Model selection
            if hasattr(self, 'model_popup'):
                selected_model = self.model_popup.selectedItem()
                if selected_model:
                    # Use the model ID stored in representedObject instead of title
                    model_id = selected_model.representedObject()
                    settings["model"] = str(model_id) if model_id else ""
            
            # Hotkey from HotkeyCapture
            if hasattr(self, 'hotkey_field'):
                settings["hotkey"] = self.hotkey_field.getHotkeyString()
            
            # Preferences - sync with OS state where applicable
            if hasattr(self, 'notifications_switch'):
                notification_enabled = bool(self.notifications_switch.state())
                settings["show_notifications"] = notification_enabled
                
                # Handle both enabling and disabling notifications
                if notification_enabled:
                    # Request permission when turning ON notifications
                    if not self.settings_manager.get_os_notification_status():
                        self.requestNotificationPermission_(None)
                else:
                    # When turning OFF notifications, just update the setting
                    # Note: We can't programmatically revoke OS notification permission,
                    # but the app will respect the show_notifications setting
                    print("Debug - Notifications disabled in app settings")
            
            if hasattr(self, 'startup_switch'):
                startup_enabled = bool(self.startup_switch.state())
                settings["launch_at_startup"] = startup_enabled
                
                # Update OS startup setting for both on and off
                self.updateStartupSetting_(startup_enabled)
            
            # Prompts (from table view)
            if hasattr(self, 'prompts_data'):
                settings["prompts"] = []
                for prompt in self.prompts_data:
                    if prompt.get("name") and prompt.get("text"):  # Only save valid prompts
                        settings["prompts"].append({
                            "name": prompt["name"],
                            "text": prompt["text"]
                        })
                print(f"Debug - Saving {len(settings['prompts'])} prompts to settings")
                
                # Log prompts being saved
                for i, prompt in enumerate(settings["prompts"]):
                    print(f"Debug - Prompt {i+1}: name='{prompt['name']}', text_length={len(prompt['text'])}")
            else:
                print("Debug - Warning: No prompts_data found, preserving existing prompts")
                # Preserve existing prompts if prompts_data is not available
                existing_prompts = self.settings_manager.get("prompts", [])
                settings["prompts"] = existing_prompts
                print(f"Debug - Preserved {len(existing_prompts)} existing prompts")
            
            # Inline validation to avoid PyObjC signature issues
            try:
                # Check that we have a valid provider
                provider = settings.get("llm_provider")
                if not provider or provider not in self.settings_manager.llm_providers:
                    self.show_save_error("Invalid AI provider selected")
                    return
                
                # Check that we have an API key for the provider
                api_key = settings.get(f"{provider}_api_key", "").strip()
                if not api_key:
                    self.show_save_error(f"API key required for {self.settings_manager.llm_providers[provider]['name']}")
                    return
                
                # Check that we have a valid model
                model = settings.get("model")
                provider_models = self.settings_manager.llm_providers[provider].get("models", [])
                
                # Extract model IDs for validation (support both old and new format)
                valid_model_ids = []
                for provider_model in provider_models:
                    if isinstance(provider_model, dict):
                        valid_model_ids.append(provider_model.get("id", ""))
                    else:
                        valid_model_ids.append(provider_model)
                
                if model not in valid_model_ids:
                    self.show_save_error(f"Invalid model '{model}' for provider {provider}")
                    return
                
                # Check hotkey format
                hotkey = settings.get("hotkey", "").strip()
                if not hotkey:
                    self.show_save_error("Hotkey cannot be empty")
                    return
                
                # Check prompts
                prompts = settings.get("prompts", [])
                if not prompts:
                    self.show_save_error("At least one prompt is required")
                    return
                
            except Exception as e:
                self.show_save_error(f"Validation error: {str(e)}")
                return
            
            # Save settings
            if self.settings_manager.save_settings(settings):
                print("Settings saved successfully")
                
                # Notify callback if set
                if self.on_settings_changed:
                    self.on_settings_changed(settings)
                
                # Show success notification
                self.settings_manager.show_success("Settings saved successfully")
                
                # Close window
                self.window().performClose_(None)
            else:
                self.show_save_error("Failed to save settings to file")
                
        except Exception as e:
            print(f"Error saving settings: {e}")
            self.show_save_error(f"Unexpected error: {str(e)}")
    
    def validateApiKey_withProvider_(self, api_key, provider):
        """Validate API key for the given provider (basic validation)"""
        try:
            # Use LLM client's validation method
            from utils.llm_client import LLMClientManager
            llm_manager = LLMClientManager()
            
            is_valid, error_msg = llm_manager.validate_api_key(provider, api_key)
            
            if is_valid:
                # Mark as potentially valid (would need actual API call for real validation)
                self.settings_manager.set_api_key_validation(provider, True, None)
                return True
            else:
                self.settings_manager.set_api_key_validation(provider, False, error_msg)
                return False
            
        except Exception as e:
            self.settings_manager.set_api_key_validation(
                provider, False, f"Validation error: {str(e)}"
            )
            return False
    
    def requestNotificationPermission_(self, sender):
        """Request notification permission from the OS"""
        try:
            # For macOS 10.14+, request authorization
            center = NSUserNotificationCenter.defaultUserNotificationCenter()
            center.requestAuthorizationWithOptions_completionHandler_(
                7,  # Badge + Sound + Alert
                None
            )
        except Exception as e:
            print(f"Error requesting notification permission: {e}")
    
    def updateStartupSetting_(self, enabled: bool):
        """Update the launch at startup setting in the OS"""
        try:
            if enabled:
                print("Debug - Adding Potter to login items")
                # Add to login items
                result = subprocess.run([
                    'osascript', '-e',
                    'tell application "System Events" to make login item at end with properties {path:"/Applications/Potter.app", hidden:false}'
                ], capture_output=True, text=True)
                if result.returncode == 0:
                    print("Debug - Successfully added to login items")
                else:
                    print(f"Debug - Failed to add to login items: {result.stderr}")
            else:
                print("Debug - Removing Potter from login items")
                # Remove from login items
                result = subprocess.run([
                    'osascript', '-e',
                    'tell application "System Events" to delete login item "Potter"'
                ], capture_output=True, text=True)
                if result.returncode == 0:
                    print("Debug - Successfully removed from login items")
                else:
                    # Try alternative removal methods
                    print(f"Debug - First removal attempt failed: {result.stderr}")
                    # Try removing by app name without .app extension
                    result2 = subprocess.run([
                        'osascript', '-e',
                        'tell application "System Events" to delete every login item whose name is "Potter"'
                    ], capture_output=True, text=True)
                    if result2.returncode == 0:
                        print("Debug - Successfully removed from login items (alternative method)")
                    else:
                        print(f"Debug - All removal attempts failed: {result2.stderr}")
        except Exception as e:
            print(f"Error updating startup setting: {e}")
    
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
        """Cancel changes and close settings window"""
        self.window().close()
    
    def windowShouldClose_(self, window):
        """Handle window close events"""
        print("Debug - Settings window should close called")
        return True
    
    def windowWillClose_(self, notification):
        """Handle window will close notification"""
        print("Debug - Settings window will close")
        
        # Stop log monitoring when window closes
        self.stopLogMonitoring()
        
        # Stop periodic permission checking
        if hasattr(self, 'permission_timer') and self.permission_timer:
            self.permission_timer.invalidate()
            self.permission_timer = None
            print("Debug - Stopped periodic permission checking")
        
        # Unregister from appearance change notifications
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
            print("Debug - Unregistered from appearance change notifications")
        except Exception as e:
            print(f"Debug - Error unregistering from notifications: {e}")
        
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

    def validatePromptName_(self, name, exclude_index=None):
        """Validate prompt name for duplicates. Returns error message or None if valid."""
        if not hasattr(self, 'prompts_data') or not self.prompts_data:
            return None
        
        for i, prompt in enumerate(self.prompts_data):
            if exclude_index is not None and i == exclude_index:
                continue
            if prompt.get("name", "") == name:
                return f"A prompt named '{name}' already exists."
        return None

    def addPrompt_(self, sender):
        """Add a new prompt using dialog"""
        print("Debug - addPrompt_ called")
        
        # Create and show dialog modally
        dialog = PromptDialog.alloc().initWithPrompt_isEdit_(None, False)
        
        # Set parent window controller reference for icon access
        dialog.parent_window_controller = self
        
        # Set up name validator
        dialog.name_validator = lambda name: self.validatePromptName_(name)
        
        def on_result(result):
            print(f"Debug - addPrompt callback called with result: {result}")
            if result:  # User didn't cancel and validation passed
                # Add the new prompt
                self.prompts_data.append(result)
                self.prompts_table.reloadData()
                self.updatePromptsCount()
                
                # Save to settings file immediately
                self.savePromptsToSettings()
                
                # Select the new row
                new_index = len(self.prompts_data) - 1
                self.prompts_table.selectRowIndexes_byExtendingSelection_(
                    NSIndexSet.indexSetWithIndex_(new_index), False
                )
                self.prompts_table.scrollRowToVisible_(new_index)
                print(f"Debug - Added new prompt at index {new_index}")
            else:
                print("Debug - Add prompt was cancelled")
        
        dialog.callback = on_result
        
        # Run the dialog modally
        try:
            result = dialog.runModalDialog()
            print(f"Debug - Modal dialog returned: {result}")
        except Exception as e:
            print(f"Debug - Error running add prompt dialog: {e}")
            import traceback
            traceback.print_exc()
    
    def removePrompt_(self, sender):
        """Remove selected prompt"""
        print("Debug - removePrompt_ called")
        if not hasattr(self, 'prompts_data') or not self.prompts_data:
            print("Debug - No prompts data available")
            return
        
        selected_row = self.prompts_table.selectedRow()
        if selected_row < 0:
            # No selection, show alert
            print("Debug - No row selected for removal")
            alert = NSAlert.alloc().init()
            alert.setMessageText_("No Selection")
            alert.setInformativeText_("Please select a prompt to remove.")
            alert.setAlertStyle_(NSAlertStyleInformational)
            
            # Set custom icon based on theme
            try:
                self._set_dialog_icon(alert)
            except Exception as e:
                print(f"Debug - Could not set no selection dialog icon: {e}")
            
            alert.runModal()
            return
        
        # Get prompt name for confirmation
        prompt_name = self.prompts_data[selected_row].get("name", "this prompt")
        print(f"Debug - Confirming removal of prompt: {prompt_name}")
        
        # Confirm deletion
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Delete Prompt")
        alert.setInformativeText_(f"Are you sure you want to delete '{prompt_name}'?")
        alert.setAlertStyle_(NSAlertStyleWarning)
        alert.addButtonWithTitle_("Delete")
        alert.addButtonWithTitle_("Cancel")
        
        # Set custom icon based on theme
        try:
            self._set_dialog_icon(alert)
        except Exception as e:
            print(f"Debug - Could not set delete prompt dialog icon: {e}")
        
        response = alert.runModal()
        if response == NSAlertFirstButtonReturn:  # Delete
            self.prompts_data.pop(selected_row)
            self.prompts_table.reloadData()
            self.updatePromptsCount()
            
            # Save to settings file immediately
            self.savePromptsToSettings()
            
            print(f"Debug - Removed prompt: {prompt_name}")
        else:
            print("Debug - Prompt removal cancelled")
    
    def editPrompt_(self, sender):
        """Edit selected prompt using dialog"""
        print("Debug - editPrompt_ called")
        if not hasattr(self, 'prompts_data') or not self.prompts_data:
            print("Debug - No prompts data available")
            return
        
        selected_row = self.prompts_table.selectedRow()
        if selected_row < 0:
            # No selection, show alert
            print("Debug - No row selected for editing")
            alert = NSAlert.alloc().init()
            alert.setMessageText_("No Selection")
            alert.setInformativeText_("Please select a prompt to edit.")
            alert.setAlertStyle_(NSAlertStyleInformational)
            
            # Set custom icon based on theme
            try:
                self._set_dialog_icon(alert)
            except Exception as e:
                print(f"Debug - Could not set no selection dialog icon: {e}")
            
            alert.runModal()
            return
        
        # Get current prompt
        current_prompt = self.prompts_data[selected_row]
        original_name = current_prompt["name"]
        print(f"Debug - Editing prompt: {original_name}")
        
        # Create and show dialog modally
        dialog = PromptDialog.alloc().initWithPrompt_isEdit_(current_prompt, True)
        
        # Set parent window controller reference for icon access
        dialog.parent_window_controller = self
        
        # Set up name validator (excluding current index)
        dialog.name_validator = lambda name: self.validatePromptName_(name, exclude_index=selected_row)
        
        def on_result(result):
            print(f"Debug - editPrompt callback called with result: {result}")
            if result:  # User didn't cancel and validation passed
                # Update the prompt
                self.prompts_data[selected_row] = result
                self.prompts_table.reloadData()
                
                # Save to settings file immediately
                self.savePromptsToSettings()
                
                # Keep selection
                self.prompts_table.selectRowIndexes_byExtendingSelection_(
                    NSIndexSet.indexSetWithIndex_(selected_row), False
                )
                print(f"Debug - Updated prompt at index {selected_row}")
            else:
                print("Debug - Edit prompt was cancelled")
        
        dialog.callback = on_result
        
        # Run the dialog modally
        try:
            result = dialog.runModalDialog()
            print(f"Debug - Edit modal dialog returned: {result}")
        except Exception as e:
            print(f"Debug - Error running edit prompt dialog: {e}")
            import traceback
            traceback.print_exc()
    
    def startPeriodicPermissionCheck(self):
        """Start periodic permission checking for about a minute"""
        self.permission_check_count = 0
        self.max_permission_checks = 20  # Check 20 times over ~1 minute (every 3 seconds)
        
        # Initialize with current permissions to avoid false positives
        self.last_permissions_status = self.get_permissions_status()
        print(f"Debug - Initial permission status: {self.last_permissions_status}")
        
        self.permission_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            3.0, self, "checkPermissionsPeriodically:", None, True
        )
        print("Debug - Started periodic permission checking")
    
    def checkPermissionsPeriodically_(self, timer):
        """Check permissions periodically and auto-update UI"""
        self.permission_check_count += 1
        
        # Check if we should stop periodic checking
        if self.permission_check_count >= self.max_permission_checks:
            print("Debug - Stopping periodic permission checking")
            if self.permission_timer:
                self.permission_timer.invalidate()
                self.permission_timer = None
            return
        
        # Get current permissions
        old_permissions = getattr(self, 'last_permissions_status', {})
        new_permissions = self.get_permissions_status()
        
        # Check if any permissions changed from False to True (newly granted)
        permissions_newly_granted = False
        for key in ['accessibility', 'system_events']:
            old_value = old_permissions.get(key, False)
            new_value = new_permissions.get(key, False)
            if not old_value and new_value:  # Changed from False to True
                permissions_newly_granted = True
                print(f"Debug - Permission newly granted: {key} changed from {old_value} to {new_value}")
        
        # Update stored permissions
        self.last_permissions_status = new_permissions
        
        # Only update UI if there were actual changes
        if permissions_newly_granted:
            # Update the UI
            self.updatePermissionDisplays_(new_permissions)
            
            # Only prompt for restart when permissions are newly granted
            self.promptForRestart()
        elif old_permissions != new_permissions:
            # Some change occurred, but not newly granted permissions
            self.updatePermissionDisplays_(new_permissions)
    
    def updatePermissionDisplays_(self, permissions_status):
        """Update permission status displays"""
        try:
            # Update accessibility status
            if hasattr(self, 'accessibility_status'):
                if permissions_status.get('accessibility', False):
                    self.accessibility_status.setStringValue_("✓")
                    self.accessibility_status.setTextColor_(NSColor.systemGreenColor())
                    if hasattr(self, 'accessibility_btn'):
                        self.accessibility_btn.setTitle_("Manage")  # Keep enabled for management
                        self.accessibility_btn.setEnabled_(True)
                else:
                    self.accessibility_status.setStringValue_("✗")
                    self.accessibility_status.setTextColor_(NSColor.systemRedColor())
                    if hasattr(self, 'accessibility_btn'):
                        self.accessibility_btn.setTitle_("Grant Access")
                        self.accessibility_btn.setEnabled_(True)
            
            # Update system events status
            if hasattr(self, 'system_events_status'):
                if permissions_status.get('system_events', False):
                    self.system_events_status.setStringValue_("✓")
                    self.system_events_status.setTextColor_(NSColor.systemGreenColor())
                    if hasattr(self, 'system_events_btn'):
                        self.system_events_btn.setTitle_("Manage")  # Keep enabled for management
                        self.system_events_btn.setEnabled_(True)
                else:
                    self.system_events_status.setStringValue_("✗")
                    self.system_events_status.setTextColor_(NSColor.systemRedColor())
                    if hasattr(self, 'system_events_btn'):
                        self.system_events_btn.setTitle_("Grant Access")
                        self.system_events_btn.setEnabled_(True)
            
            print("Debug - Permission displays updated")
        except Exception as e:
            print(f"Debug - Error updating permission displays: {e}")
    
    def promptForRestart(self):
        """Prompt user to restart after permission changes"""
        try:
            # Stop periodic checking since permissions are now granted
            if hasattr(self, 'permission_timer') and self.permission_timer:
                self.permission_timer.invalidate()
                self.permission_timer = None
            
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Permissions Updated")
            alert.setInformativeText_("New permissions have been granted. Potter needs to restart to use them effectively.\n\nWould you like to restart Potter now?")
            alert.setAlertStyle_(NSAlertStyleInformational)
            alert.addButtonWithTitle_("Restart Now")
            alert.addButtonWithTitle_("Later")
            
            response = alert.runModal()
            if response == NSAlertFirstButtonReturn:  # Restart
                print("Debug - User chose to restart after permission grant")
                self.restartApp()
        except Exception as e:
            print(f"Debug - Error in promptForRestart: {e}")
    
    def refreshPermissions_(self, sender):
        """Refresh permission status display"""
        print("Debug - Refreshing permissions...")
        
        # Get updated permissions
        permissions_status = self.get_permissions_status()
        
        # Update displays
        self.updatePermissionDisplays_(permissions_status)
        
        # Update notification status
        if hasattr(self, 'notification_status') and hasattr(self, 'notification_btn'):
            notification_text, notification_color = self.get_notification_status()
            if "✅" in notification_text or "✓" in notification_text:
                self.notification_status.setStringValue_("✓")
                self.notification_status.setTextColor_(NSColor.systemGreenColor())
                self.notification_btn.setTitle_("Manage")  # Keep enabled for management
                self.notification_btn.setEnabled_(True)
            else:
                self.notification_status.setStringValue_("✗")
                self.notification_status.setTextColor_(NSColor.systemRedColor())
                self.notification_btn.setTitle_("Grant Access")
                self.notification_btn.setEnabled_(True)
        
        # Check if we should prompt for restart
        if any(permissions_status.get(key, False) for key in ['accessibility', 'system_events']):
            self.promptForRestart()
        
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
            
            # Set custom icon based on theme
            try:
                self._set_dialog_icon(alert)
            except Exception as e:
                print(f"Debug - Could not set reset permissions dialog icon: {e}")
            
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
                    
                    # Set custom icon based on theme
                    try:
                        self._set_dialog_icon(success_alert)
                    except Exception as e:
                        print(f"Debug - Could not set success dialog icon: {e}")
                    
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
    
    def is_first_launch_for_build(self) -> bool:
        """Check if this is the first launch for this specific build"""
        try:
            from utils.instance_checker import load_build_id
            current_build = load_build_id()
            current_build_id = current_build.get("build_id", "unknown")
            
            if not os.path.exists(self.first_run_file):
                return True
            
            with open(self.first_run_file, 'r') as f:
                first_run_data = json.load(f)
            
            # Check if this build ID has been launched before
            launched_builds = first_run_data.get("launched_builds", [])
            return current_build_id not in launched_builds
            
        except Exception as e:
            print(f"Error checking first launch: {e}")
            return True  # Default to first launch to be safe
    
    def mark_build_launched(self):
        """Mark this build as having been launched"""
        try:
            from utils.instance_checker import load_build_id
            current_build = load_build_id()
            current_build_id = current_build.get("build_id", "unknown")
            
            # Load existing data or create new
            first_run_data = {"launched_builds": [], "permission_requests": {}}
            if os.path.exists(self.first_run_file):
                with open(self.first_run_file, 'r') as f:
                    first_run_data = json.load(f)
            
            # Add this build to launched builds
            if current_build_id not in first_run_data.get("launched_builds", []):
                first_run_data.setdefault("launched_builds", []).append(current_build_id)
            
            # Save updated data
            with open(self.first_run_file, 'w') as f:
                json.dump(first_run_data, f, indent=2)
                
        except Exception as e:
            print(f"Error marking build launched: {e}")
    
    def has_declined_permission(self, permission_type: str) -> bool:
        """Check if user has previously declined a permission"""
        try:
            if not os.path.exists(self.first_run_file):
                return False
            
            with open(self.first_run_file, 'r') as f:
                first_run_data = json.load(f)
            
            permission_requests = first_run_data.get("permission_requests", {})
            return permission_requests.get(permission_type, {}).get("declined", False)
            
        except Exception as e:
            print(f"Error checking permission decline: {e}")
            return False
    
    def mark_permission_declined(self, permission_type: str):
        """Mark that user has declined a permission"""
        try:
            # Load existing data or create new
            first_run_data = {"launched_builds": [], "permission_requests": {}}
            if os.path.exists(self.first_run_file):
                with open(self.first_run_file, 'r') as f:
                    first_run_data = json.load(f)
            
            # Mark permission as declined
            first_run_data.setdefault("permission_requests", {})[permission_type] = {
                "declined": True,
                "timestamp": time.time()
            }
            
            # Save updated data
            with open(self.first_run_file, 'w') as f:
                json.dump(first_run_data, f, indent=2)
                
        except Exception as e:
            print(f"Error marking permission declined: {e}")
    
    def should_show_settings_on_startup(self) -> bool:
        """Determine if settings should be shown on startup"""
        # Show settings if this is first time for this build OR no API key is set up
        is_first_launch = self.is_first_launch_for_build()
        current_provider = self.settings_manager.get_current_provider()
        api_key = self.settings_manager.get(f"{current_provider}_api_key", "").strip()
        
        current_provider = self.get_current_provider()
        api_key = self.get(f"{current_provider}_api_key", "").strip()
        
        # Also check environment variable as fallback
        if not api_key and current_provider == "openai":
            api_key = os.getenv('OPENAI_API_KEY', "").strip()
        
        return is_first_launch or not api_key  # Changed from AND to OR
    
    def autoSaveCurrentSettings(self):
        """Auto-save current UI settings to file immediately"""
        try:
            # Get all current settings
            current_settings = self.settings_manager.get_all_settings()
            
            # Update with current UI values
            if hasattr(self, 'provider_popup'):
                selected_item = self.provider_popup.selectedItem()
                if selected_item:
                    current_settings["llm_provider"] = selected_item.representedObject()
            
            if hasattr(self, 'model_popup'):
                selected_model = self.model_popup.selectedItem()
                if selected_model:
                    # Use the model ID stored in representedObject instead of title
                    model_id = selected_model.representedObject()
                    current_settings["model"] = str(model_id) if model_id else ""
            
            if hasattr(self, 'notifications_switch'):
                current_settings["show_notifications"] = bool(self.notifications_switch.state())
            
            if hasattr(self, 'startup_switch'):
                current_settings["launch_at_startup"] = bool(self.startup_switch.state())
            
            # Save to file
            success = self.settings_manager.save_settings(current_settings)
            print(f"Debug - Auto-saved settings: {success}")
            return success
        except Exception as e:
            print(f"Debug - Error auto-saving settings: {e}")
            return False

    def savePromptsToSettings(self):
        """Save current prompts data to settings immediately"""
        if not hasattr(self, 'prompts_data'):
            return False
        
        try:
            # Get current settings
            current_settings = {}
            for key in self.settings_manager.get_all_settings().keys():
                current_settings[key] = self.settings_manager.get(key)
            
            # Update prompts
            current_settings["prompts"] = []
            for prompt in self.prompts_data:
                if prompt.get("name") and prompt.get("text"):
                    current_settings["prompts"].append({
                        "name": prompt["name"],
                        "text": prompt["text"]
                    })
            
            # Save to file
            success = self.settings_manager.save_settings(current_settings)
            print(f"Debug - Saved {len(current_settings['prompts'])} prompts to settings: {success}")
            return success
        except Exception as e:
            print(f"Debug - Error saving prompts to settings: {e}")
            return False

    def updatePromptsCount(self):
        """Update the prompts count label"""
        if hasattr(self, 'prompts_count_label') and hasattr(self, 'prompts_data'):
            count = len(self.prompts_data) if self.prompts_data else 0
            self.prompts_count_label.setStringValue_(f"{count} prompts")


def show_settings(settings_manager, on_settings_changed=None):
    """Show the settings window"""
    try:
        controller = SettingsWindow.alloc().initWithSettingsManager_(settings_manager)
        
        # Set the callback if provided
        if on_settings_changed:
            controller.on_settings_changed = on_settings_changed
        
        # Center the window on screen before showing it
        window = controller.window()
        window.center()
        
        # Show the window
        window.makeKeyAndOrderFront_(None)
        
        # Bring to front
        from AppKit import NSApplication
        app = NSApplication.sharedApplication()
        app.activateIgnoringOtherApps_(True)
        
        return controller
        
    except Exception as e:
        print(f"Error showing settings: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Test the settings window
    settings_manager = SettingsManager()
    show_settings(settings_manager) 