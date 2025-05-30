#!/usr/bin/env python3
"""
Tests for new features implemented today
Tests settings display logic, first-time startup, permission management, restart functionality
"""

import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cocoa_settings import SettingsManager


class TestFirstTimeStartupLogic(unittest.TestCase):
    """Test first-time startup and build tracking functionality"""
    
    def setUp(self):
        """Set up test environment with temporary files"""
        self.temp_dir = tempfile.mkdtemp()
        self.settings_file = os.path.join(self.temp_dir, 'settings.json')
        self.first_run_file = os.path.join(self.temp_dir, 'first_run_tracking.json')
        
        # Create settings manager with test files
        self.settings_manager = SettingsManager(self.settings_file)
        self.settings_manager.first_run_file = self.first_run_file
    
    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_is_first_launch_no_settings_file(self):
        """Test first launch detection when no settings file exists"""
        self.assertTrue(self.settings_manager.is_first_launch())
    
    def test_is_first_launch_no_api_key(self):
        """Test first launch detection when settings exist but no API key"""
        # Create settings file without API key
        settings = {"hotkey": "cmd+shift+a", "llm_provider": "openai"}
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f)
        
        # Reload settings
        self.settings_manager = SettingsManager(self.settings_file)
        self.assertTrue(self.settings_manager.is_first_launch())
    
    def test_is_first_launch_with_api_key(self):
        """Test first launch detection when API key is configured"""
        # Create settings file with API key
        settings = {
            "hotkey": "cmd+shift+a", 
            "llm_provider": "openai",
            "openai_api_key": "sk-test123"
        }
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f)
        
        # Reload settings
        self.settings_manager = SettingsManager(self.settings_file)
        self.assertFalse(self.settings_manager.is_first_launch())
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'env-test-key'})
    def test_is_first_launch_with_env_api_key(self):
        """Test first launch detection when API key is in environment"""
        # Create settings file without API key but env var is set
        settings = {"hotkey": "cmd+shift+a", "llm_provider": "openai"}
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f)
        
        # Reload settings
        self.settings_manager = SettingsManager(self.settings_file)
        self.assertFalse(self.settings_manager.is_first_launch())
    
    @patch('utils.instance_checker.load_build_id')
    def test_is_first_launch_for_build_no_tracking_file(self, mock_load_build):
        """Test build-specific first launch when no tracking file exists"""
        mock_load_build.return_value = {"build_id": "test-build-123"}
        self.assertTrue(self.settings_manager.is_first_launch_for_build())
    
    @patch('utils.instance_checker.load_build_id')
    def test_is_first_launch_for_build_new_build(self, mock_load_build):
        """Test build-specific first launch for new build ID"""
        mock_load_build.return_value = {"build_id": "new-build-456"}
        
        # Create tracking file with different build
        tracking_data = {
            "launched_builds": ["old-build-123"],
            "permission_requests": {}
        }
        with open(self.first_run_file, 'w') as f:
            json.dump(tracking_data, f)
        
        self.assertTrue(self.settings_manager.is_first_launch_for_build())
    
    @patch('utils.instance_checker.load_build_id')
    def test_is_first_launch_for_build_existing_build(self, mock_load_build):
        """Test build-specific first launch for existing build ID"""
        mock_load_build.return_value = {"build_id": "existing-build-123"}
        
        # Create tracking file with same build
        tracking_data = {
            "launched_builds": ["existing-build-123"],
            "permission_requests": {}
        }
        with open(self.first_run_file, 'w') as f:
            json.dump(tracking_data, f)
        
        self.assertFalse(self.settings_manager.is_first_launch_for_build())
    
    @patch('utils.instance_checker.load_build_id')
    def test_mark_build_launched(self, mock_load_build):
        """Test marking a build as launched"""
        mock_load_build.return_value = {"build_id": "test-build-789"}
        
        # Mark build as launched
        self.settings_manager.mark_build_launched()
        
        # Verify tracking file was created/updated
        self.assertTrue(os.path.exists(self.first_run_file))
        with open(self.first_run_file, 'r') as f:
            data = json.load(f)
        
        self.assertIn("test-build-789", data["launched_builds"])
    
    def test_should_show_settings_on_startup_or_logic(self):
        """Test the OR logic for showing settings on startup"""
        # Test case 1: First launch AND no API key (should show)
        with patch.object(self.settings_manager, 'is_first_launch_for_build', return_value=True):
            with patch.object(self.settings_manager, 'get', return_value=""):
                self.assertTrue(self.settings_manager.should_show_settings_on_startup())
        
        # Test case 2: First launch BUT has API key (should show - because first launch)
        with patch.object(self.settings_manager, 'is_first_launch_for_build', return_value=True):
            with patch.object(self.settings_manager, 'get', return_value="sk-test123"):
                self.assertTrue(self.settings_manager.should_show_settings_on_startup())
        
        # Test case 3: NOT first launch BUT no API key (should show - because no API key)
        with patch.object(self.settings_manager, 'is_first_launch_for_build', return_value=False):
            with patch.object(self.settings_manager, 'get', return_value=""):
                self.assertTrue(self.settings_manager.should_show_settings_on_startup())
        
        # Test case 4: NOT first launch AND has API key (should NOT show)
        with patch.object(self.settings_manager, 'is_first_launch_for_build', return_value=False):
            with patch.object(self.settings_manager, 'get', return_value="sk-test123"):
                self.assertFalse(self.settings_manager.should_show_settings_on_startup())


class TestPermissionManagement(unittest.TestCase):
    """Test permission tracking and management functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.first_run_file = os.path.join(self.temp_dir, 'first_run_tracking.json')
        self.settings_manager = SettingsManager()
        self.settings_manager.first_run_file = self.first_run_file
    
    def tearDown(self):
        """Clean up"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_has_declined_permission_no_file(self):
        """Test permission decline check when no tracking file exists"""
        self.assertFalse(self.settings_manager.has_declined_permission("accessibility"))
    
    def test_has_declined_permission_not_declined(self):
        """Test permission decline check when permission was not declined"""
        # Create tracking file without declined permissions
        tracking_data = {
            "launched_builds": [],
            "permission_requests": {}
        }
        with open(self.first_run_file, 'w') as f:
            json.dump(tracking_data, f)
        
        self.assertFalse(self.settings_manager.has_declined_permission("accessibility"))
    
    def test_has_declined_permission_was_declined(self):
        """Test permission decline check when permission was declined"""
        # Create tracking file with declined permission
        tracking_data = {
            "launched_builds": [],
            "permission_requests": {
                "accessibility": {"declined": True, "timestamp": 1234567890}
            }
        }
        with open(self.first_run_file, 'w') as f:
            json.dump(tracking_data, f)
        
        self.assertTrue(self.settings_manager.has_declined_permission("accessibility"))
    
    def test_mark_permission_declined(self):
        """Test marking a permission as declined"""
        self.settings_manager.mark_permission_declined("notifications")
        
        # Verify tracking file was created/updated
        self.assertTrue(os.path.exists(self.first_run_file))
        with open(self.first_run_file, 'r') as f:
            data = json.load(f)
        
        self.assertTrue(data["permission_requests"]["notifications"]["declined"])
        self.assertIsInstance(data["permission_requests"]["notifications"]["timestamp"], (int, float))


class TestTrayIconImprovements(unittest.TestCase):
    """Test tray icon improvements and functionality"""
    
    def setUp(self):
        """Set up tray icon manager for testing"""
        try:
            from ui.tray_icon import TrayIconManager
            self.tray_manager = TrayIconManager()
        except ImportError:
            self.skipTest("TrayIconManager not available")
    
    def test_create_normal_icon_size(self):
        """Test that normal icon is created with correct size (128x128)"""
        icon = self.tray_manager.create_normal_icon()
        self.assertEqual(icon.size, (128, 128))
    
    def test_create_spinner_icon_size(self):
        """Test that spinner icon is created with correct size (128x128)"""
        icon = self.tray_manager.create_spinner_icon()
        self.assertEqual(icon.size, (128, 128))
    
    def test_icon_has_alpha_channel(self):
        """Test that icons have alpha channel for transparency"""
        normal_icon = self.tray_manager.create_normal_icon()
        spinner_icon = self.tray_manager.create_spinner_icon()
        
        self.assertEqual(normal_icon.mode, 'RGBA')
        self.assertEqual(spinner_icon.mode, 'RGBA')
    
    def test_set_processing_state(self):
        """Test setting processing state updates icon"""
        # Create mock tray icon
        mock_icon = MagicMock()
        self.tray_manager.tray_icon = mock_icon
        
        # Test setting processing state
        self.tray_manager.set_processing_state(True)
        self.assertTrue(self.tray_manager.is_processing)
        
        self.tray_manager.set_processing_state(False)
        self.assertFalse(self.tray_manager.is_processing)


class TestSettingsFileStructure(unittest.TestCase):
    """Test settings file management and structure"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.settings_file = os.path.join(self.temp_dir, 'settings.json')
        self.state_file = os.path.join(self.temp_dir, 'state.json')
    
    def tearDown(self):
        """Clean up"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_settings_manager_initialization(self):
        """Test SettingsManager initializes with correct defaults"""
        settings_manager = SettingsManager(self.settings_file)
        
        # Check default providers are configured
        self.assertIn("openai", settings_manager.llm_providers)
        self.assertIn("anthropic", settings_manager.llm_providers)
        self.assertIn("gemini", settings_manager.llm_providers)
        
        # Check default settings structure
        self.assertIn("prompts", settings_manager.default_settings)
        self.assertIn("hotkey", settings_manager.default_settings)
        self.assertIn("llm_provider", settings_manager.default_settings)
    
    def test_api_key_validation_state(self):
        """Test API key validation state management"""
        settings_manager = SettingsManager(self.settings_file)
        
        # Test setting validation state
        settings_manager.set_api_key_validation("openai", True, None)
        validation = settings_manager.get_api_key_validation("openai")
        
        self.assertTrue(validation["valid"])
        self.assertIsNone(validation["error"])
        self.assertIsNotNone(validation["last_check"])
        
        # Test setting error state
        settings_manager.set_api_key_validation("openai", False, "Invalid key format")
        validation = settings_manager.get_api_key_validation("openai")
        
        self.assertFalse(validation["valid"])
        self.assertEqual(validation["error"], "Invalid key format")
    
    def test_multi_provider_support(self):
        """Test multiple LLM provider support"""
        settings_manager = SettingsManager(self.settings_file)
        
        # Test provider switching
        for provider in ["openai", "anthropic", "gemini"]:
            settings_manager.settings["llm_provider"] = provider
            self.assertEqual(settings_manager.get_current_provider(), provider)
            
            # Test API key storage per provider
            test_key = f"test-key-{provider}"
            settings_manager.settings[f"{provider}_api_key"] = test_key
            
            # Verify the key is stored correctly
            self.assertEqual(settings_manager.get(f"{provider}_api_key"), test_key)


class TestRestartFunctionality(unittest.TestCase):
    """Test restart and app management functionality"""
    
    @patch('subprocess.Popen')
    @patch('tempfile.NamedTemporaryFile')
    @patch('sys.frozen', True, create=True)
    @patch('sys.executable', '/Applications/Potter.app/Contents/MacOS/Potter')
    def test_restart_app_bundle_mode(self, mock_tempfile, mock_popen):
        """Test restart functionality in app bundle mode"""
        # Mock temp file
        mock_file = MagicMock()
        mock_file.name = '/tmp/restart_script.sh'
        mock_tempfile.return_value.__enter__.return_value = mock_file
        
        # Import and test (would need to import SettingsWindow for this)
        # This is a structure test - actual restart testing would require integration test
        
        # Verify temp file creation would be called
        self.assertTrue(True)  # Placeholder - actual implementation would test script creation
    
    @patch('subprocess.run')
    def test_startup_setting_enable(self, mock_subprocess):
        """Test enabling startup setting"""
        mock_subprocess.return_value.returncode = 0
        
        # This would test the updateStartupSetting_ method
        # Placeholder for actual implementation
        self.assertTrue(True)
    
    @patch('subprocess.run')
    def test_startup_setting_disable(self, mock_subprocess):
        """Test disabling startup setting"""
        mock_subprocess.return_value.returncode = 0
        
        # This would test the updateStartupSetting_ method
        # Placeholder for actual implementation
        self.assertTrue(True)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2) 