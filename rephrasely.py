#!/usr/bin/env python3
"""
Rephrasely - macOS Global Text Rephrasing Service
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

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Enable debug logging temporarily
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rephrasely.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SingleInstanceChecker:
    """Ensures only one instance of the application is running"""
    
    def __init__(self, app_name="rephrasely"):
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
            print("❌ Another instance of Rephrasely is already running!")
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
                    "name": "rephrase",
                    "text": "Please rephrase the following text to make it clearer and more professional:",
                    "output_format": "text"
                },
                {
                    "name": "summarize", 
                    "text": "Please provide a concise summary of the following text:",
                    "output_format": "text"
                },
                {
                    "name": "expand",
                    "text": "Please expand on the following text with more detail and examples:",
                    "output_format": "text"
                },
                {
                    "name": "casual",
                    "text": "Please rewrite the following text in a more casual, friendly tone:",
                    "output_format": "text"
                },
                {
                    "name": "formal",
                    "text": "Please rewrite the following text in a more formal, professional tone:",
                    "output_format": "text"
                }
            ])
            
            # Convert list to dictionary for backwards compatibility
            self.prompts = {}
            for prompt in prompts_list:
                self.prompts[prompt["name"]] = prompt["text"]
            
            # Parse hotkey
            hotkey_str = self.settings_manager.get("hotkey", "cmd+shift+r")
            self.hotkey_combo = self.parse_hotkey(hotkey_str)
            
            # AI model settings
            self.model = self.settings_manager.get("model", "gpt-3.5-turbo")
            self.max_tokens = self.settings_manager.get("max_tokens", 1000)
            self.temperature = self.settings_manager.get("temperature", 0.7)
            self.auto_paste = self.settings_manager.get("auto_paste", True)
            self.show_notifications = self.settings_manager.get("show_notifications", True)
        else:
            # Fallback to defaults
            self.prompts = {
                'rephrase': 'Please rephrase the following text to make it clearer and more professional:',
                'summarize': 'Please provide a concise summary of the following text:',
                'expand': 'Please expand on the following text with more detail and examples:',
                'casual': 'Please rewrite the following text in a more casual, friendly tone:',
                'formal': 'Please rewrite the following text in a more formal, professional tone:'
            }
            self.hotkey_combo = {Key.cmd, Key.shift, keyboard.KeyCode.from_char('r')}
            self.model = "gpt-3.5-turbo"
            self.max_tokens = 1000
            self.temperature = 0.7
            self.auto_paste = True
            self.show_notifications = True
        
        self.current_keys = set()
        self.current_prompt = 'rephrase'
    
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
            
            return keys if keys else {Key.cmd, Key.shift, keyboard.KeyCode.from_char('r')}
        except Exception as e:
            logger.error(f"Failed to parse hotkey '{hotkey_str}': {e}")
            return {Key.cmd, Key.shift, keyboard.KeyCode.from_char('r')}
    
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
                self.listener = Listener(
                    on_press=self.on_key_press,
                    on_release=self.on_key_release
                )
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
                
                # Create menu items
                menu_items = [
                    pystray.MenuItem(f"Mode: {self.current_prompt.title()}", lambda: None, enabled=False),
                    pystray.Menu.SEPARATOR,
                ]
                
                # Add permission status indicators
                accessibility_status = "✅" if permissions.get("accessibility", False) else "❌"
                
                menu_items.extend([
                    pystray.MenuItem(f"Accessibility (Copy/Type) {accessibility_status}", lambda: None, enabled=False),
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
            self.openai_client = openai.OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.openai_client = None
    
    def check_accessibility_permissions(self):
        """Check if the app has accessibility permissions"""
        if not MACOS_PERMISSIONS_AVAILABLE:
            return False
        
        try:
            # Use the proper accessibility API to check permissions
            from ApplicationServices import AXIsProcessTrusted
            is_trusted = AXIsProcessTrusted()
            logger.info(f"Accessibility permission check: {is_trusted}")
            return is_trusted
        except ImportError:
            logger.warning("ApplicationServices not available, falling back to window list check")
            try:
                # Fallback method - try to get window list
                window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
                return window_list and len(window_list) > 0
            except Exception as e:
                logger.warning(f"Window list check failed: {e}")
                return False
        except Exception as e:
            logger.warning(f"Accessibility permission check failed: {e}")
            return False
    
    def check_screen_recording_permissions(self):
        """Check if the app has screen recording permissions (needed for some keyboard monitoring)"""
        if not MACOS_PERMISSIONS_AVAILABLE:
            return False
        
        try:
            # Try to capture screen content
            from Quartz import CGWindowListCreateImage, CGRectNull, kCGWindowListOptionOnScreenOnly
            image = CGWindowListCreateImage(CGRectNull, kCGWindowListOptionOnScreenOnly, kCGNullWindowID, 0)
            return image is not None
        except Exception as e:
            logger.warning(f"Screen recording permission check failed: {e}")
            return False
    
    def get_permission_status(self):
        """Get current permission status"""
        return {
            "accessibility": self.check_accessibility_permissions(),
            "screen_recording": self.check_screen_recording_permissions(),
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
            if SETTINGS_UI_AVAILABLE:
                try:
                    from AppKit import NSAlert, NSAlertStyleWarning
                    
                    alert = NSAlert.alloc().init()
                    alert.setMessageText_("Accessibility Permission Required")
                    alert.setInformativeText_("Rephrasely needs accessibility permission to:\n\n• Monitor your global hotkey (Cmd+Shift+R)\n• Copy text from any app (simulates Cmd+C)\n• Paste processed text into any app (simulates Cmd+V)\n\nPlease grant permission in System Settings.")
                    alert.setAlertStyle_(NSAlertStyleWarning)
                    alert.addButtonWithTitle_("Open System Settings")
                    alert.addButtonWithTitle_("Continue Anyway")
                    
                    response = alert.runModal()
                    if response == 1000:  # First button
                        self.open_system_preferences_security()
                        return False  # Don't continue startup yet
                    # else continue anyway
                        
                except Exception as e:
                    logger.error(f"Failed to show permission dialog: {e}")
            else:
                print("⚠️  Accessibility permission required!")
                print("   Needed for: global hotkey monitoring, copying from apps, pasting into apps")
                print("   Please grant permission in System Settings > Privacy & Security > Accessibility")
                print("   Then restart Rephrasely")
                return False
        
        return True
    
    def copy_selected_text(self):
        """Copy currently selected text to clipboard"""
        try:
            # Simulate Cmd+C to copy selected text
            subprocess.run(['osascript', '-e', 'tell application "System Events" to keystroke "c" using command down'], 
                         check=True, capture_output=True)
            time.sleep(0.1)  # Small delay to ensure copy completes
            return True
        except subprocess.CalledProcessError:
            logger.error("Failed to copy selected text")
            return False
    
    def paste_text_alternative(self):
        """Alternative paste method using different AppleScript approach"""
        try:
            # Get the frontmost application and paste there
            script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                tell application process frontApp
                    keystroke "v" using command down
                end tell
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                         check=True, capture_output=True, text=True)
            
            logger.info("Alternative paste command executed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Alternative paste failed: {e}")
            return False

    def paste_text(self):
        """Paste text from clipboard with fallback methods"""
        if not self.auto_paste:
            logger.info("Auto-paste disabled, skipping paste operation")
            return True
        
        try:
            # Add a longer delay to ensure clipboard is updated and focus is restored
            time.sleep(0.3)
            
            # Method 1: Simple keystroke
            try:
                result = subprocess.run(['osascript', '-e', 'tell application "System Events" to keystroke "v" using command down'], 
                             check=True, capture_output=True, text=True)
                logger.info("Paste command executed successfully")
                return True
            except subprocess.CalledProcessError:
                logger.warning("Primary paste method failed, trying alternative...")
                
                # Method 2: Alternative approach
                if self.paste_text_alternative():
                    return True
                
                logger.error("Both paste methods failed")
                return False
                
        except Exception as e:
            logger.error(f"Paste error: {e}")
            return False
    
    def process_text_with_chatgpt(self, text: str) -> Optional[str]:
        """Process text using ChatGPT"""
        if not self.openai_client:
            logger.error("OpenAI client not initialized")
            return None
        
        if not text.strip():
            logger.warning("No text to process")
            return None
        
        try:
            prompt = self.prompts.get(self.current_prompt, self.prompts['rephrase'])
            
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
        """Main function to process selected text"""
        if self.hotkey_pressed:
            logger.warning("⚠️  Hotkey already being processed, ignoring...")
            return  # Prevent multiple simultaneous executions
        
        self.hotkey_pressed = True
        self.set_processing_state(True)  # Start spinner
        logger.info("🔄 Processing text selection...")
        
        try:
            # Check if OpenAI client is available first
            if not self.openai_client:
                error_msg = "OpenAI API key not configured. Please check Settings."
                logger.error(f"❌ {error_msg}")
                self.show_notification("Configuration Error", error_msg, is_error=True)
                return
            
            # Store original clipboard content
            try:
                original_clipboard = pyperclip.paste()
                logger.debug(f"Original clipboard: {original_clipboard[:50] if original_clipboard else 'empty'}...")
            except Exception as e:
                logger.warning(f"Could not access clipboard: {e}")
                original_clipboard = ""
            
            # Copy selected text
            if not self.copy_selected_text():
                error_msg = "Failed to copy text"
                logger.error(error_msg)
                self.show_notification("Copy Failed", error_msg, is_error=True)
                return
            
            # Get text from clipboard
            try:
                new_clipboard = pyperclip.paste()
            except Exception as e:
                error_msg = f"Failed to read clipboard: {e}"
                logger.error(error_msg)
                self.show_notification("Clipboard Error", error_msg, is_error=True)
                return
            
            # Check if clipboard actually changed (indicating text was selected and copied)
            if new_clipboard == original_clipboard:
                logger.warning("Clipboard didn't change - no text may have been selected")
                # Try to proceed anyway in case text was already in clipboard
            
            if not new_clipboard or not new_clipboard.strip():
                error_msg = "No text found in clipboard"
                logger.warning(error_msg)
                self.show_notification("No Text", error_msg, is_error=True)
                return
            
            logger.info(f"Processing text ({len(new_clipboard)} chars): {new_clipboard[:50]}...")
            
            # Process with ChatGPT
            try:
                processed_text = self.process_text_with_chatgpt(new_clipboard)
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
            
            # Put processed text in clipboard
            try:
                pyperclip.copy(processed_text)
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
            
            logger.info("Clipboard updated with processed text, attempting to paste...")
            
            # Paste the processed text if auto-paste is enabled
            if self.auto_paste:
                try:
                    if self.paste_text():
                        success_msg = f"Text {self.current_prompt}d successfully"
                        logger.info("Text processing completed successfully")
                        self.show_notification("Success", success_msg, is_error=False)
                    else:
                        warning_msg = "Paste failed - processed text is in clipboard (Cmd+V to paste manually)"
                        logger.error(warning_msg)
                        self.show_notification("Paste Failed", warning_msg, is_error=True)
                except Exception as e:
                    warning_msg = f"Paste error: {e} - processed text is in clipboard (Cmd+V to paste manually)"
                    logger.error(warning_msg)
                    self.show_notification("Paste Failed", warning_msg, is_error=True)
            else:
                success_msg = f"Text {self.current_prompt}d and copied to clipboard"
                logger.info("Text processing completed - auto-paste disabled")
                self.show_notification("Success", success_msg, is_error=False)
            
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
        self.current_keys.add(key)
        
        # Debug logging for hotkey detection
        if len(self.current_keys) >= 2:  # Only log when we have multiple keys
            keys_str = ", ".join([str(k) for k in self.current_keys])
            logger.debug(f"Current keys pressed: {keys_str}")
        
        # Check if our hotkey combination is pressed
        if self.hotkey_combo.issubset(self.current_keys):
            logger.info("🎯 HOTKEY DETECTED! Processing selection...")
            # Show immediate feedback that hotkey was detected
            self.show_notification("Hotkey Detected", "Processing selected text...", is_error=False)
            # Run processing in a separate thread to avoid blocking
            threading.Thread(target=self.process_selection, daemon=True).start()
    
    def on_key_release(self, key):
        """Handle key release events"""
        try:
            self.current_keys.remove(key)
        except KeyError:
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
        
        # Create menu
        menu_items = [
            pystray.MenuItem(f"Mode: {self.current_prompt.title()}", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
        ]
        
        # Add permission status indicators
        accessibility_status = "✅" if permissions.get("accessibility", False) else "❌"
        
        menu_items.extend([
            pystray.MenuItem(f"Accessibility (Copy/Type) {accessibility_status}", lambda: None, enabled=False),
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
        
        menu = pystray.Menu(*menu_items)
        self.tray_icon = pystray.Icon("Rephrasely", image, "Rephrasely - AI Text Processor", menu)
    
    def change_mode(self, mode):
        """Change processing mode"""
        if mode in self.prompts:
            self.current_prompt = mode
            logger.info(f"Changed mode to: {mode}")
            
            # Update tray icon menu
            if self.tray_icon:
                self.tray_icon.stop()
                self.create_tray_icon()
                threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        logger.info("Shutting down Rephrasely...")
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
            logger.warning("   This will cause 'This process is not trusted!' errors")
            if not self.request_permissions():
                logger.warning("Required permissions not granted, exiting...")
                self.instance_checker.cleanup()
                sys.exit(1)
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
                sys.exit(1)
        
        # Normal startup - start all service components
        self.start_service_components()
    
    def format_hotkey(self):
        """Format hotkey combination for display"""
        if self.settings_manager:
            return self.settings_manager.get("hotkey", "Cmd+Shift+R")
        return "Cmd+Shift+R"

    def show_notification(self, title, message, is_error=False):
        """Show notification if enabled"""
        # Always log notifications for debugging
        logger.info(f"📢 Notification: {title} - {message}")
        
        # Try to show native notification if settings allow it
        if self.settings_manager and self.settings_manager.get("show_notifications", True):
            if hasattr(self.settings_manager, 'show_notification'):
                self.settings_manager.show_notification(title, message, is_error)
        
        # Also try to show macOS notification as fallback
        try:
            # Simple macOS notification using osascript
            script = f'''
            display notification "{message}" with title "{title}"
            '''
            subprocess.run(['osascript', '-e', script], check=False, capture_output=True)
        except Exception as e:
            logger.debug(f"Could not show native notification: {e}")
    
    def set_processing_state(self, processing):
        """Set processing state and update icon"""
        self.is_processing = processing
        if self.tray_icon:
            # Update the icon to show spinner or normal state
            if processing:
                self.create_spinner_icon()
            else:
                self.create_normal_icon()
            
            # Update the tray icon
            self.tray_icon.icon = self.current_icon_image
    
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
            alert.setMessageText_("Welcome to Rephrasely!")
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
        
        self.is_running = True
        
        # Start keyboard listener
        self.listener = Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.listener.start()
        
        # Create and start tray icon
        self.create_tray_icon()
        
        try:
            self.tray_icon.run()
        except KeyboardInterrupt:
            self.quit_app()

def main():
    """Main entry point"""
    print("🔄 Rephrasely - Global Text Rephrasing Service")
    print("=" * 50)
    
    # Initialize NSApplication for macOS app bundle compatibility
    try:
        from Foundation import NSBundle, NSApplication, NSObject
        
        # Check if we're running as a bundled app
        bundle = NSBundle.mainBundle()
        if bundle and bundle.bundlePath().endswith('.app'):
            # We're running as an app bundle, initialize NSApplication
            app = NSApplication.sharedApplication()
            # Make sure the app doesn't terminate when all windows are closed
            app.setActivationPolicy_(2)  # NSApplicationActivationPolicyAccessory

            class AppDelegate(NSObject):
                """Ensures app stays alive when settings window closes"""

                def applicationShouldTerminateAfterLastWindowClosed_(self, sender):
                    return False

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