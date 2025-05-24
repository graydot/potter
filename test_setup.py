#!/usr/bin/env python3
"""
Test script for Rephrasely setup
Verifies that all dependencies are working and API key is configured
"""

import os
import sys
from dotenv import load_dotenv

def test_imports():
    """Test if all required modules can be imported"""
    print("📦 Testing imports...")
    
    try:
        import openai
        print("  ✅ openai")
    except ImportError:
        print("  ❌ openai - run: pip install openai")
        return False
    
    try:
        import pyperclip
        print("  ✅ pyperclip")
    except ImportError:
        print("  ❌ pyperclip - run: pip install pyperclip")
        return False
    
    try:
        import pynput
        print("  ✅ pynput")
    except ImportError:
        print("  ❌ pynput - run: pip install pynput")
        return False
    
    try:
        import pystray
        print("  ✅ pystray")
    except ImportError:
        print("  ❌ pystray - run: pip install pystray")
        return False
    
    try:
        from PIL import Image
        print("  ✅ PIL (Pillow)")
    except ImportError:
        print("  ❌ PIL (Pillow) - run: pip install Pillow")
        return False
    
    return True

def test_env_file():
    """Test if .env file exists and contains API key"""
    print("\n🔑 Testing environment configuration...")
    
    if not os.path.exists('.env'):
        print("  ❌ .env file not found")
        print("     Create .env file with: OPENAI_API_KEY=your_api_key")
        return False
    
    print("  ✅ .env file exists")
    
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("  ❌ OPENAI_API_KEY not set in .env file")
        return False
    
    if api_key == 'your_openai_api_key_here':
        print("  ❌ OPENAI_API_KEY still has placeholder value")
        print("     Please set your actual OpenAI API key in .env file")
        return False
    
    if not api_key.startswith('sk-'):
        print("  ⚠️  API key doesn't start with 'sk-' (may be invalid)")
        print("     Please verify your OpenAI API key")
        return False
    
    print(f"  ✅ API key configured (starts with {api_key[:10]}...)")
    return True

def test_openai_connection():
    """Test connection to OpenAI API"""
    print("\n🌐 Testing OpenAI API connection...")
    
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("  ❌ No API key to test")
        return False
    
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        # Test with a minimal request
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'test'"}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        print(f"  ✅ API connection successful (response: '{result}')")
        return True
        
    except Exception as e:
        print(f"  ❌ API connection failed: {e}")
        print("     Check your API key and internet connection")
        return False

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
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test environment
    if not test_env_file():
        all_passed = False
    
    # Test OpenAI connection (only if env is OK)
    if all_passed:
        if not test_openai_connection():
            all_passed = False
    
    # Test clipboard
    if not test_clipboard():
        all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 All tests passed! Rephrasely should work correctly.")
        print("\nNext steps:")
        print("1. Run: python3 rephrasely.py")
        print("2. Grant accessibility permissions when prompted")
        print("3. Test with Cmd+Shift+R")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\nFor help:")
        print("- Check README.md for detailed setup instructions")
        print("- Run: python3 setup.py")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 