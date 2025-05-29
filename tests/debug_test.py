#!/usr/bin/env python3
"""
Debug test script for Potter dependencies
"""

print("🔍 Testing Potter dependencies...")

try:
    print("1. Testing six...")
    import six
    from six.moves import urllib
    print("   ✅ six and six.moves working")
except ImportError as e:
    print(f"   ❌ six error: {e}")

try:
    print("2. Testing pynput...")
    from pynput import keyboard
    print("   ✅ pynput working")
except ImportError as e:
    print(f"   ❌ pynput error: {e}")

try:
    print("3. Testing pyperclip...")
    import pyperclip
    pyperclip.copy("test")
    result = pyperclip.paste()
    print(f"   ✅ pyperclip working (test: '{result}')")
except Exception as e:
    print(f"   ❌ pyperclip error: {e}")

try:
    print("4. Testing openai...")
    import openai
    print("   ✅ openai working")
except ImportError as e:
    print(f"   ❌ openai error: {e}")

try:
    print("5. Testing pystray...")
    import pystray
    print("   ✅ pystray working")
except ImportError as e:
    print(f"   ❌ pystray error: {e}")

print("\n🎯 All dependency tests completed!")
print("If you see ❌ errors, run this with the virtual environment:")
print("   ./.venv/bin/python debug_test.py") 