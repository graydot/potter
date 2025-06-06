#!/usr/bin/env python3
"""
Simple UI Component Test
Tests basic UI functionality without complex components
"""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_basic_ui():
    """Test basic UI components"""
    print("🧪 Testing Basic UI Components...")
    
    try:
        # Test settings manager
        from settings.settings_manager import SettingsManager
        settings_manager = SettingsManager()
        print("✅ SettingsManager imported and created")
        
        # Test basic settings access
        settings = settings_manager.get_all_settings()
        print(f"✅ Settings loaded: {len(settings)} settings")
        
        # Test AppKit imports
        from AppKit import NSApplication, NSWindow
        print("✅ AppKit imports successful")
        
        # Test NSApplication
        app = NSApplication.sharedApplication()
        print("✅ NSApplication instance created")
        
        # Test basic window creation (without complex UI)
        from ui.settings.base_settings_window import BaseSettingsWindow
        base_window = BaseSettingsWindow.alloc().init()
        print("✅ BaseSettingsWindow created")
        
        # Test settings window creation
        from ui.settings.settings_window import SettingsWindow
        settings_window = SettingsWindow.alloc().initWithSettingsManager_(settings_manager)
        print("✅ SettingsWindow created")
        
        print("✅ All basic UI tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Basic UI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_ui()
    sys.exit(0 if success else 1) 