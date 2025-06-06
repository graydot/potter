#!/usr/bin/env python3
"""
Window Service
Manages window state, positioning, and restoration
"""

import logging
import json
from typing import Dict, Any, Optional, Tuple, List
from threading import Lock
from pathlib import Path

from .base_service import BaseService
from core.exceptions import ServiceError
from ui.settings.utils.window_positioning import WindowPositioning

logger = logging.getLogger(__name__)


class WindowState:
    """Represents a window's state"""
    
    def __init__(self, window_id: str, x: int = 0, y: int = 0, width: int = 800, height: int = 600,
                 is_visible: bool = False, is_minimized: bool = False, is_maximized: bool = False):
        self.window_id = window_id
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_visible = is_visible
        self.is_minimized = is_minimized
        self.is_maximized = is_maximized
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'window_id': self.window_id,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'is_visible': self.is_visible,
            'is_minimized': self.is_minimized,
            'is_maximized': self.is_maximized
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WindowState':
        """Create from dictionary"""
        return cls(
            window_id=data.get('window_id', ''),
            x=data.get('x', 0),
            y=data.get('y', 0),
            width=data.get('width', 800),
            height=data.get('height', 600),
            is_visible=data.get('is_visible', False),
            is_minimized=data.get('is_minimized', False),
            is_maximized=data.get('is_maximized', False)
        )


class WindowService(BaseService):
    """
    Service for managing window states and positioning
    
    Features:
    - Window state persistence
    - Window positioning and sizing
    - Multi-screen support
    - Window restoration
    - State validation
    - Automatic state saving
    """
    
    def __init__(self, settings_manager=None):
        super().__init__("window", {})
        
        self.settings_manager = settings_manager
        self.window_positioning = WindowPositioning()
        
        # Window state management
        self._window_states: Dict[str, WindowState] = {}
        self._state_lock = Lock()
        
        # Persistence
        self._state_file_path = Path.home() / ".potter" / "window_states.json"
        self._auto_save = True
        
        # Screen information cache
        self._screen_info_cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp = 0
        self._cache_ttl = 30  # seconds
        
    def _start_service(self) -> None:
        """Start the window service"""
        # Create state directory if needed
        self._state_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load saved window states
        self._load_window_states()
        
        # Update screen information
        self._update_screen_info()
        
        self.logger.info("🪟 Window service started")
    
    def _stop_service(self) -> None:
        """Stop the window service"""
        # Save current window states
        if self._auto_save:
            self._save_window_states()
        
        # Clear state
        with self._state_lock:
            self._window_states.clear()
        
        self.logger.info("🪟 Window service stopped")
    
    def _get_service_status(self) -> Dict[str, Any]:
        """Get window service specific status"""
        with self._state_lock:
            return {
                'state_file_path': str(self._state_file_path),
                'auto_save_enabled': self._auto_save,
                'tracked_windows': len(self._window_states),
                'window_states': {
                    window_id: state.to_dict()
                    for window_id, state in self._window_states.items()
                },
                'screen_info_cached': self._screen_info_cache is not None,
                'cache_age': time.time() - self._cache_timestamp if self._cache_timestamp else 0
            }
    
    def _handle_config_update(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        """Handle configuration updates"""
        if 'auto_save_window_states' in new_config:
            self._auto_save = new_config['auto_save_window_states']
        
        if 'window_state_file' in new_config:
            self._state_file_path = Path(new_config['window_state_file'])
    
    def register_window(self, window_id: str, x: int = 0, y: int = 0, 
                       width: int = 800, height: int = 600) -> None:
        """
        Register a window for state management
        
        Args:
            window_id: Unique identifier for the window
            x, y: Window position
            width, height: Window size
        """
        with self._state_lock:
            if window_id in self._window_states:
                # Update existing state
                state = self._window_states[window_id]
                state.x = x
                state.y = y
                state.width = width
                state.height = height
            else:
                # Create new state
                self._window_states[window_id] = WindowState(
                    window_id=window_id, x=x, y=y, width=width, height=height
                )
        
        self.logger.debug(f"Registered window: {window_id}")
    
    def update_window_state(self, window_id: str, x: Optional[int] = None, y: Optional[int] = None,
                           width: Optional[int] = None, height: Optional[int] = None,
                           is_visible: Optional[bool] = None, is_minimized: Optional[bool] = None,
                           is_maximized: Optional[bool] = None) -> bool:
        """
        Update a window's state
        
        Args:
            window_id: Window identifier
            x, y: New position (optional)
            width, height: New size (optional)
            is_visible: Visibility state (optional)
            is_minimized: Minimized state (optional)
            is_maximized: Maximized state (optional)
            
        Returns:
            bool: True if state was updated
        """
        with self._state_lock:
            if window_id not in self._window_states:
                self.logger.warning(f"Window '{window_id}' not registered")
                return False
            
            state = self._window_states[window_id]
            
            # Update position
            if x is not None:
                state.x = x
            if y is not None:
                state.y = y
            
            # Update size
            if width is not None:
                state.width = width
            if height is not None:
                state.height = height
            
            # Update flags
            if is_visible is not None:
                state.is_visible = is_visible
            if is_minimized is not None:
                state.is_minimized = is_minimized
            if is_maximized is not None:
                state.is_maximized = is_maximized
        
        # Auto-save if enabled
        if self._auto_save:
            self._save_window_states()
        
        self.logger.debug(f"Updated window state: {window_id}")
        return True
    
    def get_window_state(self, window_id: str) -> Optional[WindowState]:
        """
        Get a window's current state
        
        Args:
            window_id: Window identifier
            
        Returns:
            WindowState object or None if not found
        """
        with self._state_lock:
            return self._window_states.get(window_id)
    
    def get_all_window_states(self) -> Dict[str, WindowState]:
        """
        Get all window states
        
        Returns:
            Dict mapping window IDs to their states
        """
        with self._state_lock:
            return self._window_states.copy()
    
    def restore_window_state(self, window_id: str) -> Optional[Tuple[int, int, int, int]]:
        """
        Get the saved position and size for a window
        
        Args:
            window_id: Window identifier
            
        Returns:
            Tuple of (x, y, width, height) or None if not found
        """
        state = self.get_window_state(window_id)
        if state:
            # Validate position is still on screen
            validated_pos = self.window_positioning.validate_position(
                state.x, state.y, state.width, state.height
            )
            return validated_pos
        return None
    
    def center_window_on_screen(self, window_id: str, screen_index: int = 0) -> Optional[Tuple[int, int]]:
        """
        Calculate position to center a window on a screen
        
        Args:
            window_id: Window identifier
            screen_index: Screen index (0 for primary)
            
        Returns:
            Tuple of (x, y) position or None if failed
        """
        state = self.get_window_state(window_id)
        if not state:
            return None
        
        return self.window_positioning.center_on_screen(
            state.width, state.height, screen_index
        )
    
    def get_optimal_window_position(self, width: int, height: int,
                                   preferred_screen: int = 0) -> Tuple[int, int]:
        """
        Get optimal position for a new window
        
        Args:
            width: Window width
            height: Window height
            preferred_screen: Preferred screen index
            
        Returns:
            Tuple of (x, y) position
        """
        return self.window_positioning.get_optimal_position(width, height, preferred_screen)
    
    def is_position_valid(self, x: int, y: int, width: int, height: int) -> bool:
        """
        Check if a window position is valid (on screen)
        
        Args:
            x, y: Window position
            width, height: Window size
            
        Returns:
            bool: True if position is valid
        """
        return self.window_positioning.is_position_valid(x, y, width, height)
    
    def get_screen_info(self) -> Dict[str, Any]:
        """
        Get information about available screens
        
        Returns:
            Dict with screen information
        """
        import time
        
        # Check cache
        if (self._screen_info_cache and 
            time.time() - self._cache_timestamp < self._cache_ttl):
            return self._screen_info_cache
        
        # Update cache
        self._update_screen_info()
        return self._screen_info_cache or {}
    
    def unregister_window(self, window_id: str) -> bool:
        """
        Unregister a window from state management
        
        Args:
            window_id: Window identifier
            
        Returns:
            bool: True if window was unregistered
        """
        with self._state_lock:
            if window_id in self._window_states:
                del self._window_states[window_id]
                self.logger.debug(f"Unregistered window: {window_id}")
                
                # Auto-save if enabled
                if self._auto_save:
                    self._save_window_states()
                
                return True
            else:
                return False
    
    def save_states(self) -> bool:
        """
        Manually save window states to file
        
        Returns:
            bool: True if saved successfully
        """
        return self._save_window_states()
    
    def load_states(self) -> bool:
        """
        Manually load window states from file
        
        Returns:
            bool: True if loaded successfully
        """
        return self._load_window_states()
    
    def clear_all_states(self) -> None:
        """Clear all window states"""
        with self._state_lock:
            self._window_states.clear()
        
        # Remove state file
        try:
            if self._state_file_path.exists():
                self._state_file_path.unlink()
        except Exception as e:
            self.logger.error(f"Error removing state file: {e}")
        
        self.logger.info("Cleared all window states")
    
    def _save_window_states(self) -> bool:
        """Save window states to file"""
        try:
            with self._state_lock:
                data = {
                    'version': '1.0',
                    'windows': {
                        window_id: state.to_dict()
                        for window_id, state in self._window_states.items()
                    }
                }
            
            with open(self._state_file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.debug(f"Saved window states to {self._state_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving window states: {e}")
            return False
    
    def _load_window_states(self) -> bool:
        """Load window states from file"""
        try:
            if not self._state_file_path.exists():
                self.logger.debug("No window state file found")
                return True
            
            with open(self._state_file_path, 'r') as f:
                data = json.load(f)
            
            windows_data = data.get('windows', {})
            
            with self._state_lock:
                self._window_states.clear()
                for window_id, state_data in windows_data.items():
                    try:
                        state = WindowState.from_dict(state_data)
                        self._window_states[window_id] = state
                    except Exception as e:
                        self.logger.error(f"Error loading state for window '{window_id}': {e}")
            
            self.logger.debug(f"Loaded {len(self._window_states)} window states")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading window states: {e}")
            return False
    
    def _update_screen_info(self) -> None:
        """Update screen information cache"""
        try:
            import time
            screen_info = self.window_positioning.get_screen_info()
            
            self._screen_info_cache = screen_info
            self._cache_timestamp = time.time()
            
        except Exception as e:
            self.logger.error(f"Error updating screen info: {e}")


# Import time for cache timestamp
import time 