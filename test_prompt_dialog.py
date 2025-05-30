#!/usr/bin/env python3
"""
Comprehensive test script for PromptDialog functionality
Tests save/cancel buttons, validation, and modal behavior
"""

import sys
import os
import traceback
from Foundation import *
from AppKit import *

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from cocoa_settings import PromptDialog, SettingsManager
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


class PromptDialogTests:
    """Test suite for PromptDialog"""
    
    def __init__(self):
        self.test_results = []
        self.current_test = ""
    
    def log_result(self, test_name, passed, message=""):
        """Log a test result"""
        status = "PASS" if passed else "FAIL"
        result = f"[{status}] {test_name}: {message}"
        print(result)
        self.test_results.append((test_name, passed, message))
    
    def test_dialog_creation(self):
        """Test 1: Dialog can be created without errors"""
        self.current_test = "Dialog Creation"
        try:
            # Test creating new prompt dialog
            dialog = PromptDialog.alloc().initWithPrompt_isEdit_(None, False)
            if dialog and dialog.window():
                self.log_result("Create New Dialog", True, 
                                "Dialog and window created successfully")
            else:
                self.log_result("Create New Dialog", False, 
                                "Failed to create dialog or window")
            
            # Test creating edit dialog
            test_prompt = {"name": "test", "text": "test prompt text"}
            edit_dialog = PromptDialog.alloc().initWithPrompt_isEdit_(
                test_prompt, True)
            if edit_dialog and edit_dialog.window():
                self.log_result("Create Edit Dialog", True, 
                                "Edit dialog created successfully")
                
                # Check if fields are populated
                name_value = str(edit_dialog.name_field.stringValue())
                text_value = str(edit_dialog.prompt_text_view.string())
                
                if name_value == "test" and text_value == "test prompt text":
                    self.log_result("Edit Dialog Population", True, 
                                    "Fields populated correctly")
                else:
                    self.log_result("Edit Dialog Population", False, 
                                    f"Fields not populated: name='{name_value}'"
                                    f", text='{text_value}'")
            else:
                self.log_result("Create Edit Dialog", False, 
                                "Failed to create edit dialog")
                
        except Exception as e:
            self.log_result("Dialog Creation", False, f"Exception: {e}")
    
    def test_button_targets(self):
        """Test 2: Buttons have correct targets and actions"""
        self.current_test = "Button Configuration"
        try:
            dialog = PromptDialog.alloc().initWithPrompt_isEdit_(None, False)
            
            # Check save button
            save_btn = dialog.save_btn
            if save_btn:
                target = save_btn.target()
                action = save_btn.action()
                
                if target == dialog and str(action) == "save:":
                    self.log_result("Save Button Target", True, 
                                    "Save button configured correctly")
                else:
                    self.log_result("Save Button Target", False, 
                                    f"Target: {target}, Action: {action}")
            else:
                self.log_result("Save Button Target", False, 
                                "Save button not found")
            
            # Check cancel button
            cancel_btn = dialog.cancel_btn
            if cancel_btn:
                target = cancel_btn.target()
                action = cancel_btn.action()
                
                if target == dialog and str(action) == "cancel:":
                    self.log_result("Cancel Button Target", True, 
                                    "Cancel button configured correctly")
                else:
                    self.log_result("Cancel Button Target", False, 
                                    f"Target: {target}, Action: {action}")
            else:
                self.log_result("Cancel Button Target", False, 
                                "Cancel button not found")
                
        except Exception as e:
            self.log_result("Button Configuration", False, f"Exception: {e}")
    
    def test_validation(self):
        """Test 3: Input validation works correctly"""
        self.current_test = "Input Validation"
        try:
            dialog = PromptDialog.alloc().initWithPrompt_isEdit_(None, False)
            
            # Test empty name validation
            dialog.name_field.setStringValue_("")
            dialog.prompt_text_view.setString_("Some text")
            
            # Simulate save button click
            result_received = [False]

            def test_callback(result):
                result_received[0] = result
            
            dialog.callback = test_callback
            dialog.save_(None)
            
            if not result_received[0]:
                self.log_result("Empty Name Validation", True, 
                                "Correctly rejected empty name")
            else:
                self.log_result("Empty Name Validation", False, 
                                "Failed to validate empty name")
            
            # Test empty text validation
            dialog.name_field.setStringValue_("test")
            dialog.prompt_text_view.setString_("")
            
            result_received[0] = False
            dialog.save_(None)
            
            if not result_received[0]:
                self.log_result("Empty Text Validation", True, 
                                "Correctly rejected empty text")
            else:
                self.log_result("Empty Text Validation", False, 
                                "Failed to validate empty text")
            
            # Test long name validation
            dialog.name_field.setStringValue_("this_is_too_long")
            dialog.prompt_text_view.setString_("Some text")
            
            result_received[0] = False
            dialog.save_(None)
            
            if not result_received[0]:
                self.log_result("Long Name Validation", True, 
                                "Correctly rejected long name")
            else:
                self.log_result("Long Name Validation", False, 
                                "Failed to validate long name")
            
            # Test valid input
            dialog.name_field.setStringValue_("valid")
            dialog.prompt_text_view.setString_("Valid prompt text")
            
            result_received[0] = None
            dialog.save_(None)
            
            if result_received[0] and isinstance(result_received[0], dict):
                expected_name = result_received[0]["name"] == "valid"
                expected_text = result_received[0]["text"] == "Valid prompt text"
                if expected_name and expected_text:
                    self.log_result("Valid Input", True, 
                                    "Valid input accepted correctly")
                else:
                    self.log_result("Valid Input", False, 
                                    f"Incorrect result: {result_received[0]}")
            else:
                self.log_result("Valid Input", False, 
                                "Valid input not accepted")
                
        except Exception as e:
            self.log_result("Input Validation", False, f"Exception: {e}")
    
    def test_cancel_functionality(self):
        """Test 4: Cancel button works correctly"""
        self.current_test = "Cancel Functionality"
        try:
            dialog = PromptDialog.alloc().initWithPrompt_isEdit_(None, False)
            
            # Fill in some data
            dialog.name_field.setStringValue_("test")
            dialog.prompt_text_view.setString_("test text")
            
            result_received = [None]

            def test_callback(result):
                result_received[0] = result
            
            dialog.callback = test_callback
            dialog.cancel_(None)
            
            if result_received[0] is None:
                self.log_result("Cancel Functionality", True, 
                                "Cancel correctly returns None")
            else:
                self.log_result("Cancel Functionality", False, 
                                f"Cancel returned: {result_received[0]}")
                
        except Exception as e:
            self.log_result("Cancel Functionality", False, f"Exception: {e}")
    
    def test_character_count(self):
        """Test 5: Character count functionality"""
        self.current_test = "Character Count"
        try:
            dialog = PromptDialog.alloc().initWithPrompt_isEdit_(None, False)
            
            # Test initial state
            dialog.updateCharCount()
            count_text = str(dialog.char_count_label.stringValue())
            if "0/10" in count_text:
                self.log_result("Initial Character Count", True, 
                                "Initial count is correct")
            else:
                self.log_result("Initial Character Count", False, 
                                f"Initial count: {count_text}")
            
            # Test with text
            dialog.name_field.setStringValue_("test")
            dialog.updateCharCount()
            count_text = str(dialog.char_count_label.stringValue())
            if "4/10" in count_text:
                self.log_result("Character Count Update", True, 
                                "Count updates correctly")
            else:
                self.log_result("Character Count Update", False, 
                                f"Count after 'test': {count_text}")
            
            # Test automatic truncation
            dialog.name_field.setStringValue_("this_is_way_too_long")
            dialog.validateName_(None)
            final_name = str(dialog.name_field.stringValue())
            if len(final_name) <= 10:
                self.log_result("Name Truncation", True, 
                                f"Name truncated to: '{final_name}'")
            else:
                self.log_result("Name Truncation", False, 
                                f"Name not truncated: '{final_name}'")
                
        except Exception as e:
            self.log_result("Character Count", False, f"Exception: {e}")
    
    def test_modal_behavior(self):
        """Test 6: Modal dialog behavior"""
        self.current_test = "Modal Behavior"
        try:
            dialog = PromptDialog.alloc().initWithPrompt_isEdit_(None, False)
            window = dialog.window()
            
            # Check window properties
            if window:
                level = window.level()
                # Use explicit constant value since NSModalPanelWindowLevel 
                # might not be imported
                modal_level = 8  # NSModalPanelWindowLevel value
                if level == modal_level:
                    self.log_result("Modal Window Level", True, 
                                    "Window has correct modal level")
                else:
                    self.log_result("Modal Window Level", False, 
                                    f"Window level: {level}")
                
                # Check if window has default button
                default_cell = window.defaultButtonCell()
                if default_cell and default_cell == dialog.save_btn.cell():
                    self.log_result("Default Button", True, 
                                    "Save button is default")
                else:
                    self.log_result("Default Button", False, 
                                    "Save button is not default")
            else:
                self.log_result("Modal Behavior", False, "No window available")
                
        except Exception as e:
            self.log_result("Modal Behavior", False, f"Exception: {e}")
    
    def run_all_tests(self):
        """Run all tests and print summary"""
        print("=" * 60)
        print("RUNNING PROMPT DIALOG TESTS")
        print("=" * 60)
        
        test_methods = [
            self.test_dialog_creation,
            self.test_button_targets,
            self.test_validation,
            self.test_cancel_functionality,
            self.test_character_count,
            self.test_modal_behavior
        ]
        
        for test_method in test_methods:
            print(f"\nRunning {test_method.__name__}...")
            try:
                test_method()
            except Exception as e:
                self.log_result(test_method.__name__, False, 
                                f"Test crashed: {e}")
                traceback.print_exc()
        
        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        for test_name, success, message in self.test_results:
            status = "✅" if success else "❌"
            print(f"{status} {test_name}: {message}")
        
        print(f"\nResults: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED!")
            return True
        else:
            print(f"❌ {total - passed} tests failed")
            return False


def run_integration_test():
    """Run a comprehensive integration test with the SettingsManager"""
    print("\n" + "=" * 60)
    print("RUNNING INTEGRATION TEST")
    print("=" * 60)
    
    try:
        # Create settings manager
        settings_manager = SettingsManager()
        
        # Test adding a prompt through the normal workflow
        print("Testing prompt addition through SettingsManager...")
        
        initial_count = len(settings_manager.get("prompts", []))
        print(f"Initial prompt count: {initial_count}")
        
        # Create a test prompt
        test_prompt = {
            "name": "testprompt",
            "text": "This is a test prompt for validation"
        }
        
        # Add it to settings
        current_prompts = settings_manager.get("prompts", [])
        current_prompts.append(test_prompt)
        settings_manager.settings["prompts"] = current_prompts
        
        # Save settings
        if settings_manager.save_settings(settings_manager.settings):
            print("✅ Successfully added test prompt to settings")
            
            # Reload settings to verify persistence
            new_settings_manager = SettingsManager()
            new_prompts = new_settings_manager.get("prompts", [])
            
            # Check if our test prompt is there
            found_test_prompt = any(p.get("name") == "testprompt" 
                                    for p in new_prompts)
            
            if found_test_prompt:
                print("✅ Test prompt persisted correctly")
                
                # Clean up - remove test prompt
                filtered_prompts = [p for p in new_prompts 
                                    if p.get("name") != "testprompt"]
                new_settings_manager.settings["prompts"] = filtered_prompts
                new_settings_manager.save_settings(
                    new_settings_manager.settings)
                print("✅ Test prompt cleaned up")
                
                return True
            else:
                print("❌ Test prompt not found after reload")
                return False
        else:
            print("❌ Failed to save settings")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Main test runner"""
    try:
        # Initialize NSApplication if needed
        try:
            app = NSApplication.sharedApplication()
            print(f"Initialized NSApplication: {type(app).__name__}")
        except Exception as e:
            print(f"Warning: Could not initialize NSApplication: {e}")
        
        # Run unit tests
        tester = PromptDialogTests()
        unit_tests_passed = tester.run_all_tests()
        
        # Run integration test
        integration_passed = run_integration_test()
        
        # Final results
        print("\n" + "=" * 60)
        print("FINAL TEST RESULTS")
        print("=" * 60)
        
        print(f"Unit Tests: {'✅ PASSED' if unit_tests_passed else '❌ FAILED'}")
        print(f"Integration Test: "
              f"{'✅ PASSED' if integration_passed else '❌ FAILED'}")
        
        if unit_tests_passed and integration_passed:
            print("\n🎉 ALL TESTS SUCCESSFUL! "
                  "Prompt dialog is working correctly.")
            sys.exit(0)
        else:
            print("\n❌ SOME TESTS FAILED! Please check the output above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Test runner crashed: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 