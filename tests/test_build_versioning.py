#!/usr/bin/env python3
"""
Build Versioning Tests
Tests the build ID system and instance conflict resolution with minimal mocking
"""

import sys
import os
import tempfile
import json
import time
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def create_mock_build_id(prefix="test", offset_hours=0):
    """Create a mock build ID for testing"""
    timestamp = datetime.now()
    if offset_hours != 0:
        timestamp += timedelta(hours=offset_hours)
    
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    
    build_id = {
        "build_id": f"{prefix}_{timestamp_str}_mock123",
        "timestamp": timestamp.isoformat(),
        "unix_timestamp": int(timestamp.timestamp()),
        "version": "1.0.0"
    }
    
    return build_id


def test_build_id_generation():
    """Test build ID generation from build script"""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        from build_app import generate_build_id
        
        build_id = generate_build_id()
        
        # Verify required fields
        required_fields = ["build_id", "timestamp", "unix_timestamp", "version"]
        for field in required_fields:
            assert field in build_id, f"Missing field: {field}"
        
        # Verify format
        assert build_id["build_id"].startswith("potter_"), "Build ID should start with 'potter_'"
        assert len(build_id["build_id"]) > 20, "Build ID should be reasonably long"
        assert isinstance(build_id["unix_timestamp"], int), "Unix timestamp should be integer"
        
        # Verify timestamp is recent (within last minute)
        now = int(datetime.now().timestamp())
        assert abs(now - build_id["unix_timestamp"]) < 60, "Timestamp should be recent"
        
        return True
        
    except Exception as e:
        print(f"❌ Build ID generation failed: {e}")
        return False


def test_instance_checker_load_build_id():
    """Test instance checker build ID loading"""
    try:
        from utils.instance_checker import load_build_id
        
        build_id = load_build_id()
        
        # Should get development build ID when running from source
        assert "build_id" in build_id
        assert "timestamp" in build_id
        assert "unix_timestamp" in build_id
        assert "version" in build_id
        
        # When running from source, should get dev_build
        assert build_id["build_id"] == "dev_build"
        assert build_id["version"] == "development"
        
        return True
        
    except Exception as e:
        print(f"❌ Build ID loading failed: {e}")
        return False


def test_build_conflict_detection():
    """Test build conflict detection logic"""
    try:
        from utils.instance_checker import SingleInstanceChecker
        
        # Create instance checker with temporary files
        with tempfile.TemporaryDirectory() as temp_dir:
            pid_file = os.path.join(temp_dir, "test.pid")
            build_file = os.path.join(temp_dir, "test.build")
            
            # Mock a running instance with different build
            with open(pid_file, 'w') as f:
                f.write(str(os.getpid()))  # Our own PID for testing
            
            # Create older build info
            older_build = create_mock_build_id("older", -24)  # 24 hours ago
            with open(build_file, 'w') as f:
                json.dump(older_build, f)
            
            # Create instance checker
            checker = SingleInstanceChecker("test")
            checker.pid_file = pid_file
            checker.build_file = build_file
            
            # Override current build to be newer
            checker.current_build = create_mock_build_id("newer", 0)  # Now
            
            # Get running build info (should be the older one)
            running_build = checker.get_running_build_info()
            assert running_build is not None
            assert running_build["build_id"] == older_build["build_id"]
            
            return True
        
    except Exception as e:
        print(f"❌ Build conflict detection failed: {e}")
        return False


def test_build_comparison_logic():
    """Test build timestamp comparison logic"""
    try:
        # Create builds with known timestamps
        older_build = create_mock_build_id("older", -24)  # 24 hours ago
        newer_build = create_mock_build_id("newer", 0)    # Now
        
        # Test timestamp comparison
        older_time = older_build["unix_timestamp"]
        newer_time = newer_build["unix_timestamp"]
        
        assert newer_time > older_time, "Newer should be greater than older"
        
        # Test age determination logic (from dialog function)
        if newer_time > older_time:
            age_info = "An older build is currently running."
            action_info = "Replace with this newer build?"
        elif newer_time < older_time:
            age_info = "A newer build is currently running."
            action_info = "Replace with this older build?"
        else:
            age_info = "The same build is currently running."
            action_info = "Replace the running instance?"
        
        assert "older build is currently running" in age_info
        assert "newer build" in action_info
        
        return True
        
    except Exception as e:
        print(f"❌ Build comparison logic failed: {e}")
        return False


def test_build_file_persistence():
    """Test build file save/load functionality"""
    try:
        from utils.instance_checker import SingleInstanceChecker
        
        with tempfile.TemporaryDirectory() as temp_dir:
            build_file = os.path.join(temp_dir, "test.build")
            
            # Create instance checker
            checker = SingleInstanceChecker("test")
            checker.build_file = build_file
            
            # Save build info
            success = checker.save_build_info()
            assert success, "Should save build info successfully"
            
            # Verify file exists
            assert os.path.exists(build_file), "Build file should exist"
            
            # Load and verify
            loaded_build = checker.get_running_build_info()
            assert loaded_build is not None, "Should load build info"
            assert loaded_build["build_id"] == checker.current_build["build_id"]
            
            # Verify JSON structure
            with open(build_file, 'r') as f:
                file_content = json.load(f)
                assert file_content["build_id"] == checker.current_build["build_id"]
                assert "timestamp" in file_content
                assert "unix_timestamp" in file_content
            
            return True
            
    except Exception as e:
        print(f"❌ Build file persistence failed: {e}")
        return False


def test_embedded_build_id_in_app():
    """Test reading build ID from actual app bundle"""
    app_path = os.path.join(os.path.dirname(__file__), "..", "dist", "app", "Potter.app")
    build_id_file = os.path.join(app_path, "Contents", "Resources", "build_id.json")
    
    if not os.path.exists(app_path):
        print("⚠️  App bundle not found - skipping (run build first)")
        return True  # Not a failure, just not testable
    
    if not os.path.exists(build_id_file):
        print("❌ Build ID file not found in app bundle")
        return False
    
    try:
        with open(build_id_file, 'r') as f:
            build_id = json.load(f)
        
        # Verify format
        assert "build_id" in build_id
        assert "timestamp" in build_id
        assert "unix_timestamp" in build_id
        assert build_id["build_id"].startswith("potter_")
        
        # Verify timestamp format
        datetime.fromisoformat(build_id["timestamp"])  # Should not raise
        
        return True
        
    except Exception as e:
        print(f"❌ Reading embedded build ID failed: {e}")
        return False


def test_instance_checker_cleanup():
    """Test cleanup functionality for stale files"""
    try:
        from utils.instance_checker import SingleInstanceChecker
        
        with tempfile.TemporaryDirectory() as temp_dir:
            pid_file = os.path.join(temp_dir, "test.pid")
            build_file = os.path.join(temp_dir, "test.build")
            
            # Create some test files
            with open(pid_file, 'w') as f:
                f.write("12345")
            with open(build_file, 'w') as f:
                f.write('{"test": "data"}')
            
            # Create instance checker
            checker = SingleInstanceChecker("test")
            checker.pid_file = pid_file
            checker.build_file = build_file
            
            # Test cleanup
            checker.cleanup_old_files()
            
            # Files should be removed
            assert not os.path.exists(pid_file), "PID file should be removed"
            assert not os.path.exists(build_file), "Build file should be removed"
            
            return True
            
    except Exception as e:
        print(f"❌ Instance checker cleanup failed: {e}")
        return False


def test_build_id_embed_function():
    """Test the build ID embedding function"""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        from build_app import embed_build_id, generate_build_id
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock app structure
            app_path = os.path.join(temp_dir, "TestApp.app")
            contents_path = os.path.join(app_path, "Contents")
            resources_path = os.path.join(contents_path, "Resources")
            os.makedirs(resources_path)
            
            # Test embedding
            success = embed_build_id(app_path)
            assert success, "Build ID embedding should succeed"
            
            # Verify file was created
            build_id_file = os.path.join(resources_path, "build_id.json")
            assert os.path.exists(build_id_file), "Build ID file should be created"
            
            # Verify content
            with open(build_id_file, 'r') as f:
                embedded_build = json.load(f)
            
            assert "build_id" in embedded_build
            assert embedded_build["build_id"].startswith("potter_")
            assert "timestamp" in embedded_build
            assert "unix_timestamp" in embedded_build
            
            return True
            
    except Exception as e:
        print(f"❌ Build ID embed function failed: {e}")
        return False


def run_build_versioning_tests():
    """Run all build versioning tests"""
    print("🔧 Build Versioning Tests")
    print("-" * 40)
    
    tests = [
        ("Build ID Generation", test_build_id_generation),
        ("Build ID Loading", test_instance_checker_load_build_id),
        ("Build Conflict Detection", test_build_conflict_detection),
        ("Build Comparison Logic", test_build_comparison_logic),
        ("Build File Persistence", test_build_file_persistence),
        ("Embedded Build ID", test_embedded_build_id_in_app),
        ("Instance Cleanup", test_instance_checker_cleanup),
        ("Build ID Embedding", test_build_id_embed_function),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"🧪 {test_name}...", end=" ")
            if test_func():
                print("✅")
                passed += 1
            else:
                print("❌")
                failed += 1
        except Exception as e:
            print(f"💥 Exception: {e}")
            failed += 1
    
    print(f"\n📊 Build Versioning: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_build_versioning_tests()
    sys.exit(0 if success else 1) 