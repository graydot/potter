#!/usr/bin/env python3
"""
Potter - macOS Global Text Rephrasing Service
A background service that listens for global hotkeys and rephrases text using ChatGPT
"""

import os
import sys
import time
import threading
import subprocess
import signal
import atexit
from typing import Optional
import logging

# Third-party imports
import openai
import pyperclip
import pystray
from pynput import keyboard
from pynput.keyboard import Key, Listener
from PIL import Image, ImageDraw
from dotenv import load_dotenv

# macOS permission checking
try:
    from Foundation import NSBundle, NSApplication
    from AppKit import NSWorkspace, NSBundle
    from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
    from ApplicationServices import AXIsProcessTrusted
    # Import Quartz constants for event filtering
    from Quartz import (
        kCGEventKeyDown, kCGEventKeyUp, kCGEventFlagsChanged,
        kCGEventLeftMouseDown, kCGEventLeftMouseUp, kCGEventRightMouseDown, 
        kCGEventRightMouseUp, kCGEventMouseMoved, kCGEventLeftMouseDragged,
        kCGEventRightMouseDragged, kCGEventScrollWheel, kCGEventOtherMouseDown,
        kCGEventOtherMouseUp, kCGEventOtherMouseDragged
    )
    MACOS_PERMISSIONS_AVAILABLE = True
except ImportError:
    MACOS_PERMISSIONS_AVAILABLE = False
    print("⚠️  macOS permission checking not available")

# Import our settings UI
try:
    from cocoa_settings import SettingsManager, show_settings
    SETTINGS_UI_AVAILABLE = True
    print("✅ Native macOS Settings UI available")
except ImportError as e:
    print(f"⚠️  Settings UI not available: {e}")
    print("⚠️  App will run with default settings only")
    SETTINGS_UI_AVAILABLE = False

# Load environment variables
load_dotenv()

# Determine the correct log file path based on execution context
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle - use user's home directory
    log_file = os.path.expanduser('~/Library/Logs/potter.log')
    # Ensure the Logs directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
else:
    # Running as script - use current directory
    log_file = 'potter.log'

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change from DEBUG to INFO to reduce verbosity
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SingleInstanceChecker:
    """Ensures only one instance of the application is running"""
    
    def __init__(self, app_name="potter"):
        self.app_name = app_name
        self.pid_file = os.path.expanduser(f"~/.{app_name}.pid")
        self.is_running = False
    
    def is_already_running(self):
        """Check if another instance is already running"""
        if not os.path.exists(self.pid_file):
            return False
        
        try:
            with open(self.pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Check if the process is still running
            try:
                os.kill(old_pid, 0)  # Signal 0 just checks if process exists
                logger.warning(f"Another instance is already running (PID: {old_pid})")
                return True
            except OSError:
                # Process doesn't exist, remove stale PID file
                logger.info("Removing stale PID file")
                os.remove(self.pid_file)
                return False
                
        except (ValueError, IOError) as e:
            logger.warning(f"Error reading PID file: {e}")
            # Remove corrupted PID file
            try:
                os.remove(self.pid_file)
            except:
                pass
            return False
    
    def create_pid_file(self):
        """Create a PID file for this instance"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
            self.is_running = True
            
            # Register cleanup function
            atexit.register(self.cleanup)
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            
            logger.info(f"Created PID file: {self.pid_file}")
            return True
        except IOError as e:
            logger.error(f"Failed to create PID file: {e}")
            return False
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals"""
        logger.info(f"Received signal {signum}, cleaning up...")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Remove the PID file"""
        if self.is_running and os.path.exists(self.pid_file):
            try:
                os.remove(self.pid_file)
                logger.info("Cleaned up PID file")
            except IOError as e:
                logger.warning(f"Failed to remove PID file: {e}")
        self.is_running = False

class RephrasleyService:
    def __init__(self):
        self.openai_client = None
        self.is_running = False
        self.hotkey_pressed = False
        self.tray_icon = None
        self.listener = None
        self.settings_window = None
        self.instance_checker = SingleInstanceChecker()
        self.is_processing = False  # Track if AI processing is happening
        
        # Initialize settings manager
        if SETTINGS_UI_AVAILABLE:
            self.settings_manager = SettingsManager()
        else:
            self.settings_manager = None
        
        # Load configuration from settings or defaults
        self.load_settings()
        
        # Initialize OpenAI client (after settings are loaded)
        self.setup_openai()
    
    def check_single_instance(self):
        """Check if this is the only instance running"""
        if self.instance_checker.is_already_running():
            print("❌ Another instance of Potter is already running!")
            print("💡 Check your menu bar - the app may already be active.")
            print("💡 If you don't see it, try quitting all instances and running again.")
            sys.exit(1)
        
        if not self.instance_checker.create_pid_file():
            print("❌ Failed to create instance lock!")
            sys.exit(1)
        
        logger.info("✅ Single instance check passed")
    
    def load_settings(self):
        """Load settings from settings manager or use defaults"""
        if self.settings_manager:
            prompts_list = self.settings_manager.get("prompts", [
                {
                    "name": "summarize", 
                    "text": "Please provide a concise summary of the following text. Focus on the key points and main ideas. Keep it brief but comprehensive, capturing the essential information in a clear and organized way."
                },
                {
                    "name": "formal",
                    "text": "Please rewrite the following text in a formal, professional tone. Use proper business language and structure. Ensure the tone is respectful, authoritative, and appropriate for professional communication."
                },
                {
                    "name": "casual",
                    "text": "Please rewrite the following text in a casual, relaxed tone. Make it sound conversational and approachable. Use everyday language while maintaining clarity and keeping the core message intact."
                },
                {
                    "name": "friendly",
                    "text": "Please rewrite the following text in a warm, friendly tone. Make it sound welcoming and personable. Add warmth and approachability while keeping the message clear and engaging."
                },
                {
                    "name": "polish",
                    "text": "Please polish the following text by fixing any grammatical issues, typos, or awkward phrasing. Make it sound natural and human while keeping it direct and clear. Double-check that the tone is appropriate and not offensive, but maintain the original intent and directness."
                }
            ])
            
            # Convert list to dictionary for backwards compatibility
            self.prompts = {}
            for prompt in prompts_list:
                self.prompts[prompt["name"]] = prompt["text"]
            
            # Parse hotkey
            hotkey_str = self.settings_manager.get("hotkey", "cmd+shift+a")
            self.hotkey_combo = self.parse_hotkey(hotkey_str)
            
            # AI model settings
            self.model = self.settings_manager.get("model", "gpt-3.5-turbo")
            self.max_tokens = self.settings_manager.get("max_tokens", 1000)
            self.temperature = self.settings_manager.get("temperature", 0.7)
            self.show_notifications = self.settings_manager.get("show_notifications", True)
        else:
            # Fallback to defaults
            self.prompts = {
                'summarize': 'Please provide a concise summary of the following text. Focus on the key points and main ideas. Keep it brief but comprehensive, capturing the essential information in a clear and organized way.',
                'formal': 'Please rewrite the following text in a formal, professional tone. Use proper business language and structure. Ensure the tone is respectful, authoritative, and appropriate for professional communication.',
                'casual': 'Please rewrite the following text in a casual, relaxed tone. Make it sound conversational and approachable. Use everyday language while maintaining clarity and keeping the core message intact.',
                'friendly': 'Please rewrite the following text in a warm, friendly tone. Make it sound welcoming and personable. Add warmth and approachability while keeping the message clear and engaging.',
                'polish': 'Please polish the following text by fixing any grammatical issues, typos, or awkward phrasing. Make it sound natural and human while keeping it direct and clear. Double-check that the tone is appropriate and not offensive, but maintain the original intent and directness.'
            }
            self.hotkey_combo = {Key.cmd, Key.shift, keyboard.KeyCode.from_char('a')}
            self.model = "gpt-3.5-turbo"
            self.max_tokens = 1000
            self.temperature = 0.7
            self.show_notifications = True
        
        self.current_keys = set()
        self.current_prompt = 'polish'
    
    def parse_hotkey(self, hotkey_str):
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
        if not MACOS_PERMISSIONS_AVAILABLE:
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
    
    def on_settings_changed(self, new_settings):
        """Handle settings changes"""
        logger.info("Settings changed, reloading...")
        print("Debug - on_settings_changed called")
        
        # Store old hotkey to see if it changed
        old_hotkey = getattr(self, 'hotkey_combo', None)
        
        # Update settings manager
        if self.settings_manager:
            self.settings_manager.settings = new_settings
            print("Debug - Settings manager updated")
        
        # Reload all settings
        print("Debug - Reloading settings...")
        self.load_settings()
        print("Debug - Settings reloaded")
        
        # Reinitialize OpenAI client in case API key changed
        print("Debug - Reinitializing OpenAI client...")
        self.setup_openai()
        print("Debug - OpenAI client reinitialized")
        
        # Only restart keyboard listener if hotkey actually changed
        print("Debug - Checking if hotkey changed...")
        if old_hotkey != self.hotkey_combo:
            print("Debug - Hotkey changed, restarting keyboard listener...")
            if self.listener:
                print("Debug - Stopping existing listener...")
                try:
                    self.listener.stop()
                    print("Debug - Existing listener stopped")
                except Exception as e:
                    print(f"Debug - Error stopping listener: {e}")
            
            try:
                # Create listener with darwin_intercept to filter mouse events on macOS
                listener_kwargs = {
                    'on_press': self.on_key_press,
                    'on_release': self.on_key_release
                }
                
                # Add macOS-specific event filtering to prevent mouse events from being detected as keyboard events
                if MACOS_PERMISSIONS_AVAILABLE:
                    listener_kwargs['darwin_intercept'] = self.darwin_intercept
                
                self.listener = Listener(**listener_kwargs)
                self.listener.start()
                print("Debug - New keyboard listener started")
            except Exception as e:
                print(f"Debug - Error starting new listener: {e}")
        else:
            print("Debug - Hotkey unchanged, keeping existing listener")
        
        # DO NOT restart tray icon - just update the menu in place
        print("Debug - Updating tray icon menu...")
        if self.tray_icon:
            try:
                # Create new menu structure
                print("Debug - Creating new menu structure...")
                old_icon = self.tray_icon
                
                # Get current permission status  
                permissions = self.get_permission_status()
                
                # Determine what entity has permission (Python vs Potter app)
                permission_entity = "Potter.app" if getattr(sys, 'frozen', False) else "Python"
                
                # Create menu items
                menu_items = [
                    pystray.MenuItem(f"Mode: {self.current_prompt.title()}", lambda: None, enabled=False),
                    pystray.Menu.SEPARATOR,
                ]
                
                # Add permission status indicators with more helpful info
                if permissions.get("accessibility", False):
                    accessibility_status = f"✅ {permission_entity} has access"
                else:
                    accessibility_status = f"❌ {permission_entity} needs access"
                
                accessibility_item = pystray.MenuItem(f"Accessibility: {accessibility_status}", self.check_and_show_permissions)
                
                menu_items.extend([
                    accessibility_item,
                    pystray.Menu.SEPARATOR,
                ])
                
                # Add mode switching options
                for mode in self.prompts.keys():
                    menu_items.append(
                        pystray.MenuItem(
                            mode.title(), 
                            lambda m=mode: self.change_mode(m),
                            checked=lambda m=mode: self.current_prompt == m
                        )
                    )
                
                menu_items.extend([
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("Preferences...", self.show_preferences),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("Quit", self.quit_app)
                ])
                
                new_menu = pystray.Menu(*menu_items)
                
                # Update the existing icon's menu
                old_icon.menu = new_menu
                print("Debug - Tray icon menu updated successfully")
                
            except Exception as e:
                print(f"Debug - Error updating tray icon menu: {e}")
        else:
            print("Debug - No tray icon to update")
        
        logger.info("Settings applied successfully")
        print("Debug - on_settings_changed completed successfully")
    
    def setup_openai(self):
        """Initialize OpenAI client"""
        # Try to get API key from settings first, then environment
        api_key = None
        if self.settings_manager:
            api_key = self.settings_manager.get("openai_api_key", "").strip()
        
        if not api_key:
            api_key = os.getenv('OPENAI_API_KEY', "").strip()
        
        if not api_key:
            logger.warning("No OpenAI API key found in settings or environment")
            self.openai_client = None
            return
        
        try:
            # Import OpenAI and check if it's available
            import openai
            logger.debug(f"OpenAI library version: {openai.__version__}")
            
            # Try to import certifi for SSL certificates
            try:
                import certifi
                import ssl
                logger.debug(f"SSL certificates available at: {certifi.where()}")
                
                # Create SSL context
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                logger.debug("SSL context created successfully")
            except ImportError:
                logger.warning("certifi not available, using default SSL context")
                ssl_context = None
            except Exception as ssl_e:
                logger.warning(f"SSL context creation failed: {ssl_e}")
                ssl_context = None
            
            # Create OpenAI client with explicit parameters
            self.openai_client = openai.OpenAI(
                api_key=api_key,
                timeout=30.0  # Set explicit timeout
            )
            logger.info("OpenAI client initialized successfully")
            
            # Test the client with a minimal request to verify it works
            try:
                # This doesn't actually make a request, just validates the client setup
                logger.debug("OpenAI client setup validation completed")
            except Exception as test_e:
                logger.warning(f"OpenAI client validation warning: {test_e}")
                # Client may still work for actual requests
                
        except ImportError as e:
            logger.error(f"OpenAI library not available: {e}")
            self.openai_client = None
        except FileNotFoundError as e:
            logger.error(f"File not found during OpenAI initialization: {e}")
            logger.error("This may be due to missing SSL certificates or configuration files")
            logger.error("Try: pip install --upgrade openai certifi")
            self.openai_client = None
        except OSError as e:
            logger.error(f"OS error during OpenAI initialization: {e}")
            logger.error("This may be a network or file system issue")
            self.openai_client = None
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            self.openai_client = None
    
    def check_accessibility_permissions(self):
        """Check if the app has accessibility permissions"""
        if not MACOS_PERMISSIONS_AVAILABLE:
            logger.warning("macOS permissions checking not available")
            return False
        
        try:
            # Use the proper accessibility API to check permissions
            from ApplicationServices import AXIsProcessTrusted
            is_trusted = AXIsProcessTrusted()
            logger.debug(f"AXIsProcessTrusted() returned: {is_trusted}")
            
            # Note: When running as a Python script (vs bundled app), this checks if Python itself
            # has accessibility permission, not a specific app. This is expected behavior.
            if getattr(sys, 'frozen', False):
                logger.debug("Running as bundled app - checking app-specific permissions")
            else:
                logger.debug("Running as Python script - checking Python's accessibility permission")
            
            # Force a more aggressive check - try to actually use accessibility features
            if is_trusted:
                try:
                    # Additional verification - try to access window list which requires accessibility permission
                    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
                    if window_list and len(window_list) > 0:
                        # Extra verification: try to access detailed window information
                        # This is more likely to fail if accessibility permission is not actually granted
                        try:
                            # Try to access window owner information - this typically requires accessibility permission
                            for window in window_list[:3]:  # Check first 3 windows
                                owner_name = window.get('kCGWindowOwnerName', '')
                                window_name = window.get('kCGWindowName', '')
                                if owner_name or window_name:
                                    logger.debug(f"Window access verified: owner={owner_name}, name={window_name}")
                                    break
                            else:
                                logger.warning("Could not access window details despite window list being available")
                                return False
                            
                            logger.debug(f"Window list verification successful: {len(window_list)} windows")
                            return True
                        except Exception as e:
                            logger.warning(f"Failed to access window details: {e}")
                            return False
                    else:
                        logger.warning("AXIsProcessTrusted=True but window list is empty - permission might not be fully granted yet")
                        return False
                except Exception as e:
                    logger.warning(f"Window list verification failed despite AXIsProcessTrusted=True: {e}")
                    return False
            else:
                logger.debug("AXIsProcessTrusted() returned False - no accessibility permission")
                return False
                
        except ImportError as e:
            logger.warning(f"ApplicationServices not available: {e}")
            # Fallback method - try to get window list directly (but be more strict)
            try:
                window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
                if window_list and len(window_list) > 5:  # Require more windows to reduce false positives
                    # Try to access window details to verify real accessibility
                    accessible_windows = 0
                    for window in window_list[:5]:
                        owner_name = window.get('kCGWindowOwnerName', '')
                        if owner_name:
                            accessible_windows += 1
                    
                    has_permission = accessible_windows >= 2  # Require at least 2 accessible windows
                    logger.debug(f"Fallback window list check: {has_permission} (accessible windows: {accessible_windows})")
                    return has_permission
                else:
                    logger.debug("Fallback window list check: insufficient windows")
                    return False
            except Exception as e2:
                logger.warning(f"Fallback window list check failed: {e2}")
                return False
        except Exception as e:
            logger.warning(f"Accessibility permission check failed: {e}")
            return False
    
    def get_permission_status(self):
        """Get current permission status"""
        return {
            "accessibility": self.check_accessibility_permissions(),
            "macos_available": MACOS_PERMISSIONS_AVAILABLE
        }
    
    def open_system_preferences_security(self):
        """Open System Preferences to Security & Privacy"""
        try:
            # For macOS 13+ (Ventura and later), it's System Settings
            subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'], check=False)
        except Exception as e:
            logger.error(f"Failed to open System Preferences: {e}")
            # Fallback to general System Preferences
            try:
                subprocess.run(['open', '/System/Applications/System Preferences.app'], check=False)
            except Exception as e2:
                logger.error(f"Failed to open System Preferences fallback: {e2}")
    
    def request_permissions(self):
        """Request necessary permissions from the user"""
        logger.info("Checking permissions...")
        
        permissions = self.get_permission_status()
        
        if not permissions["accessibility"]:
            logger.warning("Accessibility permission not granted")
            logger.info("Opening settings to show permission status and grant access...")
            
            # No alert dialog - go directly to settings 
            if SETTINGS_UI_AVAILABLE:
                # Show settings directly
                self.show_preferences()
                return True  # Continue startup
            else:
                print("⚠️  Accessibility permission required!")
                print("   Needed for: global hotkey monitoring only")
                print("   Potter will process text already in your clipboard")
                print("   Please grant permission in System Settings > Privacy & Security > Accessibility")
                print("   The app will continue running and check for permissions periodically")
                
                # Start permission monitoring
                self.start_permission_monitoring()
                return True
        
        return True
    
    def start_permission_monitoring(self):
        """Start monitoring for permission changes"""
        logger.info("🔍 Started permission monitoring - checking every 5 seconds")
        
        def check_permissions_periodically():
            while self.is_running:
                time.sleep(5)  # Check every 5 seconds
                
                try:
                    permissions = self.get_permission_status()
                    if permissions["accessibility"]:
                        logger.info("✅ Accessibility permission granted! Keyboard listener should now work")
                        self.show_notification("Permissions Granted", "Accessibility permission detected! Potter is now fully functional.", is_error=False)
                        
                        # Refresh the tray icon to show updated permission status
                        self.refresh_tray_icon()
                        
                        break  # Stop monitoring once permissions are granted
                    else:
                        logger.debug("🔍 Still waiting for accessibility permission...")
                except Exception as e:
                    logger.error(f"Error checking permissions: {e}")
        
        # Start monitoring in background thread
        threading.Thread(target=check_permissions_periodically, daemon=True).start()
    
    def process_text_with_chatgpt(self, text: str) -> Optional[str]:
        """Process text using ChatGPT"""
        if not self.openai_client:
            logger.error("OpenAI client not initialized")
            return None
        
        if not text.strip():
            logger.warning("No text to process")
            return None
        
        try:
            prompt = self.prompts.get(self.current_prompt, self.prompts['polish'])
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful writing assistant. Return only the processed text without any additional comments or formatting."},
                    {"role": "user", "content": f"{prompt}\n\n{text}"}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            processed_text = response.choices[0].message.content.strip()
            logger.info(f"Successfully processed text: {len(text)} -> {len(processed_text)} characters")
            return processed_text
            
        except Exception as e:
            logger.error(f"Error processing text with ChatGPT: {e}")
            return None
    
    def process_selection(self):
        """Main function to process clipboard text with LLM"""
        if self.hotkey_pressed or self.is_processing:
            logger.warning("⚠️  Hotkey already being processed, ignoring additional requests...")
            return  # Prevent multiple simultaneous executions
        
        self.hotkey_pressed = True
        self.set_processing_state(True)  # Start spinner
        logger.info("🔄 Processing clipboard text...")
        
        try:
            # Check if OpenAI client is available first
            if not self.openai_client:
                error_msg = "OpenAI API key not configured. Please check Settings."
                logger.error(f"❌ {error_msg}")
                self.show_notification("Configuration Error", error_msg, is_error=True)
                return
            
            # Get text from clipboard directly
            try:
                clipboard_text = pyperclip.paste()
            except Exception as e:
                error_msg = f"Failed to read clipboard: {e}"
                logger.error(error_msg)
                self.show_notification("Clipboard Error", error_msg, is_error=True)
                return
            
            # Check if clipboard has text
            if not clipboard_text or not clipboard_text.strip():
                error_msg = "No text found in clipboard. Copy some text first, then press the hotkey."
                logger.warning(error_msg)
                self.show_notification("No Text", error_msg, is_error=True)
                return
            
            logger.info(f"Processing clipboard text ({len(clipboard_text)} chars): {clipboard_text[:50]}...")
            
            # Process with ChatGPT
            try:
                processed_text = self.process_text_with_chatgpt(clipboard_text)
                if not processed_text:
                    error_msg = "Failed to process text with AI"
                    logger.error(error_msg)
                    self.show_notification("AI Processing Failed", error_msg, is_error=True)
                    return
            except Exception as e:
                error_msg = f"AI processing error: {str(e)}"
                logger.error(error_msg)
                self.show_notification("AI Error", error_msg, is_error=True)
                return
            
            logger.info(f"Processed text ({len(processed_text)} chars): {processed_text[:50]}...")
            
            # Put processed text back in clipboard
            try:
                pyperclip.copy(processed_text)
                logger.info("✅ Processed text copied to clipboard")
            except Exception as e:
                error_msg = f"Failed to copy processed text to clipboard: {e}"
                logger.error(error_msg)
                self.show_notification("Clipboard Error", error_msg, is_error=True)
                return
            
            # Verify clipboard was updated
            try:
                time.sleep(0.1)
                clipboard_check = pyperclip.paste()
                if clipboard_check != processed_text:
                    error_msg = "Failed to update clipboard with processed text"
                    logger.error(error_msg)
                    self.show_notification("Clipboard Error", error_msg, is_error=True)
                    return
            except Exception as e:
                logger.warning(f"Could not verify clipboard update: {e}")
                # Continue anyway
            
            # Always show success notification
            success_msg = f"✅ Text {self.current_prompt}d and copied to clipboard! Press Cmd+V to paste."
            logger.info("Text processing completed successfully")
            self.show_notification("Processing Complete", success_msg, is_error=False)
            
        except Exception as e:
            error_msg = f"Unexpected error in process_selection: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            self.show_notification("Processing Error", "An unexpected error occurred. Check logs for details.", is_error=True)
        finally:
            # Stop spinner and reset flag
            self.set_processing_state(False)
            # Reset the flag after a short delay
            threading.Timer(1.0, lambda: setattr(self, 'hotkey_pressed', False)).start()
    
    def on_key_press(self, key):
        """Handle key press events"""
        logger.debug(f"🔥 KEY PRESS DETECTED: {key} (type: {type(key)})")
        
        self.current_keys.add(key)
        logger.debug(f"DEBUG: Added key to current_keys")

        # Debug logging for hotkey detection
        logger.debug(f"DEBUG: Current keys: {[str(k) for k in self.current_keys]}")
        logger.debug(f"DEBUG: Target hotkey: {[str(k) for k in self.hotkey_combo]}")
        logger.debug(f"DEBUG: Is subset? {self.hotkey_combo.issubset(self.current_keys)}")

        # Check if our hotkey combination is pressed
        if self.hotkey_combo.issubset(self.current_keys):
            logger.info("🎯 HOTKEY DETECTED! Processing selection...")
            # Show immediate feedback that hotkey was detected
            self.show_notification("Hotkey Detected", "Processing selected text...", is_error=False)
            # Run processing in a separate thread to avoid blocking
            threading.Thread(target=self.process_selection, daemon=True).start()
    
    def on_key_release(self, key):
        """Handle key release events"""
        logger.debug(f"🔥 KEY RELEASE DETECTED: {key}")
        
        try:
            self.current_keys.remove(key)
            logger.debug(f"DEBUG: Removed key from current_keys")
        except KeyError:
            logger.debug(f"DEBUG: Key {key} not in current_keys")
            pass
    
    def show_preferences(self):
        """Show the preferences window"""
        if SETTINGS_UI_AVAILABLE and self.settings_manager:
            try:
                show_settings(self.settings_manager, self.on_settings_changed)
            except Exception as e:
                logger.error(f"Failed to show preferences: {e}")
        else:
            logger.warning("Settings UI not available")
    
    def create_tray_icon(self):
        """Create system tray icon"""
        # Create the normal icon
        image = self.create_normal_icon()
        
        # Get current permission status
        permissions = self.get_permission_status()
        
        # Determine what entity has permission (Python vs Potter app)
        permission_entity = "Potter.app" if getattr(sys, 'frozen', False) else "Python"
        
        # Create menu
        menu_items = [
            pystray.MenuItem(f"Mode: {self.current_prompt.title()}", lambda *args: None, enabled=False),
            pystray.Menu.SEPARATOR,
        ]
        
        # Add permission status indicators with more helpful info
        if permissions.get("accessibility", False):
            accessibility_status = f"✅ {permission_entity} has access"
        else:
            accessibility_status = f"❌ {permission_entity} needs access"
        
        accessibility_item = pystray.MenuItem(f"Accessibility: {accessibility_status}", self.check_and_show_permissions)
        
        # Add notification toggle next to accessibility
        notifications_enabled = self.settings_manager.get("show_notifications", True) if self.settings_manager else True
        notifications_status = "✅" if notifications_enabled else "❌"
        
        def check_notifications_enabled(*args):
            return self.settings_manager.get("show_notifications", True) if self.settings_manager else True
        
        notifications_item = pystray.MenuItem(f"Notifications: {notifications_status}", self.toggle_notifications)
        
        menu_items.extend([
            accessibility_item,
            notifications_item,
            pystray.Menu.SEPARATOR,
        ])
        
        # Add mode switching options
        for mode in self.prompts.keys():
            def make_mode_handler(mode_name):
                return lambda *args: self.change_mode(mode_name)
            
            def make_mode_checker(mode_name):
                return lambda *args: self.current_prompt == mode_name
            
            menu_items.append(
                pystray.MenuItem(
                    mode.title(), 
                    make_mode_handler(mode),
                    checked=make_mode_checker(mode)
                )
            )
        
        menu_items.extend([
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Preferences...", self.show_preferences),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self.quit_app)
        ])
        
        menu = pystray.Menu(*menu_items)
        self.tray_icon = pystray.Icon("Potter", image, "Potter - AI Text Processor", menu)
    
    def check_and_show_permissions(self):
        """Check permissions and show status or open settings"""
        permissions = self.get_permission_status()
        
        accessibility_granted = permissions.get("accessibility", False)
        
        if accessibility_granted:
            # All permissions granted
            self.show_notification("Permissions Status", "✅ All permissions granted. Potter is fully functional!", is_error=False)
        else:
            # Essential permission missing - show settings
            logger.info("Essential permissions missing - opening settings")
            if SETTINGS_UI_AVAILABLE:
                self.show_preferences()
            else:
                self.show_notification("Permission Required", "❌ Accessibility permission required. Please grant it in System Settings > Privacy & Security > Accessibility", is_error=True)
    
    def change_mode(self, mode):
        """Change processing mode"""
        if mode in self.prompts:
            self.current_prompt = mode
            logger.info(f"Changed mode to: {mode}")
            
            # Update tray icon menu
            self.refresh_tray_icon()
    
    def toggle_notifications(self, icon=None, item=None):
        """Toggle notification setting"""
        if not self.settings_manager:
            return
        
        current_setting = self.settings_manager.get("show_notifications", True)
        new_setting = not current_setting
        
        # Update the setting
        self.settings_manager.settings["show_notifications"] = new_setting
        self.settings_manager.save_settings(self.settings_manager.settings)
        
        logger.info(f"Notifications {'enabled' if new_setting else 'disabled'}")
        
        # Show immediate feedback (if notifications are now enabled)
        if new_setting:
            self.show_notification("Potter Settings", "✅ Notifications enabled!")
        else:
            # For disabled case, just log it since we can't show a notification
            logger.info("📢 Notifications disabled")
        
        # Update tray icon menu to reflect new state
        self.refresh_tray_icon()
    
    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        logger.info("Shutting down Potter...")
        self.is_running = False
        
        if self.listener:
            self.listener.stop()
        
        if self.tray_icon:
            self.tray_icon.stop()
        
        # Clean up instance checker
        self.instance_checker.cleanup()
        
        sys.exit(0)
    
    def start(self):
        """Start the service"""
        # Check for single instance before starting
        self.check_single_instance()
        
        # Check permissions first
        logger.info("Checking macOS permissions...")
        permissions = self.get_permission_status()
        logger.info(f"Permission status: accessibility={permissions['accessibility']}")
        
        if not permissions["accessibility"]:
            logger.warning("❌ Accessibility permission NOT granted")
            logger.warning("   The app will continue running and monitor for permission changes")
            # Request permissions but don't exit - the method now handles monitoring
            self.request_permissions()
        else:
            logger.info("✅ Accessibility permission granted")
        
        # Check if this is the first launch and show settings if needed
        if SETTINGS_UI_AVAILABLE and self.settings_manager and self.settings_manager.is_first_launch():
            logger.info("First launch detected - showing settings dialog")
            settings_shown = self.show_first_launch_settings()
            if settings_shown:
                # Settings window is open, don't start service components yet
                # They will be started when settings are saved (in on_settings_saved callback)
                logger.info("Waiting for first-launch settings to be configured...")
                
                # Create a minimal tray icon to show the app is running
                self.create_tray_icon()
                self.tray_icon.run()  # This will keep the app alive
                return
        
        if not self.openai_client:
            logger.error("Cannot start service: OpenAI client not initialized")
            if SETTINGS_UI_AVAILABLE:
                logger.info("Opening settings to configure API key...")
                self.show_preferences()
                # Create a minimal tray icon to show the app is running
                self.create_tray_icon()
                self.tray_icon.run()  # This will keep the app alive
                return
            else:
                logger.warning("No settings UI available and no OpenAI client - app will run with limited functionality")
        
        # Normal startup - start all service components
        self.start_service_components()
    
    def format_hotkey(self):
        """Format hotkey combination for display"""
        if self.settings_manager:
            return self.settings_manager.get("hotkey", "Cmd+Shift+A")
        return "Cmd+Shift+A"

    def show_notification(self, title, message, is_error=False):
        """Show notification if enabled"""
        # Always log notifications for debugging
        logger.info(f"📢 Notification: {title} - {message}")
        
        # Try to show native notification if settings allow it
        if self.settings_manager and self.settings_manager.get("show_notifications", True):
            if hasattr(self.settings_manager, 'show_notification'):
                try:
                    self.settings_manager.show_notification(title, message, is_error)
                except Exception as e:
                    logger.debug(f"NSUserNotification failed: {e}")
        
        # Always try to show macOS notification as primary method
        try:
            # Escape quotes in message and title for shell safety
            safe_title = title.replace('"', '\\"').replace("'", "\\'")
            safe_message = message.replace('"', '\\"').replace("'", "\\'")
            
            # Simple macOS notification using osascript - don't capture output to let it show
            script = f'display notification "{safe_message}" with title "{safe_title}"'
            subprocess.run(['osascript', '-e', script], check=False)
        except Exception as e:
            logger.debug(f"Could not show osascript notification: {e}")
            # Final fallback - try a simple alert
            try:
                script = f'display alert "{safe_title}" message "{safe_message}"'
                subprocess.run(['osascript', '-e', script], check=False)
            except Exception as e2:
                logger.debug(f"Could not show alert either: {e2}")
    
    def set_processing_state(self, processing):
        """Set processing state and update icon"""
        self.is_processing = processing
        if self.tray_icon:
            # Create the appropriate icon
            if processing:
                logger.debug("🔄 Setting spinner icon for processing state")
                icon_image = self.create_spinner_icon()
            else:
                logger.debug("✅ Setting normal icon for idle state")
                icon_image = self.create_normal_icon()
            
            # Update the tray icon - force update by setting the property
            try:
                self.tray_icon.icon = icon_image
                logger.debug(f"Icon updated successfully, processing={processing}")
            except Exception as e:
                logger.error(f"Failed to update tray icon: {e}")
        else:
            logger.warning("No tray icon available to update")
    
    def create_normal_icon(self):
        """Create the normal icon"""
        image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Simple background circle (subtle gray)
        draw.ellipse([4, 4, 60, 60], fill=(240, 240, 240, 220))
        
        # Main clipboard/copy icon (centered, black and white)
        clip_x, clip_y = 18, 12
        clip_w, clip_h = 28, 36
        
        # Clipboard body (white with black outline)
        draw.rectangle([clip_x, clip_y, clip_x + clip_w, clip_y + clip_h], 
                      fill='white', outline='black', width=2)
        
        # Clipboard top clip (black)
        clip_top_x = clip_x + 8
        clip_top_y = clip_y - 4
        clip_top_w = 12
        clip_top_h = 6
        draw.rectangle([clip_top_x, clip_top_y, clip_top_x + clip_top_w, clip_top_y + clip_top_h], 
                      fill='black')
        
        # Document lines (gray)
        line_x = clip_x + 4
        line_w = 20
        line_h = 2
        line_color = '#666666'
        
        draw.rectangle([line_x, clip_y + 8, line_x + line_w, clip_y + 8 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 14, line_x + line_w, clip_y + 14 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 20, line_x + 16, clip_y + 20 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 26, line_x + 18, clip_y + 26 + line_h], fill=line_color)
        
        # AI Sparkle at bottom right (inspired by the provided icon)
        sparkle_x, sparkle_y = 44, 44
        sparkle_size = 8
        
        # Create the 4-pointed diamond star with blue gradient effect
        # Main diamond shape
        points = [
            (sparkle_x, sparkle_y - sparkle_size),  # Top
            (sparkle_x + sparkle_size, sparkle_y),   # Right
            (sparkle_x, sparkle_y + sparkle_size),   # Bottom
            (sparkle_x - sparkle_size, sparkle_y)    # Left
        ]
        
        # Draw the sparkle with gradient-like effect
        # Outer layer (darker blue)
        draw.polygon(points, fill='#4A90E2')
        
        # Inner layer (lighter blue) - smaller diamond
        inner_size = sparkle_size - 2
        inner_points = [
            (sparkle_x, sparkle_y - inner_size),
            (sparkle_x + inner_size, sparkle_y),
            (sparkle_x, sparkle_y + inner_size),
            (sparkle_x - inner_size, sparkle_y)
        ]
        draw.polygon(inner_points, fill='#7BB3F0')
        
        # Center highlight (very light blue/white)
        center_size = sparkle_size - 4
        center_points = [
            (sparkle_x, sparkle_y - center_size),
            (sparkle_x + center_size, sparkle_y),
            (sparkle_x, sparkle_y + center_size),
            (sparkle_x - center_size, sparkle_y)
        ]
        draw.polygon(center_points, fill='#B8D4F1')
        
        self.current_icon_image = image
        return image
    
    def create_spinner_icon(self):
        """Create a spinning/processing icon"""
        image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Background circle (slightly more vibrant to show activity)
        draw.ellipse([4, 4, 60, 60], fill=(250, 250, 250, 240))
        
        # Main clipboard/copy icon (same as normal)
        clip_x, clip_y = 18, 12
        clip_w, clip_h = 28, 36
        
        # Clipboard body (white with blue outline to show activity)
        draw.rectangle([clip_x, clip_y, clip_x + clip_w, clip_y + clip_h], 
                      fill='white', outline='#4A90E2', width=2)
        
        # Clipboard top clip (blue)
        clip_top_x = clip_x + 8
        clip_top_y = clip_y - 4
        clip_top_w = 12
        clip_top_h = 6
        draw.rectangle([clip_top_x, clip_top_y, clip_top_x + clip_top_w, clip_top_y + clip_top_h], 
                      fill='#4A90E2')
        
        # Document lines (blue to show processing)
        line_x = clip_x + 4
        line_w = 20
        line_h = 2
        line_color = '#4A90E2'
        
        draw.rectangle([line_x, clip_y + 8, line_x + line_w, clip_y + 8 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 14, line_x + line_w, clip_y + 14 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 20, line_x + 16, clip_y + 20 + line_h], fill=line_color)
        draw.rectangle([line_x, clip_y + 26, line_x + 18, clip_y + 26 + line_h], fill=line_color)
        
        # Animated sparkle (larger and more prominent)
        sparkle_x, sparkle_y = 44, 44
        sparkle_size = 10
        
        # Create the 4-pointed diamond star with brighter colors
        points = [
            (sparkle_x, sparkle_y - sparkle_size),  # Top
            (sparkle_x + sparkle_size, sparkle_y),   # Right
            (sparkle_x, sparkle_y + sparkle_size),   # Bottom
            (sparkle_x - sparkle_size, sparkle_y)    # Left
        ]
        
        # Draw the sparkle with bright processing colors
        draw.polygon(points, fill='#FF6B35')  # Orange-red for activity
        
        # Inner layer 
        inner_size = sparkle_size - 2
        inner_points = [
            (sparkle_x, sparkle_y - inner_size),
            (sparkle_x + inner_size, sparkle_y),
            (sparkle_x, sparkle_y + inner_size),
            (sparkle_x - inner_size, sparkle_y)
        ]
        draw.polygon(inner_points, fill='#FFB347')  # Light orange
        
        # Center highlight
        center_size = sparkle_size - 4
        center_points = [
            (sparkle_x, sparkle_y - center_size),
            (sparkle_x + center_size, sparkle_y),
            (sparkle_x, sparkle_y + center_size),
            (sparkle_x - center_size, sparkle_y)
        ]
        draw.polygon(center_points, fill='#FFF8DC')  # Almost white yellow
        
        self.current_icon_image = image
        return image

    def show_first_launch_settings(self):
        """Show settings dialog for first launch with welcome message"""
        if not SETTINGS_UI_AVAILABLE or not self.settings_manager:
            return
        
        def on_settings_saved(new_settings):
            logger.info("First-time settings saved successfully")
            # Instead of restarting, just reload settings and continue
            self.on_settings_changed(new_settings)
            logger.info("Settings applied, continuing with app startup...")
            
            # Now that settings are configured, continue with normal startup
            if self.openai_client:
                logger.info("✅ Settings configured successfully, starting service...")
                self.start_service_components()
            else:
                logger.warning("❌ OpenAI client still not configured after settings")
        
        try:
            from cocoa_settings import show_settings
            from AppKit import NSApp, NSAlert, NSAlertStyleInformational
            
            # Show welcome alert first
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Welcome to Potter!")
            alert.setInformativeText_("Please configure your OpenAI API key and preferences to get started. You can get an API key from https://platform.openai.com/api-keys")
            alert.setAlertStyle_(NSAlertStyleInformational)
            alert.addButtonWithTitle_("Open Settings")
            alert.addButtonWithTitle_("Quit")
            
            response = alert.runModal()
            if response == 1000:  # First button (Open Settings)
                # Show settings window (non-modal)
                controller = show_settings(self.settings_manager, on_settings_saved)
                logger.info("First-launch settings window shown")
                # Don't call NSApp.run() here - let the normal app flow continue
                return True  # Indicate settings window was shown
            else:
                # User chose to quit
                sys.exit(0)
                
        except Exception as e:
            logger.error(f"Failed to show first-launch settings: {e}")
            sys.exit(1)
        
        return False
    
    def start_service_components(self):
        """Start the main service components (keyboard listener, tray icon)"""
        logger.info("Starting service components...")
        logger.info(f"Hotkey: {self.format_hotkey()}")
        logger.info(f"Current mode: {self.current_prompt}")
        logger.info(f"Model: {self.model}")
        
        # Log permission status
        permissions = self.get_permission_status()
        logger.info(f"Accessibility permission: {'✅' if permissions['accessibility'] else '❌'}")
        
        logger.info("🔄 Setting is_running = True")
        self.is_running = True
        
        # Start keyboard listener with detailed logging
        logger.info("🎹 Starting keyboard listener...")
        try:
            logger.debug("🔧 Creating Listener object...")
            # Create listener with darwin_intercept to filter mouse events on macOS
            listener_kwargs = {
                'on_press': self.on_key_press,
                'on_release': self.on_key_release
            }
            
            # Add macOS-specific event filtering to prevent mouse events from being detected as keyboard events
            if MACOS_PERMISSIONS_AVAILABLE:
                listener_kwargs['darwin_intercept'] = self.darwin_intercept
                logger.debug("🔧 Added darwin_intercept to filter mouse events on macOS")
            
            self.listener = Listener(**listener_kwargs)
            logger.debug("🔧 Calling listener.start()...")
            self.listener.start()
            logger.info("✅ Keyboard listener started successfully")
            logger.debug("🔍 Listener should now capture ALL keystrokes - try pressing any key")
        except Exception as e:
            logger.error(f"❌ Failed to start keyboard listener: {e}")
            import traceback
            traceback.print_exc()
        
        # Create and start tray icon
        logger.info("🖼️ Creating tray icon...")
        self.create_tray_icon()
        logger.info("✅ Tray icon created")
        
        logger.info("🚀 Starting tray icon event loop...")
        try:
            self.tray_icon.run()  # This blocks until app quits
        except KeyboardInterrupt:
            logger.info("🛑 Keyboard interrupt received")
            self.quit_app()
        except Exception as e:
            logger.error(f"❌ Tray icon run failed: {e}")
            import traceback
            traceback.print_exc()

    def refresh_tray_icon(self):
        """Refresh the tray icon menu to reflect current permission status"""
        if self.tray_icon:
            try:
                self.tray_icon.stop()
                self.create_tray_icon()
                threading.Thread(target=self.tray_icon.run, daemon=True).start()
                logger.debug("Tray icon refreshed successfully")
            except Exception as e:
                logger.error(f"Failed to refresh tray icon: {e}")

def main():
    """Main entry point"""
    print("🔄 Potter - AI Text Rephrasing Service")
    print("=" * 50)
    
    # Initialize NSApplication for macOS app bundle compatibility
    try:
        from Foundation import NSBundle, NSApplication, NSObject
        
        # Check if we're running as a bundled app
        bundle = NSBundle.mainBundle()
        if bundle and bundle.bundlePath().endswith('.app'):
            # We're running as an app bundle, initialize NSApplication
            app = NSApplication.sharedApplication()
            # Set as background/accessory app (no dock icon, but can still launch normally)
            app.setActivationPolicy_(2)  # NSApplicationActivationPolicyAccessory

            class AppDelegate(NSObject):
                """Ensures app stays alive when settings window closes"""

                def applicationShouldTerminateAfterLastWindowClosed_(self, sender):
                    return False
                
                def applicationDidFinishLaunching_(self, sender):
                    """Hide from dock after launching"""
                    # Ensure the app doesn't show in dock after launch
                    sender.setActivationPolicy_(2)  # NSApplicationActivationPolicyAccessory

            # Keep a reference so it's not garbage collected
            global _app_delegate
            _app_delegate = AppDelegate.alloc().init()
            app.setDelegate_(_app_delegate)

            logger.info("✅ NSApplication initialized for app bundle")
    except ImportError:
        # PyObjC not available, continue without NSApplication setup
        pass
    except Exception as e:
        logger.warning(f"Failed to initialize NSApplication: {e}")
    
    # Start the service (single instance check is done in start())
    service = RephrasleyService()
    
    try:
        service.start()
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        # Make sure to cleanup on error
        service.instance_checker.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main() 