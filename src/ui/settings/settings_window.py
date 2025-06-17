#!/usr/bin/env python3
"""
Settings Window
Main settings window that integrates all settings sections
"""

import logging
import objc
from AppKit import (
    NSButton, NSButtonTypeRadio,
    NSMakeRect, NSFont, NSTextField, NSColor, NSView
)

from .base_settings_window import BaseSettingsWindow
from .sections import (
    GeneralSettingsSection,
    PromptsSettingsSection,
    AdvancedSettingsSection,
    LogsSettingsSection
)
# UI helpers imported as needed

logger = logging.getLogger(__name__)


class SettingsWindow(BaseSettingsWindow):
    """Main settings window with all sections"""
    
    def initWithSettingsManager_(self, settings_manager):
        """
        Initialize settings window with settings manager
        
        Args:
            settings_manager: Settings manager instance
        """
        self = objc.super(SettingsWindow, self).init()
        if self is None:
            return None
            
        self.settings_manager = settings_manager
        
        # Section instances
        self.general_section = None
        self.prompts_section = None
        self.advanced_section = None
        self.logs_section = None
        
        # Sidebar configuration - matching spec exactly
        self.sidebar_items = [
            {"title": "General", "icon": "gear", "tag": 0},
            {"title": "Prompts", "icon": "text.bubble", "tag": 1},
            {"title": "Advanced", "icon": "slider.horizontal.3", "tag": 2},
            {"title": "Logs", "icon": "doc.text", "tag": 3}
        ]
        
        return self
        
    def show(self):
        """Show the settings window"""
        logger.debug("Showing settings window")
        
        # Create window if needed
        if not self.window():
            self.createWindow("Potter Settings")
            
        # Center and show
        self.window().center()
        self.window().makeKeyAndOrderFront_(None)
        
        # Make first field active
        self._makeFirstFieldActive()
        
    def _createSidebar(self):
        """Create custom sidebar with section buttons matching exact spec"""
        objc.super(SettingsWindow, self)._createSidebar()
        
        # Add title at the top - matching spec position (20, 600, 160, 30)
        y_offset = 600
        header = NSTextField.alloc().initWithFrame_(NSMakeRect(20, y_offset, 160, 30))
        header.setStringValue_("Settings")
        header.setFont_(NSFont.boldSystemFontOfSize_(20))  # 20pt as per spec
        header.setBezeled_(False)
        header.setDrawsBackground_(False)
        header.setEditable_(False)
        header.setTextColor_(NSColor.labelColor())
        self.sidebar_container.addSubview_(header)
        
        # Create sidebar buttons with exact spec positioning
        y_position = y_offset - 40  # Start after title
        for item in self.sidebar_items:
            button = self._createSidebarButton_item_yPosition_(None, item, y_position)
            self.sidebar_buttons.append(button)
            self.sidebar_container.addSubview_(button)
            y_position -= 50  # 50px spacing as per spec
            
        # Create sidebar footer - matching spec
        self._createSidebarFooter()
            
    def _createSidebarButton_item_yPosition_(self, sender, item: dict, y_position: float) -> NSButton:
        """Create a sidebar button matching exact spec"""
        button = NSButton.alloc().initWithFrame_(NSMakeRect(10, y_position, 180, 40))
        button.setButtonType_(NSButtonTypeRadio)
        button.setBordered_(False)
        button.setTag_(item["tag"])
        button.setTarget_(self)
        button.setAction_("switchSection:")
        
        # Set button title with proper formatting
        title = item["title"]
        button.setTitle_(f"  {title}")  # Add space for icon
        button.setFont_(NSFont.systemFontOfSize_(14))
        
        # Configure button appearance for highlighting
        button.setBezelStyle_(12)  # NSBezelStyleRegularSquare
        button.setBordered_(True)
        button.setShowsBorderOnlyWhileMouseInside_(False)
        
        return button
        
    def _createSidebarFooter(self):
        """Create footer area with buttons - matching spec"""
        # Footer container - (0, 20, 200, 100)
        footer = NSView.alloc().initWithFrame_(NSMakeRect(0, 20, 200, 100))
        footer.setAutoresizingMask_(0)  # NSViewMaxYMargin
        
        # Separator line - (20, 80, 160, 1)
        separator = NSView.alloc().initWithFrame_(NSMakeRect(20, 80, 160, 1))
        separator.setWantsLayer_(True)
        separator.layer().setBackgroundColor_(NSColor.separatorColor().CGColor())
        footer.addSubview_(separator)
        
        # Cancel button - (20, 40, 70, 32)
        cancel_button = NSButton.alloc().initWithFrame_(NSMakeRect(20, 40, 70, 32))
        cancel_button.setTitle_("Cancel")
        cancel_button.setTarget_(self)
        cancel_button.setAction_("cancel:")
        cancel_button.setBezelStyle_(1)  # NSBezelStyleRounded
        cancel_button.setKeyEquivalent_("\x1b")  # Escape key
        footer.addSubview_(cancel_button)
        
        # Quit button - (100, 40, 80, 32)
        quit_button = NSButton.alloc().initWithFrame_(NSMakeRect(100, 40, 80, 32))
        quit_button.setTitle_("Quit Potter")
        quit_button.setTarget_(self)
        quit_button.setAction_("quitApplication:")
        quit_button.setBezelStyle_(1)  # NSBezelStyleRounded
        quit_button.setFont_(NSFont.systemFontOfSize_(13))
        footer.addSubview_(quit_button)
        
        # Add footer to sidebar container
        self.sidebar_container.addSubview_(footer)
        
    def _createContentViews(self):
        """Create all section views"""
        logger.debug("Creating content views...")
        
        # Create sections with settings changed callback
        callback = self.notifySettingsChanged
        
        # General section
        self.general_section = GeneralSettingsSection(
            self.settings_manager,
            on_settings_changed=callback
        )
        general_view = self.general_section.create_view()
        self.content_views.append(general_view)
        logger.debug("General view created successfully")
        
        # Prompts section
        self.prompts_section = PromptsSettingsSection(
            self.settings_manager,
            on_settings_changed=callback
        )
        prompts_view = self.prompts_section.create_view()
        self.content_views.append(prompts_view)
        logger.debug("Prompts view created successfully")
        
        # Advanced section
        self.advanced_section = AdvancedSettingsSection(
            self.settings_manager,
            on_settings_changed=callback
        )
        advanced_view = self.advanced_section.create_view()
        self.content_views.append(advanced_view)
        logger.debug("Advanced view created successfully")
        
        # Logs section
        self.logs_section = LogsSettingsSection(
            self.settings_manager,
            on_settings_changed=callback
        )
        logs_view = self.logs_section.create_view()
        self.content_views.append(logs_view)
        logger.debug("Logs view created successfully")
        
        logger.debug(f"Created {len(self.content_views)} content views successfully")
        
    def _makeFirstFieldActive(self):
        """Make the first field in the current section active"""
        try:
            if self.current_section == 2:  # Advanced section
                # Focus on API key field
                if self.advanced_section and hasattr(self.advanced_section, 'api_key_fields'):
                    provider = self.advanced_section.current_provider
                    field = self.advanced_section.api_key_fields.get(provider)
                    if field and field.acceptsFirstResponder():
                        logger.debug("API key field becoming first responder")
                        self.window().makeFirstResponder_(field)
                        if field.becomeFirstResponder():
                            logger.debug("API key field successfully became first responder")
        except Exception as e:
            logger.error(f"Error making first field active: {e}")
            
    def _cleanup(self):
        """Clean up when window closes"""
        logger.debug("Cleaning up settings window")
        
        # Save any pending changes
        try:
            self.settings_manager.save()
            logger.debug("Settings saved on window close")
        except Exception as e:
            logger.error(f"Error saving settings on close: {e}")
            
    # Public methods
    def showGeneralSection(self):
        """Show the general section"""
        self.showSection_(0)
        
    def showPromptsSection(self):
        """Show the prompts section"""
        self.showSection_(1)
        
    def showAdvancedSection(self):
        """Show the advanced section"""
        self.showSection_(2)
        
    def showLogsSection(self):
        """Show the logs section"""
        self.showSection_(3)
        
    def getSelectedProvider(self) -> str:
        """Get the currently selected provider"""
        if self.advanced_section:
            return self.advanced_section.current_provider
        return self.settings_manager.get("provider", "openai")
        
    # Footer button actions
    def cancel_(self, sender):
        """Handle cancel button"""
        logger.debug("Cancel button pressed - closing settings")
        if self.window():
            self.window().close()
            
    def quitApplication_(self, sender):
        """Handle quit application button"""
        logger.debug("Quit Potter button pressed")
        from AppKit import NSApplication
        NSApplication.sharedApplication().terminate_(None) 