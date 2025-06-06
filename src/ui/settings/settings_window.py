#!/usr/bin/env python3
"""
Settings Window
Main settings window that integrates all settings sections
"""

import logging
import objc
from AppKit import (
    NSButton, NSButtonTypeRadio,
    NSMakeRect, NSFont
)

from .base_settings_window import BaseSettingsWindow
from .sections import (
    GeneralSettingsSection,
    PromptsSettingsSection,
    AdvancedSettingsSection,
    LogsSettingsSection
)
from .widgets.ui_helpers import create_header_label

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
        
        # Sidebar configuration
        self.sidebar_items = [
            {"name": "General", "icon": "gear"},
            {"name": "Prompts", "icon": "doc.text"},
            {"name": "Advanced", "icon": "slider.horizontal.3"},
            {"name": "Logs", "icon": "doc.text.magnifyingglass"}
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
        """Create custom sidebar with section buttons"""
        objc.super(SettingsWindow, self)._createSidebar()
        
        y_offset = 620
        
        # Add header
        header = create_header_label(
            "Settings",
            NSMakeRect(20, y_offset, 160, 30),
            font=NSFont.boldSystemFontOfSize_(16)
        )
        self.sidebar_container.addSubview_(header)
        
        y_offset -= 50
        
        # Create section buttons
        for i, item in enumerate(self.sidebar_items):
            button = self._createSidebarButton_tag_yOffset_(item["name"], i, y_offset)
            self.sidebar_buttons.append(button)
            self.sidebar_container.addSubview_(button)
            y_offset -= 40
            
    def _createSidebarButton_tag_yOffset_(self, title: str, tag: int, y_offset: float) -> NSButton:
        """Create a sidebar button"""
        button = NSButton.alloc().initWithFrame_(
            NSMakeRect(10, y_offset, 180, 30)
        )
        button.setTitle_(title)
        button.setButtonType_(NSButtonTypeRadio)
        button.setTag_(tag)
        button.setTarget_(self)
        button.setAction_("switchSection:")
        
        # Style the button
        button.setBezelStyle_(12)  # NSBezelStyleRounded
        button.setFont_(NSFont.systemFontOfSize_(14))
        
        return button
        
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