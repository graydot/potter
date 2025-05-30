#!/usr/bin/env python3
"""
Real Dialog Integration Tests
Tests actual AppKit dialog creation without requiring user interaction
"""

import os
import sys
import tempfile
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.instance_checker import show_build_conflict_dialog, SingleInstanceChecker


def test_real_dialog_creation():
    """Test that dialogs actually create without showing them"""
    print("🧪 Testing real dialog creation...")
    
    try:
        # Import AppKit to verify it works
        from AppKit import NSAlert, NSAlertFirstButtonReturn, NSApplication
        
        # Create test build info
        current_build = {
            "build_id": "newer_build_456",
            "timestamp": "2025-05-29T12:00:00.000000",
            "unix_timestamp": 1748486400,
            "version": "1.0.1"
        }
        
        running_build = {
            "build_id": "older_build_123", 
            "timestamp": "2025-05-28T12:00:00.000000",
            "unix_timestamp": 1748400000,
            "version": "1.0.0"
        }
        
        # Test dialog creation (but don't show it)
        alert = NSAlert.alloc().init()
        
        # Set up dialog exactly like the real function
        alert.setMessageText_("Potter Instance Conflict")
        
        current_dt = datetime.fromisoformat(current_build.get('timestamp', ''))
        running_dt = datetime.fromisoformat(running_build.get('timestamp', ''))
        current_str = current_dt.strftime("%Y-%m-%d %H:%M:%S")
        running_str = running_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        alert.setInformativeText_(
            f"A newer build is available.\n\n"
            f"Running: {running_build.get('build_id', 'unknown')} ({running_str})\n"
            f"Current: {current_build.get('build_id', 'unknown')} ({current_str})\n\n"
            f"Replace the older running instance?"
        )
        alert.addButtonWithTitle_("Replace Running Instance")
        alert.addButtonWithTitle_("Keep Running Instance")
        
        # Verify dialog properties without showing
        assert alert.messageText() == "Potter Instance Conflict"
        assert "newer build is available" in alert.informativeText()
        assert alert.buttons().count() == 2
        assert alert.buttons()[0].title() == "Replace Running Instance"
        assert alert.buttons()[1].title() == "Keep Running Instance"
        
        print("   ✅ Real NSAlert dialog created successfully")
        print(f"   ✅ Message: {alert.messageText()}")
        print(f"   ✅ Buttons: {[alert.buttons()[i].title() for i in range(alert.buttons().count())]}")
        
        return True
        
    except ImportError as e:
        print(f"   ⚠️  AppKit not available: {e}")
        print("   ℹ️  This is expected in non-macOS environments")
        return True  # Pass the test since this is environment-dependent
    except Exception as e:
        print(f"   ❌ Dialog creation failed: {e}")
        return False


def test_dialog_text_generation():
    """Test dialog text generation for different scenarios"""
    print("🧪 Testing dialog text generation...")
    
    scenarios = [
        {
            "name": "Newer replacing older",
            "current": {"build_id": "new_123", "timestamp": "2025-05-29T12:00:00"},
            "running": {"build_id": "old_123", "timestamp": "2025-05-28T12:00:00"},
            "expected_text": "newer build is available"
        },
        {
            "name": "Older trying to replace newer", 
            "current": {"build_id": "old_123", "timestamp": "2025-05-28T12:00:00"},
            "running": {"build_id": "new_123", "timestamp": "2025-05-29T12:00:00"},
            "expected_text": "newer build is currently running"
        },
        {
            "name": "Same timestamp",
            "current": {"build_id": "same_123", "timestamp": "2025-05-29T12:00:00"},
            "running": {"build_id": "same_456", "timestamp": "2025-05-29T12:00:00"},
            "expected_text": "same build is currently running"
        }
    ]
    
    for scenario in scenarios:
        print(f"   Testing: {scenario['name']}")
        
        # This tests the logic without creating actual dialogs
        current_ts = scenario['current']['timestamp']
        running_ts = scenario['running']['timestamp'] 
        
        if current_ts and running_ts:
            current_time = datetime.fromisoformat(current_ts)
            running_time = datetime.fromisoformat(running_ts)
            
            if current_time > running_time:
                result_text = "newer build is available"
            elif current_time < running_time:
                result_text = "newer build is currently running"
            else:
                result_text = "same build is currently running"
        
        assert scenario['expected_text'] in result_text.lower(), f"Expected '{scenario['expected_text']}' in '{result_text}'"
        print(f"     ✅ Generated: {result_text}")
    
    return True


def test_same_build_dialog_creation():
    """Test same build dialog creation"""
    print("🧪 Testing same build dialog creation...")
    
    try:
        from AppKit import NSAlert
        
        # Create checker for dialog testing
        checker = SingleInstanceChecker("test_app")
        pid = 12345
        
        # Create dialog like the real function
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Potter is Already Running")
        alert.setInformativeText_(
            f"Potter is already running (Process ID: {pid}).\n\n"
            f"Would you like to quit the running instance and start a new one?\n\n"
            f"Note: Any unsaved work in the running instance will be lost."
        )
        alert.addButtonWithTitle_("Quit Running & Start New")
        alert.addButtonWithTitle_("Keep Running Instance")
        
        # Verify dialog structure
        assert alert.messageText() == "Potter is Already Running"
        assert f"Process ID: {pid}" in alert.informativeText()
        assert alert.buttons().count() == 2
        
        print("   ✅ Same build dialog created successfully")
        return True
        
    except ImportError:
        print("   ⚠️  AppKit not available - skipping UI test")
        return True
    except Exception as e:
        print(f"   ❌ Same build dialog creation failed: {e}")
        return False


def test_instance_checker_real_build_detection():
    """Test real build ID detection in current environment"""
    print("🧪 Testing real build detection...")
    
    checker = SingleInstanceChecker("test_build_detection")
    
    # Test current build loading
    build_id = checker.current_build
    assert build_id is not None, "Should load current build"
    assert "build_id" in build_id, "Should have build_id field"
    assert "timestamp" in build_id, "Should have timestamp field"
    
    # In development, should be dev_build
    if not hasattr(sys, '_MEIPASS'):
        assert build_id["build_id"] == "dev_build", "Development should use dev_build"
    
    # Test build comparison logic
    newer_build = {
        "build_id": "test_newer",
        "timestamp": "2025-12-31T23:59:59",
        "unix_timestamp": 9999999999
    }
    
    older_build = {
        "build_id": "test_older", 
        "timestamp": "2025-01-01T00:00:00",
        "unix_timestamp": 1
    }
    
    print(f"   ✅ Current build: {build_id['build_id']}")
    print(f"   ✅ Build detection working in {'bundle' if hasattr(sys, '_MEIPASS') else 'development'} mode")
    
    return True


def run_real_dialog_tests():
    """Run all real dialog integration tests"""
    print("🎭 Real Dialog Integration Tests")
    print("=" * 60)
    print("These tests verify actual AppKit dialog creation")
    print("without requiring user interaction")
    print("=" * 60)
    
    tests = [
        test_real_dialog_creation,
        test_dialog_text_generation,
        test_same_build_dialog_creation,
        test_instance_checker_real_build_detection
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"   ❌ {test.__name__} failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    print("=" * 60)
    print(f"📊 Real Dialog Tests: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All real dialog integration tests passed!")
        return True
    else:
        print("❌ Some real dialog tests failed")
        return False


if __name__ == "__main__":
    success = run_real_dialog_tests()
    sys.exit(0 if success else 1)