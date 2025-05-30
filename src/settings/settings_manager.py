#!/usr/bin/env python3
"""
Settings Manager for Potter
Handles settings file management, multi-LLM support, and first-time startup logic
"""

import json
import os
import sys
import time
from typing import Dict, Any


class SettingsManager:
    """Enhanced settings manager with multi-LLM support and first-time startup tracking"""
    
    def __init__(self, settings_file=None):
        # Determine appropriate settings file location
        if settings_file is None:
            if getattr(sys, 'frozen', False):
                # Running as PyInstaller bundle - use user's Application Support directory
                settings_dir = os.path.expanduser('~/Library/Application Support/Potter')
                os.makedirs(settings_dir, exist_ok=True)
                self.settings_file = os.path.join(settings_dir, 'settings.json')
                self.state_file = os.path.join(settings_dir, 'state.json')
                self.first_run_file = os.path.join(settings_dir, 'first_run_tracking.json')
            else:
                # Running as script - use config directory
                self.settings_file = "config/settings.json"
                self.state_file = "config/state.json"
                self.first_run_file = "config/first_run_tracking.json"
        else:
            self.settings_file = settings_file
            self.state_file = settings_file.replace('settings.json', 'state.json')
            self.first_run_file = settings_file.replace('settings.json', 'first_run_tracking.json')
        
        # LLM Provider configurations
        self.llm_providers = {
            "openai": {
                "name": "OpenAI", 
                "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"],
                "api_key_prefix": "sk-",
                "help_url": "https://platform.openai.com/api-keys"
            },
            "anthropic": {
                "name": "Anthropic",
                "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
                "api_key_prefix": "sk-ant-",
                "help_url": "https://console.anthropic.com/settings/keys"
            },
            "gemini": {
                "name": "Google Gemini",
                "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
                "api_key_prefix": "AIza",
                "help_url": "https://makersuite.google.com/app/apikey"
            }
        }
        
        self.default_settings = {
            "prompts": [
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
            ],
            "hotkey": "cmd+shift+a",
            "llm_provider": "openai",
            "model": "gpt-3.5-turbo",
            "show_notifications": True,
            "launch_at_startup": False,
            "openai_api_key": "",
            "anthropic_api_key": "",
            "gemini_api_key": ""
        }
        
        self.default_state = {
            "api_key_validation": {
                "openai": {"valid": None, "last_check": None, "error": None},
                "anthropic": {"valid": None, "last_check": None, "error": None},
                "gemini": {"valid": None, "last_check": None, "error": None}
            },
            "os_permissions": {
                "notifications_enabled": None,
                "launch_at_startup_enabled": None,
                "last_check": None
            }
        }
        
        self.settings = self.load_settings()
        self.state = self.load_state()
    
    def load_state(self) -> Dict[str, Any]:
        """Load application state from file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    loaded = json.load(f)
                    state = self.default_state.copy()
                    
                    # Deep merge loaded state
                    for key, value in loaded.items():
                        if key in state and isinstance(state[key], dict) and isinstance(value, dict):
                            state[key].update(value)
                        else:
                            state[key] = value
                    
                    return state
            else:
                return self.default_state.copy()
        except Exception as e:
            print(f"Error loading state: {e}")
            return self.default_state.copy()
    
    def save_state(self, state: Dict[str, Any]) -> bool:
        """Save application state to file"""
        try:
            self.state = state
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving state: {e}")
            return False
    
    def get_current_provider(self) -> str:
        """Get the currently selected LLM provider"""
        return self.get("llm_provider", "openai")
    
    def get_current_api_key(self) -> str:
        """Get the API key for the current provider"""
        provider = self.get_current_provider()
        return self.get(f"{provider}_api_key", "")
    
    def set_api_key_validation(self, provider: str, valid: bool, error: str = None):
        """Set API key validation state for a provider"""
        if "api_key_validation" not in self.state:
            self.state["api_key_validation"] = {}
        
        if provider not in self.state["api_key_validation"]:
            self.state["api_key_validation"][provider] = {}
        
        self.state["api_key_validation"][provider].update({
            "valid": valid,
            "last_check": time.time(),
            "error": error
        })
        self.save_state(self.state)
    
    def get_api_key_validation(self, provider: str) -> Dict[str, Any]:
        """Get API key validation state for a provider"""
        if "api_key_validation" not in self.state:
            return {"valid": None, "last_check": None, "error": None}
        
        return self.state["api_key_validation"].get(provider, {
            "valid": None, "last_check": None, "error": None
        })
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file, create default if not exists"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    settings = self.default_settings.copy()
                    
                    # Update settings with loaded values
                    for key, value in loaded.items():
                        settings[key] = value
                    
                    return settings
            else:
                return self.default_settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to file"""
        try:
            self.settings = settings
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get(self, key: str, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def is_first_launch(self) -> bool:
        """Check if this is the first launch (no settings file exists or no API key)"""
        # Check if settings file exists
        if not os.path.exists(self.settings_file):
            return True
        
        # Check if OpenAI API key is configured (in settings or environment)
        api_key_in_settings = self.get("openai_api_key", "").strip()
        api_key_in_env = os.getenv('OPENAI_API_KEY', "").strip()
        
        if not api_key_in_settings and not api_key_in_env:
            return True
        
        return False
    
    def is_first_launch_for_build(self) -> bool:
        """Check if this is the first launch for this specific build"""
        try:
            from utils.instance_checker import load_build_id
            current_build = load_build_id()
            current_build_id = current_build.get("build_id", "unknown")
            
            if not os.path.exists(self.first_run_file):
                return True
            
            with open(self.first_run_file, 'r') as f:
                first_run_data = json.load(f)
            
            # Check if this build ID has been launched before
            launched_builds = first_run_data.get("launched_builds", [])
            return current_build_id not in launched_builds
            
        except Exception as e:
            print(f"Error checking first launch: {e}")
            return True  # Default to first launch to be safe
    
    def mark_build_launched(self):
        """Mark this build as having been launched"""
        try:
            from utils.instance_checker import load_build_id
            current_build = load_build_id()
            current_build_id = current_build.get("build_id", "unknown")
            
            # Load existing data or create new
            first_run_data = {"launched_builds": [], "permission_requests": {}}
            if os.path.exists(self.first_run_file):
                with open(self.first_run_file, 'r') as f:
                    first_run_data = json.load(f)
            
            # Add this build to launched builds
            if current_build_id not in first_run_data.get("launched_builds", []):
                first_run_data.setdefault("launched_builds", []).append(current_build_id)
            
            # Save updated data
            with open(self.first_run_file, 'w') as f:
                json.dump(first_run_data, f, indent=2)
                
        except Exception as e:
            print(f"Error marking build launched: {e}")
    
    def has_declined_permission(self, permission_type: str) -> bool:
        """Check if user has previously declined a permission"""
        try:
            if not os.path.exists(self.first_run_file):
                return False
            
            with open(self.first_run_file, 'r') as f:
                first_run_data = json.load(f)
            
            permission_requests = first_run_data.get("permission_requests", {})
            return permission_requests.get(permission_type, {}).get("declined", False)
            
        except Exception as e:
            print(f"Error checking permission decline: {e}")
            return False
    
    def mark_permission_declined(self, permission_type: str):
        """Mark that user has declined a permission"""
        try:
            # Load existing data or create new
            first_run_data = {"launched_builds": [], "permission_requests": {}}
            if os.path.exists(self.first_run_file):
                with open(self.first_run_file, 'r') as f:
                    first_run_data = json.load(f)
            
            # Mark permission as declined
            first_run_data.setdefault("permission_requests", {})[permission_type] = {
                "declined": True,
                "timestamp": time.time()
            }
            
            # Save updated data
            with open(self.first_run_file, 'w') as f:
                json.dump(first_run_data, f, indent=2)
                
        except Exception as e:
            print(f"Error marking permission declined: {e}")
    
    def should_show_settings_on_startup(self) -> bool:
        """Determine if settings should be shown on startup"""
        # Show settings if this is first time for this build OR no API key is set up
        is_first_launch = self.is_first_launch_for_build()
        current_provider = self.get_current_provider()
        api_key = self.get(f"{current_provider}_api_key", "").strip()
        
        # Also check environment variable as fallback
        if not api_key and current_provider == "openai":
            api_key = os.getenv('OPENAI_API_KEY', "").strip()
        
        return is_first_launch or not api_key  # Changed from AND to OR 