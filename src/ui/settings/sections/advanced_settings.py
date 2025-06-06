#!/usr/bin/env python3
"""
Advanced Settings Section
Handles advanced app settings like API configuration and model selection
"""

import logging
from typing import Optional, Callable, Dict
from AppKit import (
    NSView, NSMakeRect, NSFont,
    NSSegmentedControl, NSSegmentStyleTexturedRounded,
    NSSegmentSwitchTrackingSelectOne
)

from ..widgets.ui_helpers import (
    create_label, create_description_label, create_button,
    create_popup_button, create_text_field
)
from ..widgets.pasteable_text_field import PasteableSecureTextField
from ..validators.api_key_validator import APIKeyValidator

logger = logging.getLogger(__name__)


class AdvancedSettingsSection:
    """Manages the advanced settings section"""
    
    # Provider configuration
    PROVIDERS = {
        "openai": {
            "name": "OpenAI",
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
            "key_field": "openai_api_key",
            "key_prefix": "sk-"
        },
        "anthropic": {
            "name": "Anthropic",
            "models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022",
                       "claude-3-opus-20240229", "claude-3-sonnet-20240229"],
            "key_field": "anthropic_api_key",
            "key_prefix": "sk-ant-"
        },
        "google": {
            "name": "Google Gemini",
            "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"],
            "key_field": "google_api_key",
            "key_prefix": "AI"
        }
    }
    
    def __init__(self, settings_manager, on_settings_changed: Optional[Callable] = None):
        """
        Initialize advanced settings section
        
        Args:
            settings_manager: Settings manager instance
            on_settings_changed: Callback when settings change
        """
        self.settings_manager = settings_manager
        self.on_settings_changed = on_settings_changed
        
        # UI elements
        self.view = None
        self.provider_segment = None
        self.api_key_fields = {}
        self.model_popups = {}
        self.validate_buttons = {}
        self.temperature_field = None
        self.max_tokens_field = None
        self.timeout_field = None
        self.retry_field = None
        
        # Validator
        self.api_validator = APIKeyValidator()
        
        # Current provider
        self.current_provider = self.settings_manager.get("provider", "openai")
        
    def create_view(self, width: int = 700, height: int = 600) -> NSView:
        """
        Create the advanced settings view
        
        Args:
            width: View width
            height: View height
            
        Returns:
            NSView containing the advanced settings
        """
        logger.debug("Creating advanced settings view")
        
        # Create main view
        self.view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))
        
        y_offset = height - 40
        
        # Title
        title = create_label(
            "Advanced",
            NSMakeRect(20, y_offset, 200, 30),
            font=NSFont.boldSystemFontOfSize_(18)
        )
        self.view.addSubview_(title)
        
        y_offset -= 50
        
        # Provider selection
        y_offset = self._create_provider_selection(y_offset)
        
        # API configuration sections
        y_offset = self._create_api_sections(y_offset)
        
        # Model parameters
        y_offset = self._create_model_parameters(y_offset)
        
        # Connection settings
        y_offset = self._create_connection_settings(y_offset)
        
        return self.view
        
    def _create_provider_selection(self, y_offset: int) -> int:
        """Create provider selection segment"""
        label = create_label(
            "AI Provider:",
            NSMakeRect(20, y_offset, 100, 25),
            font=NSFont.boldSystemFontOfSize_(14)
        )
        self.view.addSubview_(label)
        
        # Create segmented control
        self.provider_segment = NSSegmentedControl.alloc().initWithFrame_(
            NSMakeRect(130, y_offset, 300, 25)
        )
        self.provider_segment.setSegmentCount_(3)
        self.provider_segment.setLabel_forSegment_("OpenAI", 0)
        self.provider_segment.setLabel_forSegment_("Anthropic", 1)
        self.provider_segment.setLabel_forSegment_("Google", 2)
        self.provider_segment.setSegmentStyle_(NSSegmentStyleTexturedRounded)
        self.provider_segment.setTrackingMode_(NSSegmentSwitchTrackingSelectOne)
        
        # Select current provider
        provider_index = {"openai": 0, "anthropic": 1, "google": 2}.get(self.current_provider, 0)
        self.provider_segment.setSelectedSegment_(provider_index)
        
        self.provider_segment.setTarget_(self)
        self.provider_segment.setAction_("providerChanged:")
        
        self.view.addSubview_(self.provider_segment)
        
        return y_offset - 50
        
    def _create_api_sections(self, y_offset: int) -> int:
        """Create API configuration sections for each provider"""
        for provider_id, config in self.PROVIDERS.items():
            y_offset = self._create_provider_section(provider_id, config, y_offset)
            
        # Show only current provider section
        self._update_provider_visibility()
        
        return y_offset
        
    def _create_provider_section(self, provider_id: str, config: Dict, y_offset: int) -> int:
        """Create section for a specific provider"""
        # Section container
        section_view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 700, 200))
        section_view.setIdentifier_(f"{provider_id}_section")
        
        section_y = 160
        
        # Section title
        title = create_label(
            f"{config['name']} Configuration",
            NSMakeRect(20, section_y, 300, 20),
            font=NSFont.boldSystemFontOfSize_(14)
        )
        section_view.addSubview_(title)
        
        section_y -= 35
        
        # API Key field
        key_label = create_label(
            "API Key:",
            NSMakeRect(20, section_y, 80, 25)
        )
        section_view.addSubview_(key_label)
        
        # Use secure text field
        key_field = PasteableSecureTextField.alloc().initWithFrame_(
            NSMakeRect(110, section_y, 350, 25)
        )
        key_field.setPlaceholderString_(f"Enter your {config['name']} API key")
        
        # Load existing key
        existing_key = self.settings_manager.get(config['key_field'], "")
        if existing_key:
            key_field.setStringValue_(existing_key)
            
        key_field.setTarget_(self)
        key_field.setAction_("apiKeyChanged:")
        key_field.setIdentifier_(provider_id)
        
        section_view.addSubview_(key_field)
        self.api_key_fields[provider_id] = key_field
        
        # Validate button
        validate_btn = create_button(
            "Validate",
            NSMakeRect(470, section_y, 80, 25),
            action=self.validateApiKey_,
            target=self
        )
        validate_btn.setIdentifier_(provider_id)
        section_view.addSubview_(validate_btn)
        self.validate_buttons[provider_id] = validate_btn
        
        section_y -= 35
        
        # Model selection
        model_label = create_label(
            "Model:",
            NSMakeRect(20, section_y, 80, 25)
        )
        section_view.addSubview_(model_label)
        
        model_popup = create_popup_button(
            NSMakeRect(110, section_y, 250, 25),
            items=config['models'],
            action=self.modelChanged_,
            target=self
        )
        model_popup.setIdentifier_(provider_id)
        
        # Select current model
        current_model = self.settings_manager.get(f"{provider_id}_model", config['models'][0])
        if current_model in config['models']:
            model_popup.selectItemWithTitle_(current_model)
            
        section_view.addSubview_(model_popup)
        self.model_popups[provider_id] = model_popup
        
        section_y -= 30
        
        # Description
        desc = create_description_label(
            f"Configure your {config['name']} API settings for AI-powered text processing",
            NSMakeRect(20, section_y, 600, 20)
        )
        section_view.addSubview_(desc)
        
        # Add section to main view
        section_view.setFrameOrigin_(NSMakeRect(0, y_offset - 200, 0, 0).origin)
        self.view.addSubview_(section_view)
        
        return y_offset - 200
        
    def _create_model_parameters(self, y_offset: int) -> int:
        """Create model parameter settings"""
        # Section title
        title = create_label(
            "Model Parameters",
            NSMakeRect(20, y_offset, 200, 20),
            font=NSFont.boldSystemFontOfSize_(14)
        )
        self.view.addSubview_(title)
        
        y_offset -= 35
        
        # Temperature
        temp_label = create_label(
            "Temperature:",
            NSMakeRect(20, y_offset, 100, 25)
        )
        self.view.addSubview_(temp_label)
        
        self.temperature_field = create_text_field(
            NSMakeRect(130, y_offset, 80, 25),
            placeholder="0.7"
        )
        temp_value = self.settings_manager.get("temperature", 0.7)
        self.temperature_field.setStringValue_(str(temp_value))
        self.temperature_field.setTarget_(self)
        self.temperature_field.setAction_("parameterChanged:")
        self.view.addSubview_(self.temperature_field)
        
        temp_desc = create_description_label(
            "Controls randomness (0.0 - 2.0)",
            NSMakeRect(220, y_offset, 300, 25)
        )
        self.view.addSubview_(temp_desc)
        
        y_offset -= 35
        
        # Max tokens
        tokens_label = create_label(
            "Max Tokens:",
            NSMakeRect(20, y_offset, 100, 25)
        )
        self.view.addSubview_(tokens_label)
        
        self.max_tokens_field = create_text_field(
            NSMakeRect(130, y_offset, 80, 25),
            placeholder="2000"
        )
        tokens_value = self.settings_manager.get("max_tokens", 2000)
        self.max_tokens_field.setStringValue_(str(tokens_value))
        self.max_tokens_field.setTarget_(self)
        self.max_tokens_field.setAction_("parameterChanged:")
        self.view.addSubview_(self.max_tokens_field)
        
        tokens_desc = create_description_label(
            "Maximum response length",
            NSMakeRect(220, y_offset, 300, 25)
        )
        self.view.addSubview_(tokens_desc)
        
        return y_offset - 40
        
    def _create_connection_settings(self, y_offset: int) -> int:
        """Create connection settings"""
        # Section title
        title = create_label(
            "Connection Settings",
            NSMakeRect(20, y_offset, 200, 20),
            font=NSFont.boldSystemFontOfSize_(14)
        )
        self.view.addSubview_(title)
        
        y_offset -= 35
        
        # Timeout
        timeout_label = create_label(
            "Timeout (sec):",
            NSMakeRect(20, y_offset, 100, 25)
        )
        self.view.addSubview_(timeout_label)
        
        self.timeout_field = create_text_field(
            NSMakeRect(130, y_offset, 80, 25),
            placeholder="30"
        )
        timeout_value = self.settings_manager.get("timeout", 30)
        self.timeout_field.setStringValue_(str(timeout_value))
        self.timeout_field.setTarget_(self)
        self.timeout_field.setAction_("parameterChanged:")
        self.view.addSubview_(self.timeout_field)
        
        y_offset -= 35
        
        # Retry attempts
        retry_label = create_label(
            "Retry Attempts:",
            NSMakeRect(20, y_offset, 100, 25)
        )
        self.view.addSubview_(retry_label)
        
        self.retry_field = create_text_field(
            NSMakeRect(130, y_offset, 80, 25),
            placeholder="3"
        )
        retry_value = self.settings_manager.get("retry_attempts", 3)
        self.retry_field.setStringValue_(str(retry_value))
        self.retry_field.setTarget_(self)
        self.retry_field.setAction_("parameterChanged:")
        self.view.addSubview_(self.retry_field)
        
        return y_offset - 40
        
    # Action methods
    def providerChanged_(self, sender):
        """Handle provider selection change"""
        segment_index = sender.selectedSegment()
        provider_map = {0: "openai", 1: "anthropic", 2: "google"}
        self.current_provider = provider_map.get(segment_index, "openai")
        
        logger.info(f"Changed provider to: {self.current_provider}")
        
        self.settings_manager.set_setting("provider", self.current_provider)
        self._update_provider_visibility()
        self._notify_settings_changed()
        
    def apiKeyChanged_(self, sender):
        """Handle API key change"""
        provider = sender.identifier()
        key = sender.stringValue()
        
        if provider and provider in self.PROVIDERS:
            key_field = self.PROVIDERS[provider]['key_field']
            self.settings_manager.set_setting(key_field, key)
            logger.info(f"Updated {provider} API key")
            self._notify_settings_changed()
            
    def modelChanged_(self, sender):
        """Handle model selection change"""
        provider = sender.identifier()
        model = sender.titleOfSelectedItem()
        
        if provider:
            self.settings_manager.set_setting(f"{provider}_model", model)
            logger.info(f"Changed {provider} model to: {model}")
            self._notify_settings_changed()
            
    def parameterChanged_(self, sender):
        """Handle parameter changes"""
        try:
            if sender == self.temperature_field:
                value = float(sender.stringValue())
                if 0.0 <= value <= 2.0:
                    self.settings_manager.set_setting("temperature", value)
                    
            elif sender == self.max_tokens_field:
                value = int(sender.stringValue())
                if value > 0:
                    self.settings_manager.set_setting("max_tokens", value)
                    
            elif sender == self.timeout_field:
                value = int(sender.stringValue())
                if value > 0:
                    self.settings_manager.set_setting("timeout", value)
                    
            elif sender == self.retry_field:
                value = int(sender.stringValue())
                if value >= 0:
                    self.settings_manager.set_setting("retry_attempts", value)
                    
            self._notify_settings_changed()
        except ValueError:
            logger.warning("Invalid parameter value entered")
            
    def validateApiKey_(self, sender):
        """Validate API key for a provider"""
        provider = sender.identifier()
        if not provider or provider not in self.PROVIDERS:
            return
            
        key_field = self.api_key_fields.get(provider)
        if not key_field:
            return
            
        key = key_field.stringValue()
        if not key:
            logger.warning(f"No {provider} API key to validate")
            return
            
        # Validate format
        is_valid, error = self.api_validator.validate_format(key, provider)
        
        if is_valid:
            logger.info(f"✅ {provider} API key format is valid")
            # TODO: Add actual API validation
        else:
            logger.warning(f"❌ {provider} API key validation failed: {error}")
            
    def _update_provider_visibility(self):
        """Show only the current provider's section"""
        for subview in self.view.subviews():
            identifier = subview.identifier()
            if identifier and identifier.endswith("_section"):
                provider = identifier.replace("_section", "")
                subview.setHidden_(provider != self.current_provider)
                
    def _notify_settings_changed(self):
        """Notify that settings have changed"""
        if self.on_settings_changed:
            try:
                self.on_settings_changed()
            except Exception as e:
                logger.error(f"Error in settings changed callback: {e}") 