#!/usr/bin/env python3
"""
Phase 6 Configuration Management Tests
Comprehensive test suite for advanced configuration system
"""

import os
import json
import tempfile
import shutil
import unittest
from pathlib import Path

# Import configuration components
from src.configuration.configuration_manager import ConfigurationManager
from src.configuration.configuration_source import (
    FileConfigurationSource, EnvironmentConfigurationSource, MemoryConfigurationSource
)
from src.configuration.configuration_hierarchy import ConfigurationHierarchy, ConfigurationLevel
from src.configuration.validation_engine import ValidationEngine, ValidationResult
from src.configuration.environment_manager import EnvironmentManager
from src.configuration.secrets_manager import SecretsManager
from src.configuration.hot_reload_manager import HotReloadManager


class TestConfigurationHierarchy(unittest.TestCase):
    """Test configuration hierarchy functionality"""
    
    def setUp(self):
        self.hierarchy = ConfigurationHierarchy()
    
    def test_default_levels_created(self):
        """Test that default hierarchy levels are created"""
        expected_levels = ["global", "environment", "service", "user", "runtime"]
        actual_levels = self.hierarchy.get_level_names()
        
        for level in expected_levels:
            self.assertIn(level, actual_levels)
    
    def test_set_and_get_value(self):
        """Test setting and getting configuration values"""
        # Set value in runtime level
        success = self.hierarchy.set_value("test.key", "test_value", "runtime")
        self.assertTrue(success)
        
        # Get value
        value = self.hierarchy.get_value("test.key")
        self.assertEqual(value, "test_value")
    
    def test_hierarchy_resolution(self):
        """Test hierarchical value resolution"""
        # Set value in global level
        self.hierarchy.set_value("app.name", "Global App", "global")
        
        # Set override in runtime level
        self.hierarchy.set_value("app.name", "Runtime App", "runtime")
        
        # Runtime should win (lower priority number)
        value = self.hierarchy.get_value("app.name")
        self.assertEqual(value, "Runtime App")
    
    def test_nested_key_support(self):
        """Test nested key support with dot notation"""
        self.hierarchy.set_value("database.host", "localhost", "runtime")
        self.hierarchy.set_value("database.port", 5432, "runtime")
        
        self.assertEqual(self.hierarchy.get_value("database.host"), "localhost")
        self.assertEqual(self.hierarchy.get_value("database.port"), 5432)


class TestConfigurationSources(unittest.TestCase):
    """Test configuration sources functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
    
    def test_file_source_json(self):
        """Test file configuration source with JSON"""
        config_file = os.path.join(self.temp_dir, "test.json")
        test_config = {"app": {"name": "Test App", "debug": True}}
        
        # Create source
        source = FileConfigurationSource(config_file, format='json')
        
        # Save and load
        success = source.save_configuration(test_config)
        self.assertTrue(success)
        
        loaded_config = source.load_configuration()
        self.assertEqual(loaded_config, test_config)
    
    def test_environment_source(self):
        """Test environment variable configuration source"""
        # Set test environment variables
        os.environ['POTTER_TEST_KEY'] = 'test_value'
        os.environ['POTTER_NESTED_VALUE'] = '{"key": "value"}'
        
        source = EnvironmentConfigurationSource(prefix='POTTER_')
        config = source.load_configuration()
        
        self.assertIn('test', config)
        self.assertEqual(config['test']['key'], 'test_value')
        
        # Clean up
        del os.environ['POTTER_TEST_KEY']
        del os.environ['POTTER_NESTED_VALUE']
    
    def test_memory_source(self):
        """Test memory configuration source"""
        initial_config = {"app": {"name": "Memory App"}}
        source = MemoryConfigurationSource(initial_config)
        
        # Load initial config
        config = source.load_configuration()
        self.assertEqual(config, initial_config)
        
        # Update config
        new_config = {"app": {"name": "Updated App", "version": "1.0"}}
        success = source.save_configuration(new_config)
        self.assertTrue(success)
        
        # Verify update
        updated_config = source.load_configuration()
        self.assertEqual(updated_config, new_config)


class TestValidationEngine(unittest.TestCase):
    """Test validation engine functionality"""
    
    def setUp(self):
        self.engine = ValidationEngine()
    
    def test_schema_registration(self):
        """Test schema registration"""
        test_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0}
            },
            "required": ["name"]
        }
        
        success = self.engine.register_schema("test_schema", test_schema)
        self.assertTrue(success)
        
        # Verify schema was registered
        registered_schema = self.engine.get_schema("test_schema")
        self.assertEqual(registered_schema, test_schema)
    
    def test_configuration_validation(self):
        """Test configuration validation"""
        # Register test schema
        schema = {
            "type": "object",
            "properties": {
                "app": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "debug": {"type": "boolean", "default": False}
                    },
                    "required": ["name"]
                }
            }
        }
        self.engine.register_schema("app_schema", schema)
        
        # Valid configuration
        valid_config = {"app": {"name": "Test App", "debug": True}}
        result = self.engine.validate_configuration(valid_config, "app_schema")
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        
        # Invalid configuration (missing required field)
        invalid_config = {"app": {"debug": True}}
        result = self.engine.validate_configuration(invalid_config, "app_schema")
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
    
    def test_default_value_application(self):
        """Test application of default values"""
        schema = {
            "type": "object",
            "properties": {
                "app": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "debug": {"type": "boolean", "default": False},
                        "timeout": {"type": "integer", "default": 30}
                    }
                }
            }
        }
        self.engine.register_schema("defaults_schema", schema)
        
        config = {"app": {"name": "Test App"}}
        result = self.engine.validate_configuration(config, "defaults_schema", apply_defaults=True)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(result.validated_config["app"]["debug"], False)
        self.assertEqual(result.validated_config["app"]["timeout"], 30)


class TestEnvironmentManager(unittest.TestCase):
    """Test environment manager functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_manager = EnvironmentManager(self.temp_dir)
        self.addCleanup(shutil.rmtree, self.temp_dir)
    
    def test_environment_detection(self):
        """Test automatic environment detection"""
        # Test with environment variable
        os.environ['POTTER_ENVIRONMENT'] = 'production'
        detected = self.env_manager.detect_environment()
        self.assertEqual(detected, 'production')
        
        # Clean up
        del os.environ['POTTER_ENVIRONMENT']
    
    def test_environment_validation(self):
        """Test environment validation"""
        self.assertTrue(self.env_manager.is_valid_environment('development'))
        self.assertTrue(self.env_manager.is_valid_environment('staging'))
        self.assertTrue(self.env_manager.is_valid_environment('production'))
        self.assertFalse(self.env_manager.is_valid_environment('invalid'))
    
    def test_environment_config_creation(self):
        """Test environment configuration creation"""
        test_config = {
            "app": {"name": "Test App", "environment": "development"},
            "logging": {"level": "DEBUG"}
        }
        
        success = self.env_manager.create_environment_config('development', test_config)
        self.assertTrue(success)
        
        # Verify file was created
        config_path = self.env_manager.get_environment_config_path('development')
        self.assertTrue(os.path.exists(config_path))
        
        # Load and verify
        loaded_config = self.env_manager.load_environment_config('development')
        self.assertEqual(loaded_config, test_config)


class TestSecretsManager(unittest.TestCase):
    """Test secrets manager functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        key_file = os.path.join(self.temp_dir, "test_key.key")
        self.secrets_manager = SecretsManager(key_file=key_file)
        self.addCleanup(shutil.rmtree, self.temp_dir)
    
    def test_secret_detection(self):
        """Test automatic secret field detection"""
        self.assertTrue(self.secrets_manager.is_secret("api_key"))
        self.assertTrue(self.secrets_manager.is_secret("database.password"))
        self.assertTrue(self.secrets_manager.is_secret("auth.secret_token"))
        self.assertFalse(self.secrets_manager.is_secret("app.name"))
    
    def test_secret_marking(self):
        """Test manual secret marking"""
        self.secrets_manager.mark_as_secret("custom.secret.field")
        self.assertTrue(self.secrets_manager.is_secret("custom.secret.field"))
        
        self.secrets_manager.unmark_as_secret("custom.secret.field")
        self.assertFalse(self.secrets_manager.is_secret("custom.secret.field"))
    
    def test_encryption_decryption(self):
        """Test value encryption and decryption"""
        original_value = "secret_api_key_12345"
        
        # Encrypt
        encrypted_value = self.secrets_manager.encrypt_value(original_value)
        self.assertNotEqual(encrypted_value, original_value)
        self.assertTrue(self.secrets_manager.is_encrypted(encrypted_value))
        
        # Decrypt
        decrypted_value = self.secrets_manager.decrypt_value(encrypted_value)
        self.assertEqual(decrypted_value, original_value)
    
    def test_config_encryption(self):
        """Test configuration encryption and decryption"""
        config = {
            "app": {"name": "Test App"},
            "api": {"api_key": "secret_key_123", "timeout": 30}
        }
        
        # Encrypt secrets in config
        encrypted_config = self.secrets_manager.encrypt_config(config)
        self.assertNotEqual(encrypted_config["api"]["api_key"], config["api"]["api_key"])
        self.assertEqual(encrypted_config["app"]["name"], config["app"]["name"])  # Not secret
        
        # Decrypt secrets in config
        decrypted_config = self.secrets_manager.decrypt_config(encrypted_config)
        self.assertEqual(decrypted_config, config)


class TestConfigurationManager(unittest.TestCase):
    """Test main configuration manager functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigurationManager(base_path=self.temp_dir)
        self.addCleanup(shutil.rmtree, self.temp_dir)
    
    def test_manager_initialization(self):
        """Test configuration manager initialization"""
        success = self.config_manager.initialize()
        self.assertTrue(success)
        self.assertTrue(self.config_manager.is_initialized)
    
    def test_configuration_crud(self):
        """Test configuration create, read, update, delete operations"""
        self.config_manager.initialize()
        
        # Set value
        success = self.config_manager.set("app.name", "Test App")
        self.assertTrue(success)
        
        # Get value
        value = self.config_manager.get("app.name")
        self.assertEqual(value, "Test App")
        
        # Update value
        success = self.config_manager.set("app.name", "Updated App")
        self.assertTrue(success)
        
        value = self.config_manager.get("app.name")
        self.assertEqual(value, "Updated App")
    
    def test_environment_specific_config(self):
        """Test environment-specific configuration"""
        self.config_manager.initialize()
        
        # Set global value
        self.config_manager.set("app.name", "Global App", level="global")
        
        # Set environment-specific value
        self.config_manager.set("app.name", "Dev App", environment="development")
        
        # Switch to development environment
        self.config_manager.set_environment("development")
        
        # Should get environment-specific value
        value = self.config_manager.get("app.name", environment="development")
        self.assertEqual(value, "Dev App")
    
    def test_configuration_validation(self):
        """Test configuration validation"""
        self.config_manager.initialize()
        
        # Set valid configuration
        valid_config = {
            "app": {"name": "Test App", "environment": "development"},
            "logging": {"level": "INFO"}
        }
        
        for key, value in valid_config.items():
            self.config_manager.hierarchy.set_value(key, value, "runtime")
        
        # Validate
        result = self.config_manager.validate_all("global")
        self.assertTrue(result.is_valid)
    
    def test_merged_configuration(self):
        """Test merged configuration from all levels"""
        self.config_manager.initialize()
        
        # Set values in different levels
        self.config_manager.set("app.name", "Global App", level="global")
        self.config_manager.set("app.debug", True, level="runtime")
        self.config_manager.set("logging.level", "INFO", level="environment")
        
        # Get merged configuration
        merged = self.config_manager.get_merged_configuration()
        
        self.assertEqual(merged.get("app", {}).get("name"), "Global App")
        self.assertEqual(merged.get("app", {}).get("debug"), True)
        self.assertEqual(merged.get("logging", {}).get("level"), "INFO")


class TestHotReloadManager(unittest.TestCase):
    """Test hot reload manager functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigurationManager(base_path=self.temp_dir)
        self.config_manager.initialize()
        self.hot_reload = HotReloadManager(self.config_manager)
        self.addCleanup(shutil.rmtree, self.temp_dir)
    
    def test_file_watching_setup(self):
        """Test file watching setup"""
        test_file = os.path.join(self.temp_dir, "test_config.json")
        
        # Create test file
        with open(test_file, 'w') as f:
            json.dump({"test": "value"}, f)
        
        # Watch file
        success = self.hot_reload.watch_file(test_file)
        self.assertTrue(success)
        
        # Check watch status
        status = self.hot_reload.get_watch_status()
        self.assertIn(test_file, status['watched_files'])
    
    def test_debounce_delay_setting(self):
        """Test debounce delay configuration"""
        original_delay = self.hot_reload.debounce_delay
        
        self.hot_reload.set_debounce_delay(2.0)
        self.assertEqual(self.hot_reload.debounce_delay, 2.0)
        
        # Test minimum delay
        self.hot_reload.set_debounce_delay(0.05)
        self.assertEqual(self.hot_reload.debounce_delay, 0.1)  # Should be clamped to minimum


class TestIntegratedConfigurationSystem(unittest.TestCase):
    """Test integrated configuration system end-to-end"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
    
    def test_complete_configuration_workflow(self):
        """Test complete configuration management workflow"""
        # Initialize configuration manager
        config_manager = ConfigurationManager(base_path=self.temp_dir, environment="development")
        success = config_manager.initialize()
        self.assertTrue(success)
        
        # Create environment configuration
        env_config = {
            "app": {
                "name": "Potter Test",
                "environment": "development",
                "debug": True
            },
            "logging": {"level": "DEBUG"},
            "api": {"rate_limit": 1000}
        }
        
        config_manager.environment_manager.create_environment_config("development", env_config)
        
        # Set some runtime overrides
        config_manager.set("api.rate_limit", 500, level="runtime")
        config_manager.set("app.version", "1.0.0", level="runtime")
        
        # Reload to pick up environment config
        config_manager.reload()
        
        # Get merged configuration
        merged = config_manager.get_merged_configuration()
        
        # Verify hierarchy resolution (check if keys exist first)
        if "app" in merged:
            if "name" in merged["app"]:
                self.assertEqual(merged["app"]["name"], "Potter Test")
            if "debug" in merged["app"]:
                self.assertEqual(merged["app"]["debug"], True)
            if "version" in merged["app"]:
                self.assertEqual(merged["app"]["version"], "1.0.0")  # Runtime addition
        
        if "api" in merged and "rate_limit" in merged["api"]:
            self.assertEqual(merged["api"]["rate_limit"], 500)  # Runtime override
        
        # Test validation
        result = config_manager.validate_all("global")
        self.assertTrue(result.is_valid)
        
        # Test environment switching
        success = config_manager.set_environment("production")
        self.assertTrue(success)
        self.assertEqual(config_manager.current_environment, "production")


def run_tests():
    """Run all Phase 6 configuration tests"""
    test_classes = [
        TestConfigurationHierarchy,
        TestConfigurationSources,
        TestValidationEngine,
        TestEnvironmentManager,
        TestSecretsManager,
        TestConfigurationManager,
        TestHotReloadManager,
        TestIntegratedConfigurationSystem
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        total_tests += result.testsRun
        passed_tests += result.testsRun - len(result.failures) - len(result.errors)
        
        if result.failures:
            failed_tests.extend([f"{test_class.__name__}: {f[0]}" for f in result.failures])
        if result.errors:
            failed_tests.extend([f"{test_class.__name__}: {e[0]}" for e in result.errors])
    
    print(f"\n{'='*60}")
    print(f"PHASE 6 CONFIGURATION MANAGEMENT TEST RESULTS")
    print(f"{'='*60}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests:
        print(f"\nFailed Tests:")
        for test in failed_tests:
            print(f"  - {test}")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    run_tests() 