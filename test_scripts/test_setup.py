#!/usr/bin/env python3
"""
Test script for Rephrasely setup
Verifies that all dependencies are working and files are in the right place
"""

import os
import sys
import platform

def test_python_version():
    """Test if Python version is adequate"""
    print("🐍 Testing Python version...")
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"  ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ❌ Python {version.major}.{version.minor}.{version.micro} (need 3.8+)")
        return False

def test_virtual_env():
    """Test if virtual environment is activated"""
    print("\n🔧 Testing virtual environment...")
    
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("  ✅ Virtual environment is active")
        return True
    else:
        print("  ⚠️  No virtual environment detected")
        print("     Recommended: source .venv/bin/activate")
        return True  # Not a failure, just a recommendation

def test_dependencies():
    """Test if all required modules can be imported"""
    print("\n📦 Testing dependencies...")
    
    required_modules = [
        ('openai', 'openai'),
        ('pyperclip', 'pyperclip'),
        ('pynput', 'pynput'),
        ('pystray', 'pystray'),
        ('PIL', 'Pillow'),
        ('tkinter', 'tkinter (built-in)')
    ]
    
    all_good = True
    for module_name, display_name in required_modules:
        try:
            __import__(module_name)
            print(f"  ✅ {display_name}")
        except ImportError:
            print(f"  ❌ {display_name} - run: pip install {module_name if module_name != 'PIL' else 'Pillow'}")
            all_good = False
    
    return all_good

def test_app_files():
    """Test if source files exist"""
    print("\n📁 Testing source files...")
    
    files_to_check = [
        "../src/rephrasely.py",
        "../src/settings_ui.py", 
        "../src/cocoa_settings.py",
        "../requirements.txt"
    ]
    
    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} not found")
            all_exist = False
    
    return all_exist

def test_permissions():
    """Test macOS permissions (informational only)"""
    print("\n🔐 Testing system compatibility...")
    
    if platform.system() != 'Darwin':
        print("  ⚠️  Not running on macOS - app may not work correctly")
        return False
    
    print("  ✅ Running on macOS")
    print("  ℹ️  Accessibility permissions will be requested when app starts")
    return True

def test_clipboard():
    """Test clipboard functionality"""
    print("\n📋 Testing clipboard access...")
    
    try:
        import pyperclip
        
        # Test writing to clipboard
        test_text = "Rephrasely test"
        pyperclip.copy(test_text)
        
        # Test reading from clipboard
        clipboard_content = pyperclip.paste()
        
        if clipboard_content == test_text:
            print("  ✅ Clipboard read/write successful")
            return True
        else:
            print("  ❌ Clipboard content mismatch")
            return False
            
    except Exception as e:
        print(f"  ❌ Clipboard test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Rephrasely Setup Test")
    print("=" * 50)
    
    all_passed = True
    
    # Test Python version
    if not test_python_version():
        all_passed = False
    
    # Test virtual environment
    test_virtual_env()  # Not critical
    
    # Test dependencies
    if not test_dependencies():
        all_passed = False
    
    # Test source files
    if not test_app_files():
        all_passed = False
    
    # Test clipboard
    if not test_clipboard():
        print("  ⚠️  Clipboard may not work properly")
    
    # Test permissions (macOS only)
    test_permissions()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed!")
        print("\n✅ Your Rephrasely setup is ready!")
        print("\nNext steps:")
        print("1. Build the app: python scripts/build_app.py")
        print("2. Install: cp -r dist/app/Rephrasely.app /Applications/")
        print("3. Launch and configure API key in app settings")
        print("4. Test with Cmd+Shift+R")
    else:
        print("❌ Some tests failed!")
        print("\n🔧 Please fix the issues above and run the test again.")
        print("\nTo install missing dependencies:")
        print("pip install -r requirements.txt")
        
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 