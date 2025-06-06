#!/usr/bin/env python3
"""
UI Helper Functions
Common UI creation utilities for Potter settings
"""

import logging
from typing import Tuple, Optional
from AppKit import (
    NSTextField, NSView, NSButton, NSSwitch, NSImage, NSFont, NSColor,
    NSMakeRect, NSMakeSize, NSButtonTypeSwitch, NSButtonTypePushOnPushOff,
    NSBezelStyleRegularSquare, NSImageLeft, NSImageScaleProportionallyDown,
    NSTextAlignmentLeft, NSChangeGrayCellMask, NSChangeBackgroundCellMask,
    NSObject, NSPopUpButton
)
import objc

logger = logging.getLogger(__name__)


def create_section_header(title: str, y_position: float) -> NSTextField:
    """
    Create a modern section header
    
    Args:
        title: Header text
        y_position: Y coordinate for positioning
        
    Returns:
        NSTextField configured as header
    """
    header = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_position, 620, 35))
    header.setStringValue_(title)
    header.setFont_(NSFont.boldSystemFontOfSize_(24))
    header.setBezeled_(False)
    header.setDrawsBackground_(False)
    header.setEditable_(False)
    header.setTextColor_(NSColor.labelColor())
    return header


def create_section_separator(y_position: float) -> NSView:
    """
    Create a visual separator line
    
    Args:
        y_position: Y coordinate for positioning
        
    Returns:
        NSView configured as separator
    """
    separator = NSView.alloc().initWithFrame_(NSMakeRect(40, y_position, 620, 1))
    separator.setWantsLayer_(True)
    separator.layer().setBackgroundColor_(NSColor.separatorColor().CGColor())
    return separator


def create_modern_switch(frame, title: str, initial_state: bool = False) -> Tuple[NSView, NSButton]:
    """
    Create a modern switch control with label
    
    Args:
        frame: NSRect for the control frame
        title: Label text
        initial_state: Initial on/off state
        
    Returns:
        Tuple of (container view, switch control)
    """
    container = NSView.alloc().initWithFrame_(frame)
    
    # Label
    label = NSTextField.alloc().initWithFrame_(
        NSMakeRect(0, 5, frame.size.width - 60, 20)
    )
    label.setStringValue_(title)
    label.setBezeled_(False)
    label.setDrawsBackground_(False)
    label.setEditable_(False)
    label.setFont_(NSFont.systemFontOfSize_(14))
    label.setTextColor_(NSColor.labelColor())
    container.addSubview_(label)
    
    # Switch (try NSSwitch first, fallback to checkbox)
    try:
        switch = NSSwitch.alloc().initWithFrame_(
            NSMakeRect(frame.size.width - 50, 0, 50, 30)
        )
        switch.setState_(1 if initial_state else 0)
    except Exception:
        # Fallback for older macOS
        switch = NSButton.alloc().initWithFrame_(
            NSMakeRect(frame.size.width - 50, 0, 50, 30)
        )
        switch.setButtonType_(NSButtonTypeSwitch)
        switch.setState_(1 if initial_state else 0)
    
    container.addSubview_(switch)
    
    return container, switch


def create_sidebar_button(item: dict, y_position: float) -> NSButton:
    """
    Create enhanced sidebar button with icon and highlighting
    
    Args:
        item: Dict with 'title', 'icon', and 'tag' keys
        y_position: Y coordinate for positioning
        
    Returns:
        NSButton configured for sidebar
    """
    button = NSButton.alloc().initWithFrame_(NSMakeRect(10, y_position, 180, 40))
    button.setButtonType_(NSButtonTypePushOnPushOff)  # Toggle for highlighting
    button.setBordered_(False)
    button.setTag_(item["tag"])
    
    # Create custom attributed title with icon and text
    icon_name = item["icon"]
    title = item["title"]
    
    # Try to use SF Symbols if available
    icon = None
    if hasattr(NSImage, 'imageWithSystemSymbolName_accessibilityDescription_'):
        icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            icon_name, None
        )
        if icon:
            icon.setSize_(NSMakeSize(16, 16))
    
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
    button.setBezelStyle_(NSBezelStyleRegularSquare)
    button.setBordered_(True)
    button.setShowsBorderOnlyWhileMouseInside_(False)
    
    # Create custom cell for better control
    cell = button.cell()
    if hasattr(cell, 'setHighlightsBy_'):
        cell.setHighlightsBy_(NSChangeGrayCellMask)
    if hasattr(cell, 'setShowsStateBy_'):
        cell.setShowsStateBy_(NSChangeBackgroundCellMask)
    
    return button


def create_label(text: str, frame, 
                 font: Optional[NSFont] = None,
                 color: Optional[NSColor] = None,
                 alignment: int = NSTextAlignmentLeft) -> NSTextField:
    """
    Create a label with customizable font and color
    
    Args:
        text: Label text
        frame: NSRect for the label frame
        font: Optional custom font
        color: Optional text color
        alignment: Text alignment
        
    Returns:
        NSTextField configured as label
    """
    label = NSTextField.alloc().initWithFrame_(frame)
    label.setStringValue_(text)
    
    if font:
        label.setFont_(font)
    else:
        label.setFont_(NSFont.systemFontOfSize_(13))
    
    label.setBezeled_(False)
    label.setDrawsBackground_(False)
    label.setEditable_(False)
    
    if color:
        label.setTextColor_(color)
    else:
        label.setTextColor_(NSColor.labelColor())
        
    label.setAlignment_(alignment)
    
    return label


def create_description_label(text: str, frame) -> NSTextField:
    """
    Create a description label with secondary color
    
    Args:
        text: Label text
        frame: NSRect for the label frame
        
    Returns:
        NSTextField configured as description label
    """
    return create_label(
        text, 
        frame,
        font=NSFont.systemFontOfSize_(11),
        color=NSColor.secondaryLabelColor()
    )


def create_header_label(text: str, frame, font: Optional[NSFont] = None) -> NSTextField:
    """
    Create a header label
    
    Args:
        text: Label text
        frame: NSRect for the label frame
        font: Optional custom font (defaults to bold 16pt)
        
    Returns:
        NSTextField configured as header label
    """
    if not font:
        font = NSFont.boldSystemFontOfSize_(16)
    
    return create_label(text, frame, font=font)


def create_switch(frame, title: str, action=None, target=None) -> NSButton:
    """
    Create a switch/checkbox control
    
    Args:
        frame: NSRect for the control frame
        title: Label text
        action: Optional action selector (string or method)
        target: Optional target object
        
    Returns:
        NSButton configured as switch
    """
    switch = NSButton.alloc().initWithFrame_(frame)
    switch.setButtonType_(NSButtonTypeSwitch)
    switch.setTitle_(title)
    
    if action:
        # Convert method to selector string if needed
        if hasattr(action, '__name__'):
            action_name = action.__name__
        else:
            action_name = str(action)
        switch.setAction_(action_name)
    if target:
        switch.setTarget_(target)
    
    return switch


def create_popup_button(frame, items: list, action=None, target=None) -> NSPopUpButton:
    """
    Create a popup button (dropdown)
    
    Args:
        frame: NSRect for the button frame
        items: List of menu items
        action: Optional action selector (string or method)
        target: Optional target object
        
    Returns:
        NSPopUpButton configured with items
    """
    from AppKit import NSPopUpButton
    
    popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(frame, False)
    
    for item in items:
        popup.addItemWithTitle_(item)
    
    if action:
        # Convert method to selector string if needed
        if hasattr(action, '__name__'):
            action_name = action.__name__
        else:
            action_name = str(action)
        popup.setAction_(action_name)
    if target:
        popup.setTarget_(target)
    
    return popup


def create_text_field(frame, placeholder: str = "") -> NSTextField:
    """
    Create an editable text field
    
    Args:
        frame: NSRect for the field frame
        placeholder: Placeholder text
        
    Returns:
        NSTextField configured as editable
    """
    field = NSTextField.alloc().initWithFrame_(frame)
    field.setPlaceholderString_(placeholder)
    field.setBezeled_(True)
    field.setBezelStyle_(0)  # NSTextFieldSquareBezel = 0
    field.setEditable_(True)
    field.setSelectable_(True)
    
    return field


def create_button(title: str, frame, action=None, target=None) -> NSButton:
    """
    Create a standard button
    
    Args:
        title: Button title
        frame: NSRect for the button frame
        action: Optional action selector (string or method)
        target: Optional target object
        
    Returns:
        NSButton configured with title and action
    """
    button = NSButton.alloc().initWithFrame_(frame)
    button.setTitle_(title)
    button.setBezelStyle_(1)  # NSBezelStyleRounded = 1
    
    if action:
        # Convert method to selector string if needed
        if hasattr(action, '__name__'):
            action_name = action.__name__
        else:
            action_name = str(action)
        button.setAction_(action_name)
    if target:
        button.setTarget_(target)
    
    return button


class LinkTarget(NSObject):
    """Target class for clickable links"""
    
    def initWithURL_(self, url: str):
        """Initialize with URL"""
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


def create_clickable_link(frame, text: str, url: str) -> NSButton:
    """
    Create a clickable link button
    
    Args:
        frame: NSRect for the button frame
        text: Link text
        url: URL to open
        
    Returns:
        NSButton configured as link
    """
    button = NSButton.alloc().initWithFrame_(frame)
    button.setTitle_(text)
    button.setButtonType_(7)  # NSButtonTypeMomentaryPushIn = 7
    button.setBezelStyle_(1)  # NSBezelStyleRounded = 1
    button.setFont_(NSFont.systemFontOfSize_(11))
    
    # Set up click handling
    target = LinkTarget.alloc().initWithURL_(url)
    button.setTarget_(target)
    button.setAction_("openURL:")
    button.setRepresentedObject_(target)  # Keep reference
    
    return button 