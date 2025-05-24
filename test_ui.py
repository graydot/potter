#!/usr/bin/env python3
"""
Quick test for the native macOS settings UI
"""

try:
    from cocoa_settings import SettingsManager, show_settings
    from Foundation import NSApplication
    
    print("✅ Native macOS Settings UI loaded successfully")
    
    # Create app instance
    app = NSApplication.sharedApplication()
    
    # Create settings manager
    settings_manager = SettingsManager()
    print(f"✅ Settings manager created with {len(settings_manager.settings)} settings")
    
    # Show settings window
    controller = show_settings(settings_manager)
    
    if controller:
        print("✅ Settings window created successfully")
        print("✅ You should see a native macOS preferences window")
        
        # Run the app
        app.run()
    else:
        print("❌ Failed to create settings window")

except ImportError as e:
    print(f"❌ Failed to import native UI: {e}")
except Exception as e:
    print(f"❌ Error: {e}") 