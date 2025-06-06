#!/usr/bin/env python3
"""
Hotkey Capture Widget
A custom NSView that captures and displays hotkey combinations
"""

import logging
from typing import Callable
from AppKit import (
    NSView, NSButton, NSTextField, NSMakeRect, NSFont, NSColor,
    NSBezelStyleRounded, NSEventModifierFlagCommand,
    NSEventModifierFlagOption, NSEventModifierFlagControl,
    NSEventModifierFlagShift, NSControlSizeRegular, NSBlueControlTint
)
import objc

logger = logging.getLogger(__name__)


class HotkeyCapture(NSView):
    """Hotkey capture control that displays keys as pill buttons"""

    def initWithFrame_manager_(self, frame, settings_manager):
        """
        Initialize hotkey capture widget

        Args:
            frame: NSRect for the widget frame
            settings_manager: Settings manager instance
        """
        self = objc.super(HotkeyCapture, self).initWithFrame_(frame)
        if self is None:
            return None

        self.settings_manager = settings_manager
        self.reset_callback = None
        self.hotkey_parts = []
        self.is_capturing = False

        # Create container for pills
        self.pill_container = NSView.alloc().initWithFrame_(
            NSMakeRect(0, 0, frame.size.width - 100, frame.size.height)
        )
        self.addSubview_(self.pill_container)

        # Create capture button
        self.capture_button = NSButton.alloc().initWithFrame_(
            NSMakeRect(frame.size.width - 90, 0, 90, frame.size.height)
        )
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

    def setHotkeyString_(self, hotkey_string: str):
        """Set hotkey from string like 'cmd+shift+a'"""
        self.hotkey_parts = hotkey_string.split('+') if hotkey_string else []
        self.updatePillDisplay()

    def getHotkeyString(self) -> str:
        """Get hotkey as string"""
        return '+'.join(self.hotkey_parts) if self.hotkey_parts else ""

    def setResetCallback_(self, callback: Callable):
        """Set callback to be called when hotkey changes"""
        self.reset_callback = callback

    def updatePillDisplay(self):
        """Update the pill button display"""
        # Clear existing pills
        for subview in list(self.pill_container.subviews()):
            subview.removeFromSuperview()

        if not self.hotkey_parts:
            # Show placeholder
            placeholder = NSTextField.alloc().initWithFrame_(
                NSMakeRect(0, 5, 200, 15)
            )
            placeholder.setStringValue_("Click Capture to set hotkey")
            placeholder.setBezeled_(False)
            placeholder.setDrawsBackground_(False)
            placeholder.setEditable_(False)
            placeholder.setFont_(NSFont.systemFontOfSize_(11))
            placeholder.setTextColor_(NSColor.placeholderTextColor())
            self.pill_container.addSubview_(placeholder)
            return

        # Create pills for each key part
        x_offset = 0
        for i, part in enumerate(self.hotkey_parts):
            # Calculate pill width
            font = NSFont.boldSystemFontOfSize_(12)

            # Measure text size
            ns_string = objc.pyobjc_id(part)
            attributes = {objc.pyobjc_id("NSFont"): font}
            text_size = ns_string.sizeWithAttributes_(attributes)

            # Add padding
            base_padding = 24
            extra_padding = max(8, int((4 - len(part)) * 4))
            pill_width = int(text_size.width) + base_padding + extra_padding

            # Ensure minimum width for single characters
            if len(part) == 1:
                pill_width = max(pill_width, 40)

            pill_height = 24

            # Create pill button
            pill = NSButton.alloc().initWithFrame_(
                NSMakeRect(x_offset, 0, pill_width, pill_height)
            )
            pill.setTitle_(part)
            pill.setFont_(font)
            pill.setBezelStyle_(NSBezelStyleRounded)
            pill.setBordered_(True)
            pill.setEnabled_(False)  # Not clickable, just visual

            # Style the pill
            try:
                pill.setControlSize_(NSControlSizeRegular)

                # Set a nice blue tint for better visibility
                if hasattr(pill, 'setControlTint_'):
                    pill.setControlTint_(NSBlueControlTint)

                # Try to set background color
                cell = pill.cell()
                if hasattr(cell, 'setBackgroundColor_'):
                    cell.setBackgroundColor_(
                        NSColor.systemBlueColor().colorWithAlphaComponent_(0.1)
                    )

            except Exception as e:
                logger.debug(f"Pill styling error: {e}")

            self.pill_container.addSubview_(pill)
            x_offset += pill_width + 8

            # Add "+" between pills
            if i < len(self.hotkey_parts) - 1:
                plus_label = NSTextField.alloc().initWithFrame_(
                    NSMakeRect(x_offset, 6, 12, 15)
                )
                plus_label.setStringValue_("+")
                plus_label.setBezeled_(False)
                plus_label.setDrawsBackground_(False)
                plus_label.setEditable_(False)
                plus_label.setFont_(NSFont.boldSystemFontOfSize_(12))
                plus_label.setTextColor_(NSColor.secondaryLabelColor())
                self.pill_container.addSubview_(plus_label)
                x_offset += 18

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