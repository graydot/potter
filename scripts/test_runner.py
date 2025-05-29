#!/usr/bin/env python3
"""
Potter Test Runner
Comprehensive test suite for Potter application.
"""

import sys
import os
import subprocess
import ast

def print_section(title):
    """Print a test section header"""
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

def run_command(cmd, description):
    """Run a command and return True if successful"""
    print(f"\n🔍 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print(f"✅ {description} passed")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} failed")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

def check_python_syntax():
    """Check Python syntax for all Python files"""
    print_section("PYTHON SYNTAX CHECK")
    
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories and build directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['build', 'dist', '__pycache__']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    if not python_files:
        print("No Python files found")
        return True
    
    all_passed = True
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to parse the file
            ast.parse(content, filename=file_path)
            print(f"✅ {file_path}")
            
        except SyntaxError as e:
            print(f"❌ {file_path}: Syntax error at line {e.lineno}: {e.msg}")
            all_passed = False
        except Exception as e:
            print(f"❌ {file_path}: Error reading file: {e}")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print("🧪 Potter Test Runner")
    print(f"Running in: {os.getcwd()}")
    
    # Track overall success
    all_tests_passed = True
    
    # 1. Python syntax check
    if not check_python_syntax():
        all_tests_passed = False
    
    # 2. Run setup test
    print_section("SETUP TEST")
    if not run_command("python test_scripts/test_setup.py", "Setup test"):
        all_tests_passed = False
    
    # 3. Run debug test
    print_section("DEBUG TEST")
    if not run_command("python test_scripts/debug_test.py", "Debug test"):
        all_tests_passed = False
    
    # 4. Run UI test (non-interactive)
    print_section("UI TEST")
    if not run_command("python test_scripts/test_ui.py --non-interactive", "UI test"):
        all_tests_passed = False
    
    # Final result
    print_section("TEST RESULTS")
    if all_tests_passed:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 