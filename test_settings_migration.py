#!/usr/bin/env python3
"""
Test settings migration from old format to new format
"""

import json
import os
import tempfile
from cocoa_settings import SettingsManager

def test_migration():
    """Test migration from old settings format to new format"""
    
    # Create temporary settings file with old format
    old_settings = {
        "prompts": {
            'rephrase': 'Please rephrase the following text to make it clearer and more professional:',
            'summarize': 'Please provide a concise summary of the following text:',
            'custom_mode': 'Custom prompt for testing migration'
        },
        "hotkey": "cmd+shift+r",
        "model": "gpt-4",
        "auto_paste": True
    }
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(old_settings, f, indent=2)
        temp_file = f.name
    
    try:
        print("📝 Testing settings migration...")
        print(f"Old format: {old_settings['prompts']}")
        
        # Load with SettingsManager (should migrate automatically)
        settings_manager = SettingsManager(temp_file)
        
        # Check if migration worked
        new_prompts = settings_manager.get("prompts", [])
        print(f"New format: {new_prompts}")
        
        # Verify structure
        if isinstance(new_prompts, list):
            print("✅ Successfully migrated to new list format")
            
            for prompt in new_prompts:
                if all(key in prompt for key in ["name", "text", "output_format"]):
                    print(f"  ✅ Prompt '{prompt['name']}': {prompt['text'][:50]}...")
                else:
                    print(f"  ❌ Invalid prompt structure: {prompt}")
        else:
            print("❌ Migration failed - still in old format")
        
        # Test saving in new format
        if settings_manager.save_settings(settings_manager.settings):
            print("✅ Successfully saved in new format")
        else:
            print("❌ Failed to save new format")
            
    finally:
        # Clean up
        os.unlink(temp_file)
        print("🧹 Cleaned up temporary file")

def test_new_format():
    """Test creating settings with new format from scratch"""
    print("\n📝 Testing new format from scratch...")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    try:
        # Create new settings manager (should use defaults)
        settings_manager = SettingsManager(temp_file)
        prompts = settings_manager.get("prompts", [])
        
        print(f"Default prompts: {len(prompts)} items")
        for prompt in prompts:
            print(f"  - {prompt['name']}: {prompt['output_format']} format")
        
        # Add a custom prompt
        new_prompt = {
            "name": "test_custom",
            "text": "This is a test custom prompt",
            "output_format": "images"
        }
        prompts.append(new_prompt)
        
        # Save
        settings_manager.settings["prompts"] = prompts
        if settings_manager.save_settings(settings_manager.settings):
            print("✅ Successfully added and saved custom prompt")
        else:
            print("❌ Failed to save custom prompt")
            
    finally:
        # Clean up
        os.unlink(temp_file)
        print("🧹 Cleaned up temporary file")

if __name__ == "__main__":
    test_migration()
    test_new_format()
    print("\n✅ All migration tests completed!") 