#!/usr/bin/env python3
"""
Automated Instance Detection Tests
Tests instance detection without requiring human interaction
"""

import os
import sys
import tempfile
import time
import signal
import multiprocessing
import json
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.instance_checker import SingleInstanceChecker, show_build_conflict_dialog


def test_basic_instance_detection():
    """Test basic instance detection without dialogs"""
    print("🧪 Testing basic instance detection...")
    
    # Use temporary files to avoid conflicts
    with tempfile.TemporaryDirectory() as temp_dir:
        app_name = f"test_potter_{int(time.time())}"
        
        # Create first checker
        checker1 = SingleInstanceChecker(app_name=app_name)
        checker1.pid_file = os.path.join(temp_dir, f".{app_name}.pid")
        checker1.build_file = os.path.join(temp_dir, f".{app_name}.build")
        
        # Should not be running initially
        assert not checker1.is_already_running(), "Should not detect instance initially"
        
        # Create PID file
        success = checker1.create_pid_file()
        assert success, "Should successfully create PID file"
        assert os.path.exists(checker1.pid_file), "PID file should exist"
        assert os.path.exists(checker1.build_file), "Build file should exist"
        
        # Create second checker with same name
        checker2 = SingleInstanceChecker(app_name=app_name)
        checker2.pid_file = os.path.join(temp_dir, f".{app_name}.pid")
        checker2.build_file = os.path.join(temp_dir, f".{app_name}.build")
        
        # Mock the dialog to auto-return False (keep running instance)
        with patch.object(checker2, 'show_same_build_dialog', return_value=False):
            result = checker2.is_already_running()
            assert result, "Should detect running instance"
        
        # Test with dialog returning True (replace instance)
        # First, write a fake PID that doesn't correspond to the current process
        fake_pid = 999999
        with open(checker2.pid_file, 'w') as f:
            f.write(str(fake_pid))
        
        with patch.object(checker2, 'show_same_build_dialog', return_value=True):
            with patch('os.kill') as mock_kill:
                with patch('time.sleep'):  # Speed up the test
                    # Mock the first kill (check if process exists) to succeed
                    # Mock the second kill (terminate) to succeed  
                    # Mock the third kill (check if gone) to fail (process gone)
                    mock_kill.side_effect = [None, None, OSError("No such process")]
                    result = checker2.is_already_running()
                    assert not result, "Should allow replacement when user approves"
        
        # Cleanup
        checker1.cleanup()
    
    print("   ✅ Basic instance detection passed")
    return True


def test_build_conflict_detection():
    """Test build conflict detection without human interaction"""
    print("🧪 Testing build conflict detection...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        app_name = f"test_potter_conflict_{int(time.time())}"
        
        # Create first checker with specific build
        checker1 = SingleInstanceChecker(app_name=app_name)
        checker1.pid_file = os.path.join(temp_dir, f".{app_name}.pid")
        checker1.build_file = os.path.join(temp_dir, f".{app_name}.build")
        checker1.current_build = {
            "build_id": "old_build_123",
            "timestamp": "2025-05-28T12:00:00.000000",
            "unix_timestamp": 1748400000,
            "version": "1.0.0"
        }
        
        # Create PID file
        checker1.create_pid_file()
        
        # Create second checker with different build
        checker2 = SingleInstanceChecker(app_name=app_name)
        checker2.pid_file = os.path.join(temp_dir, f".{app_name}.pid")
        checker2.build_file = os.path.join(temp_dir, f".{app_name}.build")
        checker2.current_build = {
            "build_id": "new_build_456",
            "timestamp": "2025-05-29T12:00:00.000000",
            "unix_timestamp": 1748486400,
            "version": "1.0.1"
        }
        
        # Mock the build conflict dialog to return False (keep old)
        with patch('utils.instance_checker.show_build_conflict_dialog', return_value=False):
            result = checker2.is_already_running()
            assert result, "Should keep running instance when user chooses to"
        
        # Mock the build conflict dialog to return True (replace)
        # Write a fake PID again
        fake_pid = 999998
        with open(checker2.pid_file, 'w') as f:
            f.write(str(fake_pid))
        
        with patch('utils.instance_checker.show_build_conflict_dialog', return_value=True):
            with patch('os.kill') as mock_kill:
                with patch('time.sleep'):  # Speed up the test
                    mock_kill.side_effect = [None, None, OSError("No such process")]  # Check exists, terminate, check gone
                    result = checker2.is_already_running()
                    assert not result, "Should replace when user approves"
        
        # Cleanup
        checker1.cleanup()
    
    print("   ✅ Build conflict detection passed")
    return True


def test_stale_file_cleanup():
    """Test cleanup of stale PID files"""
    print("🧪 Testing stale file cleanup...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        app_name = f"test_potter_stale_{int(time.time())}"
        
        checker = SingleInstanceChecker(app_name=app_name)
        checker.pid_file = os.path.join(temp_dir, f".{app_name}.pid")
        checker.build_file = os.path.join(temp_dir, f".{app_name}.build")
        
        # Create fake PID file with non-existent process
        fake_pid = 999999  # Very unlikely to exist
        with open(checker.pid_file, 'w') as f:
            f.write(str(fake_pid))
        
        with open(checker.build_file, 'w') as f:
            json.dump({"build_id": "fake", "timestamp": "2025-01-01T00:00:00"}, f)
        
        # Should clean up stale files and return False
        result = checker.is_already_running()
        assert not result, "Should cleanup stale files and allow new instance"
        assert not os.path.exists(checker.pid_file), "Stale PID file should be removed"
        assert not os.path.exists(checker.build_file), "Stale build file should be removed"
    
    print("   ✅ Stale file cleanup passed")
    return True


def test_app_bundle_vs_development():
    """Test build ID loading in different environments"""
    print("🧪 Testing app bundle vs development detection...")
    
    from utils.instance_checker import load_build_id
    
    # Test development mode (current environment)
    build_id = load_build_id()
    assert build_id is not None, "Should load build ID"
    assert "build_id" in build_id, "Build ID should have build_id field"
    assert "timestamp" in build_id, "Build ID should have timestamp field"
    
    # In development, should get dev_build
    if not hasattr(sys, '_MEIPASS'):
        assert build_id["build_id"] == "dev_build", "Development should use dev_build ID"
    
    print(f"   ✅ Loaded build ID: {build_id['build_id']}")
    return True


def test_dialog_mocking():
    """Test that dialogs can be properly mocked"""
    print("🧪 Testing dialog mocking...")
    
    # Create fake build info
    current_build = {
        "build_id": "new_build",
        "timestamp": "2025-05-29T12:00:00.000000",
        "unix_timestamp": 1748486400,
        "version": "1.0.1"
    }
    
    running_build = {
        "build_id": "old_build", 
        "timestamp": "2025-05-28T12:00:00.000000",
        "unix_timestamp": 1748400000,
        "version": "1.0.0"
    }
    
    # Mock AppKit imports that happen inside the function
    with patch.dict('sys.modules', {'AppKit': MagicMock()}):
        mock_appkit = sys.modules['AppKit']
        mock_alert = MagicMock()
        mock_appkit.NSAlert = MagicMock()
        mock_appkit.NSAlert.alloc.return_value.init.return_value = mock_alert
        mock_appkit.NSAlertFirstButtonReturn = 1000
        
        # Test "replace" choice (first button)
        mock_alert.runModal.return_value = 1000
        
        result = show_build_conflict_dialog(current_build, running_build)
        assert result == True, "Should return True for replace choice"
        
        # Test "keep" choice (second button)  
        mock_alert.runModal.return_value = 1001
        
        result = show_build_conflict_dialog(current_build, running_build)
        assert result == False, "Should return False for keep choice"
    
    print("   ✅ Dialog mocking passed")
    return True


def run_automated_instance_tests():
    """Run all automated instance detection tests"""
    print("🤖 Running Automated Instance Detection Tests")
    print("=" * 60)
    
    tests = [
        test_basic_instance_detection,
        test_build_conflict_detection, 
        test_stale_file_cleanup,
        test_app_bundle_vs_development,
        test_dialog_mocking
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print(f"   ❌ {test.__name__} failed")
        except Exception as e:
            failed += 1
            print(f"   ❌ {test.__name__} failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    print("=" * 60)
    print(f"📊 Automated Instance Tests: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All automated instance detection tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = run_automated_instance_tests()
    sys.exit(0 if success else 1)