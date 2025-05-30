#!/usr/bin/env python3
"""
Simple Test Runner Alias
Runs the auto-discovery test runner from project root
"""

import sys
import os
import subprocess

def main():
    """Run the auto-discovery test runner"""
    test_runner_path = os.path.join(os.path.dirname(__file__), 'tests', 'auto_test_runner.py')
    
    if not os.path.exists(test_runner_path):
        print("❌ Test runner not found at:", test_runner_path)
        return False
    
    # Run the test runner
    result = subprocess.run([sys.executable, test_runner_path], 
                          cwd=os.path.dirname(__file__))
    
    return result.returncode == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 