#!/usr/bin/env python3
"""
General Settings Section
Handles general app settings like startup, updates, and appearance
"""

import os
import logging
from typing import Optional, Callable
from AppKit import (
    NSView, NSMakeRect, NSFont,
    NSControlStateValueOn, NSControlStateValueOff,
    NSApp, NSBundle, NSWorkspace, NSURL
)

from ..widgets.ui_helpers import (
    create_label, create_description_label, create_button,
    create_switch, create_popup_button
)

logger = logging.getLogger(__name__)


class GeneralSettingsSection:
    """Manages the general settings section"""
    
    def __init__(self, settings_manager, on_settings_changed: Optional[Callable] = None):
        """
        Initialize general settings section
        
        Args:
            settings_manager: Settings manager instance
            on_settings_changed: Callback when settings change
        """
        self.settings_manager = settings_manager
        self.on_settings_changed = on_settings_changed
        
        # UI elements
        self.view = None
        self.launch_at_startup_switch = None
        self.check_updates_switch = None
        self.auto_update_switch = None
        self.theme_popup = None
        self.show_dock_icon_switch = None
        self.show_notifications_switch = None
        
    def create_view(self, width: int = 700, height: int = 900) -> NSView:
        """
        Create the general settings view matching exact specification
        
        Args:
            width: View width
            height: View height
            
        Returns:
            NSView containing the general settings
        """
        logger.debug("Creating general settings view")
        
        # Create main view with exact spec dimensions
        self.view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))
        
        # Y-axis origin: 850px (content flows downward) - matching spec
        y_pos = 850
        
        # Section header - (40, y_pos, 620, 35) - "General Settings"
        header = self._create_section_header("General Settings", y_pos)
        self.view.addSubview_(header)
        y_pos -= 50
        
        # Separator - (40, y_pos-50, 620, 1)
        separator = self._create_section_separator(y_pos)
        self.view.addSubview_(separator)
        y_pos -= 40
        
        # AI Provider Configuration Section
        y_pos = self._create_ai_provider_section(y_pos)
        
        # Global Hotkey Section
        y_pos = self._create_hotkey_section(y_pos)
        
        # Permissions Section
        y_pos = self._create_permissions_section(y_pos)
        
        # Application Preferences Section
        y_pos = self._create_application_preferences_section(y_pos)
        
        return self.view
    
    def _create_section_header(self, title: str, y_position: float):
        """Create a modern section header matching spec"""
        from AppKit import NSTextField, NSColor
        header = NSTextField.alloc().initWithFrame_(NSMakeRect(40, y_position, 620, 35))
        header.setStringValue_(title)
        header.setFont_(NSFont.boldSystemFontOfSize_(24))
        header.setBezeled_(False)
        header.setDrawsBackground_(False)
        header.setEditable_(False)
        header.setTextColor_(NSColor.labelColor())
        return header
    
    def _create_section_separator(self, y_position: float):
        """Create a visual separator matching spec"""
        from AppKit import NSView, NSColor
        separator = NSView.alloc().initWithFrame_(NSMakeRect(40, y_position, 620, 1))
        separator.setWantsLayer_(True)
        separator.layer().setBackgroundColor_(NSColor.separatorColor().CGColor())
        return separator
    
    def _create_ai_provider_section(self, y_pos: int) -> int:
        """Create AI Provider Configuration section matching spec"""
        # LLM Provider section
        llm_section_label = create_label(
            "AI Provider Configuration",
            NSMakeRect(40, y_pos, 620, 20),
            font=NSFont.boldSystemFontOfSize_(16)
        )
        self.view.addSubview_(llm_section_label)
        y_pos -= 35
        
        # Provider selection - Label: (40, y_pos, 120, 22), Popup: (160, y_pos, 200, 22)
        provider_label = create_label("Provider:", NSMakeRect(40, y_pos, 120, 22))
        self.view.addSubview_(provider_label)
        
        # Create popup with provider options
        self.provider_popup = create_popup_button(
            NSMakeRect(160, y_pos, 200, 22),
            items=["OpenAI", "Anthropic", "Google"],
            action=self.providerChanged_,
            target=self
        )
        self.view.addSubview_(self.provider_popup)
        y_pos -= 30
        
        # API Key section
        api_key_label = create_label("API Key:", NSMakeRect(40, y_pos, 120, 22))
        self.view.addSubview_(api_key_label)
        
        # API Key field: (160, y_pos, 300, 22)
        self.api_key_field = create_text_field(NSMakeRect(160, y_pos, 300, 22))
        self.api_key_field.setFont_(NSFont.monospacedSystemFontOfSize_weight_(12, 0))
        self.view.addSubview_(self.api_key_field)
        
        # Verify & Save button: (510, y_pos, 110, 22) - RIGHT EDGE AT 620px
        verify_button = create_button(
            "Verify & Save",
            NSMakeRect(510, y_pos, 110, 22),
            action=self.verifyApiKey_,
            target=self
        )
        self.view.addSubview_(verify_button)
        
        # Validation label: (160, y_pos-25, 400, 20)
        self.api_validation_label = create_label("", NSMakeRect(160, y_pos - 25, 400, 20))
        self.view.addSubview_(self.api_validation_label)
        y_pos -= 50  # Extra space for validation label
        
        # Model selection - Label: (40, y_pos, 120, 22), Popup: (160, y_pos, 250, 22)
        model_label = create_label("Model:", NSMakeRect(40, y_pos, 120, 22))
        self.view.addSubview_(model_label)
        
        self.model_popup = create_popup_button(
            NSMakeRect(160, y_pos, 250, 22),
            items=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            action=self.modelChanged_,
            target=self
        )
        self.view.addSubview_(self.model_popup)
        y_pos -= 50
        
        return y_pos
        
    def _create_hotkey_section(self, y_pos: int) -> int:
        """Create Global Hotkey section matching spec"""
        # Hotkey section
        hotkey_section_label = create_label(
            "Global Hotkey",
            NSMakeRect(40, y_pos, 620, 20),
            font=NSFont.boldSystemFontOfSize_(16)
        )
        self.view.addSubview_(hotkey_section_label)
        y_pos -= 35
        
        # Hotkey field - (40, y_pos, 120, 22) for label, (160, y_pos, 350, 30) for field
        hotkey_label = create_label("Hotkey:", NSMakeRect(40, y_pos, 120, 22))
        self.view.addSubview_(hotkey_label)
        
        # Create hotkey capture control placeholder
        self.hotkey_field = create_text_field(NSMakeRect(160, y_pos, 350, 30))
        self.hotkey_field.setPlaceholderString_("Click to set hotkey")
        self.view.addSubview_(self.hotkey_field)
        
        # Reset button: (540, y_pos, 80, 22) - RIGHT EDGE AT 620px
        reset_button = create_button(
            "Reset",
            NSMakeRect(540, y_pos, 80, 22),
            action=self.resetHotkey_,
            target=self
        )
        self.view.addSubview_(reset_button)
        y_pos -= 50
        
        return y_pos
        
    def _create_application_preferences_section(self, y_pos: int) -> int:
        """Create Application Preferences section matching spec"""
        # Application Preferences section
        prefs_section_label = create_label(
            "Application Preferences", 
            NSMakeRect(40, y_pos, 620, 20),
            font=NSFont.boldSystemFontOfSize_(16)
        )
        self.view.addSubview_(prefs_section_label)
        y_pos -= 35
        
        # Notifications toggle - (40, y_pos, 580, 30) - RIGHT EDGE AT 620px
        notifications_container, self.notifications_switch = self._create_modern_switch(
            NSMakeRect(40, y_pos, 580, 30),
            "Show notifications",
            self.settings_manager.get("show_notifications", False)
        )
        self.notifications_switch.setTarget_(self)
        self.notifications_switch.setAction_("toggleNotifications_")
        self.view.addSubview_(notifications_container)
        y_pos -= 40
        
        # Launch at startup toggle - (40, y_pos, 580, 30) - RIGHT EDGE AT 620px  
        startup_container, self.startup_switch = self._create_modern_switch(
            NSMakeRect(40, y_pos, 580, 30),
            "Launch at startup",
            self._is_launch_at_startup_enabled()
        )
        self.startup_switch.setTarget_(self)
        self.startup_switch.setAction_("toggleLaunchAtStartup_")
        self.view.addSubview_(startup_container)
        
        return y_pos - 50
        
    def _create_modern_switch(self, frame, title: str, initial_state: bool = False):
        """Create a modern switch control matching spec - returns (container, switch)"""
        from AppKit import NSView, NSTextField, NSSwitch, NSButton, NSButtonTypeSwitch, NSColor
        
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
        
        # Switch positioned at right edge - (530, 0, 50, 30) within container  
        try:
            switch = NSSwitch.alloc().initWithFrame_(NSMakeRect(530, 0, 50, 30))
            switch.setState_(1 if initial_state else 0)
        except Exception:
            # Fallback for older macOS
            switch = NSButton.alloc().initWithFrame_(NSMakeRect(530, 0, 50, 30))
            switch.setButtonType_(NSButtonTypeSwitch)
            switch.setState_(1 if initial_state else 0)
        
        container.addSubview_(switch)
        
        return container, switch
    
    # Action methods for new sections
    def providerChanged_(self, sender):
        """Handle provider change"""
        logger.debug("Provider changed")
        if self.on_settings_changed:
            self.on_settings_changed()
            
    def verifyApiKey_(self, sender):
        """Handle API key verification"""
        logger.debug("Verifying API key")
        # TODO: Implement API key verification
        
    def modelChanged_(self, sender):
        """Handle model change"""
        logger.debug("Model changed")
        if self.on_settings_changed:
            self.on_settings_changed()
            
    def resetHotkey_(self, sender):
        """Handle hotkey reset"""
        logger.debug("Resetting hotkey")
        if self.on_settings_changed:
            self.on_settings_changed()
    
    def _create_startup_section(self, y_offset: int) -> int:
        """Create startup settings section"""
        # Section title
        section_title = create_label(
            "Startup",
            NSMakeRect(20, y_offset, 200, 20),
            font=NSFont.boldSystemFontOfSize_(14)
        )
        self.view.addSubview_(section_title)
        
        y_offset -= 35
        
        # Launch at startup
        self.launch_at_startup_switch = create_switch(
            NSMakeRect(20, y_offset, 300, 25),
            title="Launch Potter at startup",
            action=self.toggleLaunchAtStartup_,
            target=self
        )
        self.launch_at_startup_switch.setState_(
            NSControlStateValueOn if self._is_launch_at_startup_enabled() else NSControlStateValueOff
        )
        self.view.addSubview_(self.launch_at_startup_switch)
        
        y_offset -= 30
        
        desc = create_description_label(
            "Automatically start Potter when you log in to your computer",
            NSMakeRect(20, y_offset, 600, 20)
        )
        self.view.addSubview_(desc)
        
        return y_offset - 40
    
    def _create_updates_section(self, y_offset: int) -> int:
        """Create updates settings section"""
        # Section title
        section_title = create_label(
            "Updates",
            NSMakeRect(20, y_offset, 200, 20),
            font=NSFont.boldSystemFontOfSize_(14)
        )
        self.view.addSubview_(section_title)
        
        y_offset -= 35
        
        # Check for updates
        self.check_updates_switch = create_switch(
            NSMakeRect(20, y_offset, 300, 25),
            title="Check for updates automatically",
            action=self.toggleCheckUpdates_,
            target=self
        )
        check_updates = self.settings_manager.get("check_for_updates", True)
        self.check_updates_switch.setState_(
            NSControlStateValueOn if check_updates else NSControlStateValueOff
        )
        self.view.addSubview_(self.check_updates_switch)
        
        y_offset -= 35
        
        # Auto update
        self.auto_update_switch = create_switch(
            NSMakeRect(20, y_offset, 300, 25),
            title="Download updates automatically",
            action=self.toggleAutoUpdate_,
            target=self
        )
        self.auto_update_switch.setState_(
            NSControlStateValueOn if self.settings_manager.get("auto_update", False) else NSControlStateValueOff
        )
        self.auto_update_switch.setEnabled_(self.check_updates_switch.state() == NSControlStateValueOn)
        self.view.addSubview_(self.auto_update_switch)
        
        y_offset -= 30
        
        desc = create_description_label(
            "Keep Potter up to date with the latest features and improvements",
            NSMakeRect(20, y_offset, 600, 20)
        )
        self.view.addSubview_(desc)
        
        return y_offset - 40
    
    def _create_appearance_section(self, y_offset: int) -> int:
        """Create appearance settings section"""
        # Section title
        section_title = create_label(
            "Appearance",
            NSMakeRect(20, y_offset, 200, 20),
            font=NSFont.boldSystemFontOfSize_(14)
        )
        self.view.addSubview_(section_title)
        
        y_offset -= 35
        
        # Theme selection
        theme_label = create_label(
            "Theme:",
            NSMakeRect(20, y_offset, 80, 25)
        )
        self.view.addSubview_(theme_label)
        
        self.theme_popup = create_popup_button(
            NSMakeRect(110, y_offset, 150, 25),
            items=["System", "Light", "Dark"],
            action=self.changeTheme_,
            target=self
        )
        
        current_theme = self.settings_manager.get("theme", "System")
        self.theme_popup.selectItemWithTitle_(current_theme)
        self.view.addSubview_(self.theme_popup)
        
        y_offset -= 35
        
        # Show dock icon
        self.show_dock_icon_switch = create_switch(
            NSMakeRect(20, y_offset, 300, 25),
            title="Show Potter in Dock",
            action=self.toggleDockIcon_,
            target=self
        )
        show_dock = self.settings_manager.get("show_dock_icon", True)
        self.show_dock_icon_switch.setState_(
            NSControlStateValueOn if show_dock else NSControlStateValueOff
        )
        self.view.addSubview_(self.show_dock_icon_switch)
        
        y_offset -= 30
        
        desc = create_description_label(
            "Show Potter icon in the Dock when running",
            NSMakeRect(20, y_offset, 600, 20)
        )
        self.view.addSubview_(desc)
        
        return y_offset - 40
    
    def _create_notifications_section(self, y_offset: int) -> int:
        """Create notifications settings section"""
        # Section title
        section_title = create_label(
            "Notifications",
            NSMakeRect(20, y_offset, 200, 20),
            font=NSFont.boldSystemFontOfSize_(14)
        )
        self.view.addSubview_(section_title)
        
        y_offset -= 35
        
        # Show notifications
        self.show_notifications_switch = create_switch(
            NSMakeRect(20, y_offset, 300, 25),
            title="Show notifications",
            action=self.toggleNotifications_,
            target=self
        )
        self.show_notifications_switch.setState_(
            NSControlStateValueOn if self.settings_manager.get("show_notifications", True) else NSControlStateValueOff
        )
        self.view.addSubview_(self.show_notifications_switch)
        
        y_offset -= 30
        
        desc = create_description_label(
            "Display notifications for text processing results and errors",
            NSMakeRect(20, y_offset, 600, 20)
        )
        self.view.addSubview_(desc)
        
        return y_offset - 40
    
    def _create_permissions_section(self, y_offset: int) -> int:
        """Create permissions settings section"""
        # Section title
        section_title = create_label(
            "Permissions",
            NSMakeRect(20, y_offset, 200, 20),
            font=NSFont.boldSystemFontOfSize_(14)
        )
        self.view.addSubview_(section_title)
        
        y_offset -= 35
        
        # Reset permissions button
        reset_button = create_button(
            "Reset All Permissions",
            NSMakeRect(20, y_offset, 180, 25),
            action=self.resetPermissions_,
            target=self
        )
        self.view.addSubview_(reset_button)
        
        y_offset -= 30
        
        desc = create_description_label(
            "Reset all system permissions for Potter (accessibility, notifications, etc.)",
            NSMakeRect(20, y_offset, 600, 20)
        )
        self.view.addSubview_(desc)
        
        return y_offset - 40
    
    def _create_about_section(self, y_offset: int) -> int:
        """Create about section"""
        # Section title
        section_title = create_label(
            "About",
            NSMakeRect(20, y_offset, 200, 20),
            font=NSFont.boldSystemFontOfSize_(14)
        )
        self.view.addSubview_(section_title)
        
        y_offset -= 35
        
        # Version info
        bundle = NSBundle.mainBundle()
        version = bundle.objectForInfoDictionaryKey_("CFBundleShortVersionString") or "1.0.0"
        build = bundle.objectForInfoDictionaryKey_("CFBundleVersion") or "1"
        
        version_label = create_label(
            f"Potter version {version} (build {build})",
            NSMakeRect(20, y_offset, 400, 20)
        )
        self.view.addSubview_(version_label)
        
        y_offset -= 35
        
        # Links
        website_button = create_button(
            "Visit Website",
            NSMakeRect(20, y_offset, 120, 25),
            action=self.openWebsite_,
            target=self
        )
        self.view.addSubview_(website_button)
        
        support_button = create_button(
            "Get Support",
            NSMakeRect(150, y_offset, 120, 25),
            action=self.openSupport_,
            target=self
        )
        self.view.addSubview_(support_button)
        
        return y_offset - 40
    
    # Action methods
    def toggleLaunchAtStartup_(self, sender):
        """Toggle launch at startup setting"""
        enabled = sender.state() == NSControlStateValueOn
        logger.info(f"Setting launch at startup: {enabled}")
        
        try:
            if enabled:
                self._enable_launch_at_startup()
            else:
                self._disable_launch_at_startup()
            
            self._notify_settings_changed()
        except Exception as e:
            logger.error(f"Error toggling launch at startup: {e}")
            sender.setState_(NSControlStateValueOff if enabled else NSControlStateValueOn)
    
    def toggleCheckUpdates_(self, sender):
        """Toggle check for updates setting"""
        enabled = sender.state() == NSControlStateValueOn
        logger.info(f"Setting check for updates: {enabled}")
        
        self.settings_manager.set_setting("check_for_updates", enabled)
        
        # Enable/disable auto update based on this setting
        self.auto_update_switch.setEnabled_(enabled)
        if not enabled:
            self.auto_update_switch.setState_(NSControlStateValueOff)
            self.settings_manager.set_setting("auto_update", False)
        
        self._notify_settings_changed()
    
    def toggleAutoUpdate_(self, sender):
        """Toggle auto update setting"""
        enabled = sender.state() == NSControlStateValueOn
        logger.info(f"Setting auto update: {enabled}")
        
        self.settings_manager.set_setting("auto_update", enabled)
        self._notify_settings_changed()
    
    def changeTheme_(self, sender):
        """Change app theme"""
        theme = sender.titleOfSelectedItem()
        logger.info(f"Changing theme to: {theme}")
        
        self.settings_manager.set_setting("theme", theme)
        
        # Apply theme change
        # TODO: Implement theme application
        
        self._notify_settings_changed()
    
    def toggleDockIcon_(self, sender):
        """Toggle dock icon visibility"""
        show = sender.state() == NSControlStateValueOn
        logger.info(f"Setting show dock icon: {show}")
        
        self.settings_manager.set_setting("show_dock_icon", show)
        
        # Apply dock icon change
        try:
            if show:
                NSApp.setActivationPolicy_(0)  # NSApplicationActivationPolicyRegular
            else:
                NSApp.setActivationPolicy_(2)  # NSApplicationActivationPolicyAccessory
        except Exception as e:
            logger.error(f"Error changing dock icon visibility: {e}")
        
        self._notify_settings_changed()
    
    def toggleNotifications_(self, sender):
        """Toggle notifications setting"""
        enabled = sender.state() == NSControlStateValueOn
        logger.info(f"Setting show notifications: {enabled}")
        
        self.settings_manager.set_setting("show_notifications", enabled)
        self._notify_settings_changed()
    
    def openWebsite_(self, sender):
        """Open Potter website"""
        url = NSURL.URLWithString_("https://potter.app")
        NSWorkspace.sharedWorkspace().openURL_(url)
    
    def openSupport_(self, sender):
        """Open support page"""
        url = NSURL.URLWithString_("https://potter.app/support")
        NSWorkspace.sharedWorkspace().openURL_(url)
    
    def resetPermissions_(self, sender):
        """Reset all permissions for the Potter app with confirmation dialogs"""
        import subprocess
        from AppKit import NSAlert, NSAlertFirstButtonReturn, NSAlertStyleCritical, NSAlertStyleInformational
        
        try:
            # Show confirmation dialog first
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Reset All Permissions")
            alert.setInformativeText_(
                "This will reset ALL system permissions for Potter, including:\n\n"
                "• Accessibility (required for global hotkeys)\n"
                "• Notifications\n"
                "• Any other granted permissions\n\n"
                "You will need to re-grant permissions and restart the app. Continue?"
            )
            alert.setAlertStyle_(NSAlertStyleCritical)
            alert.addButtonWithTitle_("Reset Permissions")
            alert.addButtonWithTitle_("Cancel")
            
            # Set themed icon - get parent window to access _set_dialog_icon method
            parent_window = self.view.window()
            if parent_window and hasattr(parent_window.windowController(), '_set_dialog_icon'):
                parent_window.windowController()._set_dialog_icon(alert)
            
            response = alert.runModal()
            if response != NSAlertFirstButtonReturn:  # User clicked Cancel
                logger.debug("Permission reset cancelled by user")
                return
            
            # Run the tccutil reset command for our app bundle ID
            bundle_id = "com.potter.app"
            
            try:
                # Reset all permissions for our bundle ID
                result = subprocess.run(['tccutil', 'reset', 'All', bundle_id], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    # Success - show confirmation and offer to restart
                    success_alert = NSAlert.alloc().init()
                    success_alert.setMessageText_("Permissions Reset Successfully")
                    success_alert.setInformativeText_(
                        "All permissions for Potter have been reset.\n\n"
                        "Potter needs to be restarted for changes to take effect. "
                        "Would you like to restart now?"
                    )
                    success_alert.setAlertStyle_(NSAlertStyleInformational)
                    success_alert.addButtonWithTitle_("Restart Potter")
                    success_alert.addButtonWithTitle_("Later")
                    
                    # Set themed icon
                    if parent_window and hasattr(parent_window.windowController(), '_set_dialog_icon'):
                        parent_window.windowController()._set_dialog_icon(success_alert)
                    
                    restart_response = success_alert.runModal()
                    if restart_response == NSAlertFirstButtonReturn:  # Restart
                        self._restart_app()
                    
                    logger.info("Permissions reset successfully")
                        
                else:
                    # Command failed
                    error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                    self._show_permission_reset_error(f"Failed to reset permissions: {error_msg}")
                    
            except subprocess.TimeoutExpired:
                self._show_permission_reset_error("Permission reset timed out. Please try again.")
            except FileNotFoundError:
                self._show_permission_reset_error("tccutil command not found. This feature requires macOS 10.11 or later.")
            except Exception as e:
                self._show_permission_reset_error(f"Unexpected error: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error in resetPermissions: {e}")
            self._show_permission_reset_error(f"Failed to reset permissions: {str(e)}")
    
    def _show_permission_reset_error(self, message: str):
        """Show permission reset error dialog with themed icon"""
        from AppKit import NSAlert, NSAlertStyleCritical
        
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Permission Reset Failed")
        alert.setInformativeText_(message)
        alert.setAlertStyle_(NSAlertStyleCritical)
        
        # Set themed icon
        parent_window = self.view.window()
        if parent_window and hasattr(parent_window.windowController(), '_set_dialog_icon'):
            parent_window.windowController()._set_dialog_icon(alert)
        
        alert.runModal()
        logger.error(f"Permission reset error: {message}")
    
    def _restart_app(self):
        """Restart the Potter application"""
        import sys
        
        try:
            logger.info("Restarting Potter application...")
            
            # Get the executable path
            if getattr(sys, 'frozen', False):
                # Running as app bundle
                executable_path = sys.executable
            else:
                # Running in development - restart Python script
                executable_path = sys.executable
                script_path = sys.argv[0]
            
            # Close current window
            if self.view.window():
                self.view.window().close()
            
            # Quit current app and restart
            import subprocess
            if getattr(sys, 'frozen', False):
                # App bundle - restart the .app
                app_bundle = executable_path.split('/Contents/MacOS/')[0]
                subprocess.Popen(['open', app_bundle])
            else:
                # Development - restart Python script
                subprocess.Popen([executable_path, script_path])
            
            # Quit current instance
            from AppKit import NSApplication
            NSApplication.sharedApplication().terminate_(None)
            
        except Exception as e:
            logger.error(f"Error restarting app: {e}")
            self._show_permission_reset_error(f"Failed to restart Potter: {str(e)}. Please restart manually.")
    
    # Helper methods
    def _is_launch_at_startup_enabled(self) -> bool:
        """Check if launch at startup is enabled"""
        try:
            # Check if login item exists
            bundle_path = NSBundle.mainBundle().bundlePath()
            login_items_path = os.path.expanduser(
                "~/Library/LaunchAgents/com.potter.app.plist"
            )
            return os.path.exists(login_items_path)
        except Exception as e:
            logger.error(f"Error checking launch at startup: {e}")
            return False
    
    def _enable_launch_at_startup(self):
        """Enable launch at startup"""
        try:
            bundle_path = NSBundle.mainBundle().bundlePath()
            app_path = os.path.join(bundle_path, "Contents", "MacOS", "Potter")
            
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.potter.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>{app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""
            
            launch_agents_dir = os.path.expanduser("~/Library/LaunchAgents")
            os.makedirs(launch_agents_dir, exist_ok=True)
            
            plist_path = os.path.join(launch_agents_dir, "com.potter.app.plist")
            with open(plist_path, 'w') as f:
                f.write(plist_content)
            
            logger.info("Enabled launch at startup")
        except Exception as e:
            logger.error(f"Error enabling launch at startup: {e}")
            raise
    
    def _disable_launch_at_startup(self):
        """Disable launch at startup"""
        try:
            plist_path = os.path.expanduser(
                "~/Library/LaunchAgents/com.potter.app.plist"
            )
            if os.path.exists(plist_path):
                os.remove(plist_path)
            
            logger.info("Disabled launch at startup")
        except Exception as e:
            logger.error(f"Error disabling launch at startup: {e}")
            raise
    
    def _notify_settings_changed(self):
        """Notify that settings have changed"""
        if self.on_settings_changed:
            try:
                self.on_settings_changed()
            except Exception as e:
                logger.error(f"Error in settings changed callback: {e}") 