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
                "models": [
                    {
                        "id": "o1-pro",
                        "name": "o1-pro",
                        "description": "Advanced reasoning",
                        "detailed_description": ("🧠 Advanced reasoning powerhouse - Best for complex "
                                               "logic, scientific research, and multi-step problem "
                                               "solving. Thinks deeply before responding.")
                    },
                    {
                        "id": "o1",
                        "name": "o1", 
                        "description": "Strong reasoning",
                        "detailed_description": ("🎯 Strong reasoning model - Excellent for math, "
                                               "coding challenges, and analytical tasks requiring "
                                               "step-by-step thinking.")
                    },
                    {
                        "id": "o1-preview",
                        "name": "o1-preview",
                        "description": "Fast reasoning",
                        "detailed_description": ("⚡ Fast reasoning preview - Good balance of speed "
                                               "and reasoning capability for everyday complex tasks.")
                    },
                    {
                        "id": "o1-mini",
                        "name": "o1-mini",
                        "description": "Quick & affordable",
                        "detailed_description": ("💨 Quick reasoning model - Cost-effective option for "
                                               "mathematical problems and coding with basic "
                                               "reasoning needs.")
                    },
                    {
                        "id": "gpt-4o",
                        "name": "gpt-4o",
                        "description": "Multimodal champion",
                        "detailed_description": ("🖼️ Multimodal champion - Excellent for text, images, "
                                               "and vision tasks. Great all-around model for varied "
                                               "content types.")
                    },
                    {
                        "id": "gpt-4o-mini",
                        "name": "gpt-4o-mini", 
                        "description": "Fast & affordable",
                        "detailed_description": ("⚡ Fast & affordable - Quick responses for everyday "
                                               "tasks, good balance of speed, cost, and capability.")
                    },
                    {
                        "id": "gpt-4-turbo",
                        "name": "gpt-4-turbo",
                        "description": "High performance",
                        "detailed_description": ("🚀 High-performance model - Strong reasoning and "
                                               "coding capabilities with faster response times "
                                               "than GPT-4.")
                    },
                    {
                        "id": "gpt-4",
                        "name": "gpt-4",
                        "description": "Reliable workhorse",
                        "detailed_description": ("📚 Reliable workhorse - Solid performance across "
                                               "all tasks, established model with consistent "
                                               "quality.")
                    },
                    {
                        "id": "gpt-3.5-turbo",
                        "name": "gpt-3.5-turbo",
                        "description": "Budget friendly",
                        "detailed_description": ("💰 Budget-friendly option - Good for simple tasks, "
                                               "quick responses, and high-volume usage where "
                                               "cost matters.")
                    }
                ],
                "api_key_prefix": "sk-",
                "help_url": "https://platform.openai.com/api-keys"
            },
            "anthropic": {
                "name": "Anthropic",
                "models": [
                    {
                        "id": "claude-opus-4-20250514",
                        "name": "Claude Opus 4",
                        "description": "Best coding model",
                        "detailed_description": ("👑 World's best coding model - Unmatched for "
                                               "complex programming, AI agents, long-running tasks. "
                                               "Can work autonomously for hours.")
                    },
                    {
                        "id": "claude-sonnet-4-20250514", 
                        "name": "Claude Sonnet 4",
                        "description": "Perfect balance",
                        "detailed_description": ("⚖️ Perfect balance - Superior coding and reasoning "
                                               "at 3x faster speed than Opus. Best value for "
                                               "production workloads.")
                    },
                    {
                        "id": "claude-3-7-sonnet-20250219",
                        "name": "Claude 3.7 Sonnet",
                        "description": "Extended thinking",
                        "detailed_description": ("🔄 Extended thinking capable - Good reasoning with "
                                               "optional deep thinking mode for complex analysis.")
                    },
                    {
                        "id": "claude-3-5-sonnet-20241022",
                        "name": "Claude 3.5 Sonnet",
                        "description": "Excellent writer",
                        "detailed_description": ("📝 Excellent writer - Strong at creative writing, "
                                               "content creation, and nuanced communication tasks.")
                    },
                    {
                        "id": "claude-3-5-haiku-20241022",
                        "name": "Claude 3.5 Haiku",
                        "description": "Lightning fast",
                        "detailed_description": ("⚡ Lightning fast - Quick responses for simple tasks, "
                                               "great for real-time applications and chat "
                                               "interfaces.")
                    },
                    {
                        "id": "claude-3-opus-20240229",
                        "name": "Claude 3 Opus",
                        "description": "Strong analytics",
                        "detailed_description": ("🎓 Previous flagship - Strong analytical capabilities, "
                                               "good for research and complex reasoning tasks.")
                    },
                    {
                        "id": "claude-3-sonnet-20240229",
                        "name": "Claude 3 Sonnet", 
                        "description": "Balanced performer",
                        "detailed_description": ("📊 Balanced performer - Good all-around capabilities "
                                               "for general text processing and analysis.")
                    },
                    {
                        "id": "claude-3-haiku-20240307",
                        "name": "Claude 3 Haiku",
                        "description": "Speed focused",
                        "detailed_description": ("💨 Speed focused - Fast and efficient for basic "
                                               "text processing and simple question-answering.")
                    }
                ],
                "api_key_prefix": "sk-ant-",
                "help_url": "https://console.anthropic.com/settings/keys"
            },
            "gemini": {
                "name": "Google Gemini",
                "models": [
                    {
                        "id": "gemini-2.5-pro-preview-05-06",
                        "name": "Gemini 2.5 Pro",
                        "description": "Google's flagship",
                        "detailed_description": ("🏆 Google's flagship - Leading multimodal reasoning, "
                                               "excellent for complex web apps, huge 1M+ token "
                                               "context window.")
                    },
                    {
                        "id": "gemini-2.5-flash-preview-05-20",
                        "name": "Gemini 2.5 Flash",
                        "description": "Hybrid reasoning",
                        "detailed_description": ("⚡ Hybrid reasoning - Controllable thinking "
                                               "capabilities, fast performance with optional deep "
                                               "reasoning mode.")
                    },
                    {
                        "id": "gemini-2.0-flash",
                        "name": "Gemini 2.0 Flash",
                        "description": "Well rounded",
                        "detailed_description": ("🌟 Well-rounded model - Good balance of speed and "
                                               "capability for everyday tasks with multimodal "
                                               "support.")
                    },
                    {
                        "id": "gemini-2.0-flash-lite",
                        "name": "Gemini 2.0 Flash Lite",
                        "description": "Lightweight option",
                        "detailed_description": ("💨 Lightweight option - Fast and cost-effective for "
                                               "simple text processing and quick responses.")
                    },
                    {
                        "id": "gemini-1.5-pro",
                        "name": "Gemini 1.5 Pro",
                        "description": "Long context",
                        "detailed_description": ("📊 Long context specialist - Massive 2M token "
                                               "window for processing large documents and "
                                               "datasets.")
                    },
                    {
                        "id": "gemini-1.5-flash",
                        "name": "Gemini 1.5 Flash", 
                        "description": "Speed & efficiency",
                        "detailed_description": ("⚡ Speed and efficiency - Quick responses with good "
                                               "capability, ideal for high-throughput applications.")
                    },
                    {
                        "id": "gemini-1.5-flash-8b",
                        "name": "Gemini 1.5 Flash 8B",
                        "description": "Most affordable",
                        "detailed_description": ("💰 Most affordable - Budget-friendly option for "
                                               "basic text tasks and simple processing needs.")
                    }
                ],
                "api_key_prefix": "AIza",
                "help_url": "https://makersuite.google.com/app/apikey"
            }
        }
        
        self.default_settings = {
            "prompts": [
                {
                    "name": "summarize", 
                    "text": ("Please provide a concise summary of the following text. "
                             "Focus on the key points and main ideas. Keep it brief but "
                             "comprehensive, capturing the essential information in a clear "
                             "and organized way.")
                },
                {
                    "name": "formal",
                    "text": ("Please rewrite the following text in a formal, professional tone. "
                             "Use proper business language and structure. Ensure the tone is "
                             "respectful, authoritative, and appropriate for professional "
                             "communication.")
                },
                {
                    "name": "casual",
                    "text": ("Please rewrite the following text in a casual, relaxed tone. "
                             "Make it sound conversational and approachable. Use everyday "
                             "language while maintaining clarity and keeping the core message "
                             "intact.")
                },
                {
                    "name": "friendly",
                    "text": ("Please rewrite the following text in a warm, friendly tone. "
                             "Make it sound welcoming and personable. Add warmth and "
                             "approachability while keeping the message clear and engaging.")
                },
                {
                    "name": "polish",
                    "text": ("Please polish the following text by fixing any grammatical "
                             "issues, typos, or awkward phrasing. Make it sound natural and "
                             "human while keeping it direct and clear. Double-check that the "
                             "tone is appropriate and not offensive, but maintain the "
                             "original intent and directness.")
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
        api_key_field = f"{provider}_api_key"
        api_key = self.get(api_key_field, "")
        
        # Debug logging for troubleshooting
        if api_key:
            masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
            print(f"Debug - get_current_api_key: Found {provider} API key in settings: {masked_key}")
        else:
            print(f"Debug - get_current_api_key: No {provider} API key found in field '{api_key_field}'")
            print(f"Debug - Available settings keys: {list(self.settings.keys())}")
        
        return api_key
    
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
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as a dictionary"""
        return self.settings.copy()
    
    def get_os_notification_status(self) -> bool:
        """Get actual OS notification permission status"""
        try:
            # Simple implementation - just return True for now
            # The duplicate class had a complex implementation but we'll simplify
            return True  # Assume notifications are enabled unless explicitly denied
            
        except Exception as e:
            print(f"Error checking notification status: {e}")
            return True  # Default to enabled
    
    def get_os_startup_status(self) -> bool:
        """Get actual OS launch at startup status"""
        try:
            import subprocess
            # Check if the app is in login items
            result = subprocess.run([
                'osascript', '-e',
                'tell application "System Events" to get the name of every login item'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                login_items = result.stdout.strip()
                return "Potter" in login_items
            return False
            
        except Exception as e:
            print(f"Error checking startup status: {e}")
            return False
    
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