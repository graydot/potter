#!/usr/bin/env python3
"""
Potter Main Service Module
The main service that orchestrates all components
"""

import os
import logging
import threading
import time
from typing import Dict, Optional, Callable

# Import our modular components
from utils.instance_checker import SingleInstanceChecker
from utils.openai_client import OpenAIClientManager, validate_api_key_format, get_api_key_from_env
from core.permissions import PermissionManager
from core.hotkeys import HotkeyManager
from core.text_processor import TextProcessor
from ui.tray_icon import TrayIconManager
from ui.notifications import NotificationManager

logger = logging.getLogger(__name__)

# Settings UI availability check
try:
    from cocoa_settings import SettingsManager
    SETTINGS_UI_AVAILABLE = True
except ImportError:
    SETTINGS_UI_AVAILABLE = False


class PotterService:
    """Main Potter service that orchestrates all components"""
    
    def __init__(self):
        # Core components
        self.instance_checker = SingleInstanceChecker()
        self.permission_manager = PermissionManager()
        self.openai_manager = OpenAIClientManager()
        self.text_processor = TextProcessor(self.openai_manager)
        self.hotkey_manager = HotkeyManager(on_hotkey_pressed=self._handle_hotkey_pressed)
        self.tray_icon_manager = TrayIconManager(
            on_mode_change=self._handle_mode_change,
            on_preferences=self._handle_preferences,
            on_notifications_toggle=self._handle_notifications_toggle,
            on_quit=self._handle_quit
        )
        self.notification_manager = NotificationManager()
        
        # Settings management
        self.settings_manager = SettingsManager() if SETTINGS_UI_AVAILABLE else None
        self.settings_window = None
        
        # State
        self.is_running = False
        self.is_processing = False
        
        # Load and apply settings
        self._load_settings()
        
        # Setup periodic checks
        self._setup_periodic_checks()
    
    def _load_settings(self):
        """Load settings and configure components"""
        try:
            # Get settings from manager or use defaults
            if self.settings_manager:
                settings = self.settings_manager.settings
            else:
                settings = self._get_default_settings()
            
            # Configure OpenAI client
            api_key = settings.get("openai_api_key", "").strip()
            if not api_key:
                api_key = get_api_key_from_env()
            
            if api_key and validate_api_key_format(api_key):
                self.openai_manager.setup_client(api_key)
            else:
                logger.warning("No valid OpenAI API key found")
            
            # Configure hotkey
            hotkey_str = settings.get("hotkey", "cmd+shift+a")
            self.hotkey_manager.update_hotkey(hotkey_str)
            
            # Configure text processor with prompts
            prompts = {}
            for prompt_config in settings.get("prompts", []):
                name = prompt_config.get("name", "")
                text = prompt_config.get("text", "")
                if name and text:
                    prompts[name] = text
            
            if not prompts:
                prompts = self._get_default_prompts()
            
            self.text_processor.update_prompts(prompts)
            
            # Configure AI settings
            self.text_processor.update_settings(
                model=settings.get("model", "gpt-3.5-turbo"),
                max_tokens=settings.get("max_tokens", 1000),
                temperature=settings.get("temperature", 0.7)
            )
            
            # Configure notifications
            notifications_enabled = settings.get("notifications", True)
            self.notification_manager.set_notifications_enabled(notifications_enabled)
            
            logger.info("Settings loaded and applied successfully")
            
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            # Use defaults if loading fails
            self._apply_default_settings()
    
    def _get_default_settings(self) -> Dict:
        """Get default settings when no settings file is available"""
        return {
            "prompts": [
                {"name": "summarize", "text": "Please provide a concise summary of the following text."},
                {"name": "formal", "text": "Please rewrite the following text in a formal, professional tone."},
                {"name": "casual", "text": "Please rewrite the following text in a casual, relaxed tone."}
            ],
            "hotkey": "cmd+shift+a",
            "model": "gpt-3.5-turbo",
            "max_tokens": 1000,
            "temperature": 0.7,
            "notifications": True,
            "openai_api_key": ""
        }
    
    def _get_default_prompts(self) -> Dict[str, str]:
        """Get default prompts"""
        return {
            "polish": "Please polish and improve the following text while maintaining its original meaning and tone.",
            "summarize": "Please provide a concise summary of the following text.",
            "formal": "Please rewrite the following text in a formal, professional tone."
        }
    
    def _apply_default_settings(self):
        """Apply default settings when loading fails"""
        self.text_processor.update_prompts(self._get_default_prompts())
        self.hotkey_manager.update_hotkey("cmd+shift+a")
        self.text_processor.update_settings()
        self.notification_manager.set_notifications_enabled(True)
        logger.info("Applied default settings")
    
    def _setup_periodic_checks(self):
        """Setup periodic background checks"""
        def periodic_check():
            while self.is_running:
                try:
                    # Check permissions every 30 seconds
                    permissions = self.permission_manager.get_permission_status()
                    
                    # Update tray icon menu if needed
                    if self.tray_icon_manager.tray_icon:
                        self.tray_icon_manager.update_menu(
                            current_mode=self.text_processor.get_current_mode(),
                            available_modes=self.text_processor.get_available_modes(),
                            permissions=permissions,
                            notifications_enabled=self.notification_manager.is_notifications_enabled()
                        )
                    
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    logger.error(f"Error in periodic check: {e}")
                    time.sleep(60)  # Wait longer if there's an error
        
        self.periodic_thread = threading.Thread(target=periodic_check, daemon=True)
    
    def start(self) -> bool:
        """Start the Potter service"""
        logger.info("🚀 Starting Potter service...")
        
        # Check for existing instance
        if self.instance_checker.is_already_running():
            logger.error("Another instance is already running")
            return False
        
        # Create PID file
        if not self.instance_checker.create_pid_file():
            logger.error("Failed to create PID file")
            return False
        
        # Check/request permissions
        permissions = self.permission_manager.get_permission_status()
        
        # Show first launch welcome if needed
        if not self.openai_manager.is_available():
            self.notification_manager.show_api_key_needed()
            if self.settings_manager:
                self._show_preferences()
        elif not permissions["accessibility"]:
            self.permission_manager.request_permissions(show_preferences_callback=self._show_preferences)
        
        # Start components
        self.is_running = True
        
        # Start hotkey listener
        self.hotkey_manager.start_listener()
        
        # Create and start tray icon
        self.tray_icon_manager.create_tray_icon(
            current_mode=self.text_processor.get_current_mode(),
            available_modes=self.text_processor.get_available_modes(),
            permissions=permissions,
            notifications_enabled=self.notification_manager.is_notifications_enabled()
        )
        
        # Start periodic checks
        self.periodic_thread.start()
        
        logger.info("✅ Potter service started successfully")
        
        # Run tray icon (blocking)
        self.tray_icon_manager.run()
        
        return True
    
    def stop(self):
        """Stop the Potter service"""
        logger.info("🛑 Stopping Potter service...")
        
        self.is_running = False
        
        # Stop components
        self.hotkey_manager.stop_listener()
        self.tray_icon_manager.stop()
        
        # Cleanup
        self.instance_checker.cleanup()
        
        logger.info("✅ Potter service stopped")
    
    # Event handlers
    def _handle_hotkey_pressed(self):
        """Handle hotkey press"""
        if self.is_processing:
            logger.debug("Already processing, ignoring hotkey")
            return
        
        logger.info("🎯 Hotkey detected! Processing clipboard text...")
        
        # Show immediate feedback
        self.notification_manager.show_hotkey_detected()
        
        # Process text
        success = self.text_processor.process_clipboard_text(
            notification_callback=self.notification_manager.show_notification,
            progress_callback=self._set_processing_state
        )
        
        if success:
            mode = self.text_processor.get_current_mode()
            self.notification_manager.show_text_processed(mode)
    
    def _handle_mode_change(self, mode: str):
        """Handle mode change from tray menu"""
        logger.info(f"Mode changed to: {mode}")
        self.text_processor.change_mode(mode)
        
        # Update tray menu
        permissions = self.permission_manager.get_permission_status()
        self.tray_icon_manager.update_menu(
            current_mode=self.text_processor.get_current_mode(),
            available_modes=self.text_processor.get_available_modes(),
            permissions=permissions,
            notifications_enabled=self.notification_manager.is_notifications_enabled()
        )
    
    def _handle_preferences(self):
        """Handle preferences menu item"""
        self._show_preferences()
    
    def _handle_notifications_toggle(self):
        """Handle notifications toggle"""
        current_state = self.notification_manager.is_notifications_enabled()
        new_state = not current_state
        self.notification_manager.set_notifications_enabled(new_state)
        
        # Update settings if available
        if self.settings_manager:
            self.settings_manager.settings["notifications"] = new_state
            self.settings_manager.save_settings()
        
        # Update tray menu
        permissions = self.permission_manager.get_permission_status()
        self.tray_icon_manager.update_menu(
            current_mode=self.text_processor.get_current_mode(),
            available_modes=self.text_processor.get_available_modes(),
            permissions=permissions,
            notifications_enabled=new_state
        )
        
        status = "enabled" if new_state else "disabled"
        self.notification_manager.show_info(f"Notifications {status}")
    
    def _handle_quit(self):
        """Handle quit from tray menu"""
        logger.info("Quit requested from tray menu")
        self.stop()
    
    def _show_preferences(self):
        """Show preferences window"""
        if not SETTINGS_UI_AVAILABLE:
            logger.warning("Settings UI not available")
            self.notification_manager.show_error("Settings UI not available in this build")
            return
        
        if self.settings_window:
            logger.debug("Settings window already open")
            return
        
        try:
            logger.info("Opening settings window...")
            # Create settings window
            self.settings_window = self.settings_manager.show_settings_window()
            logger.info("Settings window opened successfully")
        except Exception as e:
            logger.error(f"Failed to show settings window: {e}")
            self.notification_manager.show_error("Failed to open settings")
    
    def _set_processing_state(self, processing: bool):
        """Set processing state and update UI"""
        self.is_processing = processing
        self.tray_icon_manager.set_processing_state(processing)
        logger.debug(f"Processing state: {processing}")
    
    def get_permission_status(self) -> Dict:
        """Get current permission status"""
        return self.permission_manager.get_permission_status()
    
    def reload_settings(self):
        """Reload settings (useful for testing)"""
        logger.info("Reloading settings...")
        self._load_settings()
        logger.info("Settings reloaded") 