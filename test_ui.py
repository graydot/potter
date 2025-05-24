#!/usr/bin/env python3
"""
Test script for the native macOS settings UI
"""

import sys
import os

try:
    from cocoa_settings import SettingsManager, show_settings
    from Foundation import NSApplication
    print("✅ Native macOS Settings UI loaded successfully")
    
    # Create settings manager
    settings_manager = SettingsManager()
    print(f"✅ Settings manager created with {len(settings_manager.settings)} settings")
    
    # Create and show settings window
    app = NSApplication.sharedApplication()
    
    def on_settings_changed(settings):
        """Called when settings are saved"""
        print("✅ Settings saved successfully")
        # Terminate the app when settings are saved
        app.terminate_(None)
    
    controller = show_settings(settings_manager, on_settings_changed)
    
    if controller:
        print("✅ Settings window created successfully")
        print("✅ You should see a native macOS preferences window")
        
        # Debug: Check content view
        window = controller.window()
        content_view = window.contentView()
        subviews = content_view.subviews()
        print(f"🔍 Content view has {len(subviews)} subviews")
        
        for i, subview in enumerate(subviews):
            print(f"  Subview {i}: {subview.__class__.__name__}")
        
        # Make window delegate to handle close
        class WindowDelegate:
            def windowWillClose_(self, notification):
                """Called when window is about to close"""
                print("✅ Settings window closed")
                app.terminate_(None)
        
        window_delegate = WindowDelegate()
        window.setDelegate_(window_delegate)
        
        app.run()
    else:
        print("❌ Failed to create settings window")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 