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
    level=logging.INFO,
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
        
        # Initialize settings manager
        if SETTINGS_UI_AVAILABLE:
            self.settings_manager = SettingsManager()
        else:
            self.settings_manager = None
        
        # Configuration from settings or defaults
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.load_settings()
        
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
            self.prompts = self.settings_manager.get("prompts", {
                'rephrase': 'Please rephrase the following text to make it clearer and more professional:',
                'summarize': 'Please provide a concise summary of the following text:',
                'expand': 'Please expand on the following text with more detail and examples:',
                'casual': 'Please rewrite the following text in a more casual, friendly tone:',
                'formal': 'Please rewrite the following text in a more formal, professional tone:'
            })
            
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
        
        # Update settings manager
        if self.settings_manager:
            self.settings_manager.settings = new_settings
        
        # Reload all settings
        self.load_settings()
        
        # Restart keyboard listener with new hotkey
        if self.listener:
            self.listener.stop()
            self.listener = Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.listener.start()
        
        # Update tray icon menu
        if self.tray_icon:
            self.tray_icon.stop()
            self.create_tray_icon()
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        
        logger.info("Settings applied successfully")
    
    def setup_openai(self):
        """Initialize OpenAI client"""
        if not self.api_key:
            logger.error("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
            return False
        
        try:
            self.openai_client = openai.OpenAI(api_key=self.api_key)
            logger.info("OpenAI client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return False
    
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
            return  # Prevent multiple simultaneous executions
        
        self.hotkey_pressed = True
        logger.info("Processing text selection...")
        
        try:
            # Store original clipboard content
            original_clipboard = pyperclip.paste()
            
            # Copy selected text
            if not self.copy_selected_text():
                logger.error("Failed to copy text")
                return
            
            # Get text from clipboard
            new_clipboard = pyperclip.paste()
            
            # Check if clipboard actually changed (indicating text was selected and copied)
            if new_clipboard == original_clipboard:
                logger.warning("Clipboard didn't change - no text may have been selected")
                # Try to proceed anyway in case text was already in clipboard
            
            if not new_clipboard or not new_clipboard.strip():
                logger.warning("No text found in clipboard")
                return
            
            logger.info(f"Processing text ({len(new_clipboard)} chars): {new_clipboard[:50]}...")
            
            # Process with ChatGPT
            processed_text = self.process_text_with_chatgpt(new_clipboard)
            if not processed_text:
                logger.error("Failed to process text")
                return
            
            logger.info(f"Processed text ({len(processed_text)} chars): {processed_text[:50]}...")
            
            # Put processed text in clipboard
            pyperclip.copy(processed_text)
            
            # Verify clipboard was updated
            time.sleep(0.1)
            clipboard_check = pyperclip.paste()
            if clipboard_check != processed_text:
                logger.error("Failed to update clipboard with processed text")
                return
            
            logger.info("Clipboard updated with processed text, attempting to paste...")
            
            # Paste the processed text
            if self.paste_text():
                logger.info("Text processing completed successfully")
            else:
                logger.error("Paste operation failed - processed text is in clipboard, you can paste manually with Cmd+V")
            
        except Exception as e:
            logger.error(f"Error in process_selection: {e}")
        finally:
            # Reset the flag after a short delay
            threading.Timer(1.0, lambda: setattr(self, 'hotkey_pressed', False)).start()
    
    def on_key_press(self, key):
        """Handle key press events"""
        self.current_keys.add(key)
        
        # Check if our hotkey combination is pressed
        if self.hotkey_combo.issubset(self.current_keys):
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
        # Create a clean copy icon with AI sparkle
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
        
        # Create menu
        menu_items = [
            pystray.MenuItem(f"Mode: {self.current_prompt.title()}", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
        ]
        
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
        if not self.openai_client:
            logger.error("Cannot start service: OpenAI client not initialized")
            sys.exit(1)
        
        # Check for single instance before starting
        self.check_single_instance()
        
        logger.info("Starting Rephrasely service...")
        logger.info(f"Hotkey: {self.format_hotkey()}")
        logger.info(f"Current mode: {self.current_prompt}")
        logger.info(f"Model: {self.model}")
        
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
    
    def format_hotkey(self):
        """Format hotkey combination for display"""
        if self.settings_manager:
            return self.settings_manager.get("hotkey", "Cmd+Shift+R")
        return "Cmd+Shift+R"

def main():
    """Main entry point"""
    print("🔄 Rephrasely - Global Text Rephrasing Service")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your_api_key_here")
        sys.exit(1)
    
    # Initialize NSApplication for macOS app bundle compatibility
    try:
        from Foundation import NSBundle, NSApplication
        
        # Check if we're running as a bundled app
        bundle = NSBundle.mainBundle()
        if bundle and bundle.bundlePath().endswith('.app'):
            # We're running as an app bundle, initialize NSApplication
            app = NSApplication.sharedApplication()
            # Make sure the app doesn't terminate when all windows are closed
            app.setActivationPolicy_(2)  # NSApplicationActivationPolicyAccessory
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