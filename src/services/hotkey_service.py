#!/usr/bin/env python3
"""
Hotkey Service
Manages global hotkey registration and handling
"""

import logging
from typing import Dict, Any, Optional, Callable, List
from threading import Lock

from .base_service import BaseService
from core.exceptions import ServiceError, HotkeyRegistrationException
from ui.settings.validators.hotkey_validator import HotkeyValidator

# Import hotkey management
try:
    import pynput
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

logger = logging.getLogger(__name__)


class HotkeyService(BaseService):
    """
    Service for managing global hotkeys
    
    Features:
    - Global hotkey registration
    - Hotkey conflict detection
    - Multiple hotkey support
    - Callback management
    - System integration
    - Hotkey validation
    """
    
    def __init__(self, settings_manager=None):
        super().__init__("hotkey", {})
        
        self.settings_manager = settings_manager
        self.hotkey_validator = HotkeyValidator()
        
        # Hotkey management
        self._registered_hotkeys: Dict[str, Dict[str, Any]] = {}
        self._keyboard_listener: Optional[Any] = None
        self._hotkey_lock = Lock()
        
        # Current pressed keys for combination detection
        self._pressed_keys = set()
        
    def _start_service(self) -> None:
        """Start the hotkey service"""
        if not PYNPUT_AVAILABLE:
            self.logger.warning("⚠️ pynput not available - hotkey functionality disabled")
            return
        
        # Start keyboard listener
        self._start_keyboard_listener()
        
        # Load hotkeys from settings
        if self.settings_manager:
            self._load_hotkeys_from_settings()
        
        self.logger.info("⌨️ Hotkey service started")
    
    def _stop_service(self) -> None:
        """Stop the hotkey service"""
        # Stop keyboard listener
        if self._keyboard_listener:
            try:
                self._keyboard_listener.stop()
                self._keyboard_listener = None
            except Exception as e:
                self.logger.error(f"Error stopping keyboard listener: {e}")
        
        # Clear registered hotkeys
        with self._hotkey_lock:
            self._registered_hotkeys.clear()
            self._pressed_keys.clear()
        
        self.logger.info("⌨️ Hotkey service stopped")
    
    def _get_service_status(self) -> Dict[str, Any]:
        """Get hotkey service specific status"""
        with self._hotkey_lock:
            return {
                'pynput_available': PYNPUT_AVAILABLE,
                'listener_active': self._keyboard_listener is not None,
                'registered_hotkeys': len(self._registered_hotkeys),
                'hotkey_details': {
                    name: {
                        'combination': info['combination'],
                        'enabled': info['enabled']
                    }
                    for name, info in self._registered_hotkeys.items()
                }
            }
    
    def _handle_config_update(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        """Handle configuration updates"""
        if 'hotkey' in new_config or 'hotkeys' in new_config:
            self._load_hotkeys_from_settings()
    
    def register_hotkey(self, name: str, combination: str, callback: Callable[[], None], 
                       enabled: bool = True) -> bool:
        """
        Register a global hotkey
        
        Args:
            name: Unique name for the hotkey
            combination: Hotkey combination (e.g., "cmd+shift+a")
            callback: Function to call when hotkey is pressed
            enabled: Whether the hotkey is initially enabled
            
        Returns:
            bool: True if registered successfully
        """
        if not PYNPUT_AVAILABLE:
            self.logger.warning("Cannot register hotkey - pynput not available")
            return False
        
        try:
            # Validate hotkey combination
            is_valid, error_msg = self.hotkey_validator.validate(combination)
            if not is_valid:
                raise ServiceError(f"Invalid hotkey combination '{combination}': {error_msg}")
            
            # Check for conflicts
            conflicts = self.hotkey_validator.get_conflicts(combination)
            if conflicts:
                self.logger.warning(f"Hotkey '{combination}' may conflict with: {conflicts}")
            
            # Normalize the combination
            normalized = self.hotkey_validator.normalize_hotkey(combination)
            
            with self._hotkey_lock:
                # Check if hotkey already registered
                if name in self._registered_hotkeys:
                    self.logger.warning(f"Hotkey '{name}' already registered - updating")
                
                # Store hotkey info
                self._registered_hotkeys[name] = {
                    'combination': normalized,
                    'original_combination': combination,
                    'callback': callback,
                    'enabled': enabled,
                    'keys': self._parse_hotkey_combination(normalized)
                }
            
            self.logger.info(f"✅ Registered hotkey '{name}': {combination}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to register hotkey '{name}': {e}")
            raise ServiceError(f"Failed to register hotkey '{name}'", details=str(e))
    
    def unregister_hotkey(self, name: str) -> bool:
        """
        Unregister a hotkey
        
        Args:
            name: Name of the hotkey to unregister
            
        Returns:
            bool: True if unregistered successfully
        """
        with self._hotkey_lock:
            if name in self._registered_hotkeys:
                del self._registered_hotkeys[name]
                self.logger.info(f"🗑️ Unregistered hotkey: {name}")
                return True
            else:
                self.logger.warning(f"Hotkey '{name}' not found for unregistration")
                return False
    
    def enable_hotkey(self, name: str) -> bool:
        """
        Enable a registered hotkey
        
        Args:
            name: Name of the hotkey to enable
            
        Returns:
            bool: True if enabled successfully
        """
        with self._hotkey_lock:
            if name in self._registered_hotkeys:
                self._registered_hotkeys[name]['enabled'] = True
                self.logger.info(f"✅ Enabled hotkey: {name}")
                return True
            else:
                self.logger.warning(f"Hotkey '{name}' not found for enabling")
                return False
    
    def disable_hotkey(self, name: str) -> bool:
        """
        Disable a registered hotkey
        
        Args:
            name: Name of the hotkey to disable
            
        Returns:
            bool: True if disabled successfully
        """
        with self._hotkey_lock:
            if name in self._registered_hotkeys:
                self._registered_hotkeys[name]['enabled'] = False
                self.logger.info(f"⏸️ Disabled hotkey: {name}")
                return True
            else:
                self.logger.warning(f"Hotkey '{name}' not found for disabling")
                return False
    
    def get_registered_hotkeys(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all registered hotkeys
        
        Returns:
            Dict mapping hotkey names to their info
        """
        with self._hotkey_lock:
            return {
                name: {
                    'combination': info['combination'],
                    'original_combination': info['original_combination'],
                    'enabled': info['enabled']
                }
                for name, info in self._registered_hotkeys.items()
            }
    
    def validate_hotkey(self, combination: str) -> tuple[bool, str]:
        """
        Validate a hotkey combination
        
        Args:
            combination: Hotkey combination to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return self.hotkey_validator.validate(combination)
    
    def check_conflicts(self, combination: str) -> List[str]:
        """
        Check for hotkey conflicts
        
        Args:
            combination: Hotkey combination to check
            
        Returns:
            List of conflicting system shortcuts
        """
        return self.hotkey_validator.get_conflicts(combination)
    
    def _start_keyboard_listener(self) -> None:
        """Start the global keyboard listener"""
        if not PYNPUT_AVAILABLE:
            return
        
        try:
            self._keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self._keyboard_listener.start()
            self.logger.debug("Started keyboard listener")
            
        except Exception as e:
            self.logger.error(f"Failed to start keyboard listener: {e}")
            raise ServiceError("Failed to start keyboard listener", details=str(e))
    
    def _on_key_press(self, key) -> None:
        """Handle key press events"""
        try:
            key_name = self._get_key_name(key)
            if key_name:
                self._pressed_keys.add(key_name)
                self._check_hotkey_match()
                
        except Exception as e:
            self.logger.debug(f"Error handling key press: {e}")
    
    def _on_key_release(self, key) -> None:
        """Handle key release events"""
        try:
            key_name = self._get_key_name(key)
            if key_name:
                self._pressed_keys.discard(key_name)
                
        except Exception as e:
            self.logger.debug(f"Error handling key release: {e}")
    
    def _get_key_name(self, key) -> Optional[str]:
        """Convert a pynput key to a standardized name"""
        if not PYNPUT_AVAILABLE:
            return None
        
        try:
            # Handle special keys
            if hasattr(key, 'name'):
                key_name = key.name.lower()
                # Map special keys to our standard names
                key_mapping = {
                    'cmd': 'cmd',
                    'ctrl': 'ctrl', 
                    'alt': 'alt',
                    'shift': 'shift',
                    'space': 'space',
                    'enter': 'enter',
                    'tab': 'tab',
                    'esc': 'esc'
                }
                return key_mapping.get(key_name, key_name)
            
            # Handle character keys
            elif hasattr(key, 'char') and key.char:
                return key.char.lower()
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error getting key name: {e}")
            return None
    
    def _check_hotkey_match(self) -> None:
        """Check if current pressed keys match any registered hotkeys"""
        with self._hotkey_lock:
            for name, hotkey_info in self._registered_hotkeys.items():
                if not hotkey_info['enabled']:
                    continue
                
                required_keys = set(hotkey_info['keys'])
                if required_keys.issubset(self._pressed_keys):
                    # Hotkey match! Call the callback
                    try:
                        self.logger.debug(f"Hotkey triggered: {name}")
                        hotkey_info['callback']()
                    except Exception as e:
                        self.logger.error(f"Error executing hotkey callback for '{name}': {e}")
    
    def _parse_hotkey_combination(self, combination: str) -> List[str]:
        """Parse a hotkey combination into individual keys"""
        return [key.strip().lower() for key in combination.split('+')]
    
    def _load_hotkeys_from_settings(self) -> None:
        """Load hotkeys from settings"""
        if not self.settings_manager:
            return
        
        try:
            # Load main hotkey (for backward compatibility)
            hotkey = self.settings_manager.get("hotkey", "")
            if hotkey:
                # We need a callback - this will be set by the main app
                self.logger.info(f"Main hotkey configured: {hotkey}")
            
            # Load additional hotkeys if any
            hotkeys_config = self.settings_manager.get("hotkeys", {})
            for name, config in hotkeys_config.items():
                if isinstance(config, dict) and 'combination' in config:
                    combination = config['combination']
                    enabled = config.get('enabled', True)
                    self.logger.info(f"Configured hotkey '{name}': {combination}")
            
        except Exception as e:
            self.logger.error(f"Error loading hotkeys from settings: {e}")
    
    def set_main_hotkey_callback(self, callback: Callable[[], None]) -> bool:
        """
        Set the callback for the main application hotkey
        
        Args:
            callback: Function to call when main hotkey is pressed
            
        Returns:
            bool: True if set successfully
        """
        if not self.settings_manager:
            return False
        
        try:
            hotkey = self.settings_manager.get("hotkey", "")
            if hotkey:
                return self.register_hotkey("main", hotkey, callback, True)
            else:
                self.logger.warning("No main hotkey configured in settings")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting main hotkey callback: {e}")
            return False 