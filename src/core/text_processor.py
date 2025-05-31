#!/usr/bin/env python3
"""
Text Processing Module
Handles clipboard operations and text processing workflows
"""

import time
import logging
from typing import Optional, Dict, Callable
import pyperclip
from utils.llm_client import LLMClientManager

logger = logging.getLogger(__name__)


class TextProcessor:
    """Handles text processing workflows and clipboard operations"""
    
    def __init__(self, llm_manager: LLMClientManager, prompts: Dict[str, str] = None):
        self.llm_manager = llm_manager
        self.prompts = prompts or {}
        self.current_mode = 'polish'
        self.processing_settings = {
            'model': 'gpt-3.5-turbo',
            'max_tokens': 1000,
            'temperature': 0.7
        }
    
    def update_prompts(self, prompts: Dict[str, str]):
        """Update the available prompts"""
        self.prompts = prompts
        
        # Ensure current mode is still valid
        if self.current_mode not in self.prompts:
            self.current_mode = next(iter(self.prompts.keys())) if self.prompts else 'polish'
    
    def change_mode(self, mode: str) -> bool:
        """Change the current processing mode"""
        if mode in self.prompts:
            self.current_mode = mode
            logger.info(f"Changed mode to: {mode}")
            return True
        else:
            logger.warning(f"Invalid mode: {mode}")
            return False
    
    def update_settings(self, model: str = None, max_tokens: int = None, temperature: float = None):
        """Update processing settings"""
        if model:
            self.processing_settings['model'] = model
        if max_tokens:
            self.processing_settings['max_tokens'] = max_tokens
        if temperature is not None:
            self.processing_settings['temperature'] = temperature
        
        logger.info(f"Updated processing settings: {self.processing_settings}")
    
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
            logger.error(f"❌ Failed to read clipboard: {e}")
            return None
    
    def set_clipboard_text(self, text: str) -> bool:
        """Set text to clipboard"""
        try:
            logger.info(f"📋 Copying {len(text)} characters to clipboard...")
            pyperclip.copy(text)
            logger.info("✅ Successfully copied processed text to clipboard")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to copy text to clipboard: {e}")
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
        if not self.llm_manager.is_available():
            logger.error("❌ LLM client not available")
            return None
        
        current_prompt = self.prompts.get(self.current_mode)
        if not current_prompt:
            logger.error(f"❌ No prompt found for mode: {self.current_mode}")
            return None
        
        logger.info(f"🤖 Sending text to LLM (mode: {self.current_mode}, model: {self.processing_settings['model']})...")
        try:
            result = self.llm_manager.process_text(
                text=text,
                prompt=current_prompt,
                model=self.processing_settings['model'],
                max_tokens=self.processing_settings['max_tokens'],
                temperature=self.processing_settings['temperature']
            )
            if result:
                logger.info(f"✅ LLM processing completed successfully ({len(result)} characters returned)")
            else:
                logger.error("❌ LLM processing returned empty result")
            return result
        except Exception as e:
            logger.error(f"❌ Error during LLM processing: {e}")
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
        
        def report_error(error_message: str):
            if error_callback:
                error_callback(error_message)
        
        # Start processing
        set_processing(True)
        logger.info("🔄 Processing clipboard text...")
        
        try:
            # Check if LLM client is available first
            if not self.llm_manager.is_available():
                provider = self.llm_manager.get_current_provider() or "LLM"
                error_msg = f"{provider.title()} API key not configured. Please check Settings."
                logger.error(f"❌ {error_msg}")
                show_notification("Configuration Error", error_msg, is_error=True)
                report_error("API key not configured")
                return False
            
            # Get text from clipboard
            clipboard_text = self.get_clipboard_text()
            if not clipboard_text:
                error_msg = "No text found in clipboard. Copy some text first, then press the hotkey."
                logger.warning(f"⚠️ {error_msg}")
                show_notification("No Text", error_msg, is_error=True)
                report_error("No text in clipboard")
                return False
            
            logger.info(f"📝 Processing clipboard text ({len(clipboard_text)} chars): {clipboard_text[:50]}...")
            
            # Process with LLM
            processed_text = self.process_text_with_current_mode(clipboard_text)
            if not processed_text:
                # Check if it might be a context window issue
                estimated_tokens = len(clipboard_text) // 4
                if estimated_tokens > 3000:  # Likely context issue
                    error_msg = f"Text too large ({estimated_tokens:,} tokens estimated). Try smaller text or use GPT-4 Turbo."
                    short_error = "Text too large for model"
                else:
                    error_msg = "Failed to process text with AI"
                    short_error = "LLM processing failed"
                
                logger.error(f"❌ {error_msg}")
                show_notification("AI Processing Failed", error_msg, is_error=True)
                report_error(short_error)
                return False
            
            logger.info(f"🎆 Processed text ({len(processed_text)} chars): {processed_text[:50]}...")
            
            # Put processed text back in clipboard
            if not self.set_clipboard_text(processed_text):
                error_msg = "Failed to copy processed text to clipboard"
                logger.error(f"❌ {error_msg}")
                show_notification("Clipboard Error", error_msg, is_error=True)
                report_error("Clipboard write failed")
                return False
            
            logger.info("✅ Processed text copied to clipboard")
            
            # Verify clipboard was updated
            if not self.verify_clipboard_update(processed_text):
                error_msg = "Failed to update clipboard with processed text"
                logger.error(f"❌ {error_msg}")
                show_notification("Clipboard Error", error_msg, is_error=True)
                report_error("Clipboard verification failed")
                return False
            
            # Success notification
            success_msg = f"✅ Text {self.current_mode}d and copied to clipboard! Press Cmd+V to paste."
            logger.info("✅ Text processing workflow completed successfully")
            show_notification("Processing Complete", success_msg, is_error=False)
            
            return True
            
        except Exception as e:
            error_msg = f"Unexpected error in text processing: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            show_notification("Processing Error", "An unexpected error occurred. Check logs for details.", is_error=True)
            report_error(f"Unexpected error: {str(e)}")
            return False
        finally:
            # Always stop processing indicator
            set_processing(False)
    
    def get_current_mode(self) -> str:
        """Get the current processing mode"""
        return self.current_mode
    
    def get_available_modes(self) -> list:
        """Get list of available processing modes"""
        return list(self.prompts.keys())
    
    def get_mode_description(self, mode: str) -> Optional[str]:
        """Get description/prompt for a specific mode"""
        return self.prompts.get(mode) 