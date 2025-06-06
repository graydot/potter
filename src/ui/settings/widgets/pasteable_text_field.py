#!/usr/bin/env python3
"""
Pasteable Text Field Widget
NSTextField that explicitly supports paste operations and keyboard shortcuts
"""

import logging
from AppKit import (
    NSTextField, NSSecureTextField, NSTextFieldRoundedBezel, NSFont, NSPasteboard,
    NSPasteboardTypeString, NSEventModifierFlagCommand,
    NSLineBreakByClipping, NSApp
)
import objc

logger = logging.getLogger(__name__)


class PasteableTextField(NSTextField):
    """NSTextField that explicitly supports paste operations"""

    def initWithFrame_(self, frame):
        """
        Initialize pasteable text field

        Args:
            frame: NSRect for the text field frame
        """
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
        logger.debug("API key field becoming first responder")
        result = objc.super(PasteableTextField, self).becomeFirstResponder()
        if result:
            logger.debug("API key field successfully became first responder")
        else:
            logger.debug("API key field failed to become first responder")
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
                logger.debug(f"Pasted text: {len(string)} characters")
                return True
        except Exception as e:
            logger.error(f"Paste error: {e}")
        return False

    def copy_(self, sender):
        """Handle copy operation"""
        try:
            # Get selected text or all text
            field_editor = self.currentEditor()
            if field_editor and field_editor.selectedRange().length > 0:
                selected_text = field_editor.string().substringWithRange_(
                    field_editor.selectedRange()
                )
            else:
                selected_text = self.stringValue()

            if selected_text:
                pasteboard = NSPasteboard.generalPasteboard()
                pasteboard.clearContents()
                pasteboard.setString_forType_(
                    selected_text, NSPasteboardTypeString
                )
                logger.debug(f"Copied text: {len(selected_text)} characters")
                return True
        except Exception as e:
            logger.error(f"Copy error: {e}")
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
                logger.debug("Cut operation completed")
                return True
        except Exception as e:
            logger.error(f"Cut error: {e}")
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
            logger.debug("Select all completed")
            return True
        except Exception as e:
            logger.error(f"Select all error: {e}")
        return False


class PasteableSecureTextField(NSSecureTextField):
    """NSSecureTextField that supports paste operations"""
    
    def performKeyEquivalent_(self, event):
        """Handle key equivalents including paste"""
        # Check for Cmd+V (paste)
        if (event.modifierFlags() & NSEventModifierFlagCommand and
                event.charactersIgnoringModifiers().lower() == 'v'):
            self.paste_(None)
            return True
            
        return objc.super(PasteableSecureTextField, self).performKeyEquivalent_(event)
    
    def paste_(self, sender):
        """Handle paste operation"""
        try:
            pasteboard = NSPasteboard.generalPasteboard()
            string = pasteboard.stringForType_(NSPasteboardTypeString)
            
            if string:
                # Insert at current position
                self.setStringValue_(string)
                
                # Notify of change
                if self.target() and self.action():
                    NSApp.sendAction_to_from_(self.action(), self.target(), self)
                    
                logger.debug(f"Pasted text into secure field: {len(string)} characters")
                return True
        except Exception as e:
            logger.error(f"Secure field paste error: {e}")
        return False


__all__ = ['PasteableTextField', 'PasteableSecureTextField'] 