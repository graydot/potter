#!/usr/bin/env python3
"""
Debug the actual paths used by _set_dialog_icon
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def debug_actual_paths():
    """Debug the exact paths and logic used in _set_dialog_icon"""
    print("🔍 Debugging Actual Dialog Icon Paths")
    print("=" * 50)
    
    try:
        # Import and create settings window
        from cocoa_settings import SettingsWindow, SettingsManager, NSAlert
        settings_manager = SettingsManager()
        settings_window = SettingsWindow.alloc().initWithSettingsManager_(settings_manager)
        
        # Get current appearance
        current_appearance = settings_window._get_current_appearance()
        print(f"Current appearance: {current_appearance}")
        
        # Simulate the exact logic from _set_dialog_icon
        if current_appearance == 'dark':
            logo_filename = 'light.png'  # Use light logo on dark theme
        else:
            logo_filename = 'dark.png'   # Use dark logo on light theme
        
        print(f"Selected logo filename: {logo_filename}")
        
        # Build path exactly like the method does
        if getattr(sys, 'frozen', False):
            # Running as app bundle
            app_bundle_path = os.path.dirname(sys.executable)
            logo_path = os.path.join(app_bundle_path, '..', 'Resources', 'assets', logo_filename)
            print(f"Bundle path: {logo_path}")
        else:
            # Running in development - this is the exact same logic as _set_dialog_icon
            script_dir = os.path.dirname(os.path.abspath('/Users/jebasinghemmanuel/Workspace/rephrasely/src/cocoa_settings.py'))
            project_root = os.path.dirname(script_dir)
            logo_path = os.path.join(project_root, 'assets', logo_filename)
            print(f"Development path: {logo_path}")
        
        print(f"Final logo path: {logo_path}")
        print(f"File exists: {os.path.exists(logo_path)}")
        
        # Test the actual method
        print("\nTesting actual _set_dialog_icon method...")
        test_alert = NSAlert.alloc().init()
        test_alert.setMessageText_("Test")
        
        # Call method and capture debug output
        settings_window._set_dialog_icon(test_alert)
        
        # Now test switching themes to see if it changes
        print("\nTesting theme responsiveness...")
        print("(To properly test this, you'd need to change your system theme and run again)")
        
        # Test both theme scenarios manually
        test_scenarios = [
            ('light', 'dark.png'),
            ('dark', 'light.png')
        ]
        
        for theme, expected_file in test_scenarios:
            print(f"\nScenario: {theme} theme should use {expected_file}")
            
            # Build path for this scenario
            script_dir = os.path.dirname(os.path.abspath('/Users/jebasinghemmanuel/Workspace/rephrasely/src/cocoa_settings.py'))
            project_root = os.path.dirname(script_dir)
            test_path = os.path.join(project_root, 'assets', expected_file)
            
            print(f"  Path: {test_path}")
            print(f"  Exists: {os.path.exists(test_path)}")
            
            if os.path.exists(test_path):
                try:
                    from cocoa_settings import NSImage, NSMakeSize
                    image = NSImage.alloc().initWithContentsOfFile_(test_path)
                    if image:
                        print(f"  ✅ Image loads successfully")
                        image.setSize_(NSMakeSize(64, 64))
                        print(f"  ✅ Image resize works")
                    else:
                        print(f"  ❌ Image failed to load")
                except Exception as e:
                    print(f"  ❌ Image loading error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_actual_paths() 