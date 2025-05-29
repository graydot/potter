#!/usr/bin/env python3
"""
Potter Comprehensive Test Runner
Runs all test suites to verify app functionality before refactoring
"""

import sys
import os
import subprocess
import importlib.util

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def run_test_file(test_file_path):
    """Run a single test file and return results"""
    try:
        print(f"\n{'='*60}")
        print(f"Running {os.path.basename(test_file_path)}")
        print('='*60)
        
        # Import and run the test module
        spec = importlib.util.spec_from_file_location("test_module", test_file_path)
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)
        
        # Run the main function if it exists
        if hasattr(test_module, 'main'):
            success = test_module.main()
            return success
        else:
            print("❌ No main() function found in test file")
            return False
            
    except Exception as e:
        print(f"❌ Failed to run {test_file_path}: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_import_functionality():
    """Test that core modules can be imported"""
    print("\n🧪 Testing Core Module Imports")
    print("=" * 40)
    
    import_tests = [
        ("Potter Main Module", "import potter"),
        ("Settings Manager", "from cocoa_settings import SettingsManager"),
        ("Settings UI", "from cocoa_settings import show_settings"),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, import_statement in import_tests:
        try:
            exec(import_statement)
            print(f"✅ {test_name}: Import successful")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: Import failed - {e}")
            failed += 1
    
    print(f"\n📊 Import Results: {passed} passed, {failed} failed")
    return failed == 0


def check_critical_functionality():
    """Test critical app functionality that must work"""
    print("\n🧪 Testing Critical Functionality")
    print("=" * 40)
    
    tests_passed = 0
    tests_failed = 0
    
    try:
        # Test 1: Potter service can be instantiated
        print("Testing Potter service instantiation...")
        from potter import PotterService
        service = PotterService()
        print("✅ PotterService instantiation successful")
        tests_passed += 1
        
        # Test 2: Settings manager works
        print("Testing settings manager...")
        if service.settings_manager:
            hotkey = service.settings_manager.get("hotkey", "default")
            print(f"✅ Settings manager working (hotkey: {hotkey})")
            tests_passed += 1
        else:
            print("⚠️  Settings manager not available (expected in some environments)")
            
        # Test 3: Hotkey parsing works
        print("Testing hotkey parsing...")
        parsed = service.parse_hotkey("cmd+shift+a")
        if len(parsed) > 0:
            print("✅ Hotkey parsing successful")
            tests_passed += 1
        else:
            print("❌ Hotkey parsing failed")
            tests_failed += 1
            
        # Test 4: Permission checking doesn't crash
        print("Testing permission checking...")
        try:
            permissions = service.get_permission_status()
            print(f"✅ Permission checking successful (accessibility: {permissions.get('accessibility', 'unknown')})")
            tests_passed += 1
        except Exception as e:
            print(f"❌ Permission checking failed: {e}")
            tests_failed += 1
            
        # Test 5: Mode switching works
        print("Testing mode switching...")
        original_mode = service.current_prompt
        service.change_mode("formal")
        if service.current_prompt == "formal":
            service.change_mode(original_mode)  # Restore
            print("✅ Mode switching successful")
            tests_passed += 1
        else:
            print("❌ Mode switching failed")
            tests_failed += 1
            
    except Exception as e:
        print(f"❌ Critical functionality test failed: {e}")
        tests_failed += 1
    
    print(f"\n📊 Critical Tests: {tests_passed} passed, {tests_failed} failed")
    return tests_failed == 0


def main():
    """Run comprehensive test suite"""
    print("🧪 Potter Comprehensive Test Suite")
    print("=" * 50)
    print("Testing all functionality before refactoring...")
    
    # Step 1: Check imports
    imports_ok = check_import_functionality()
    
    # Step 2: Check critical functionality
    critical_ok = check_critical_functionality()
    
    # Step 3: Run detailed test suites
    test_files = [
        "tests/test_app_integration.py",
        "tests/test_ui_components.py"
    ]
    
    suite_results = []
    for test_file in test_files:
        if os.path.exists(test_file):
            success = run_test_file(test_file)
            suite_results.append((test_file, success))
        else:
            print(f"⚠️  Test file not found: {test_file}")
            suite_results.append((test_file, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("COMPREHENSIVE TEST SUMMARY")
    print('='*60)
    
    print(f"📦 Core Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"🔧 Critical Functions: {'✅ PASS' if critical_ok else '❌ FAIL'}")
    
    suite_passes = 0
    suite_failures = 0
    
    for test_file, success in suite_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"🧪 {os.path.basename(test_file)}: {status}")
        if success:
            suite_passes += 1
        else:
            suite_failures += 1
    
    print(f"\n📊 Overall Results:")
    print(f"   Test Suites: {suite_passes} passed, {suite_failures} failed")
    
    # Determine overall status
    all_passed = imports_ok and critical_ok and suite_failures == 0
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ App is ready for refactoring")
        print("\nFunctionality Verified:")
        print("  ✅ Settings UI opens when API key missing")
        print("  ✅ Settings UI opens when accessibility permission missing") 
        print("  ✅ Settings dialog cancel/apply buttons work")
        print("  ✅ Prompt editing and validation works")
        print("  ✅ Hotkey detection and processing works")
        print("  ✅ Mode switching works")
        print("  ✅ Notification toggle works")
        print("  ✅ Text processing flow works")
        print("  ✅ Permission checking works")
        print("  ✅ First launch detection works")
        
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("❌ Review failures before refactoring")
        print("\nFailures found in:")
        if not imports_ok:
            print("  ❌ Core module imports")
        if not critical_ok:
            print("  ❌ Critical functionality")
        for test_file, success in suite_results:
            if not success:
                print(f"  ❌ {os.path.basename(test_file)}")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 