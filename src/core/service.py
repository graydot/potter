#!/usr/bin/env python3
"""
Potter Service - Main orchestrator
Coordinates all components and handles the application lifecycle
"""

import logging
import time
import threading
from typing import Dict
import sys

# Core components
from core.permissions import PermissionManager
from core.hotkeys import HotkeyManager
from core.text_processor import TextProcessor
from ui.tray_icon import TrayIconManager
from ui.notifications import NotificationManager
from utils.instance_checker import SingleInstanceChecker
from utils.llm_client import LLMClientManager, get_api_key_from_env, validate_api_key_format

# Settings UI (optional)
try:
    from cocoa_settings import SettingsManager
    SETTINGS_UI_AVAILABLE = True
except ImportError:
    SETTINGS_UI_AVAILABLE = False

logger = logging.getLogger(__name__)


class PotterService:
    """Main Potter service that orchestrates all components"""
    
    def __init__(self):
        # Core components
        self.instance_checker = SingleInstanceChecker()
        self.permission_manager = PermissionManager()
        self.llm_manager = LLMClientManager()
        
        # Settings management (create first)
        self.settings_manager = SettingsManager() if SETTINGS_UI_AVAILABLE else None
        
        # Text processor needs settings manager
        self.text_processor = TextProcessor(self.llm_manager, self.settings_manager)
        
        self.hotkey_manager = HotkeyManager(on_hotkey_pressed=self._handle_hotkey_pressed)
        self.tray_icon_manager = TrayIconManager(
            on_mode_change=self._handle_mode_change,
            on_preferences=self._handle_preferences,
            on_notifications_toggle=self._handle_notifications_toggle,
            on_process_click=self._handle_hotkey_pressed,  # Also handle tray icon clicks
            on_quit=self._handle_quit
        )
        self.notification_manager = NotificationManager()
        
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
                logger.info(f"📋 Loaded settings from manager: provider={settings.get('llm_provider', 'N/A')}")
            else:
                settings = self._get_default_settings()
                logger.warning("⚠️ Using default settings (no settings manager)")
            
            # Configure LLM provider
            provider = settings.get("llm_provider", "gemini")
            model = settings.get("model", "gpt-4o-mini")
            
            # Get API key based on provider
            api_key_field = f"{provider}_api_key"
            api_key = settings.get(api_key_field, "").strip()
            logger.info(f"🔑 Loading {provider} API key from field '{api_key_field}'")
            logger.info(f"🔍 DEBUG: Provider={provider}, API key field={api_key_field}, Key found={bool(api_key)}")
            
            if not api_key:
                api_key = get_api_key_from_env(provider)
                if api_key:
                    logger.info(f"🔑 Found {provider} API key in environment")
                else:
                    logger.warning(f"⚠️ No {provider} API key found in settings or environment")
                    logger.error(f"🔍 FAILURE: {provider} API key completely missing")
                    logger.error(f"🔍 Available settings: {list(settings.keys())}")
                    all_api_keys = [(k, bool(v)) for k, v in settings.items() if 'api_key' in k]
                    logger.error(f"🔍 All API key fields: {all_api_keys}")
            else:
                # Mask the key for logging
                masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
                logger.info(f"🔑 Found {provider} API key in settings: {masked_key}")
            
            if api_key and validate_api_key_format(api_key, provider):
                logger.info(f"✅ {provider} API key format is valid, setting up provider...")
                success = self.llm_manager.setup_provider(provider, api_key, model)
                if success:
                    logger.info(f"✅ {provider} provider initialized successfully")
                    current_provider = self.llm_manager.get_current_provider()
                    is_available = self.llm_manager.is_available()
                    logger.info(f"🔍 LLM manager state: current_provider={current_provider}, available={is_available}")
                else:
                    logger.error(f"❌ Failed to initialize {provider} provider despite valid key")
                    current_provider = self.llm_manager.get_current_provider()
                    is_available = self.llm_manager.is_available()
                    logger.error(f"🔍 LLM manager state: current_provider={current_provider}, available={is_available}")
                    logger.error("🔍 This means the provider setup itself failed - check logs for provider-specific errors")
            else:
                if api_key:
                    logger.error(f"❌ {provider} API key format is invalid")
                    if len(api_key) > 10:
                        logger.error(f"🔍 Key length: {len(api_key)}, starts with: {api_key[:10]}")
                    else:
                        logger.error(f"🔍 Key length: {len(api_key)}, full key: {api_key}")
                else:
                    logger.error(f"❌ {provider} API key is missing")
                logger.warning(f"⚠️ {provider} API key not configured - text processing will fail")
            
            # Configure hotkey
            hotkey_str = settings.get("hotkey", "cmd+shift+a")
            self.hotkey_manager.update_hotkey(hotkey_str)
            
            # Load prompts from settings 
            prompts_data = settings.get("prompts", [])
            prompts = {}
            for prompt_data in prompts_data:
                name = prompt_data.get("name", "")
                text = prompt_data.get("text", "")
                if name and text:
                    prompts[name] = text
            
            if not prompts:
                # Use default prompts if none configured
                default_prompts = self._get_default_settings()["prompts"]
                for prompt_data in default_prompts:
                    prompts[prompt_data["name"]] = prompt_data["text"]
            
            self.text_processor.update_prompts(prompts)
            
            # Set model - always use a model (default if not specified)
            model = settings.get("model", "gpt-4o-mini")  # Use OpenAI default if not in settings
            self.text_processor.set_model(model)
            
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
            "llm_provider": "gemini",
            "model": "gpt-4o-mini",
            "notifications": True,
            "openai_api_key": "",
            "anthropic_api_key": "",
            "google_api_key": ""
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
        self.hotkey_manager.update_hotkey("cmd+shift+a")
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
        logger.info(f"📍 Potter version: {getattr(self, 'version', 'unknown')}")
        logger.info(f"🐍 Python version: {sys.version}")
        logger.info(f"💻 Platform: {sys.platform}")
        
        # Check for existing instance
        if self.instance_checker.is_already_running():
            logger.error("❌ Another instance is already running")
            return False
        
        # Create PID file
        if not self.instance_checker.create_pid_file():
            logger.error("❌ Failed to create PID file")
            return False
        logger.info("✅ PID file created successfully")
        
        # Check/request permissions and API setup
        logger.info("🔐 Checking permissions and API setup...")
        permissions = self.permission_manager.get_permission_status()
        
        # Log detailed permission status
        for perm_name, perm_status in permissions.items():
            status_icon = "✅" if perm_status else "❌"
            logger.info(f"  {status_icon} {perm_name.title()} permission: {perm_status}")
        
        # Check if LLM provider is available
        llm_available = self.llm_manager.is_available()
        api_status_icon = "✅" if llm_available else "❌"
        current_provider = self.llm_manager.get_current_provider() or "none"
        logger.info(f"  {api_status_icon} LLM Provider ({current_provider}): {'Available' if llm_available else 'Not configured'}")
        
        needs_setup = False
        
        # Determine what setup is needed
        if not llm_available:
            logger.info("⚠️  No valid LLM provider configured - showing setup")
            self.notification_manager.show_api_key_needed()
            needs_setup = True
        elif not permissions["accessibility"]:
            logger.info("⚠️  Accessibility permission needed - showing setup")
            self.permission_manager.request_permissions(show_preferences_callback=self._show_preferences)
            needs_setup = True
        
        # Show preferences if any setup is needed
        if needs_setup and self.settings_manager:
            logger.info("⚙️  Opening settings for initial setup...")
            self._show_preferences()
        
        # Start components
        logger.info("🔧 Starting core components...")
        self.is_running = True
        
        # Start hotkey listener
        logger.info("⌨️  Starting hotkey listener...")
        self.hotkey_manager.start_listener()
        hotkey = getattr(self.hotkey_manager, 'current_hotkey', 'unknown')
        logger.info(f"  ✅ Hotkey listener active: {hotkey}")
        
        # Create and start tray icon
        logger.info("🖼️  Creating tray icon...")
        self.tray_icon_manager.create_tray_icon(
            current_mode=self.text_processor.get_current_mode(),
            available_modes=self.text_processor.get_available_modes(),
            permissions=permissions,
            notifications_enabled=self.notification_manager.is_notifications_enabled()
        )
        logger.info("  ✅ Tray icon created")
        
        # Start periodic checks
        logger.info("⏰ Starting periodic background checks...")
        self.periodic_thread.start()
        logger.info("  ✅ Background monitoring active")
        
        # Log final status
        available_modes = self.text_processor.get_available_modes()
        current_mode = self.text_processor.get_current_mode()
        logger.info(f"🎯 Current mode: {current_mode}")
        logger.info(f"📝 Available modes: {', '.join(available_modes)}")
        
        logger.info("✅ Potter service started successfully")
        logger.info("🔄 Running main tray icon loop...")
        
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
        logger.info("🔥 _handle_hotkey_pressed called! Source could be hotkey or tray click")
        
        if self.is_processing:
            logger.debug("⏭️  Already processing, ignoring hotkey")
            return
        
        hotkey = getattr(self.hotkey_manager, 'current_hotkey', 'unknown')
        logger.info(f"🎯 Hotkey detected ({hotkey})! Processing clipboard text...")
        
        # Show immediate feedback
        self.notification_manager.show_hotkey_detected()
        logger.debug("📢 Hotkey detection notification sent")
        
        # Process text with comprehensive error recovery
        logger.debug("🔄 Starting text processing...")
        success = False
        try:
            success = self.text_processor.process_clipboard_text(
                notification_callback=self.notification_manager.show_notification,
                progress_callback=self._set_processing_state,
                error_callback=self._handle_error
            )
            
            if success:
                mode = self.text_processor.get_current_mode()
                logger.info(f"✅ Text processing completed successfully (mode: {mode})")
                self.notification_manager.show_text_processed(mode)
                # Clear any previous error state on success
                self.tray_icon_manager.set_error_state(False)
            else:
                logger.warning("❌ Text processing failed")
                logger.debug("🔍 Check previous logs for error details")
                # Set error state in tray icon
                self._handle_error("Text processing failed")
        except Exception as e:
            logger.error(f"❌ Unexpected error in hotkey handler: {e}")
            import traceback
            traceback.print_exc()
            self._handle_error(f"Unexpected error: {str(e)}")
        finally:
            # CRITICAL: Always reset processing state regardless of success/failure
            # This ensures hotkeys continue working after any error
            logger.debug("🔄 Resetting processing state in finally block")
            self._set_processing_state(False)
            
            # Additional safety: Clear any stuck processing flags in text processor
            if hasattr(self.text_processor, 'is_processing'):
                self.text_processor.is_processing = False
                logger.debug("🔄 Reset text processor processing flag")
            
            # Log final state for debugging
            logger.debug(f"🔍 Final processing state: {self.is_processing}")
            logger.info("🎯 Hotkey handler completed - system ready for next hotkey")
    
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
            # Bring existing window to front
            try:
                self.settings_window.window().makeKeyAndOrderFront_(None)
            except Exception:
                # Window might be invalid, create new one
                self.settings_window = None
        
        if not self.settings_window:
            try:
                logger.info("Opening settings window...")
                # Import the show_settings function
                from cocoa_settings import show_settings
                
                # Create settings window with callback
                self.settings_window = show_settings(
                    self.settings_manager, 
                    on_settings_changed=self._on_settings_changed
                )
                
                # Set up window close callback to clear reference
                if self.settings_window and self.settings_window.window():
                    # Use proper delegate method instead of overriding close
                    # We'll handle cleanup in the settings window itself or through delegate
                    pass
                
                logger.info("Settings window opened successfully")
            except Exception as e:
                logger.error(f"Failed to show settings window: {e}")
                import traceback
                traceback.print_exc()
                self.notification_manager.show_error("Failed to open settings")
                self.settings_window = None
    
    def _on_settings_changed(self, new_settings):
        """Handle settings changes from settings window"""
        try:
            logger.info("Settings changed, updating components...")
            
            # Save settings
            if self.settings_manager:
                self.settings_manager.save_settings(new_settings)
            
            # Update LLM client if provider/API key changed
            provider = new_settings.get("llm_provider", "gemini")
            model = new_settings.get("model", "gpt-4o-mini")
            api_key_field = f"{provider}_api_key"
            api_key = new_settings.get(api_key_field, "")
            
            current_provider = self.llm_manager.get_current_provider()
            if provider != current_provider or (api_key and api_key != getattr(self.llm_manager, 'api_key', None)):
                logger.info(f"LLM provider/key updated, reinitializing {provider} client...")
                if api_key and validate_api_key_format(api_key, provider):
                    self.llm_manager.setup_provider(provider, api_key, model)
                    self.text_processor.update_settings()
            
            # Update hotkey if changed
            hotkey = new_settings.get("hotkey", "cmd+shift+a")
            if hotkey != self.hotkey_manager.current_hotkey:
                logger.info(f"Hotkey updated to: {hotkey}")
                self.hotkey_manager.update_hotkey(hotkey)
            
            # Update prompts if changed
            prompts = new_settings.get("prompts", [])
            if prompts:
                prompt_dict = {p["name"]: p["text"] for p in prompts}
                self.text_processor.update_prompts(prompt_dict)
            
            # Update notifications setting
            notifications_enabled = new_settings.get("show_notifications", True)
            self.notification_manager.set_notifications_enabled(notifications_enabled)
            
            # Update tray icon menu
            permissions = self.permission_manager.get_permission_status()
            self.tray_icon_manager.update_menu(
                current_mode=self.text_processor.get_current_mode(),
                available_modes=self.text_processor.get_available_modes(),
                permissions=permissions,
                notifications_enabled=notifications_enabled
            )
            
            # Clear settings window reference (window will close automatically)
            self.settings_window = None
            
            # Show success notification
            self.notification_manager.show_info("Settings updated successfully")
            
            logger.info("Settings update completed")
            
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            import traceback
            traceback.print_exc()
            self.notification_manager.show_error("Failed to update settings")
    
    def _set_processing_state(self, processing: bool):
        """Set processing state and update UI"""
        self.is_processing = processing
        # Clear error state when starting processing
        if processing:
            self.tray_icon_manager.set_error_state(False)
        self.tray_icon_manager.set_processing_state(processing)
        logger.debug(f"Processing state: {processing}")
    
    def _handle_error(self, error_message: str):
        """Handle error state and update UI"""
        logger.error(f"🚨 Error occurred: {error_message}")
        self.tray_icon_manager.set_error_state(True, error_message)
        # Also update the menu to show the error
        permissions = self.permission_manager.get_permission_status()
        self.tray_icon_manager.update_menu(
            current_mode=self.text_processor.get_current_mode(),
            available_modes=self.text_processor.get_available_modes(),
            permissions=permissions,
            notifications_enabled=self.notification_manager.is_notifications_enabled()
        )
    
    def get_permission_status(self) -> Dict:
        """Get current permission status"""
        return self.permission_manager.get_permission_status()
    
    def reload_settings(self):
        """Reload settings (useful for testing)"""
        logger.info("Reloading settings...")
        self._load_settings()
        logger.info("Settings reloaded") 