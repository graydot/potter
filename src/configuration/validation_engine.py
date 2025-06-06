#!/usr/bin/env python3
"""
Validation Engine
Configuration validation with JSON Schema and custom rules
"""

import json
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from copy import deepcopy

try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """
    Result of configuration validation
    """
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    schema_name: Optional[str] = None
    validated_config: Optional[Dict[str, Any]] = None
    
    def add_error(self, message: str):
        """Add validation error"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add validation warning"""
        self.warnings.append(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'schema_name': self.schema_name,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }


class ValidationEngine:
    """
    Configuration validation engine with JSON Schema and custom rules
    
    Features:
    - JSON Schema validation
    - Custom validation functions
    - Configuration transformation
    - Default value injection
    - Type coercion
    """
    
    def __init__(self):
        self.logger = logging.getLogger("config.validation")
        
        # Schema storage
        self.schemas: Dict[str, Dict[str, Any]] = {}
        
        # Custom validators
        self.custom_validators: Dict[str, Callable] = {}
        
        # Transformation functions
        self.transformers: Dict[str, Callable] = {}
        
        # Built-in schemas
        self._register_builtin_schemas()
        self._register_builtin_validators()
    
    def register_schema(self, name: str, schema: Dict[str, Any]) -> bool:
        """
        Register a JSON schema for validation
        
        Args:
            name: Schema name
            schema: JSON Schema definition
            
        Returns:
            True if schema was registered successfully
        """
        try:
            # Validate the schema itself if jsonschema is available
            if JSONSCHEMA_AVAILABLE:
                Draft7Validator.check_schema(schema)
            
            self.schemas[name] = deepcopy(schema)
            self.logger.debug(f"Registered schema: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering schema '{name}': {e}")
            return False
    
    def get_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """Get registered schema by name"""
        return self.schemas.get(name)
    
    def list_schemas(self) -> List[str]:
        """Get list of registered schema names"""
        return list(self.schemas.keys())
    
    def validate_configuration(self, config: Dict[str, Any], 
                             schema_name: str = None,
                             schema: Dict[str, Any] = None,
                             apply_defaults: bool = True,
                             transform: bool = True) -> ValidationResult:
        """
        Validate configuration against schema
        
        Args:
            config: Configuration to validate
            schema_name: Name of registered schema to use
            schema: Direct schema to use (overrides schema_name)
            apply_defaults: Apply default values from schema
            transform: Apply registered transformations
            
        Returns:
            ValidationResult object
        """
        result = ValidationResult(is_valid=True, schema_name=schema_name)
        
        try:
            # Get schema
            if schema is not None:
                validation_schema = schema
            elif schema_name:
                validation_schema = self.get_schema(schema_name)
                if not validation_schema:
                    result.add_error(f"Schema '{schema_name}' not found")
                    return result
            else:
                result.add_error("No schema specified for validation")
                return result
            
            # Start with copy of config
            validated_config = deepcopy(config)
            
            # Apply defaults if requested
            if apply_defaults:
                validated_config = self._apply_defaults(validated_config, validation_schema)
            
            # Apply transformations if requested
            if transform:
                validated_config = self._apply_transformations(validated_config, schema_name)
            
            # JSON Schema validation
            if JSONSCHEMA_AVAILABLE:
                try:
                    validate(instance=validated_config, schema=validation_schema)
                except ValidationError as e:
                    result.add_error(f"Schema validation error: {e.message}")
                    if hasattr(e, 'path') and e.path:
                        result.add_error(f"At path: {'.'.join(str(p) for p in e.path)}")
            else:
                # Fallback validation without jsonschema
                schema_errors = self._basic_schema_validation(validated_config, validation_schema)
                for error in schema_errors:
                    result.add_error(error)
            
            # Custom validation
            custom_errors = self._run_custom_validation(validated_config, schema_name)
            for error in custom_errors:
                result.add_error(error)
            
            # Set validated config
            result.validated_config = validated_config
            
        except Exception as e:
            result.add_error(f"Validation error: {str(e)}")
            self.logger.error(f"Error validating configuration: {e}")
        
        return result
    
    def add_custom_validator(self, name: str, validator: Callable[[Dict[str, Any]], List[str]]) -> bool:
        """
        Add custom validation function
        
        Args:
            name: Validator name
            validator: Function that takes config dict and returns list of error messages
            
        Returns:
            True if validator was added successfully
        """
        try:
            self.custom_validators[name] = validator
            self.logger.debug(f"Added custom validator: {name}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding custom validator '{name}': {e}")
            return False
    
    def add_transformer(self, name: str, transformer: Callable[[Dict[str, Any]], Dict[str, Any]]) -> bool:
        """
        Add configuration transformer
        
        Args:
            name: Transformer name
            transformer: Function that takes and returns config dict
            
        Returns:
            True if transformer was added successfully
        """
        try:
            self.transformers[name] = transformer
            self.logger.debug(f"Added transformer: {name}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding transformer '{name}': {e}")
            return False
    
    def _apply_defaults(self, config: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values from schema to configuration"""
        def apply_defaults_recursive(conf, sch):
            if isinstance(sch, dict):
                # Handle object properties
                if sch.get('type') == 'object' and 'properties' in sch:
                    if not isinstance(conf, dict):
                        conf = {}
                    
                    for prop, prop_schema in sch['properties'].items():
                        if prop not in conf:
                            if 'default' in prop_schema:
                                conf[prop] = deepcopy(prop_schema['default'])
                            elif prop_schema.get('type') == 'object':
                                conf[prop] = {}
                        
                        if prop in conf:
                            conf[prop] = apply_defaults_recursive(conf[prop], prop_schema)
                
                # Handle direct default
                elif 'default' in sch and conf is None:
                    conf = deepcopy(sch['default'])
            
            return conf
        
        return apply_defaults_recursive(config, schema)
    
    def _apply_transformations(self, config: Dict[str, Any], schema_name: str = None) -> Dict[str, Any]:
        """Apply registered transformations to configuration"""
        result = deepcopy(config)
        
        # Apply schema-specific transformations
        if schema_name and schema_name in self.transformers:
            try:
                result = self.transformers[schema_name](result)
            except Exception as e:
                self.logger.error(f"Error in transformer '{schema_name}': {e}")
        
        # Apply global transformations
        for name, transformer in self.transformers.items():
            if name != schema_name:  # Skip schema-specific (already applied)
                try:
                    result = transformer(result)
                except Exception as e:
                    self.logger.error(f"Error in transformer '{name}': {e}")
        
        return result
    
    def _run_custom_validation(self, config: Dict[str, Any], schema_name: str = None) -> List[str]:
        """Run custom validation functions"""
        errors = []
        
        # Run schema-specific validators
        if schema_name and schema_name in self.custom_validators:
            try:
                schema_errors = self.custom_validators[schema_name](config)
                if schema_errors:
                    errors.extend(schema_errors)
            except Exception as e:
                errors.append(f"Custom validator '{schema_name}' error: {e}")
        
        # Run global validators
        for name, validator in self.custom_validators.items():
            if name != schema_name:  # Skip schema-specific (already run)
                try:
                    validator_errors = validator(config)
                    if validator_errors:
                        errors.extend(validator_errors)
                except Exception as e:
                    errors.append(f"Custom validator '{name}' error: {e}")
        
        return errors
    
    def _basic_schema_validation(self, config: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """Basic schema validation without jsonschema library"""
        errors = []
        
        def validate_type(value, expected_type, path=""):
            if expected_type == 'object' and not isinstance(value, dict):
                errors.append(f"Expected object at {path}, got {type(value).__name__}")
            elif expected_type == 'array' and not isinstance(value, list):
                errors.append(f"Expected array at {path}, got {type(value).__name__}")
            elif expected_type == 'string' and not isinstance(value, str):
                errors.append(f"Expected string at {path}, got {type(value).__name__}")
            elif expected_type == 'number' and not isinstance(value, (int, float)):
                errors.append(f"Expected number at {path}, got {type(value).__name__}")
            elif expected_type == 'integer' and not isinstance(value, int):
                errors.append(f"Expected integer at {path}, got {type(value).__name__}")
            elif expected_type == 'boolean' and not isinstance(value, bool):
                errors.append(f"Expected boolean at {path}, got {type(value).__name__}")
        
        def validate_recursive(conf, sch, path=""):
            if isinstance(sch, dict):
                # Type validation
                if 'type' in sch:
                    validate_type(conf, sch['type'], path)
                
                # Required properties
                if sch.get('type') == 'object' and 'required' in sch:
                    if isinstance(conf, dict):
                        for required_prop in sch['required']:
                            if required_prop not in conf:
                                errors.append(f"Required property '{required_prop}' missing at {path}")
                
                # Properties validation
                if sch.get('type') == 'object' and 'properties' in sch and isinstance(conf, dict):
                    for prop, prop_schema in sch['properties'].items():
                        if prop in conf:
                            prop_path = f"{path}.{prop}" if path else prop
                            validate_recursive(conf[prop], prop_schema, prop_path)
        
        validate_recursive(config, schema)
        return errors
    
    def _register_builtin_schemas(self):
        """Register built-in schemas"""
        
        # Global application schema
        global_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "app": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "default": "Potter"},
                        "version": {"type": "string"},
                        "environment": {
                            "type": "string", 
                            "enum": ["development", "staging", "production"],
                            "default": "development"
                        },
                        "debug": {"type": "boolean", "default": False}
                    },
                    "required": ["name", "environment"]
                },
                "logging": {
                    "type": "object",
                    "properties": {
                        "level": {
                            "type": "string",
                            "enum": ["DEBUG", "INFO", "WARNING", "ERROR"],
                            "default": "INFO"
                        },
                        "file": {"type": "string"},
                        "max_size": {"type": "integer", "minimum": 1, "default": 10485760}
                    }
                },
                "api": {
                    "type": "object",
                    "properties": {
                        "rate_limit": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 100},
                        "timeout": {"type": "number", "minimum": 0.1, "maximum": 300, "default": 30}
                    }
                }
            }
        }
        
        # LLM service schema
        llm_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "providers": {
                    "type": "object",
                    "patternProperties": {
                        "^(openai|anthropic|google)$": {
                            "type": "object",
                            "properties": {
                                "api_key": {"type": "string", "secret": True},
                                "model": {"type": "string"},
                                "timeout": {"type": "number", "minimum": 1, "default": 30},
                                "retry_attempts": {"type": "integer", "minimum": 0, "maximum": 5, "default": 3}
                            },
                            "required": ["api_key", "model"]
                        }
                    }
                },
                "current_provider": {"type": "string", "enum": ["openai", "anthropic", "google"]}
            }
        }
        
        self.register_schema("global", global_schema)
        self.register_schema("llm_service", llm_schema)
    
    def _register_builtin_validators(self):
        """Register built-in custom validators"""
        
        def validate_api_keys(config: Dict[str, Any]) -> List[str]:
            """Validate API key formats"""
            errors = []
            
            providers = config.get('providers', {})
            for provider, settings in providers.items():
                api_key = settings.get('api_key', '')
                
                if provider == 'openai':
                    if not api_key.startswith('sk-') or len(api_key) < 50:
                        errors.append(f"Invalid OpenAI API key format for provider {provider}")
                
                elif provider == 'anthropic':
                    if not api_key.startswith('sk-ant-') or len(api_key) < 50:
                        errors.append(f"Invalid Anthropic API key format for provider {provider}")
                
                elif provider == 'google':
                    if not api_key.startswith('AIza') or len(api_key) < 35:
                        errors.append(f"Invalid Google API key format for provider {provider}")
            
            return errors
        
        def validate_environment_consistency(config: Dict[str, Any]) -> List[str]:
            """Validate environment-specific settings consistency"""
            errors = []
            
            app_config = config.get('app', {})
            environment = app_config.get('environment', 'development')
            debug = app_config.get('debug', False)
            
            # Production environment should not have debug enabled
            if environment == 'production' and debug:
                errors.append("Debug mode should not be enabled in production environment")
            
            # Development environment should have appropriate logging
            if environment == 'development':
                logging_config = config.get('logging', {})
                log_level = logging_config.get('level', 'INFO')
                if log_level not in ['DEBUG', 'INFO']:
                    errors.append("Development environment should use DEBUG or INFO logging level")
            
            return errors
        
        self.add_custom_validator("api_keys", validate_api_keys)
        self.add_custom_validator("environment_consistency", validate_environment_consistency)
    
    def get_validation_info(self) -> Dict[str, Any]:
        """Get information about the validation engine"""
        return {
            'jsonschema_available': JSONSCHEMA_AVAILABLE,
            'schemas_count': len(self.schemas),
            'custom_validators_count': len(self.custom_validators),
            'transformers_count': len(self.transformers),
            'registered_schemas': list(self.schemas.keys()),
            'custom_validators': list(self.custom_validators.keys()),
            'transformers': list(self.transformers.keys())
        } 