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
    
    def get_prompts(self) -> Dict[str, str]:
        """Get prompts dictionary, throw exception if none available"""
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
            
            # If no prompts found, this is an error condition
            if not prompts:
                error_msg = "No prompts configured. Please add prompts in Settings."
                report_error(error_msg, {"source": "prompts_manager"})
                raise RuntimeError(error_msg)
            
            self._cached_prompts = prompts
            logger.info(f"✅ Loaded {len(prompts)} prompts: {list(prompts.keys())}")
            return prompts
            
        except Exception as e:
            if "No prompts configured" in str(e):
                raise  # Re-raise configuration errors
            
            # Other errors, report and re-raise
            report_exception(e, {"source": "prompts_manager"}, 
                             extra_info="Failed to load prompts")
            raise RuntimeError(f"Failed to load prompts: {e}")
    
    def get_default_mode(self) -> str:
        """Get the default/first available mode, throw exception if none"""
        prompts = self.get_prompts()  # Will throw if no prompts
        
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