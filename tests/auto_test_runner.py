#!/usr/bin/env python3
"""
Auto Test Runner - Discovers and runs all test files
Now includes enhanced settings tests
"""

import os
import sys
import importlib.util
import traceback

def discover_test_files():
    """Discover all test_*.py files in the tests directory"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_files = []
    
    for file in os.listdir(test_dir):
        if file.startswith('test_') and file.endswith('.py') and file != 'test_template.py':
            test_files.append(os.path.join(test_dir, file))
    
    return sorted(test_files)

def load_and_run_test(test_file):
    """Load a test file and run its main test function"""
    print(f"\n{'='*60}")
    print(f"Running tests from: {os.path.basename(test_file)}")
    print(f"{'='*60}")
    
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location("test_module", test_file)
        test_module = importlib.util.module_from_spec(spec)
        
        # Add to sys.modules to handle imports
        module_name = f"test_module_{os.path.basename(test_file)}"
        sys.modules[module_name] = test_module
        spec.loader.exec_module(test_module)
        
        # Try to find and run the test function
        test_functions = [
            'run_enhanced_settings_tests',  # New enhanced settings tests
            'run_build_versioning_tests',   # Build versioning tests
            'run_real_integration_tests',   # Real integration tests
            'run_setup_tests',              # Setup tests
            'run_tests',                    # Generic test runner
            'main'                          # Main function fallback
        ]
        
        executed = False
        for func_name in test_functions:
            if hasattr(test_module, func_name):
                print(f"🚀 Executing {func_name}...")
                test_func = getattr(test_module, func_name)
                result = test_func()
                
                # Handle different return types
                if result is None:
                    print("✅ Test completed (no return value)")
                    executed = True
                    return True
                elif isinstance(result, bool):
                    if result:
                        print("✅ All tests in this file passed")
                    else:
                        print("❌ Some tests in this file failed")
                    executed = True
                    return result
                else:
                    print(f"✅ Test completed with result: {result}")
                    executed = True
                    return True
        
        if not executed:
            print("⚠️  No recognizable test function found")
            available_functions = [name for name in dir(test_module) 
                                 if callable(getattr(test_module, name)) 
                                 and not name.startswith('_')]
            print(f"Available functions: {available_functions}")
            return False
            
    except Exception as e:
        print(f"❌ Error running tests from {test_file}:")
        print(f"   {str(e)}")
        traceback.print_exc()
        return False

def run_all_tests():
    """Discover and run all tests"""
    print("🧪 Auto Test Runner - Discovering and Running All Tests")
    print("=" * 70)
    
    test_files = discover_test_files()
    
    if not test_files:
        print("❌ No test files found!")
        return False
    
    print(f"📁 Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"   • {os.path.basename(test_file)}")
    
    results = []
    
    for test_file in test_files:
        try:
            result = load_and_run_test(test_file)
            results.append((os.path.basename(test_file), result))
        except Exception as e:
            print(f"❌ Failed to run {test_file}: {e}")
            results.append((os.path.basename(test_file), False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for filename, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<10} {filename}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 70)
    print(f"Total: {len(results)} test files | Passed: {passed} | Failed: {failed}")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"💥 {failed} test file(s) failed!")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 