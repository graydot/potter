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
    controller = show_settings(settings_manager)
    
    if controller:
        print("✅ Settings window created successfully")
        print("✅ You should see a native macOS preferences window")
        
        # Debug: Check tab view
        window = controller.window()
        content_view = window.contentView()
        subviews = content_view.subviews()
        print(f"🔍 Content view has {len(subviews)} subviews")
        
        for i, subview in enumerate(subviews):
            print(f"  Subview {i}: {subview.__class__.__name__}")
            if hasattr(subview, 'numberOfTabViewItems'):
                tab_count = subview.numberOfTabViewItems()
                print(f"    Tab view has {tab_count} tabs")
                for j in range(tab_count):
                    tab = subview.tabViewItemAtIndex_(j)
                    print(f"      Tab {j}: {tab.label()}")
        
        app.run()
    else:
        print("❌ Failed to create settings window")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 