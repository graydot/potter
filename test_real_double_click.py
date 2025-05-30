#!/usr/bin/env python3
"""
Test what happens when actually running the app bundle twice
This simulates the real double-click scenario
"""

import subprocess
import time
import os
import json


def test_real_app_double_click():
    """Test double-clicking the real app"""
    app_path = "/Users/jebasinghemmanuel/Workspace/rephrasely/dist/app/Potter.app"
    
    if not os.path.exists(app_path):
        print("❌ App not found. Run build first.")
        return
    
    print("🧪 Testing Real App Double-Click")
    print("=" * 40)
    
    # Clean up any existing instances first
    subprocess.run(['pkill', '-f', 'Potter'], check=False)
    time.sleep(1)
    
    # Remove old instance files
    for file in ['/Users/jebasinghemmanuel/.potter.pid', '/Users/jebasinghemmanuel/.potter.build']:
        if os.path.exists(file):
            os.remove(file)
    
    print("1. Starting first instance...")
    proc1 = subprocess.Popen([app_path + '/Contents/MacOS/Potter'])
    time.sleep(3)  # Give it time to start
    
    # Check instance files
    if os.path.exists('/Users/jebasinghemmanuel/.potter.pid'):
        with open('/Users/jebasinghemmanuel/.potter.pid', 'r') as f:
            pid1 = f.read().strip()
        print(f"   ✅ First instance started (PID: {pid1})")
    else:
        print("   ❌ No PID file created")
        return
    
    if os.path.exists('/Users/jebasinghemmanuel/.potter.build'):
        with open('/Users/jebasinghemmanuel/.potter.build', 'r') as f:
            build1 = json.load(f)
        print(f"   ✅ Build ID: {build1['build_id']}")
    
    print("\n2. Starting second instance (same build)...")
    print("   🎯 This should show a dialog!")
    
    # Run second instance
    proc2 = subprocess.Popen([app_path + '/Contents/MacOS/Potter'])
    time.sleep(5)  # Give time for dialog
    
    # Check what happened
    if os.path.exists('/Users/jebasinghemmanuel/.potter.pid'):
        with open('/Users/jebasinghemmanuel/.potter.pid', 'r') as f:
            pid2 = f.read().strip()
        
        if pid1 == pid2:
            print(f"   ✅ Same PID ({pid2}) - instance detection worked")
        else:
            print(f"   ⚠️  PID changed: {pid1} → {pid2}")
    
    # Check logs
    log_path = app_path + '/Contents/Frameworks/potter.log'
    if os.path.exists(log_path):
        print("\n3. Checking logs for instance detection...")
        with open(log_path, 'r') as f:
            log_lines = f.readlines()
        
        # Look for recent instance detection logs
        recent_logs = log_lines[-50:]  # Last 50 lines
        
        for line in recent_logs:
            if 'instance' in line.lower() or 'dialog' in line.lower() or 'build' in line.lower():
                print(f"   📝 {line.strip()}")
    
    print("\n4. Cleanup...")
    subprocess.run(['pkill', '-f', 'Potter'], check=False)
    time.sleep(1)
    
    for file in ['/Users/jebasinghemmanuel/.potter.pid', '/Users/jebasinghemmanuel/.potter.build']:
        if os.path.exists(file):
            os.remove(file)
    
    print("✅ Test completed")


if __name__ == "__main__":
    test_real_app_double_click()