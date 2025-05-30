#!/usr/bin/env python3
"""
Manual Dialog Test
Shows actual dialogs for visual verification
Run this when you want to see the real user experience
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.instance_checker import show_build_conflict_dialog, SingleInstanceChecker


def manual_test_build_conflict_dialog():
    """Manually test the build conflict dialog"""
    print("🎭 Manual Build Conflict Dialog Test")
    print("=" * 50)
    print("This will show the actual dialog that users see")
    print("when different builds are detected.")
    print("=" * 50)
    
    # Create realistic build scenarios
    scenarios = [
        {
            "name": "Newer build replacing older",
            "current": {
                "build_id": "potter_20250529_150000_abc123",
                "timestamp": "2025-05-29T15:00:00.000000",
                "version": "1.0.1"
            },
            "running": {
                "build_id": "potter_20250528_120000_def456", 
                "timestamp": "2025-05-28T12:00:00.000000",
                "version": "1.0.0"
            }
        },
        {
            "name": "Older build trying to replace newer",
            "current": {
                "build_id": "potter_20250527_100000_ghi789",
                "timestamp": "2025-05-27T10:00:00.000000", 
                "version": "0.9.5"
            },
            "running": {
                "build_id": "potter_20250529_140000_jkl012",
                "timestamp": "2025-05-29T14:00:00.000000",
                "version": "1.0.1"
            }
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. Testing: {scenario['name']}")
        print(f"   Current: {scenario['current']['build_id']}")
        print(f"   Running: {scenario['running']['build_id']}")
        
        response = input("   Show this dialog? (y/n): ").strip().lower()
        if response == 'y':
            print("   Showing dialog...")
            try:
                result = show_build_conflict_dialog(scenario['current'], scenario['running'])
                print(f"   User choice: {'Replace' if result else 'Keep'} running instance")
            except Exception as e:
                print(f"   Error: {e}")
        else:
            print("   Skipped")


def manual_test_same_build_dialog():
    """Manually test the same build dialog"""
    print("\n🎭 Manual Same Build Dialog Test")
    print("=" * 50)
    print("This shows the dialog when the same build")
    print("is already running.")
    print("=" * 50)
    
    response = input("Show same build dialog? (y/n): ").strip().lower()
    if response == 'y':
        print("Showing same build dialog...")
        try:
            checker = SingleInstanceChecker()
            fake_pid = 12345
            result = checker.show_same_build_dialog(fake_pid)
            print(f"User choice: {'Replace' if result else 'Keep'} running instance")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Skipped")


def manual_test_real_instance_scenario():
    """Test a realistic instance conflict scenario"""
    print("\n🎭 Realistic Instance Conflict Test")
    print("=" * 50)
    print("This simulates what happens when you")
    print("double-click the app while it's running.")
    print("=" * 50)
    
    response = input("Simulate realistic conflict? (y/n): ").strip().lower()
    if response != 'y':
        print("Skipped")
        return
    
    import tempfile
    import json
    
    # Create temporary instance files
    with tempfile.TemporaryDirectory() as temp_dir:
        app_name = "manual_test_potter"
        
        # First "instance"
        checker1 = SingleInstanceChecker(app_name)
        checker1.pid_file = os.path.join(temp_dir, f".{app_name}.pid")
        checker1.build_file = os.path.join(temp_dir, f".{app_name}.build")
        
        # Simulate it's running
        checker1.create_pid_file()
        print("✅ First instance 'started'")
        
        # Second "instance" with different build
        checker2 = SingleInstanceChecker(app_name)
        checker2.pid_file = os.path.join(temp_dir, f".{app_name}.pid") 
        checker2.build_file = os.path.join(temp_dir, f".{app_name}.build")
        checker2.current_build = {
            "build_id": "potter_20250529_160000_new123",
            "timestamp": "2025-05-29T16:00:00.000000",
            "version": "1.0.2"
        }
        
        print("Checking if second instance should start...")
        is_running = checker2.is_already_running()
        
        if is_running:
            print("✅ Instance detection worked - second instance blocked/replaced")
        else:
            print("⚠️  Second instance was allowed to start")
        
        # Cleanup
        checker1.cleanup()


if __name__ == "__main__":
    print("🧪 Potter Manual Dialog Testing")
    print("This script lets you see the actual user experience")
    print("of the instance detection dialogs.\n")
    
    try:
        manual_test_build_conflict_dialog()
        manual_test_same_build_dialog() 
        manual_test_real_instance_scenario()
        
        print("\n✅ Manual testing completed!")
        print("The dialogs you saw are exactly what users experience.")
        
    except KeyboardInterrupt:
        print("\n⏹️  Manual testing cancelled")
    except Exception as e:
        print(f"\n❌ Error during manual testing: {e}")
        import traceback
        traceback.print_exc()