#!/usr/bin/env python3
"""
Test script to show a visual dialog with themed icon
"""

import sys
import os
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def show_test_dialog():
    """Show a test dialog with themed icon"""
    print("🎨 Testing Visual Dialog with Themed Icon")
    print("=" * 50)
    
    try:
        from cocoa_settings import NSAlert, NSImage, NSMakeSize, SettingsWindow, SettingsManager
        from AppKit import NSApplication
        
        # Initialize the app
        app = NSApplication.sharedApplication()
        
        # Create settings window to get the icon method
        settings_manager = SettingsManager()
        settings_window = SettingsWindow.alloc().initWithSettingsManager_(settings_manager)
        
        print("Creating test alert...")
        
        # Create a test alert
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Theme Icon Test")
        alert.setInformativeText_("This dialog should show a themed icon based on your current system appearance.\n\nDark theme = light icon\nLight theme = dark icon")
        alert.setAlertStyle_(1)  # Warning style
        alert.addButtonWithTitle_("OK")
        alert.addButtonWithTitle_("Check Theme")
        
        # Set the themed icon
        print("Setting themed icon...")
        try:
            settings_window._set_dialog_icon(alert)
            print("✅ Icon set successfully")
        except Exception as e:
            print(f"❌ Failed to set icon: {e}")
        
        # Get current theme for confirmation
        current_theme = settings_window._get_current_appearance()
        icon_file = 'light.png' if current_theme == 'dark' else 'dark.png'
        print(f"Current theme: {current_theme}")
        print(f"Using icon file: {icon_file}")
        
        # Show the dialog
        print("\n🔍 Showing test dialog...")
        print("Look for the custom icon in the dialog!")
        print("(It should appear as a small icon next to the message)")
        
        response = alert.runModal()
        
        if response == 1001:  # Second button (Check Theme)
            # Show another dialog with different styling
            alert2 = NSAlert.alloc().init()
            alert2.setMessageText_("Theme Confirmation")
            alert2.setInformativeText_(f"Your system is in {current_theme} mode.\n\nThe icon should be from: assets/{icon_file}")
            alert2.setAlertStyle_(0)  # Informational style
            alert2.addButtonWithTitle_("Got it!")
            
            # Set icon on this one too
            settings_window._set_dialog_icon(alert2)
            alert2.runModal()
        
        print("✅ Dialog test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error showing dialog: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = show_test_dialog()
    exit(0 if success else 1) 