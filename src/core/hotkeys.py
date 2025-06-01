#!/usr/bin/env python3
"""
Hotkey Management Module
Handles hotkey parsing, detection, and keyboard event processing
"""

import logging
from typing import Set, Callable, Optional
from pynput import keyboard
from pynput.keyboard import Key, Listener

# Import macOS event filtering
try:
    from Quartz import (
        kCGEventKeyDown, kCGEventKeyUp, kCGEventFlagsChanged,
        kCGEventLeftMouseDown, kCGEventLeftMouseUp, kCGEventRightMouseDown, 
        kCGEventRightMouseUp, kCGEventMouseMoved, kCGEventLeftMouseDragged,
        kCGEventRightMouseDragged, kCGEventScrollWheel, kCGEventOtherMouseDown,
        kCGEventOtherMouseUp, kCGEventOtherMouseDragged
    )
    MACOS_EVENT_FILTERING_AVAILABLE = True
except ImportError:
    MACOS_EVENT_FILTERING_AVAILABLE = False

logger = logging.getLogger(__name__)


class HotkeyManager:
    """Manages hotkey parsing, detection, and keyboard event processing"""
    
    def __init__(self, hotkey_combo: Set = None, on_hotkey_pressed: Callable = None):
        self.hotkey_combo = hotkey_combo or {Key.cmd, Key.shift, keyboard.KeyCode.from_char('a')}
        self.on_hotkey_pressed = on_hotkey_pressed
        self.current_keys = set()
        self.listener = None
        self.is_running = False
    
    def parse_hotkey(self, hotkey_str: str) -> Set:
        """Parse hotkey string into key combination set"""
        try:
            keys = set()
            parts = hotkey_str.lower().split('+')
            
            for part in parts:
                part = part.strip()
                if part in ['cmd', 'command']:
                    keys.add(Key.cmd)
                elif part in ['shift']:
                    keys.add(Key.shift)
                elif part in ['ctrl', 'control']:
                    keys.add(Key.ctrl)
                elif part in ['alt', 'option']:
                    keys.add(Key.alt)
                elif len(part) == 1:
                    keys.add(keyboard.KeyCode.from_char(part))
            
            return keys if keys else {Key.cmd, Key.shift, keyboard.KeyCode.from_char('a')}
        except Exception as e:
            logger.error(f"Failed to parse hotkey '{hotkey_str}': {e}")
            return {Key.cmd, Key.shift, keyboard.KeyCode.from_char('a')}
    
    def update_hotkey(self, hotkey_str: str):
        """Update the hotkey combination"""
        self.hotkey_combo = self.parse_hotkey(hotkey_str)
        logger.info(f"Updated hotkey to: {hotkey_str}")
        
        # Restart listener if running
        if self.is_running:
            self.stop_listener()
            self.start_listener()
    
    def normalize_key(self, key):
        """Normalize pynput key objects to our string representation"""
        try:
            key_str = str(key).lower()
            logger.debug(f"DEBUG: normalize_key called with key={key}, str={key_str}, type={type(key)}")
        except Exception as e:
            logger.debug(f"DEBUG: Failed to convert key to string: {e}")
            return None

        if 'cmd' in key_str or 'command' in key_str:
            logger.debug(f"DEBUG: Detected CMD key from '{key_str}'")
            return 'cmd'
        if 'shift' in key_str:
            logger.debug(f"DEBUG: Detected SHIFT key from '{key_str}'")
            return 'shift'
        if 'ctrl' in key_str or 'control' in key_str:
            logger.debug(f"DEBUG: Detected CTRL key from '{key_str}'")
            return 'ctrl'
        if 'alt' in key_str or 'option' in key_str:
            logger.debug(f"DEBUG: Detected ALT key from '{key_str}'")
            return 'alt'

        if isinstance(key, keyboard.KeyCode) and key.char:
            char = key.char.lower()
            logger.debug(f"DEBUG: Detected character '{char}' from KeyCode")
            return char

        logger.debug(f"DEBUG: No match found for key '{key_str}', returning None")
        return None
    
    def darwin_intercept(self, event_type, event):
        """
        Filter function for macOS to prevent mouse events from being processed as keyboard events.
        This fixes the issue where mouse clicks were being detected as key <0> events.
        """
        if not MACOS_EVENT_FILTERING_AVAILABLE:
            return event
            
        # Define mouse event types that should be filtered out
        mouse_events = {
            kCGEventLeftMouseDown, kCGEventLeftMouseUp, kCGEventRightMouseDown, 
            kCGEventRightMouseUp, kCGEventMouseMoved, kCGEventLeftMouseDragged,
            kCGEventRightMouseDragged, kCGEventScrollWheel, kCGEventOtherMouseDown,
            kCGEventOtherMouseUp, kCGEventOtherMouseDragged
        }
        
        # If this is a mouse event, suppress it (return None)
        if event_type in mouse_events:
            logger.debug(f"DEBUG: Filtering out mouse event type: {event_type}")
            return None
        
        # Allow keyboard events to pass through
        if event_type in {kCGEventKeyDown, kCGEventKeyUp, kCGEventFlagsChanged}:
            logger.debug(f"DEBUG: Allowing keyboard event type: {event_type}")
            return event
        
        # For any other event types, allow them through but log them
        logger.debug(f"DEBUG: Unknown event type: {event_type}, allowing through")
        return event
    
    def on_key_press(self, key):
        """Handle key press events"""
        logger.debug(f"🔥 KEY PRESS DETECTED: {key} (type: {type(key)})")
        
        self.current_keys.add(key)
        logger.debug("DEBUG: Added key to current_keys")

        # Debug logging for hotkey detection
        logger.debug(f"DEBUG: Current keys: {[str(k) for k in self.current_keys]}")
        logger.debug(f"DEBUG: Target hotkey: {[str(k) for k in self.hotkey_combo]}")
        logger.debug(f"DEBUG: Is subset? {self.hotkey_combo.issubset(self.current_keys)}")

        # Check if our hotkey combination is pressed
        if self.hotkey_combo.issubset(self.current_keys):
            logger.info("🎯 HOTKEY CAPTURED! Triggering text processing workflow...")
            
            # Clear keys IMMEDIATELY to prevent system sound, before any processing
            logger.debug("🔄 Clearing current_keys BEFORE processing to prevent system sound")
            self.current_keys.clear()
            
            if self.on_hotkey_pressed:
                try:
                    self.on_hotkey_pressed()
                    logger.debug("✅ Hotkey processing completed successfully")
                except Exception as e:
                    logger.error(f"❌ Error in hotkey handler: {e}")
                    import traceback
                    traceback.print_exc()
                    # Keys already cleared above, so no need to clear again
    
    def on_key_release(self, key):
        """Handle key release events"""
        logger.debug(f"🔥 KEY RELEASE DETECTED: {key}")
        
        try:
            self.current_keys.remove(key)
            logger.debug(f"DEBUG: Removed key from current_keys")
        except KeyError:
            logger.debug(f"DEBUG: Key {key} not in current_keys")
            pass
    
    def start_listener(self):
        """Start the keyboard listener"""
        if self.is_running:
            logger.warning("Keyboard listener already running")
            return
        
        logger.info("🎹 Starting keyboard listener...")
        try:
            logger.debug("🔧 Creating Listener object...")
            # Create listener with darwin_intercept to filter mouse events on macOS
            listener_kwargs = {
                'on_press': self.on_key_press,
                'on_release': self.on_key_release
            }
            
            # Add macOS-specific event filtering to prevent mouse events from being detected as keyboard events
            if MACOS_EVENT_FILTERING_AVAILABLE:
                listener_kwargs['darwin_intercept'] = self.darwin_intercept
                logger.debug("🔧 Added darwin_intercept to filter mouse events on macOS")
            
            self.listener = Listener(**listener_kwargs)
            logger.debug("🔧 Calling listener.start()...")
            self.listener.start()
            self.is_running = True
            logger.info("✅ Keyboard listener started successfully")
            logger.debug("🔍 Listener should now capture ALL keystrokes - try pressing any key")
        except Exception as e:
            logger.error(f"❌ Failed to start keyboard listener: {e}")
            import traceback
            traceback.print_exc()
    
    def stop_listener(self):
        """Stop the keyboard listener"""
        if self.listener and self.is_running:
            try:
                self.listener.stop()
                self.is_running = False
                logger.info("🛑 Keyboard listener stopped")
            except Exception as e:
                logger.error(f"Failed to stop keyboard listener: {e}")
    
    def restart_listener(self):
        """Restart the keyboard listener"""
        logger.info("🔄 Restarting keyboard listener...")
        self.stop_listener()
        self.start_listener()
    
    def format_hotkey_display(self) -> str:
        """Format hotkey combination for display"""
        # Convert set back to readable string
        parts = []
        
        if Key.cmd in self.hotkey_combo:
            parts.append("Cmd")
        if Key.ctrl in self.hotkey_combo:
            parts.append("Ctrl")
        if Key.alt in self.hotkey_combo:
            parts.append("Alt")
        if Key.shift in self.hotkey_combo:
            parts.append("Shift")
        
        # Find character keys
        for key in self.hotkey_combo:
            if isinstance(key, keyboard.KeyCode) and key.char:
                parts.append(key.char.upper())
        
        return "+".join(parts) if parts else "Cmd+Shift+A" 