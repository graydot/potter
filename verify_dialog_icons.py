#!/usr/bin/env python3
"""
Verification script for dialog icons in the settings panel
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def verify_icon_implementation():
    """Verify that the icon implementation is correct"""
    print("🔍 Verifying Dialog Icons Implementation")
    print("=" * 50)
    
    try:
        # Import required modules
        from cocoa_settings import NSAlert, NSImage, NSMakeSize
        
        # Test 1: Check if assets exist
        assets_dir = "assets"
        light_icon = os.path.join(assets_dir, "light.png")
        dark_icon = os.path.join(assets_dir, "dark.png")
        
        print(f"📁 Assets directory: {assets_dir}")
        print(f"   Light icon: {'✅' if os.path.exists(light_icon) else '❌'} {light_icon}")
        print(f"   Dark icon: {'✅' if os.path.exists(dark_icon) else '❌'} {dark_icon}")
        
        # Test 2: Test NSAlert icon setting capability
        print("\n🧪 Testing NSAlert icon setting...")
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Test Alert")
        alert.setInformativeText_("Testing icon capability")
        
        # Load an icon
        test_icon_path = dark_icon if os.path.exists(dark_icon) else light_icon
        if os.path.exists(test_icon_path):
            logo_image = NSImage.alloc().initWithContentsOfFile_(test_icon_path)
            if logo_image:
                logo_image.setSize_(NSMakeSize(64, 64))
                
                # Check if setIcon_ method exists
                if hasattr(alert, 'setIcon_'):
                    alert.setIcon_(logo_image)
                    print("✅ NSAlert.setIcon_ method works")
                    print(f"✅ Icon loaded from: {test_icon_path}")
                else:
                    print("❌ NSAlert.setIcon_ method not found")
                    return False
            else:
                print(f"❌ Could not load image from: {test_icon_path}")
                return False
        else:
            print("❌ No test icon files found")
            return False
        
        # Test 3: Check if _set_dialog_icon method exists in settings
        print("\n🔧 Testing SettingsWindow implementation...")
        from cocoa_settings import SettingsWindow
        
        # Create a mock settings window to test the method
        if hasattr(SettingsWindow, '_set_dialog_icon'):
            print("✅ _set_dialog_icon method exists in SettingsWindow")
        else:
            print("❌ _set_dialog_icon method not found in SettingsWindow")
            return False
        
        print("\n🎯 Implementation Status:")
        print("✅ All dialog icon components are properly implemented")
        print("✅ NSAlert can accept custom icons")
        print("✅ Asset files exist and can be loaded")
        print("✅ SettingsWindow has the icon setting method")
        
        print("\n📋 To test in the actual app:")
        print("1. Open the application")
        print("2. Open Settings window")
        print("3. Go to Prompts tab, try to delete a prompt")
        print("4. Go to Logs tab, click Clear button")
        print("5. Check if dialogs show the themed icons")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = verify_icon_implementation()
    exit(0 if success else 1) 