#!/usr/bin/env python3
"""
Manual test script for prompt dialog functionality
Run this to open the settings window and manually test the prompt dialogs
"""

import sys
import os
import time
import traceback

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from cocoa_settings import SettingsManager, show_settings
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def main():
    """Open settings window for manual testing"""
    print("🧪 Manual Prompt Dialog Test")
    print("=" * 40)
    
    try:
        # Create settings manager
        settings_manager = SettingsManager()
        count = len(settings_manager.get('prompts', []))
        print(f"✅ Settings manager loaded with {count} prompts")
        
        # Show settings window
        print("📱 Opening settings window...")
        controller = show_settings(settings_manager)
        
        if controller:
            print("✅ Settings window opened successfully!")
            print("\n📋 MANUAL TEST INSTRUCTIONS:")
            print("1. Navigate to the 'Prompts' section in the sidebar")
            print("2. Test ADD prompt:")
            print("   - Click the '+' button")
            print("   - Enter a name (max 10 chars) and prompt text")
            print("   - Click 'Save' - should add the prompt")
            print("   - Try clicking 'Cancel' - should close without saving")
            print("3. Test EDIT prompt:")
            print("   - Double-click an existing prompt")
            print("   - Modify the name or text")
            print("   - Click 'Save' - should update the prompt")
            print("   - Try 'Cancel' - should close without changes")
            print("4. Test DELETE prompt:")
            print("   - Select a prompt and click the '-' button")
            print("   - Confirm deletion - should remove the prompt")
            print("5. Test VALIDATION:")
            print("   - Try saving with empty name or text - should show error")
            print("   - Try saving with name longer than 10 chars - should show error")
            print("   - Try creating duplicate names - should show error")
            print("\n⚠️  The window will stay open for testing.")
            print("    Close the window when done testing.")
            
            # Keep the script running so the window stays open
            print("\n⏳ Waiting for window to be closed...")
            try:
                # This will keep the Python script alive
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Test interrupted by user")
        else:
            print("❌ Failed to open settings window")
            return False
            
    except Exception as e:
        print(f"❌ Error running manual test: {e}")
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 