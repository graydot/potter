#!/usr/bin/env python3
"""
Test script to verify app bundle instance detection works
"""

import os
import subprocess
import time
import signal


def test_app_bundle_instance_detection():
    """Test that the app bundle correctly detects running instances"""
    app_path = "/Users/jebasinghemmanuel/Workspace/rephrasely/dist/app/Potter.app"
    
    if not os.path.exists(app_path):
        print("❌ App bundle not found at:", app_path)
        print("Run 'python scripts/build_app.py' first")
        return False
    
    print("🧪 Testing app bundle instance detection...")
    print(f"App path: {app_path}")
    
    # Start first instance
    print("\n1. Starting first instance...")
    proc1 = subprocess.Popen(['open', app_path])
    time.sleep(3)  # Give it time to start
    
    # Check if PID files were created
    pid_file = os.path.expanduser("~/.potter.pid")
    build_file = os.path.expanduser("~/.potter.build")
    
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            pid1 = f.read().strip()
        print(f"   ✅ First instance created PID file: {pid1}")
    else:
        print("   ❌ No PID file created")
        return False
    
    if os.path.exists(build_file):
        with open(build_file, 'r') as f:
            build_info = f.read().strip()
        print(f"   ✅ Build file created: {build_info[:50]}...")
    else:
        print("   ❌ No build file created")
        return False
    
    # Try to start second instance - this should show conflict dialog
    print("\n2. Starting second instance (should show dialog)...")
    print("   ⚠️  You should see a dialog asking about replacing the instance")
    print("   📝 Click 'Keep Running Instance' to test properly")
    
    proc2 = subprocess.Popen(['open', app_path])
    time.sleep(3)  # Give it time to show dialog
    
    # Check if still only one instance
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            pid2 = f.read().strip()
        
        if pid1 == pid2:
            print(f"   ✅ Same PID maintained: {pid2}")
            print("   ✅ Instance detection working correctly!")
        else:
            print(f"   ⚠️  PID changed from {pid1} to {pid2}")
            print("   ℹ️  This means the user replaced the instance")
    
    # Cleanup - kill the Potter app
    print("\n3. Cleaning up...")
    try:
        subprocess.run(['pkill', '-f', 'Potter'], check=False)
        time.sleep(1)
        
        # Remove instance files
        for file_path in [pid_file, build_file]:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"   ✅ Removed {file_path}")
        
    except Exception as e:
        print(f"   ⚠️  Cleanup error: {e}")
    
    print("\n✅ App bundle instance detection test completed")
    return True


if __name__ == "__main__":
    test_app_bundle_instance_detection()