#!/usr/bin/env python3
"""
Enhanced Text Field
Custom NSTextField with enhanced clipboard support and better UX
"""

import logging
import objc
from AppKit import (
    NSTextField, NSTextFieldRoundedBezel, NSFont, NSLineBreakByClipping,
    NSEventModifierFlagCommand, NSPasteboard, NSPasteboardTypeString
)

logger = logging.getLogger(__name__)


class PasteableTextField(NSTextField):
    """Enhanced NSTextField with explicit clipboard support and improved UX"""
    
    def initWithFrame_(self, frame):
        """Initialize the enhanced text field"""
        self = objc.super(PasteableTextField, self).initWithFrame_(frame)
        if self is None:
            return None
        
        # Configure as modern text field
        self.setBezeled_(True)
        self.setBezelStyle_(NSTextFieldRoundedBezel)  # Modern rounded appearance
        self.setEditable_(True)
        self.setSelectable_(True)
        self.setEnabled_(True)
        self.setUsesSingleLineMode_(True)  # Force single line
        self.setLineBreakMode_(NSLineBreakByClipping)  # Clip overflow
        
        # Allow field to become first responder
        self.setRefusesFirstResponder_(False)
        
        # Set system font
        self.setFont_(NSFont.systemFontOfSize_(13))
        
        logger.debug("Enhanced text field initialized")
        return self
    
    def becomeFirstResponder(self):
        """Handle becoming first responder with logging"""
        logger.debug("Enhanced text field becoming first responder")
        result = objc.super(PasteableTextField, self).becomeFirstResponder()
        if result:
            logger.debug("Enhanced text field successfully became first responder")
        else:
            logger.debug("Enhanced text field failed to become first responder")
        return result
    
    def performKeyEquivalent_(self, event):
        """Handle enhanced keyboard shortcuts"""
        # Get modifier flags and character
        modifiers = event.modifierFlags()
        char = event.charactersIgnoringModifiers().lower()
        
        # Check for Cmd+ shortcuts
        if modifiers & NSEventModifierFlagCommand:
            if char == 'v':  # Cmd+V (paste)
                self.paste_(None)
                return True
            elif char == 'c':  # Cmd+C (copy)
                self.copy_(None)
                return True
            elif char == 'x':  # Cmd+X (cut)
                self.cut_(None)
                return True
            elif char == 'a':  # Cmd+A (select all)
                self.selectAll_(None)
                return True
        
        return objc.super(PasteableTextField, self).performKeyEquivalent_(event)
    
    def paste_(self, sender):
        """Enhanced paste operation with error handling"""
        try:
            pasteboard = NSPasteboard.generalPasteboard()
            string = pasteboard.stringForType_(NSPasteboardTypeString)
            if string:
                # Get current field editor
                field_editor = self.currentEditor()
                if field_editor:
                    # Insert at current cursor position
                    field_editor.insertText_(string)
                else:
                    # Fallback: replace entire content
                    self.setStringValue_(string)
                
                logger.debug(f"Pasted text: {len(string)} characters")
                return True
            else:
                logger.debug("No text found in pasteboard")
                
        except Exception as e:
            logger.error(f"Paste operation failed: {e}")
        
        return False
    
    def copy_(self, sender):
        """Enhanced copy operation"""
        try:
            # Get selected text or all text if no selection
            field_editor = self.currentEditor()
            if field_editor and field_editor.selectedRange().length > 0:
                # Copy selected text
                selected_text = field_editor.string().substringWithRange_(field_editor.selectedRange())
            else:
                # Copy all text
                selected_text = self.stringValue()
            
            if selected_text and len(selected_text) > 0:
                pasteboard = NSPasteboard.generalPasteboard()
                pasteboard.clearContents()
                pasteboard.setString_forType_(selected_text, NSPasteboardTypeString)
                logger.debug(f"Copied text: {len(selected_text)} characters")
                return True
            else:
                logger.debug("No text to copy")
                
        except Exception as e:
            logger.error(f"Copy operation failed: {e}")
        
        return False
    
    def cut_(self, sender):
        """Enhanced cut operation"""
        try:
            # First copy the text
            if self.copy_(sender):
                # Then delete the content
                field_editor = self.currentEditor()
                if field_editor:
                    if field_editor.selectedRange().length > 0:
                        # Delete selected text
                        field_editor.insertText_("")
                    else:
                        # Clear all text
                        self.setStringValue_("")
                else:
                    # Fallback: clear all text
                    self.setStringValue_("")
                
                logger.debug("Cut operation completed")
                return True
                
        except Exception as e:
            logger.error(f"Cut operation failed: {e}")
        
        return False
    
    def selectAll_(self, sender):
        """Enhanced select all operation"""
        try:
            field_editor = self.currentEditor()
            if field_editor:
                # Select all text in the field editor
                field_editor.selectAll_(sender)
            else:
                # Make this field first responder and then select all
                if self.window():
                    self.window().makeFirstResponder_(self)
                    field_editor = self.currentEditor()
                    if field_editor:
                        field_editor.selectAll_(sender)
            
            logger.debug("Select all operation completed")
            return True
            
        except Exception as e:
            logger.error(f"Select all operation failed: {e}")
        
        return False


class ApiKeyTextField(PasteableTextField):
    """Specialized text field for API keys with additional features"""
    
    def initWithFrame_(self, frame):
        """Initialize the API key text field"""
        self = objc.super(ApiKeyTextField, self).initWithFrame_(frame)
        if self is None:
            return None
        
        # Set placeholder text
        self.setPlaceholderString_("Enter your API key...")
        
        # Additional styling for API keys
        self.setFont_(NSFont.monospacedSystemFontOfSize_weight_(12, 0))  # Monospace font
        
        logger.debug("API key text field initialized")
        return self
    
    def paste_(self, sender):
        """Enhanced paste for API keys - auto-trim whitespace"""
        try:
            pasteboard = NSPasteboard.generalPasteboard()
            string = pasteboard.stringForType_(NSPasteboardTypeString)
            if string:
                # Trim whitespace for API keys
                cleaned_string = string.strip()
                
                field_editor = self.currentEditor()
                if field_editor:
                    field_editor.insertText_(cleaned_string)
                else:
                    self.setStringValue_(cleaned_string)
                
                logger.debug(f"Pasted and cleaned API key: {len(cleaned_string)} characters")
                return True
                
        except Exception as e:
            logger.error(f"API key paste failed: {e}")
        
        return False 