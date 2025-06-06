#!/usr/bin/env python3
"""
Hotkey Validator
Handles validation of hotkey combinations
"""

import logging
from typing import Tuple, Optional, List, Set

logger = logging.getLogger(__name__)


class HotkeyValidator:
    """Validates hotkey combinations"""
    
    # Valid modifier keys
    VALID_MODIFIERS = {'cmd', 'ctrl', 'alt', 'shift', 'option'}
    
    # Modifier aliases
    MODIFIER_ALIASES = {
        'command': 'cmd',
        'control': 'ctrl',
        'option': 'alt',
        'opt': 'alt'
    }
    
    # System reserved hotkeys that should not be used
    RESERVED_HOTKEYS = {
        'cmd+q',           # Quit
        'cmd+w',           # Close window
        'cmd+m',           # Minimize
        'cmd+h',           # Hide
        'cmd+tab',         # App switcher
        'cmd+space',       # Spotlight
        'cmd+shift+3',     # Screenshot
        'cmd+shift+4',     # Screenshot selection
        'cmd+shift+5',     # Screenshot/recording
    }
    
    def validate(self, hotkey: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a hotkey combination
        
        Args:
            hotkey: The hotkey string (e.g., 'cmd+shift+a')
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not hotkey:
            return False, "Hotkey cannot be empty"
        
        # Normalize and parse
        parts = self._parse_hotkey(hotkey)
        if not parts:
            return False, "Invalid hotkey format"
        
        modifiers, key = parts
        
        # Check if at least one modifier is present
        if not modifiers:
            return False, "Hotkey must include at least one modifier (cmd, ctrl, alt, shift)"
        
        # Check if key is valid
        if not key or not key.isalnum():
            return False, "Hotkey must end with a letter or number"
        
        # Check if it's a reserved hotkey
        normalized = self._normalize_hotkey(modifiers, key)
        if normalized in self.RESERVED_HOTKEYS:
            return False, f"'{normalized}' is a system reserved hotkey"
        
        return True, None
    
    def _parse_hotkey(self, hotkey: str) -> Optional[Tuple[Set[str], str]]:
        """
        Parse a hotkey string into modifiers and key
        
        Args:
            hotkey: The hotkey string
            
        Returns:
            Tuple of (modifiers_set, key) or None if invalid
        """
        try:
            parts = hotkey.lower().strip().split('+')
            if len(parts) < 2:
                return None
            
            # Last part should be the key
            key = parts[-1].strip()
            
            # Everything else should be modifiers
            modifiers = set()
            for part in parts[:-1]:
                modifier = part.strip()
                # Apply aliases
                modifier = self.MODIFIER_ALIASES.get(modifier, modifier)
                
                if modifier not in self.VALID_MODIFIERS:
                    return None
                    
                modifiers.add(modifier)
            
            return modifiers, key
            
        except Exception:
            return None
    
    def _normalize_hotkey(self, modifiers: Set[str], key: str) -> str:
        """
        Normalize a hotkey to a standard format
        
        Args:
            modifiers: Set of modifier keys
            key: The main key
            
        Returns:
            Normalized hotkey string
        """
        # Sort modifiers in a consistent order
        modifier_order = ['cmd', 'ctrl', 'alt', 'shift']
        sorted_modifiers = [m for m in modifier_order if m in modifiers]
        
        # Add any modifiers not in the standard order
        for m in modifiers:
            if m not in sorted_modifiers:
                sorted_modifiers.append(m)
        
        return '+'.join(sorted_modifiers + [key])
    
    def format_hotkey(self, hotkey: str) -> str:
        """
        Format a hotkey for display
        
        Args:
            hotkey: The hotkey string
            
        Returns:
            Formatted hotkey string
        """
        parts = self._parse_hotkey(hotkey)
        if not parts:
            return hotkey
        
        modifiers, key = parts
        
        # Use display names
        display_names = {
            'cmd': '⌘',
            'ctrl': '⌃',
            'alt': '⌥',
            'shift': '⇧',
            'option': '⌥'
        }
        
        # Format modifiers
        formatted_modifiers = []
        for m in ['cmd', 'ctrl', 'alt', 'shift']:
            if m in modifiers:
                formatted_modifiers.append(display_names.get(m, m.title()))
        
        return ''.join(formatted_modifiers) + key.upper()
    
    def get_conflicts(self, hotkey: str, existing_hotkeys: List[str]) -> List[str]:
        """
        Check if a hotkey conflicts with existing hotkeys
        
        Args:
            hotkey: The hotkey to check
            existing_hotkeys: List of existing hotkeys
            
        Returns:
            List of conflicting hotkeys
        """
        parts = self._parse_hotkey(hotkey)
        if not parts:
            return []
        
        modifiers, key = parts
        normalized = self._normalize_hotkey(modifiers, key)
        
        conflicts = []
        for existing in existing_hotkeys:
            existing_parts = self._parse_hotkey(existing)
            if existing_parts:
                existing_modifiers, existing_key = existing_parts
                existing_normalized = self._normalize_hotkey(existing_modifiers, existing_key)
                
                if normalized == existing_normalized:
                    conflicts.append(existing)
        
        return conflicts 