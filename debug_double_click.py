#!/usr/bin/env python3
"""
Debug what happens when double-clicking the app
"""

import os
import sys
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.instance_checker import SingleInstanceChecker, load_build_id


def debug_double_click_scenario():
    """Debug what happens during double-click"""
    print("🔍 Debugging Double-Click Scenario")
    print("=" * 50)
    
    # Load the current app's build ID (simulating second instance)
    current_build = load_build_id()
    print(f"Current build ID: {current_build}")
    
    # Check instance files
    pid_file = "/Users/jebasinghemmanuel/.potter.pid"
    build_file = "/Users/jebasinghemmanuel/.potter.build"
    
    print(f"\nInstance files:")
    print(f"PID file exists: {os.path.exists(pid_file)}")
    print(f"Build file exists: {os.path.exists(build_file)}")
    
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            running_pid = f.read().strip()
        print(f"Running PID: {running_pid}")
        
        # Check if process exists
        try:
            os.kill(int(running_pid), 0)
            print(f"Process {running_pid}: RUNNING ✅")
        except OSError:
            print(f"Process {running_pid}: NOT RUNNING ❌")
    
    if os.path.exists(build_file):
        with open(build_file, 'r') as f:
            running_build = json.load(f)
        print(f"Running build: {running_build}")
        
        # Compare builds
        current_build_id = current_build.get('build_id', 'unknown')
        running_build_id = running_build.get('build_id', 'unknown')
        
        print(f"\nBuild comparison:")
        print(f"Current: {current_build_id}")
        print(f"Running: {running_build_id}")
        print(f"Same build: {current_build_id == running_build_id}")
    
    # Create instance checker and test
    print(f"\nTesting instance checker...")
    checker = SingleInstanceChecker()
    
    print(f"Checker build ID: {checker.current_build.get('build_id')}")
    
    # This is the key test - what does is_already_running return?
    print(f"\nCalling is_already_running()...")
    try:
        result = checker.is_already_running()
        print(f"is_already_running() returned: {result}")
        
        if result:
            print("✅ Instance detection working - should have shown dialog")
        else:
            print("❌ Instance detection failed - no dialog shown")
            
    except Exception as e:
        print(f"❌ Error in instance checking: {e}")
        import traceback
        traceback.print_exc()


def debug_dialog_creation():
    """Test if we can create dialogs in this environment"""
    print(f"\n🔍 Testing Dialog Creation")
    print("=" * 30)
    
    try:
        from AppKit import NSAlert, NSApplication
        
        # Initialize NSApplication (required for dialogs)
        app = NSApplication.sharedApplication()
        print("✅ NSApplication initialized")
        
        # Try creating an alert
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Test Dialog")
        alert.setInformativeText_("This is a test to see if dialogs work")
        alert.addButtonWithTitle_("OK")
        
        print("✅ NSAlert created successfully")
        print("Dialog creation works - the issue is elsewhere")
        
        return True
        
    except ImportError as e:
        print(f"❌ AppKit import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Dialog creation failed: {e}")
        return False


def simulate_second_instance():
    """Simulate what happens when a second instance starts"""
    print(f"\n🔍 Simulating Second Instance")
    print("=" * 35)
    
    # Create a new checker (like a fresh app launch)
    checker = SingleInstanceChecker()
    
    print(f"New instance build: {checker.current_build.get('build_id')}")
    
    # Step through the detection process
    print(f"\n1. Checking if PID file exists...")
    if not os.path.exists(checker.pid_file):
        print("   ❌ No PID file - would start normally")
        return
    
    print("   ✅ PID file exists")
    
    print(f"2. Reading PID file...")
    try:
        with open(checker.pid_file, 'r') as f:
            old_pid = int(f.read().strip())
        print(f"   Old PID: {old_pid}")
    except Exception as e:
        print(f"   ❌ Error reading PID: {e}")
        return
    
    print(f"3. Checking if process exists...")
    try:
        os.kill(old_pid, 0)
        print("   ✅ Process exists")
    except OSError:
        print("   ❌ Process doesn't exist - would clean up and start")
        return
    
    print(f"4. Getting running build info...")
    running_build = checker.get_running_build_info()
    if not running_build:
        print("   ❌ No build info - would show generic dialog")
        return
    
    print(f"   Running build: {running_build.get('build_id')}")
    
    print(f"5. Comparing builds...")
    current_build_id = checker.current_build.get('build_id')
    running_build_id = running_build.get('build_id')
    
    print(f"   Current: {current_build_id}")
    print(f"   Running: {running_build_id}")
    
    if current_build_id == running_build_id:
        print("   ✅ Same build - should show same build dialog")
        
        # Test dialog creation
        print(f"6. Testing dialog...")
        try:
            # Don't actually show the dialog, just test creation
            from AppKit import NSAlert
            alert = NSAlert.alloc().init()
            print("   ✅ Dialog would be created")
            
            # The dialog SHOULD be shown here in real scenario
            print("   🎯 THIS IS WHERE THE DIALOG SHOULD APPEAR")
            
        except Exception as e:
            print(f"   ❌ Dialog creation failed: {e}")
    else:
        print("   ✅ Different builds - should show conflict dialog")


if __name__ == "__main__":
    debug_double_click_scenario()
    debug_dialog_creation()
    simulate_second_instance()
    
    print(f"\n" + "=" * 50)
    print("🎯 DIAGNOSIS:")
    print("If you see '✅ Same build - should show same build dialog'")
    print("but no dialog appeared when double-clicking, then the")
    print("issue is likely in the dialog display logic, not detection.")
    print("=" * 50)