#!/usr/bin/env python3
"""
Window Positioning Utilities
Helper functions for window positioning and state management
"""

import os
import json
import logging
from typing import Dict, Tuple, Optional
from AppKit import NSScreen, NSWindow, NSMakeRect

logger = logging.getLogger(__name__)


class WindowPositioning:
    """Manages window position and state persistence"""
    
    def __init__(self, window_id: str = "settings"):
        """
        Initialize window positioning
        
        Args:
            window_id: Unique identifier for the window
        """
        self.window_id = window_id
        self.state_file = os.path.expanduser(
            f"~/Library/Application Support/Potter/{window_id}_window_state.json"
        )
        
    def save_window_state(self, window: NSWindow):
        """
        Save window position and size
        
        Args:
            window: NSWindow instance
        """
        try:
            frame = window.frame()
            state = {
                "x": frame.origin.x,
                "y": frame.origin.y,
                "width": frame.size.width,
                "height": frame.size.height,
                "screen": self._get_screen_info(window.screen())
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            # Save state
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
                
            logger.debug(f"Saved window state: {state}")
        except Exception as e:
            logger.error(f"Error saving window state: {e}")
            
    def restore_window_state(self, window: NSWindow) -> bool:
        """
        Restore window position and size
        
        Args:
            window: NSWindow instance
            
        Returns:
            True if state was restored, False otherwise
        """
        try:
            if not os.path.exists(self.state_file):
                return False
                
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                
            # Validate position is on screen
            frame = NSMakeRect(
                state["x"], state["y"],
                state["width"], state["height"]
            )
            
            if self._is_frame_on_screen(frame):
                window.setFrame_display_(frame, True)
                logger.debug(f"Restored window state: {state}")
                return True
            else:
                logger.debug("Saved position is off-screen, centering window")
                self.center_window(window)
                return False
                
        except Exception as e:
            logger.error(f"Error restoring window state: {e}")
            return False
            
    def center_window(self, window: NSWindow):
        """Center window on main screen"""
        window.center()
        
    def cascade_window(self, window: NSWindow, from_window: Optional[NSWindow] = None):
        """
        Cascade window from another window or last position
        
        Args:
            window: Window to position
            from_window: Window to cascade from
        """
        if from_window:
            # Cascade from specific window
            from_frame = from_window.frame()
            offset = 20
            new_origin = NSMakeRect(
                from_frame.origin.x + offset,
                from_frame.origin.y - offset,
                0, 0
            ).origin
            window.setFrameOrigin_(new_origin)
        else:
            # Use default cascading
            window.center()
            
    def ensure_window_on_screen(self, window: NSWindow):
        """Ensure window is fully visible on screen"""
        frame = window.frame()
        
        if not self._is_frame_on_screen(frame):
            # Move window to be on screen
            screen = NSScreen.mainScreen()
            if screen:
                screen_frame = screen.visibleFrame()
                
                # Adjust position
                new_x = max(screen_frame.origin.x,
                            min(frame.origin.x,
                                screen_frame.origin.x + screen_frame.size.width - frame.size.width))
                new_y = max(screen_frame.origin.y,
                            min(frame.origin.y,
                                screen_frame.origin.y + screen_frame.size.height - frame.size.height))
                
                window.setFrameOrigin_(NSMakeRect(new_x, new_y, 0, 0).origin)
                
    def _is_frame_on_screen(self, frame) -> bool:
        """Check if frame is visible on any screen"""
        screens = NSScreen.screens()
        
        for screen in screens:
            screen_frame = screen.visibleFrame()
            
            # Check if frame intersects with screen
            if (frame.origin.x < screen_frame.origin.x + screen_frame.size.width and
                frame.origin.x + frame.size.width > screen_frame.origin.x and
                frame.origin.y < screen_frame.origin.y + screen_frame.size.height and
                frame.origin.y + frame.size.height > screen_frame.origin.y):
                return True
                
        return False
        
    def _get_screen_info(self, screen: NSScreen) -> Dict:
        """Get screen information"""
        if not screen:
            return {}
            
        frame = screen.frame()
        return {
            "x": frame.origin.x,
            "y": frame.origin.y,
            "width": frame.size.width,
            "height": frame.size.height
        }
        
    def get_default_window_size(self) -> Tuple[int, int]:
        """Get default window size based on screen"""
        screen = NSScreen.mainScreen()
        if screen:
            screen_frame = screen.visibleFrame()
            # Use 80% of screen size, max 900x650
            width = min(900, int(screen_frame.size.width * 0.8))
            height = min(650, int(screen_frame.size.height * 0.8))
            return (width, height)
        return (900, 650)
    
    def get_screen_info(self) -> Dict:
        """Get information about all available screens"""
        try:
            screens = NSScreen.screens()
            screen_info = {
                'count': len(screens),
                'screens': []
            }
            
            for i, screen in enumerate(screens):
                frame = screen.frame()
                visible_frame = screen.visibleFrame()
                
                screen_data = {
                    'index': i,
                    'is_main': screen == NSScreen.mainScreen(),
                    'frame': {
                        'x': frame.origin.x,
                        'y': frame.origin.y,
                        'width': frame.size.width,
                        'height': frame.size.height
                    },
                    'visible_frame': {
                        'x': visible_frame.origin.x,
                        'y': visible_frame.origin.y,
                        'width': visible_frame.size.width,
                        'height': visible_frame.size.height
                    }
                }
                screen_info['screens'].append(screen_data)
            
            return screen_info
            
        except Exception as e:
            logger.error(f"Error getting screen info: {e}")
            return {
                'count': 1,
                'screens': [{
                    'index': 0,
                    'is_main': True,
                    'frame': {'x': 0, 'y': 0, 'width': 1920, 'height': 1080},
                    'visible_frame': {'x': 0, 'y': 0, 'width': 1920, 'height': 1080}
                }]
            }
    
    def validate_position(self, x: int, y: int, width: int, height: int) -> Tuple[int, int, int, int]:
        """
        Validate and adjust window position to ensure it's on screen
        
        Args:
            x, y: Window position
            width, height: Window size
            
        Returns:
            Tuple of validated (x, y, width, height)
        """
        try:
            frame = NSMakeRect(x, y, width, height)
            
            if self._is_frame_on_screen(frame):
                return (x, y, width, height)
            else:
                # Center on main screen if off-screen
                screen = NSScreen.mainScreen()
                if screen:
                    screen_frame = screen.visibleFrame()
                    new_x = int(screen_frame.origin.x + (screen_frame.size.width - width) / 2)
                    new_y = int(screen_frame.origin.y + (screen_frame.size.height - height) / 2)
                    return (new_x, new_y, width, height)
                else:
                    return (100, 100, width, height)
                    
        except Exception as e:
            logger.error(f"Error validating position: {e}")
            return (100, 100, width, height)
    
    def center_on_screen(self, width: int, height: int, screen_index: int = 0) -> Tuple[int, int]:
        """
        Calculate position to center window on specified screen
        
        Args:
            width: Window width
            height: Window height
            screen_index: Screen index (0 for main)
            
        Returns:
            Tuple of (x, y) position
        """
        try:
            screens = NSScreen.screens()
            if screen_index < len(screens):
                screen = screens[screen_index]
            else:
                screen = NSScreen.mainScreen()
            
            if screen:
                screen_frame = screen.visibleFrame()
                x = int(screen_frame.origin.x + (screen_frame.size.width - width) / 2)
                y = int(screen_frame.origin.y + (screen_frame.size.height - height) / 2)
                return (x, y)
            else:
                return (100, 100)
                
        except Exception as e:
            logger.error(f"Error centering on screen: {e}")
            return (100, 100)
    
    def get_optimal_position(self, width: int, height: int, preferred_screen: int = 0) -> Tuple[int, int]:
        """
        Get optimal position for a new window
        
        Args:
            width: Window width
            height: Window height
            preferred_screen: Preferred screen index
            
        Returns:
            Tuple of (x, y) position
        """
        # For now, just center on the preferred screen
        return self.center_on_screen(width, height, preferred_screen)
    
    def is_position_valid(self, x: int, y: int, width: int, height: int) -> bool:
        """
        Check if a window position is valid (on screen)
        
        Args:
            x, y: Window position
            width, height: Window size
            
        Returns:
            bool: True if position is valid
        """
        try:
            frame = NSMakeRect(x, y, width, height)
            return self._is_frame_on_screen(frame)
        except Exception:
            return False 