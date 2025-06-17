#!/usr/bin/env python3
"""
Base Settings Window
Base class for settings windows with common functionality
"""

import os
import sys
import logging
from typing import Callable
from AppKit import (
    NSWindowController, NSWindow, NSView, NSSplitView, NSScrollView,
    NSMakeRect, NSMakeSize, NSWindowStyleMaskTitled, NSWindowStyleMaskClosable,
    NSWindowStyleMaskResizable, NSBackingStoreBuffered, NSNormalWindowLevel,
    NSViewWidthSizable, NSViewHeightSizable, NSSplitViewDividerStyleThin,
    NSColor, NSImage, NSApplication, NSNotificationCenter
)
import objc

from .widgets.theme_aware_icon import ThemeAwareIcon
from .utils import WindowPositioning
from .widgets.ui_helpers import create_header_label

logger = logging.getLogger(__name__)


class BaseSettingsWindow(NSWindowController):
    """Base class for settings windows with sidebar navigation"""

    def __init__(self):
        """Initialize base settings window"""
        objc.super(BaseSettingsWindow, self).__init__()
        
        # UI elements
        self.current_section = 0
        self.content_views = []
        self.sidebar_items = []
        self.sidebar_buttons = []
        self.split_view = None
        self.sidebar_container = None
        self.content_scroll_view = None
        self.content_container = None
        
        # Callbacks
        self.on_settings_changed = None
        
        # Theme handling
        self.theme_icon = ThemeAwareIcon()
        
        # Window positioning
        self.window_positioning = WindowPositioning("settings")
        
        logger.debug("BaseSettingsWindow initialized")
        
    def createWindow(self, title: str = "Settings", 
                     width: int = 900, height: int = 650,
                     min_width: int = 800, min_height: int = 600):
        """
        Create and configure the settings window
        
        Args:
            title: Window title
            width: Window width
            height: Window height
            min_width: Minimum window width
            min_height: Minimum window height
        """
        logger.debug(f"Creating settings window: {title}")
        
        # Create window
        frame = NSMakeRect(100, 100, width, height)
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | 
            NSWindowStyleMaskResizable,
            NSBackingStoreBuffered,
            False
        )
        
        window.setTitle_(title)
        window.setLevel_(NSNormalWindowLevel)
        window.setMinSize_(NSMakeSize(min_width, min_height))
        window.setDelegate_(self)
        
        # Set window icon
        self._set_window_icon(window)
        
        # Create split view
        self.split_view = NSSplitView.alloc().initWithFrame_(
            window.contentView().bounds()
        )
        self.split_view.setVertical_(True)
        self.split_view.setDividerStyle_(NSSplitViewDividerStyleThin)
        self.split_view.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable
        )
        
        # Create sidebar
        self._createSidebar()
        
        # Create content area
        self._createContentArea()
        
        # Add to split view
        self.split_view.addSubview_(self.sidebar_container)
        self.split_view.addSubview_(self.content_scroll_view)
        
        # Set split view positions
        self.split_view.setPosition_ofDividerAtIndex_(200, 0)
        
        window.contentView().addSubview_(self.split_view)
        
        # Create content views
        self._createContentViews()
        
        # Show initial section
        if self.content_views:
            self.showSection_(0)
        
        self.setWindow_(window)
        
        # Register for appearance changes
        self._register_for_appearance_changes()
        
        # Restore window position
        if not self.window_positioning.restore_window_state(window):
            window.center()
        
        logger.debug("Settings window created successfully")
    
    def _createSidebar(self):
        """Create sidebar container - override to customize"""
        self.sidebar_container = NSView.alloc().initWithFrame_(
            NSMakeRect(0, 0, 200, 650)
        )
        self.sidebar_container.setAutoresizingMask_(NSViewHeightSizable)
        
        # Sidebar background
        self.sidebar_container.setWantsLayer_(True)
        if hasattr(NSColor, 'controlBackgroundColor'):
            bg_color = NSColor.controlBackgroundColor()
        else:
            bg_color = NSColor.windowBackgroundColor()
        self.sidebar_container.layer().setBackgroundColor_(bg_color.CGColor())
        
        # Initialize buttons list
        self.sidebar_buttons = []
    
    def _createContentArea(self):
        """Create scrollable content area"""
        self.content_scroll_view = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(200, 0, 700, 650)
        )
        self.content_scroll_view.setHasVerticalScroller_(True)
        self.content_scroll_view.setHasHorizontalScroller_(False)
        self.content_scroll_view.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable
        )
        self.content_scroll_view.setBorderType_(0)  # NSNoBorder = 0
        
        # Content container
        self.content_container = NSView.alloc().initWithFrame_(
            NSMakeRect(0, 0, 700, 650)
        )
        self.content_scroll_view.setDocumentView_(self.content_container)
    
    def _createContentViews(self):
        """Create content views - override in subclass"""
        logger.warning("_createContentViews not implemented in subclass")
        self.content_views = []
    
    def showSection_(self, section: int):
        """
        Show a specific section
        
        Args:
            section: Section index to show
        """
        if not 0 <= section < len(self.content_views):
            logger.error(f"Invalid section index: {section}")
            return
        
        logger.debug(f"Showing section {section}")
        
        # Update current section
        self.current_section = section
        
        # Update sidebar selection
        self._updateSidebarSelection_(section)
        
        # Clear content container
        for subview in list(self.content_container.subviews()):
            subview.removeFromSuperview()
        
        # Add new content view
        content_view = self.content_views[section]
        if content_view:
            self.content_container.addSubview_(content_view)
            
            # Update scroll view size
            content_size = content_view.frame().size
            self.content_container.setFrameSize_(content_size)
            
            # Scroll to top
            self.content_scroll_view.contentView().scrollToPoint_(
                NSMakeRect(0, 0, 0, 0).origin
            )
            self.content_scroll_view.reflectScrolledClipView_(
                self.content_scroll_view.contentView()
            )
    
    def _updateSidebarSelection_(self, selected_section: int):
        """Update sidebar button selection states"""
        for i, button in enumerate(self.sidebar_buttons):
            if i == selected_section:
                # Selected state
                button.setState_(1)  # NSControlStateValueOn
                button.setFont_(NSFont.boldSystemFontOfSize_(14))
            else:
                # Unselected state
                button.setState_(0)  # NSControlStateValueOff
                button.setFont_(NSFont.systemFontOfSize_(14))
    
    def switchSection_(self, sender):
        """Handle sidebar button clicks"""
        section = sender.tag()
        self.showSection_(section)
    
    def _set_window_icon(self, window):
        """Set window icon using theme-aware icon"""
        try:
            self.theme_icon.set_window_icon(window)
            self._update_dock_icon()
        except Exception as e:
            logger.error(f"Error setting window icon: {e}")
    
    def _update_dock_icon(self):
        """Update dock icon for current appearance"""
        try:
            # Get current theme
            theme = self.theme_icon.get_current_theme()
            
            # Get icon path
            icon_path = self.theme_icon.get_icon_path("logo", theme)
            
            if os.path.exists(icon_path):
                # Load and set the icon
                ns_image = NSImage.alloc().initWithContentsOfFile_(icon_path)
                if ns_image:
                    ns_image.setSize_(NSMakeSize(128, 128))
                    app = NSApplication.sharedApplication()
                    app.setApplicationIconImage_(ns_image)
                    logger.debug(f"Updated dock icon for {theme} mode")
        except Exception as e:
            logger.error(f"Error updating dock icon: {e}")
    
    def _register_for_appearance_changes(self):
        """Register for system appearance change notifications"""
        try:
            notification_center = NSNotificationCenter.defaultCenter()
            # Try to get the notification name safely
            try:
                from AppKit import NSApplicationDidChangeEffectiveAppearanceNotification
                notification_name = NSApplicationDidChangeEffectiveAppearanceNotification
            except ImportError:
                # Fallback for older macOS/PyObjC versions
                notification_name = "NSApplicationDidChangeEffectiveAppearanceNotification"
            
            notification_center.addObserver_selector_name_object_(
                self,
                objc.selector(self.appearanceDidChange_, signature=b'v@:@'),
                notification_name,
                None
            )
            logger.debug("Registered for appearance change notifications")
        except Exception as e:
            logger.error(f"Failed to register for appearance changes: {e}")
    
    def appearanceDidChange_(self, notification):
        """Handle system appearance changes"""
        try:
            logger.debug("System appearance changed - updating UI")
            self._update_dock_icon()
            
            # Update tray icon if available
            self._update_tray_icon()
        except Exception as e:
            logger.error(f"Error handling appearance change: {e}")
    
    def _update_tray_icon(self):
        """Update tray icon for appearance change"""
        try:
            potter_module = sys.modules.get('__main__')
            if (potter_module and 
                hasattr(potter_module, 'service') and 
                hasattr(potter_module.service, 'tray_icon')):
                logger.debug("Updating tray icon for appearance change")
                potter_module.service.tray_icon.update_icon_for_appearance()
        except Exception as e:
            logger.debug(f"Could not update tray icon: {e}")
    
    def _get_current_appearance(self) -> str:
        """
        Get current macOS appearance
        
        Returns:
            str: 'dark' for dark mode, 'light' for light mode
        """
        try:
            from AppKit import NSApplication
            import subprocess
            
            # Method 1: Try NSApplication effective appearance
            app = NSApplication.sharedApplication()
            if hasattr(app, 'effectiveAppearance'):
                app_appearance = app.effectiveAppearance()
                if app_appearance:
                    appearance_name = str(app_appearance.name())
                    if "Dark" in appearance_name:
                        return 'dark'
                    else:
                        return 'light'
            
            # Method 2: Check system defaults
            result = subprocess.run(
                ['defaults', 'read', '-g', 'AppleInterfaceStyle'], 
                capture_output=True, 
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                interface_style = result.stdout.strip()
                return 'dark' if interface_style == "Dark" else 'light'
            
        except Exception as e:
            logger.debug(f"Error detecting appearance: {e}")
        
        # Default to light mode
        return 'light'
    
    def _set_dialog_icon(self, alert_object):
        """
        Set themed icon on NSAlert dialog based on current appearance
        
        Args:
            alert_object: NSAlert object to set icon on
        """
        try:
            current_appearance = self._get_current_appearance()
            
            # Use opposite icon for contrast (dark theme -> light icon, light theme -> dark icon)
            icon_filename = 'light.png' if current_appearance == 'dark' else 'dark.png'
            
            # Build path based on runtime environment
            if getattr(sys, 'frozen', False):
                # Running as app bundle
                app_bundle_path = os.path.dirname(sys.executable)
                icon_path = os.path.join(app_bundle_path, '..', 'Resources', 'assets', icon_filename)
            else:
                # Running in development - navigate from current file to project root
                current_file = os.path.abspath(__file__)
                # From src/ui/settings/base_settings_window.py to project root
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
                icon_path = os.path.join(project_root, 'assets', icon_filename)
            
            if os.path.exists(icon_path):
                # Load and configure icon
                logo_image = NSImage.alloc().initWithContentsOfFile_(icon_path)
                if logo_image:
                    # Resize to appropriate dialog icon size
                    logo_image.setSize_(NSMakeSize(64, 64))
                    
                    # Set the icon on the alert
                    if hasattr(alert_object, 'setIcon_'):
                        alert_object.setIcon_(logo_image)
                        logger.debug(f"Dialog icon set using {icon_filename}")
                    else:
                        logger.warning("Alert object does not have setIcon_ method")
                else:
                    logger.warning(f"Could not load icon image from {icon_path}")
            else:
                logger.warning(f"Icon file not found at {icon_path}")
                
        except Exception as e:
            logger.error(f"Error setting dialog icon: {e}")
    
    # Window delegate methods
    def windowShouldClose_(self, window):
        """Handle window close button"""
        return True
    
    def windowWillClose_(self, notification):
        """Clean up when window closes"""
        logger.debug("Settings window closing")
        
        # Save window position
        if self.window():
            self.window_positioning.save_window_state(self.window())
        
        # Unregister notifications
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
        except Exception:
            pass
        
        # Call cleanup in subclass
        self._cleanup()
    
    def _cleanup(self):
        """Cleanup method - override in subclass"""
        pass
    
    def setOnSettingsChanged_(self, callback: Callable):
        """Set callback for when settings change"""
        self.on_settings_changed = callback
    
    def notifySettingsChanged(self):
        """Notify that settings have changed"""
        if self.on_settings_changed:
            try:
                self.on_settings_changed()
                logger.debug("Settings change callback executed")
            except Exception as e:
                logger.error(f"Error in settings change callback: {e}") 