#!/usr/bin/env python3
"""
Secrets Manager
Secure handling of sensitive configuration data
"""

import os
import base64
import logging
from typing import Dict, Any, Set, Optional
from copy import deepcopy

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Manages encryption and decryption of sensitive configuration data
    
    Features:
    - Symmetric encryption for secrets
    - Key derivation from password
    - Automatic secret detection
    - Secure key storage
    """
    
    def __init__(self, master_key: str = None, key_file: str = None):
        """
        Initialize secrets manager
        
        Args:
            master_key: Master encryption key (if None, generates one)
            key_file: Path to key file for persistent key storage
        """
        self.logger = logging.getLogger("config.secrets")
        
        # Encryption key
        self.key_file = key_file or os.path.expanduser("~/.potter/encryption.key")
        self._cipher = None
        
        # Secret field tracking
        self.secret_fields: Set[str] = set()
        self.encrypted_prefix = "ENCRYPTED:"
        
        # Initialize encryption
        if CRYPTOGRAPHY_AVAILABLE:
            self._initialize_encryption(master_key)
        else:
            self.logger.warning("Cryptography library not available, secrets will not be encrypted")
    
    def _initialize_encryption(self, master_key: str = None):
        """Initialize encryption with key"""
        try:
            if master_key:
                # Use provided master key
                encryption_key = self._derive_key_from_password(master_key)
            elif os.path.exists(self.key_file):
                # Load key from file
                encryption_key = self._load_key_from_file()
            else:
                # Generate new key
                encryption_key = self._generate_new_key()
                self._save_key_to_file(encryption_key)
            
            self._cipher = Fernet(encryption_key)
            self.logger.debug("Encryption initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing encryption: {e}")
            self._cipher = None
    
    def _derive_key_from_password(self, password: str, salt: bytes = None) -> bytes:
        """Derive encryption key from password"""
        if salt is None:
            salt = b'potter_config_salt'  # In production, use a random salt
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def _generate_new_key(self) -> bytes:
        """Generate new encryption key"""
        return Fernet.generate_key()
    
    def _load_key_from_file(self) -> bytes:
        """Load encryption key from file"""
        with open(self.key_file, 'rb') as f:
            return f.read()
    
    def _save_key_to_file(self, key: bytes):
        """Save encryption key to file"""
        os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
        
        with open(self.key_file, 'wb') as f:
            f.write(key)
        
        # Set secure file permissions (owner only)
        os.chmod(self.key_file, 0o600)
        self.logger.debug(f"Saved encryption key to {self.key_file}")
    
    def encrypt_value(self, value: str) -> str:
        """
        Encrypt a configuration value
        
        Args:
            value: Value to encrypt
            
        Returns:
            Encrypted value with prefix
        """
        if not CRYPTOGRAPHY_AVAILABLE or not self._cipher:
            self.logger.warning("Encryption not available, returning value as-is")
            return value
        
        try:
            if isinstance(value, str):
                encrypted_bytes = self._cipher.encrypt(value.encode('utf-8'))
                encrypted_str = base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
                return f"{self.encrypted_prefix}{encrypted_str}"
            else:
                self.logger.warning("Can only encrypt string values")
                return str(value)
                
        except Exception as e:
            self.logger.error(f"Error encrypting value: {e}")
            return value
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """
        Decrypt a configuration value
        
        Args:
            encrypted_value: Encrypted value with prefix
            
        Returns:
            Decrypted value
        """
        if not CRYPTOGRAPHY_AVAILABLE or not self._cipher:
            return encrypted_value
        
        try:
            if not isinstance(encrypted_value, str):
                return str(encrypted_value)
            
            if not encrypted_value.startswith(self.encrypted_prefix):
                # Not encrypted, return as-is
                return encrypted_value
            
            # Remove prefix and decrypt
            encrypted_str = encrypted_value[len(self.encrypted_prefix):]
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_str.encode('utf-8'))
            decrypted_bytes = self._cipher.decrypt(encrypted_bytes)
            
            return decrypted_bytes.decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Error decrypting value: {e}")
            return encrypted_value
    
    def is_encrypted(self, value: str) -> bool:
        """
        Check if a value is encrypted
        
        Args:
            value: Value to check
            
        Returns:
            True if value is encrypted
        """
        return (isinstance(value, str) and 
                value.startswith(self.encrypted_prefix))
    
    def mark_as_secret(self, key_path: str):
        """
        Mark a configuration path as secret
        
        Args:
            key_path: Dot-notation path to secret field
        """
        self.secret_fields.add(key_path)
        self.logger.debug(f"Marked as secret: {key_path}")
    
    def unmark_as_secret(self, key_path: str):
        """
        Unmark a configuration path as secret
        
        Args:
            key_path: Dot-notation path to remove from secrets
        """
        self.secret_fields.discard(key_path)
        self.logger.debug(f"Unmarked as secret: {key_path}")
    
    def is_secret(self, key_path: str) -> bool:
        """
        Check if a configuration path is marked as secret
        
        Args:
            key_path: Dot-notation path to check
            
        Returns:
            True if path is marked as secret
        """
        # Direct match
        if key_path in self.secret_fields:
            return True
        
        # Check for pattern matches (e.g., *.api_key)
        for secret_pattern in self.secret_fields:
            if self._matches_secret_pattern(key_path, secret_pattern):
                return True
        
        # Check for common secret field names
        key_parts = key_path.split('.')
        last_part = key_parts[-1].lower()
        
        secret_keywords = [
            'api_key', 'secret', 'password', 'token', 'key',
            'private_key', 'access_token', 'auth_token'
        ]
        
        return any(keyword in last_part for keyword in secret_keywords)
    
    def _matches_secret_pattern(self, key_path: str, pattern: str) -> bool:
        """Check if key path matches secret pattern"""
        if '*' in pattern:
            # Simple wildcard matching
            pattern_parts = pattern.split('*')
            if len(pattern_parts) == 2:
                start, end = pattern_parts
                return key_path.startswith(start) and key_path.endswith(end)
        
        return key_path == pattern
    
    def encrypt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt secret values in configuration
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configuration with encrypted secret values
        """
        if not CRYPTOGRAPHY_AVAILABLE or not self._cipher:
            return deepcopy(config)
        
        result = deepcopy(config)
        self._encrypt_config_recursive(result, "")
        return result
    
    def decrypt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt secret values in configuration
        
        Args:
            config: Configuration dictionary with encrypted values
            
        Returns:
            Configuration with decrypted secret values
        """
        if not CRYPTOGRAPHY_AVAILABLE or not self._cipher:
            return deepcopy(config)
        
        result = deepcopy(config)
        self._decrypt_config_recursive(result, "")
        return result
    
    def _encrypt_config_recursive(self, config: Any, path: str):
        """Recursively encrypt secret values in configuration"""
        if isinstance(config, dict):
            for key, value in config.items():
                current_path = f"{path}.{key}" if path else key
                
                if self.is_secret(current_path) and isinstance(value, str):
                    # Encrypt secret value
                    if not self.is_encrypted(value):
                        config[key] = self.encrypt_value(value)
                elif isinstance(value, (dict, list)):
                    # Recurse into nested structures
                    self._encrypt_config_recursive(value, current_path)
        
        elif isinstance(config, list):
            for i, item in enumerate(config):
                current_path = f"{path}[{i}]"
                self._encrypt_config_recursive(item, current_path)
    
    def _decrypt_config_recursive(self, config: Any, path: str):
        """Recursively decrypt secret values in configuration"""
        if isinstance(config, dict):
            for key, value in config.items():
                current_path = f"{path}.{key}" if path else key
                
                if isinstance(value, str) and self.is_encrypted(value):
                    # Decrypt encrypted value
                    config[key] = self.decrypt_value(value)
                elif isinstance(value, (dict, list)):
                    # Recurse into nested structures
                    self._decrypt_config_recursive(value, current_path)
        
        elif isinstance(config, list):
            for i, item in enumerate(config):
                current_path = f"{path}[{i}]"
                self._decrypt_config_recursive(item, current_path)
    
    def add_secret_patterns(self, patterns: list):
        """
        Add multiple secret field patterns
        
        Args:
            patterns: List of secret field patterns
        """
        for pattern in patterns:
            self.mark_as_secret(pattern)
    
    def get_secret_info(self) -> Dict[str, Any]:
        """
        Get information about secrets manager
        
        Returns:
            Dictionary with secrets manager information
        """
        return {
            'encryption_available': CRYPTOGRAPHY_AVAILABLE and self._cipher is not None,
            'key_file': self.key_file,
            'key_file_exists': os.path.exists(self.key_file),
            'secret_fields_count': len(self.secret_fields),
            'secret_fields': list(self.secret_fields),
            'encrypted_prefix': self.encrypted_prefix
        }
    
    def initialize_default_secrets(self):
        """Initialize default secret field patterns"""
        default_patterns = [
            "*.api_key",
            "*.secret",
            "*.password",
            "*.token",
            "*.private_key",
            "*.access_token",
            "*.auth_token",
            "llm_providers.*.api_key",
            "database.password",
            "auth.secret_key"
        ]
        
        self.add_secret_patterns(default_patterns)
        self.logger.debug(f"Initialized {len(default_patterns)} default secret patterns") 