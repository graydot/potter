#!/usr/bin/env python3
"""
Text Processing Module
Handles clipboard operations and text processing workflows
"""

import time
import logging
from typing import Optional, Callable
import pyperclip
from utils.llm_client import LLMClientManager
from utils.prompts_manager import get_prompts_manager
from utils.exception_reporter import report_exception, report_error

logger = logging.getLogger(__name__)


class TextProcessor:
    """Handles text processing workflows and clipboard operations - pure orchestrator"""
    
    def __init__(self, llm_manager: LLMClientManager, settings_manager=None):
        self.llm_manager = llm_manager
        self.settings_manager = settings_manager
        self.prompts_manager = get_prompts_manager(settings_manager)
        
        # Validate that we can get initial mode (will throw if no prompts)
        try:
            current_mode = self._get_current_mode()
            logger.info(f"TextProcessor initialized, current mode: {current_mode}")
        except RuntimeError as e:
            report_error(str(e), {"component": "text_processor"})
            raise RuntimeError("Cannot initialize TextProcessor: " + str(e))
    
    def _get_current_mode(self) -> str:
        """Get current mode from settings or prompts manager default"""
        if self.settings_manager:
            # Get from settings first
            current_mode = self.settings_manager.get("current_prompt", None)
            if current_mode and self.prompts_manager.validate_mode(current_mode):
                return current_mode
        
        # Fall back to prompts manager default (will throw if no prompts)
        return self.prompts_manager.get_default_mode()
    
    def change_mode(self, mode: str) -> bool:
        """Change the current processing mode"""
        if self.prompts_manager.validate_mode(mode):
            # Save to settings if available
            if self.settings_manager:
                current_settings = self.settings_manager.get_all_settings()
                current_settings["current_prompt"] = mode
                self.settings_manager.save_settings(current_settings)
            
            logger.info(f"Changed mode to: {mode}")
            return True
        else:
            logger.warning(f"Invalid mode: {mode}")
            return False
    
    def get_clipboard_text(self) -> Optional[str]:
        """Get text from clipboard"""
        try:
            logger.info("📎 Reading text from clipboard...")
            clipboard_text = pyperclip.paste()
            if not clipboard_text or not clipboard_text.strip():
                logger.warning("⚠️ No text found in clipboard")
                return None
            logger.info(f"✅ Successfully read {len(clipboard_text)} characters from clipboard")
            return clipboard_text
        except Exception as e:
            report_exception(e, {"component": "text_processor", "action": "get_clipboard"})
            return None
    
    def set_clipboard_text(self, text: str) -> bool:
        """Set text to clipboard"""
        try:
            logger.info(f"📋 Copying {len(text)} characters to clipboard...")
            pyperclip.copy(text)
            logger.info("✅ Successfully copied processed text to clipboard")
            return True
        except Exception as e:
            report_exception(e, {"component": "text_processor", "action": "set_clipboard"})
            return False
    
    def verify_clipboard_update(self, expected_text: str) -> bool:
        """Verify that clipboard was updated with expected text"""
        try:
            time.sleep(0.1)  # Small delay to ensure clipboard update
            clipboard_check = pyperclip.paste()
            return clipboard_check == expected_text
        except Exception as e:
            logger.warning(f"Could not verify clipboard update: {e}")
            return True  # Assume success if we can't verify
    
    def process_text_with_current_mode(self, text: str) -> Optional[str]:
        """Process text using the current mode/prompt"""
        try:
            # Get current mode from settings/prompts manager
            current_mode = self._get_current_mode()
            
            # Get current model from LLM manager (will throw if not available)
            if not self.llm_manager.is_available():
                raise RuntimeError("LLM client not available - check API key configuration")
            
            current_model = self.llm_manager.get_current_model()
            if not current_model:
                # Get default from current provider
                current_provider = self.llm_manager.get_current_provider()
                if not current_provider or current_provider not in self.llm_manager.providers:
                    raise RuntimeError("No valid LLM provider configured")
                
                provider = self.llm_manager.providers[current_provider]
                current_model = provider.get_default_model()
                logger.info(f"Using default model for {current_provider}: {current_model}")
            
            # Get prompt text from prompts manager
            current_prompt = self.prompts_manager.get_prompt_text(current_mode)
            if not current_prompt:
                error_msg = f"No prompt found for mode: {current_mode}"
                report_error(error_msg, {"mode": current_mode, "component": "text_processor"})
                return None
            
            logger.info(f"🤖 Sending text to LLM (mode: {current_mode}, model: {current_model})...")
            result = self.llm_manager.process_text(
                text=text,
                prompt=current_prompt,
                model=current_model
            )
            
            if result:
                logger.info(f"✅ LLM processing completed successfully ({len(result)} characters returned)")
            else:
                report_error("LLM processing returned empty result", 
                           {"mode": current_mode, "model": current_model})
            
            return result
            
        except Exception as e:
            report_exception(e, {
                "component": "text_processor",
                "action": "process_text"
            }, extra_info="Failed to process text with current mode")
            return None
    
    def process_clipboard_text(self, 
                               notification_callback: Callable[[str, str, bool], None] = None,
                               progress_callback: Callable[[bool], None] = None,
                               error_callback: Callable[[str], None] = None) -> bool:
        """
        Main function to process clipboard text with LLM
        
        Args:
            notification_callback: Function to show notifications (title, message, is_error)
            progress_callback: Function to show/hide processing state (processing)
            error_callback: Function to report errors (error_message)
        
        Returns:
            bool: True if processing was successful, False otherwise
        """
        
        def show_notification(title: str, message: str, is_error: bool = False):
            if notification_callback:
                notification_callback(title, message, is_error)
            else:
                logger.info(f"📢 Notification: {title} - {message}")
        
        def set_processing(processing: bool):
            if progress_callback:
                progress_callback(processing)
        
        def report_error_callback(error_message: str):
            if error_callback:
                error_callback(error_message)
        
        # Start processing
        set_processing(True)
        logger.info("🔄 Processing clipboard text...")
        
        try:
            # Check if LLM client is available first
            if not self.llm_manager.is_available():
                provider_name = "LLM"
                if self.settings_manager:
                    try:
                        intended_provider = self.settings_manager.get_current_provider()
                        provider_name = intended_provider.title()
                    except Exception:
                        pass
                
                error_msg = f"{provider_name} API key not configured. Please check Settings."
                logger.error(f"❌ {error_msg}")
                show_notification("Configuration Error", error_msg, is_error=True)
                report_error_callback(f"{provider_name} API key not configured")
                return False
            
            # Get text from clipboard
            clipboard_text = self.get_clipboard_text()
            if not clipboard_text:
                error_msg = "No text found in clipboard. Copy some text first, then press the hotkey."
                logger.warning(f"⚠️ {error_msg}")
                show_notification("No Text", error_msg, is_error=True)
                report_error_callback("No text in clipboard")
                return False
            
            logger.info(f"📝 Processing clipboard text ({len(clipboard_text)} chars): {clipboard_text[:50]}...")
            
            # Process with LLM
            processed_text = self.process_text_with_current_mode(clipboard_text)
            if not processed_text:
                provider = self.llm_manager.get_current_provider() or "LLM"
                if not self.llm_manager.is_available():
                    error_msg = f"{provider.title()} client not properly initialized"
                    short_error = f"{provider.title()} client error"
                else:
                    error_msg = f"Failed to process text with {provider.title()} API"
                    short_error = f"{provider.title()} API error"
                
                logger.error(f"❌ {error_msg}")
                show_notification("AI Processing Failed", error_msg, is_error=True)
                report_error_callback(short_error)
                return False
            
            logger.info(f"🎆 Processed text ({len(processed_text)} chars): {processed_text[:50]}...")
            
            # Put processed text back in clipboard
            if not self.set_clipboard_text(processed_text):
                error_msg = "Failed to copy processed text to clipboard"
                logger.error(f"❌ {error_msg}")
                show_notification("Clipboard Error", error_msg, is_error=True)
                report_error_callback("Clipboard write failed")
                return False
            
            logger.info("✅ Processed text copied to clipboard")
            
            # Verify clipboard was updated
            if not self.verify_clipboard_update(processed_text):
                error_msg = "Failed to update clipboard with processed text"
                logger.error(f"❌ {error_msg}")
                show_notification("Clipboard Error", error_msg, is_error=True)
                report_error_callback("Clipboard verification failed")
                return False
            
            # Success notification - get current mode dynamically
            current_mode = self._get_current_mode()
            success_msg = f"✅ Text {current_mode}d and copied to clipboard! Press Cmd+V to paste."
            logger.info("✅ Text processing workflow completed successfully")
            show_notification("Processing Complete", success_msg, is_error=False)
            
            return True
            
        except Exception as e:
            error_msg = f"Unexpected error in text processing: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            show_notification("Processing Error", 
                              "An unexpected error occurred. Check logs for details.", 
                              is_error=True)
            report_error_callback(f"Unexpected error: {str(e)}")
            return False
        finally:
            # Always stop processing indicator
            set_processing(False)
    
    def get_current_mode(self) -> str:
        """Get the current processing mode from settings/prompts manager"""
        return self._get_current_mode()
    
    def get_available_modes(self) -> list:
        """Get list of available processing modes from prompts manager"""
        try:
            return list(self.prompts_manager.get_prompts().keys())
        except RuntimeError:
            return []  # No prompts available
    
    def get_mode_description(self, mode: str) -> Optional[str]:
        """Get description/prompt for a specific mode from prompts manager"""
        return self.prompts_manager.get_prompt_text(mode) 