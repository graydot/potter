#!/usr/bin/env python3
"""
Test script to debug theme detection and icon path logic
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_theme_detection():
    """Test the theme detection and icon path logic"""
    print("🔍 Testing Theme Detection and Icon Paths")
    print("=" * 60)
    
    try:
        # Import required modules
        from cocoa_settings import SettingsWindow, SettingsManager
        
        # Create a test settings window to access the methods
        settings_manager = SettingsManager()
        settings_window = SettingsWindow.alloc().initWithSettingsManager_(settings_manager)
        
        # Test 1: Check current appearance detection
        print("1. 🎨 Testing appearance detection...")
        current_appearance = settings_window._get_current_appearance()
        print(f"   Current appearance: {current_appearance}")
        
        # Test 2: Check icon file selection logic
        print("\n2. 🖼️ Testing icon selection logic...")
        if current_appearance == 'dark':
            selected_icon = 'light.png'  # Light icon on dark theme
            print(f"   Dark theme detected → using {selected_icon}")
        else:
            selected_icon = 'dark.png'   # Dark icon on light theme  
            print(f"   Light theme detected → using {selected_icon}")
        
        # Test 3: Check path building
        print("\n3. 📁 Testing path building...")
        
        # Test both development and bundle paths
        if getattr(sys, 'frozen', False):
            # Running as app bundle
            app_bundle_path = os.path.dirname(sys.executable)
            icon_path = os.path.join(app_bundle_path, '..', 'Resources', 'assets', selected_icon)
            print(f"   Bundle path: {icon_path}")
        else:
            # Running in development
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir) if 'src' in script_dir else script_dir
            icon_path = os.path.join(project_root, 'assets', selected_icon)
            print(f"   Development path: {icon_path}")
        
        # Test 4: Check if files exist
        print("\n4. ✅ Testing file existence...")
        print(f"   Selected icon path: {icon_path}")
        print(f"   File exists: {'✅ YES' if os.path.exists(icon_path) else '❌ NO'}")
        
        # Show all available icon files
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        print(f"\n   Available files in assets:")
        if os.path.exists(assets_dir):
            for file in os.listdir(assets_dir):
                if file.endswith('.png'):
                    full_path = os.path.join(assets_dir, file)
                    print(f"     ✅ {file} ({full_path})")
        else:
            print(f"     ❌ Assets directory not found: {assets_dir}")
        
        # Test 5: Test the actual _set_dialog_icon method
        print("\n5. 🔧 Testing _set_dialog_icon method...")
        from cocoa_settings import NSAlert, NSImage, NSMakeSize
        
        test_alert = NSAlert.alloc().init()
        test_alert.setMessageText_("Theme Test")
        test_alert.setInformativeText_("Testing themed icon")
        
        # Call the method and see what happens
        try:
            settings_window._set_dialog_icon(test_alert)
            print("   ✅ _set_dialog_icon executed without errors")
        except Exception as e:
            print(f"   ❌ _set_dialog_icon failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 6: Try alternative appearance detection methods
        print("\n6. 🔍 Testing alternative appearance detection...")
        try:
            from AppKit import NSApplication, NSAppearance
            app = NSApplication.sharedApplication()
            
            # Method 1: Check app effective appearance
            if hasattr(app, 'effectiveAppearance'):
                app_appearance = app.effectiveAppearance()
                if app_appearance:
                    appearance_name = str(app_appearance.name())
                    print(f"   App effective appearance: {appearance_name}")
                    is_dark = "Dark" in appearance_name
                    print(f"   Is dark mode: {is_dark}")
            
            # Method 2: Check system defaults
            import subprocess
            result = subprocess.run(['defaults', 'read', '-g', 'AppleInterfaceStyle'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                interface_style = result.stdout.strip()
                print(f"   System interface style: {interface_style}")
                is_dark_defaults = interface_style == "Dark"
                print(f"   Is dark mode (defaults): {is_dark_defaults}")
            else:
                print(f"   Could not read system defaults (light mode assumed)")
                
        except Exception as e:
            print(f"   Error testing alternative methods: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in theme detection test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_theme_detection()
    exit(0 if success else 1) 