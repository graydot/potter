#!/usr/bin/env python3
"""
Prompts Manager - Handles prompt loading and management
"""

import logging
from typing import Dict, Optional
from utils.exception_reporter import report_exception, report_error

logger = logging.getLogger(__name__)


class PromptsManager:
    """Manages prompts with proper error handling"""
    
    def __init__(self, settings_manager=None):
        self.settings_manager = settings_manager
        self._cached_prompts = None
    
    def _get_default_prompts(self) -> Dict[str, str]:
        """Get default prompts as fallback"""
        return {
            "summarize": "Please provide a concise summary of the following text. Focus on the key points and main ideas. Keep it brief but comprehensive, capturing the essential information in a clear and organized way.",
            "formal": "Please rewrite the following text in a formal, professional tone. Use proper business language and structure. Ensure the tone is respectful, authoritative, and appropriate for professional communication.",
            "casual": "Please rewrite the following text in a casual, relaxed tone. Make it sound conversational and approachable. Use everyday language while maintaining clarity and keeping the core message intact.",
            "friendly": "Please rewrite the following text in a warm, friendly tone. Make it sound welcoming and personable. Add warmth and approachability while keeping the message clear and engaging.",
            "polish": "Please polish the following text by fixing any grammatical issues, typos, or awkward phrasing. Make it sound natural and human while keeping it direct and clear. Double-check that the tone is appropriate and not offensive, but maintain the original intent and directness."
        }
    
    def get_prompts(self) -> Dict[str, str]:
        """Get prompts dictionary, use defaults if none available"""
        if self._cached_prompts is not None:
            return self._cached_prompts
        
        try:
            prompts = {}
            
            # Try to load from settings
            if self.settings_manager:
                prompts_data = self.settings_manager.get("prompts", [])
                for prompt_data in prompts_data:
                    name = prompt_data.get("name", "").strip()
                    text = prompt_data.get("text", "").strip()
                    if name and text:
                        prompts[name] = text
            
            # If no prompts found, use defaults instead of crashing
            if not prompts:
                prompts = self._get_default_prompts()
                logger.info("No prompts configured in settings, using default prompts")
                report_error("No prompts configured in settings, using defaults", 
                           {"source": "prompts_manager", "action": "fallback_to_defaults"})
            
            self._cached_prompts = prompts
            logger.info(f"✅ Loaded {len(prompts)} prompts: {list(prompts.keys())}")
            return prompts
            
        except Exception as e:
            # On any error, use defaults to prevent crash
            logger.error(f"Error loading prompts: {e}")
            report_exception(e, {"source": "prompts_manager"}, 
                           extra_info="Failed to load prompts, using defaults")
            
            prompts = self._get_default_prompts()
            logger.info("Using default prompts due to error")
            self._cached_prompts = prompts
            return prompts
    
    def get_default_mode(self) -> str:
        """Get the default/first available mode"""
        prompts = self.get_prompts()  # Will never throw now, always returns defaults if needed
        
        # Return first available prompt
        first_mode = next(iter(prompts.keys()))
        logger.info(f"Using default mode: {first_mode}")
        return first_mode
    
    def validate_mode(self, mode: str) -> bool:
        """Check if a mode exists"""
        try:
            prompts = self.get_prompts()
            return mode in prompts
        except Exception:
            return False
    
    def get_prompt_text(self, mode: str) -> Optional[str]:
        """Get prompt text for a specific mode"""
        try:
            prompts = self.get_prompts()
            return prompts.get(mode)
        except Exception as e:
            report_exception(e, {"mode": mode}, extra_info="Failed to get prompt text")
            return None
    
    def invalidate_cache(self):
        """Clear cached prompts (call when settings change)"""
        self._cached_prompts = None
        logger.debug("Prompts cache invalidated")


# Global instance
_prompts_manager = None


def get_prompts_manager(settings_manager=None):
    """Get global prompts manager instance"""
    global _prompts_manager
    if _prompts_manager is None:
        _prompts_manager = PromptsManager(settings_manager)
    return _prompts_manager 