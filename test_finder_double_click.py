#!/usr/bin/env python3
"""
Test simulating actual Finder double-click behavior
"""

import subprocess
import time
import os


def test_finder_style_launch():
    """Test launching app the way Finder does (via 'open' command)"""
    app_path = "/Users/jebasinghemmanuel/Workspace/rephrasely/dist/app/Potter.app"
    
    if not os.path.exists(app_path):
        print("❌ App not found")
        return
    
    print("🧪 Testing Finder-Style Double-Click")
    print("=" * 40)
    print("This simulates actual Finder behavior using 'open' command")
    
    # Clean up first
    subprocess.run(['pkill', '-f', 'Potter'], check=False)
    time.sleep(1)
    
    for file in ['/Users/jebasinghemmanuel/.potter.pid', '/Users/jebasinghemmanuel/.potter.build']:
        if os.path.exists(file):
            os.remove(file)
    
    print("\n1. First launch (via 'open' command)...")
    subprocess.run(['open', app_path])
    time.sleep(4)  # Give time to start
    
    if os.path.exists('/Users/jebasinghemmanuel/.potter.pid'):
        with open('/Users/jebasinghemmanuel/.potter.pid', 'r') as f:
            pid1 = f.read().strip()
        print(f"   ✅ First instance (PID: {pid1})")
    else:
        print("   ❌ First instance failed to start")
        return
    
    print("\n2. Second launch - should show dialog...")
    print("   🎯 Watch for dialog popup!")
    print("   ⏱️  Waiting 10 seconds...")
    
    # Launch second instance
    subprocess.run(['open', app_path])
    
    # Wait and watch
    for i in range(10):
        time.sleep(1)
        print(f"   {10-i} seconds remaining...")
        
        # Check if PID changed
        if os.path.exists('/Users/jebasinghemmanuel/.potter.pid'):
            with open('/Users/jebasinghemmanuel/.potter.pid', 'r') as f:
                current_pid = f.read().strip()
            if current_pid != pid1:
                print(f"   🔄 PID changed: {pid1} → {current_pid}")
                print("   ✅ User must have chosen to replace!")
                break
    else:
        print(f"   ✅ PID unchanged ({pid1}) - dialog worked or user kept running")
    
    print("\n3. Cleanup...")
    subprocess.run(['pkill', '-f', 'Potter'], check=False)
    time.sleep(1)
    
    print("✅ Test completed")
    print("\nIf you saw a dialog, the instance detection is working!")
    print("If no dialog appeared, there's still an issue.")


if __name__ == "__main__":
    test_finder_style_launch()