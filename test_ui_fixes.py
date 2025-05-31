#!/usr/bin/env python3
"""
Test script to demonstrate UI fixes:
1. Dialog icons based on theme
2. General tab alignment improvements
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from settings.settings_manager import SettingsManager
from cocoa_settings import show_settings


def main():
    """Test the UI fixes"""
    print("🎨 Testing UI Fixes")
    print("=" * 50)
    
    # Initialize settings manager
    settings_manager = SettingsManager()
    
    print("✅ Dialog Icons:")
    print("  - Dialogs now use light/dark icons based on current theme")
    print("  - Edit prompt dialog has theme-appropriate icon")
    print("  - Clear logs confirmation dialog has theme-appropriate icon")
    print()
    
    print("✅ General Tab Alignment:")
    print("  - Switches (notifications, startup) aligned to right edge")
    print("  - Buttons (Verify & Save, Reset, Open Settings) aligned to right edge")
    print("  - Right edges aligned at x=620 for consistent layout")
    print()
    
    print("🖼️  Opening Settings Window...")
    print("Navigate to General tab to see alignment improvements")
    print("Try adding/editing prompts to see dialog icons")
    
    # Show settings window
    def on_settings_changed():
        print("Settings changed!")
    
    show_settings(settings_manager, on_settings_changed)


if __name__ == "__main__":
    main() 