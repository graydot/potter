#!/usr/bin/env python3
"""
Test script for the native macOS settings UI
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_ui_components():
    """Test UI components can be imported and created without running the GUI"""
    try:
        print("🧪 Testing UI Component Imports...")
        
        # Test basic imports
        from cocoa_settings import SettingsManager, show_settings
        print("✅ SettingsManager and show_settings imported successfully")
        
        # Test Foundation imports
        from Foundation import NSApplication
        print("✅ Foundation framework imported successfully")
        
        # Test settings manager creation
        settings_manager = SettingsManager()
        print(f"✅ Settings manager created with {len(settings_manager.settings)} settings")
        
        # Test that we can access settings
        prompts = settings_manager.get("prompts", [])
        hotkey = settings_manager.get("hotkey", "")
        model = settings_manager.get("model", "")
        
        print(f"✅ Settings accessible: {len(prompts)} prompts, hotkey: {hotkey}, model: {model}")
        
        # Test NSApplication creation (but don't run it)
        app = NSApplication.sharedApplication()  # noqa: F841
        print("✅ NSApplication instance created successfully")
        
        # Test settings window creation (but don't show it)
        print("🧪 Testing settings window creation...")
        
        def dummy_callback(settings):
            """Dummy callback for testing"""
            pass
        
        # Create the settings window controller but don't run the event loop
        controller = show_settings(settings_manager, dummy_callback)
        
        if controller:
            print("✅ Settings window controller created successfully")
            
            # Test that we can access the window
            window = controller.window()
            if window:
                print("✅ Settings window object accessible")
                
                # Test content view
                content_view = window.contentView()
                if content_view:
                    subviews = content_view.subviews()
                    print(f"✅ Content view has {len(subviews)} subviews")
                else:
                    print("❌ Content view not accessible")
                    return False
                
                # Close the window immediately (don't run event loop)
                window.close()
                print("✅ Settings window closed successfully")
            else:
                print("❌ Settings window not accessible")
                return False
        else:
            print("❌ Failed to create settings window controller")
            return False
        
        print("✅ All UI component tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ UI Component Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_ui_components():
        print("🎉 UI component test completed successfully!")
        sys.exit(0)
    else:
        print("❌ UI component test failed!")
        sys.exit(1) 