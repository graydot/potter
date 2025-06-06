#!/usr/bin/env python3
"""
Prompt Dialog
Dialog for adding and editing prompts in Potter
"""

import logging
from typing import Optional, Dict, Callable
from AppKit import (
    NSWindowController, NSWindow, NSMakeRect, NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable, NSWindowStyleMaskMiniaturizable,
    NSBackingStoreBuffered, NSModalPanelWindowLevel, NSTextField,
    NSScrollView, NSTextView, NSBezelBorder, NSButton, NSFont,
    NSColor, NSAlert, NSAlertStyleWarning,
    NSModalResponseOK, NSModalResponseCancel, NSEventModifierFlagCommand,
    NSApp, NSRunContinuesResponse, NSRunStoppedResponse
)
import objc

from ..validators.prompt_validator import PromptValidator
from ..widgets.theme_aware_icon import ThemeAwareIcon

logger = logging.getLogger(__name__)


class PromptDialog(NSWindowController):
    """Dialog for adding/editing prompts"""

    def initWithPrompt_isEdit_(self, prompt: Optional[Dict[str, str]] = None,
                               is_edit: bool = False):
        """
        Initialize prompt dialog

        Args:
            prompt: Existing prompt data {"name": str, "text": str} or None
            is_edit: Whether this is editing an existing prompt
        """
        self = objc.super(PromptDialog, self).init()
        if self is None:
            return None

        self.prompt = prompt or {"name": "", "text": ""}
        self.is_edit = is_edit
        self.result = None
        self.callback = None
        self.response_code = None
        self.name_validator_callback = None  # External validation callback

        # Create validators
        self.prompt_validator = PromptValidator()
        self.theme_icon = ThemeAwareIcon()

        logger.debug(
            f"Creating prompt dialog, is_edit={is_edit}, prompt={self.prompt}"
        )
        self.createDialog()
        return self

    def createDialog(self):
        """Create the dialog window"""
        # Create window
        frame = NSMakeRect(100, 100, 500, 350)
        style_mask = (NSWindowStyleMaskTitled |
                      NSWindowStyleMaskClosable |
                      NSWindowStyleMaskMiniaturizable)

        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame, style_mask, NSBackingStoreBuffered, False
        )

        title = "Edit Prompt" if self.is_edit else "Add New Prompt"
        window.setTitle_(title)
        window.setLevel_(NSModalPanelWindowLevel)
        window.setReleasedWhenClosed_(False)
        window.setDelegate_(self)
        content_view = window.contentView()

        # Make window accept key events
        window.setAcceptsMouseMovedEvents_(True)
        window.makeKeyWindow()

        # Try to set window icon
        try:
            self.theme_icon.set_window_icon(window)
        except Exception as e:
            logger.debug(f"Could not set prompt dialog icon: {e}")

        # Name field (max 10 chars)
        name_label = NSTextField.alloc().initWithFrame_(
            NSMakeRect(20, 280, 100, 20)
        )
        name_label.setStringValue_("Name (max 10):")
        name_label.setBezeled_(False)
        name_label.setDrawsBackground_(False)
        name_label.setEditable_(False)
        content_view.addSubview_(name_label)

        self.name_field = NSTextField.alloc().initWithFrame_(
            NSMakeRect(130, 280, 200, 25)
        )
        self.name_field.setStringValue_(self.prompt.get("name", ""))
        self.name_field.setTarget_(self)
        self.name_field.setAction_("validateName:")
        content_view.addSubview_(self.name_field)

        # Character count label
        self.char_count_label = NSTextField.alloc().initWithFrame_(
            NSMakeRect(340, 280, 100, 20)
        )
        self.char_count_label.setBezeled_(False)
        self.char_count_label.setDrawsBackground_(False)
        self.char_count_label.setEditable_(False)
        self.char_count_label.setFont_(NSFont.systemFontOfSize_(10))
        self.char_count_label.setTextColor_(NSColor.secondaryLabelColor())
        content_view.addSubview_(self.char_count_label)

        # Name error label (initially hidden)
        self.name_error_label = NSTextField.alloc().initWithFrame_(
            NSMakeRect(130, 255, 300, 20)
        )
        self.name_error_label.setStringValue_("")
        self.name_error_label.setBezeled_(False)
        self.name_error_label.setDrawsBackground_(False)
        self.name_error_label.setEditable_(False)
        self.name_error_label.setFont_(NSFont.systemFontOfSize_(11))
        self.name_error_label.setTextColor_(NSColor.systemRedColor())
        self.name_error_label.setHidden_(True)
        content_view.addSubview_(self.name_error_label)

        # Prompt text field
        prompt_label = NSTextField.alloc().initWithFrame_(
            NSMakeRect(20, 220, 100, 20)
        )
        prompt_label.setStringValue_("Prompt Text:")
        prompt_label.setBezeled_(False)
        prompt_label.setDrawsBackground_(False)
        prompt_label.setEditable_(False)
        content_view.addSubview_(prompt_label)

        # Scrollable text view for prompt
        scroll_view = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(20, 120, 460, 90)
        )
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setHasHorizontalScroller_(False)
        scroll_view.setBorderType_(NSBezelBorder)

        self.prompt_text_view = NSTextView.alloc().initWithFrame_(
            scroll_view.contentView().bounds()
        )
        self.prompt_text_view.setString_(self.prompt.get("text", ""))
        self.prompt_text_view.setFont_(NSFont.systemFontOfSize_(12))
        self.prompt_text_view.setDelegate_(self)
        self.prompt_text_view.setImportsGraphics_(False)
        scroll_view.setDocumentView_(self.prompt_text_view)
        content_view.addSubview_(scroll_view)

        # Text error label (initially hidden)
        self.text_error_label = NSTextField.alloc().initWithFrame_(
            NSMakeRect(20, 95, 460, 20)
        )
        self.text_error_label.setStringValue_("")
        self.text_error_label.setBezeled_(False)
        self.text_error_label.setDrawsBackground_(False)
        self.text_error_label.setEditable_(False)
        self.text_error_label.setFont_(NSFont.systemFontOfSize_(11))
        self.text_error_label.setTextColor_(NSColor.systemRedColor())
        self.text_error_label.setHidden_(True)
        content_view.addSubview_(self.text_error_label)

        # Buttons
        cancel_button = NSButton.alloc().initWithFrame_(
            NSMakeRect(320, 20, 80, 30)
        )
        cancel_button.setTitle_("Cancel")
        cancel_button.setTarget_(self)
        cancel_button.setAction_("cancel:")
        cancel_button.setKeyEquivalent_("\x1b")  # Escape key
        content_view.addSubview_(cancel_button)

        self.save_button = NSButton.alloc().initWithFrame_(
            NSMakeRect(410, 20, 80, 30)
        )
        self.save_button.setTitle_("Save")
        self.save_button.setTarget_(self)
        self.save_button.setAction_("save:")
        self.save_button.setKeyEquivalent_("\r")  # Return key
        self.save_button.setEnabled_(True)
        content_view.addSubview_(self.save_button)

        # Update initial state
        self.updateCharCount()
        self.validateName_(None)

        self.setWindow_(window)

    def setNameValidator_(self, validator_callback: Callable):
        """Set external name validator callback"""
        self.name_validator_callback = validator_callback

    def validateName_(self, sender):
        """Validate the prompt name"""
        name = self.name_field.stringValue().strip()

        # Clear previous errors
        self.clearValidationErrors()

        # Basic validation
        is_valid, error = self.prompt_validator.validate_name(name, [])

        if not is_valid:
            self.showNameError_(error)
            return False

        # External validation (for duplicates)
        if self.name_validator_callback:
            is_valid, error = self.name_validator_callback(name)
            if not is_valid:
                self.showNameError_(error)
                return False

        return True

    def clearValidationErrors(self):
        """Clear all validation error messages"""
        self.name_error_label.setHidden_(True)
        self.text_error_label.setHidden_(True)
        self.name_field.setTextColor_(NSColor.labelColor())
        self.save_button.setEnabled_(True)

    def showNameError_(self, message: str):
        """Show name validation error"""
        self.name_error_label.setStringValue_(message)
        self.name_error_label.setHidden_(False)
        self.name_field.setTextColor_(NSColor.systemRedColor())
        self.save_button.setEnabled_(False)

    def showTextError_(self, message: str):
        """Show text validation error"""
        self.text_error_label.setStringValue_(message)
        self.text_error_label.setHidden_(False)
        self.save_button.setEnabled_(False)

    def textDidChange_(self, notification):
        """Handle text changes in the prompt text view"""
        self.updateCharCount()

    def updateCharCount(self):
        """Update character count display"""
        name_length = len(self.name_field.stringValue())
        remaining = self.prompt_validator.MAX_NAME_LENGTH - name_length

        if remaining < 0:
            self.char_count_label.setStringValue_(f"{abs(remaining)} over")
            self.char_count_label.setTextColor_(NSColor.systemRedColor())
        else:
            self.char_count_label.setStringValue_(f"{remaining} left")
            self.char_count_label.setTextColor_(NSColor.secondaryLabelColor())

    def save_(self, sender):
        """Save the prompt"""
        name = self.name_field.stringValue().strip()
        text = self.prompt_text_view.string().strip()

        # Validate name
        if not self.validateName_(None):
            return

        # Validate text
        is_valid, error = self.prompt_validator.validate_content(text)
        if not is_valid:
            self.showTextError_(error)
            return

        # Check for actual changes
        if (self.is_edit and
                name == self.prompt.get("name", "") and
                text == self.prompt.get("text", "")):
            # No changes made
            self.showAlertWithTitle_message_(
                "No Changes",
                "No changes were made to the prompt."
            )
            return

        # Save result
        self.result = {"name": name, "text": text}
        self.response_code = NSModalResponseOK

        logger.info(f"Saving prompt: {name}")

        # Call callback if set
        if self.callback:
            self.callback(self.result)

        # End modal if running modal
        self.endModalDialog()

        # Close window
        self.window().close()

    def cancel_(self, sender):
        """Cancel the dialog"""
        logger.debug("Prompt dialog cancelled")
        self.result = None
        self.response_code = NSModalResponseCancel

        if self.callback:
            self.callback(None)

        self.endModalDialog()
        self.window().close()

    def endModalDialog(self):
        """End modal dialog if running"""
        try:
            app = NSApp()
            if app and hasattr(app, 'stopModalWithCode_'):
                if self.response_code == NSModalResponseOK:
                    app.stopModalWithCode_(NSRunStoppedResponse)
                else:
                    app.stopModalWithCode_(NSRunContinuesResponse)
        except Exception as e:
            logger.error(f"Error ending modal dialog: {e}")

    def showAlertWithTitle_message_(self, title: str, message: str):
        """Show an alert dialog"""
        alert = NSAlert.alloc().init()
        alert.setMessageText_(title)
        alert.setInformativeText_(message)
        alert.setAlertStyle_(NSAlertStyleWarning)
        alert.addButtonWithTitle_("OK")

        # Set icon
        self.theme_icon.set_dialog_icon(alert)

        alert.runModal()

    def runModalDialog(self) -> Optional[Dict[str, str]]:
        """Run the dialog as modal and return result"""
        try:
            window = self.window()
            if not window:
                logger.error("No window available for modal dialog")
                return None

            # Make window key and front
            window.makeKeyAndOrderFront_(None)
            window.center()

            # Run modal
            app = NSApp()
            response = app.runModalForWindow_(window)

            # Check response
            if response == NSRunStoppedResponse and self.result:
                return self.result

            return None

        except Exception as e:
            logger.error(f"Error running modal dialog: {e}")
            return None
        finally:
            # Ensure window is closed
            if self.window():
                self.window().close()

    # Window delegate methods
    def windowShouldClose_(self, window):
        """Handle window close button"""
        self.cancel_(None)
        return True

    def windowWillClose_(self, notification):
        """Clean up when window closes"""
        logger.debug("Prompt dialog window closing")

    def performKeyEquivalent_(self, event):
        """Handle keyboard shortcuts"""
        # Check for Escape key
        if event.keyCode() == 53:  # Escape
            self.cancel_(None)
            return True

        # Check for Cmd+W
        if (event.modifierFlags() & NSEventModifierFlagCommand and
                event.charactersIgnoringModifiers().lower() == 'w'):
            self.cancel_(None)
            return True

        return False

    def keyDown_(self, event):
        """Handle key down events"""
        # Forward to performKeyEquivalent
        if self.performKeyEquivalent_(event):
            return

        # Let superclass handle
        objc.super(PromptDialog, self).keyDown_(event)

    def cancelOperation_(self, sender):
        """Handle cancel operation (Escape key)"""
        self.cancel_(None) 