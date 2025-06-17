#!/usr/bin/env python3
"""
Logs Settings Section
Handles log viewing and management in settings
"""

import os
import logging
from typing import Optional, Callable
from datetime import datetime
from AppKit import (
    NSView, NSTextView, NSScrollView,
    NSMakeRect, NSFont, NSColor,
    NSViewWidthSizable, NSViewHeightSizable, NSBezelBorder
)

from ..widgets.ui_helpers import create_label, create_button, create_switch

logger = logging.getLogger(__name__)


class LogsSettingsSection:
    """Manages the logs settings section"""
    
    def __init__(self, settings_manager, on_settings_changed: Optional[Callable] = None):
        """
        Initialize logs settings section
        
        Args:
            settings_manager: Settings manager instance
            on_settings_changed: Callback when settings change
        """
        self.settings_manager = settings_manager
        self.on_settings_changed = on_settings_changed
        
        # UI elements
        self.view = None
        self.text_view = None
        self.scroll_view = None
        self.refresh_button = None
        self.clear_button = None
        self.export_button = None
        self.auto_scroll_switch = None
        self.debug_mode_switch = None
        
        # State
        self.auto_scroll = True
        
    def create_view(self, width: int = 700, height: int = 600) -> NSView:
        """
        Create the logs settings view
        
        Args:
            width: View width
            height: View height
            
        Returns:
            NSView containing the logs settings
        """
        logger.debug("Creating logs settings view")
        
        # Create main view
        self.view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))
        
        y_offset = height - 40
        
        # Title
        title = create_label(
            "Logs",
            NSMakeRect(20, y_offset, 200, 30),
            font=NSFont.boldSystemFontOfSize_(18)
        )
        self.view.addSubview_(title)
        
        # Description
        y_offset -= 30
        desc = create_label(
            "View application logs and debug information",
            NSMakeRect(20, y_offset, 600, 20),
            font=NSFont.systemFontOfSize_(13),
            color=NSColor.secondaryLabelColor()
        )
        self.view.addSubview_(desc)
        
        y_offset -= 40
        
        # Controls
        y_offset = self._create_controls(y_offset)
        
        y_offset -= 20
        
        # Log viewer
        log_height = y_offset - 40
        self._create_log_viewer(20, 40, width - 40, log_height)
        
        # Load initial logs
        self._load_logs()
        
        return self.view
        
    def _create_controls(self, y_offset: int) -> int:
        """Create control buttons and switches"""
        # Refresh button
        self.refresh_button = create_button(
            "Refresh",
            NSMakeRect(20, y_offset, 80, 25),
            action=self.refreshLogs_,
            target=self
        )
        self.view.addSubview_(self.refresh_button)
        
        # Clear button
        self.clear_button = create_button(
            "Clear",
            NSMakeRect(110, y_offset, 80, 25),
            action=self.clearLogs_,
            target=self
        )
        self.view.addSubview_(self.clear_button)
        
        # Export button
        self.export_button = create_button(
            "Export",
            NSMakeRect(200, y_offset, 80, 25),
            action=self.exportLogs_,
            target=self
        )
        self.view.addSubview_(self.export_button)
        
        # Auto-scroll switch
        self.auto_scroll_switch = create_switch(
            NSMakeRect(350, y_offset, 150, 25),
            title="Auto-scroll",
            action=self.toggleAutoScroll_,
            target=self
        )
        self.auto_scroll_switch.setState_(1 if self.auto_scroll else 0)
        self.view.addSubview_(self.auto_scroll_switch)
        
        # Debug mode switch
        self.debug_mode_switch = create_switch(
            NSMakeRect(510, y_offset, 150, 25),
            title="Debug mode",
            action=self.toggleDebugMode_,
            target=self
        )
        debug_enabled = self.settings_manager.get("debug_mode", False)
        self.debug_mode_switch.setState_(1 if debug_enabled else 0)
        self.view.addSubview_(self.debug_mode_switch)
        
        return y_offset - 35
        
    def _create_log_viewer(self, x: float, y: float, width: float, height: float):
        """Create the log text viewer"""
        # Create scroll view
        self.scroll_view = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(x, y, width, height)
        )
        self.scroll_view.setHasVerticalScroller_(True)
        self.scroll_view.setHasHorizontalScroller_(True)
        self.scroll_view.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable
        )
        self.scroll_view.setBorderType_(NSBezelBorder)
        
        # Create text view
        content_size = self.scroll_view.contentSize()
        self.text_view = NSTextView.alloc().initWithFrame_(
            NSMakeRect(0, 0, content_size.width, content_size.height)
        )
        self.text_view.setEditable_(False)
        self.text_view.setSelectable_(True)
        self.text_view.setRichText_(True)
        self.text_view.setImportsGraphics_(False)
        self.text_view.setFont_(NSFont.monospacedSystemFontOfSize_weight_(11, 0))
        self.text_view.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable
        )
        
        # Set text container properties
        text_container = self.text_view.textContainer()
        text_container.setContainerSize_(NSMakeRect(0, 0, width, 1000000).size)
        text_container.setWidthTracksTextView_(True)
        
        # Set as document view
        self.scroll_view.setDocumentView_(self.text_view)
        
        # Add to view
        self.view.addSubview_(self.scroll_view)
        
    def _load_logs(self):
        """Load logs from file"""
        try:
            log_file = self._get_log_file_path()
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Limit to last 10000 lines for performance
                lines = content.split('\n')
                if len(lines) > 10000:
                    lines = lines[-10000:]
                    content = '\n'.join(lines)
                    
                self._display_logs(content)
            else:
                self._display_logs("No log file found.")
                
        except Exception as e:
            logger.error(f"Error loading logs: {e}")
            self._display_logs(f"Error loading logs: {str(e)}")
            
    def _display_logs(self, content: str):
        """Display log content in text view"""
        # Create attributed string with syntax highlighting
        attributed_string = self._create_attributed_log_string(content)
        
        # Set text
        self.text_view.textStorage().setAttributedString_(attributed_string)
        
        # Auto-scroll to bottom if enabled
        if self.auto_scroll:
            self.text_view.scrollToEndOfDocument_(None)
            
    def _create_attributed_log_string(self, content: str):
        """Create attributed string with log level coloring"""
        from AppKit import NSMutableAttributedString, NSAttributedString
        
        attributed = NSMutableAttributedString.alloc().init()
        
        for line in content.split('\n'):
            line_attr = None
            color = NSColor.labelColor()  # Default color
            
            # Color based on log level
            if '[ERROR]' in line or 'ERROR' in line:
                color = NSColor.systemRedColor()
            elif '[WARNING]' in line or 'WARNING' in line:
                color = NSColor.systemOrangeColor()
            elif '[INFO]' in line or 'INFO' in line:
                color = NSColor.systemBlueColor()
            elif '[DEBUG]' in line or 'DEBUG' in line:
                color = NSColor.systemGrayColor()
                
            # Create attributed string for line
            line_attr = NSAttributedString.alloc().initWithString_attributes_(
                line + '\n',
                {
                    'NSColor': color,
                    'NSFont': NSFont.monospacedSystemFontOfSize_weight_(11, 0)
                }
            )
            
            attributed.appendAttributedString_(line_attr)
            
        return attributed
        
    def _get_log_file_path(self) -> str:
        """Get the path to the log file"""
        # Try to get from logging configuration
        for handler in logging.getLogger().handlers:
            if hasattr(handler, 'baseFilename'):
                return handler.baseFilename
                
        # Fallback to default location
        log_dir = os.path.expanduser("~/Library/Logs/Potter")
        return os.path.join(log_dir, "potter.log")
        
    # Action methods
    def refreshLogs_(self, sender):
        """Refresh log display"""
        logger.debug("Refreshing logs")
        self._load_logs()
        
    def clearLogs_(self, sender):
        """Clear log display with confirmation dialog"""
        logger.debug("Clearing log display")
        
        # Show confirmation dialog with themed icon
        from AppKit import NSAlert, NSAlertFirstButtonReturn
        
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Clear all logs?")
        alert.setInformativeText_("This will clear the log display. The log file will remain unchanged.")
        alert.addButtonWithTitle_("Clear")
        alert.addButtonWithTitle_("Cancel")
        alert.setAlertStyle_(1)  # NSAlertStyleInformational
        
        # Set themed icon - get parent window to access _set_dialog_icon method
        parent_window = self.view.window()
        if parent_window and hasattr(parent_window.windowController(), '_set_dialog_icon'):
            parent_window.windowController()._set_dialog_icon(alert)
        
        # Show modal dialog
        response = alert.runModal()
        
        if response == NSAlertFirstButtonReturn:  # Clear button clicked
            self.text_view.setString_("")
            logger.info("Log display cleared by user")
        else:
            logger.debug("Clear logs cancelled by user")
        
    def exportLogs_(self, sender):
        """Export logs to file"""
        try:
            # Get desktop path
            desktop = os.path.expanduser("~/Desktop")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = os.path.join(desktop, f"potter_logs_{timestamp}.txt")
            
            # Get log content
            content = self.text_view.string()
            
            # Write to file
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"Exported logs to: {export_path}")
            
            # Show in Finder
            from AppKit import NSWorkspace, NSURL
            workspace = NSWorkspace.sharedWorkspace()
            url = NSURL.fileURLWithPath_(export_path)
            workspace.activateFileViewerSelectingURLs_([url])
            
        except Exception as e:
            logger.error(f"Error exporting logs: {e}")
            
    def toggleAutoScroll_(self, sender):
        """Toggle auto-scroll setting"""
        self.auto_scroll = sender.state() == 1
        logger.debug(f"Auto-scroll: {self.auto_scroll}")
        
    def toggleDebugMode_(self, sender):
        """Toggle debug mode"""
        debug_enabled = sender.state() == 1
        self.settings_manager.set_setting("debug_mode", debug_enabled)
        
        # Update logging level
        if debug_enabled:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.info("Debug mode enabled")
        else:
            logging.getLogger().setLevel(logging.INFO)
            logger.info("Debug mode disabled")
            
        self._notify_settings_changed()
        
    def _notify_settings_changed(self):
        """Notify that settings have changed"""
        if self.on_settings_changed:
            try:
                self.on_settings_changed()
            except Exception as e:
                logger.error(f"Error in settings changed callback: {e}") 