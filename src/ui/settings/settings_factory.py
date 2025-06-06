#!/usr/bin/env python3
"""
Settings Factory
Factory functions for creating and managing settings windows
"""

import logging
from typing import Optional
from AppKit import NSApplication

from .settings_window import SettingsWindow

# Handle different import contexts
try:
    from ...settings.settings_manager import SettingsManager
except ImportError:
    # Fallback for test environment
    from settings.settings_manager import SettingsManager

logger = logging.getLogger(__name__)

# Global settings window instance
_settings_window_instance = None


def show_settings(settings_manager: Optional[SettingsManager] = None,
                  on_settings_changed: Optional[callable] = None) -> SettingsWindow:
    """
    Show the settings window
    
    Args:
        settings_manager: Settings manager instance (creates one if not provided)
        on_settings_changed: Callback when settings change
        
    Returns:
        SettingsWindow instance
    """
    global _settings_window_instance
    
    logger.debug("Showing settings window")
    
    # Create settings manager if not provided
    if settings_manager is None:
        logger.debug("Creating new settings manager")
        settings_manager = SettingsManager()
    
    # Create or reuse window instance
    if _settings_window_instance is None:
        logger.debug("Creating new settings window instance")
        _settings_window_instance = SettingsWindow.alloc().initWithSettingsManager_(settings_manager)
        
        # Set callback if provided
        if on_settings_changed:
            _settings_window_instance.setOnSettingsChanged_(on_settings_changed)
    else:
        logger.debug("Reusing existing settings window instance")
        
        # Update callback if provided
        if on_settings_changed:
            _settings_window_instance.setOnSettingsChanged_(on_settings_changed)
    
    # Show the window
    _settings_window_instance.show()
    
    # Make app active
    NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
    
    return _settings_window_instance


def get_settings_window() -> Optional[SettingsWindow]:
    """
    Get the current settings window instance
    
    Returns:
        SettingsWindow instance or None if not created
    """
    return _settings_window_instance


def close_settings():
    """Close the settings window if open"""
    global _settings_window_instance
    
    if _settings_window_instance and _settings_window_instance.window():
        logger.debug("Closing settings window")
        _settings_window_instance.window().close()
        _settings_window_instance = None


def show_settings_at_section(section: str,
                             settings_manager: Optional[SettingsManager] = None,
                             on_settings_changed: Optional[callable] = None) -> SettingsWindow:
    """
    Show settings window at a specific section
    
    Args:
        section: Section name ('general', 'prompts', 'advanced', 'logs')
        settings_manager: Settings manager instance
        on_settings_changed: Callback when settings change
        
    Returns:
        SettingsWindow instance
    """
    window = show_settings(settings_manager, on_settings_changed)
    
    # Navigate to section
    section_map = {
        'general': window.showGeneralSection,
        'prompts': window.showPromptsSection,
        'advanced': window.showAdvancedSection,
        'logs': window.showLogsSection
    }
    
    if section.lower() in section_map:
        section_map[section.lower()]()
    else:
        logger.warning(f"Unknown settings section: {section}")
    
    return window


def show_api_key_settings(provider: str = None,
                          settings_manager: Optional[SettingsManager] = None,
                          on_settings_changed: Optional[callable] = None) -> SettingsWindow:
    """
    Show settings window focused on API key configuration
    
    Args:
        provider: Provider to focus on ('openai', 'anthropic', 'google')
        settings_manager: Settings manager instance
        on_settings_changed: Callback when settings change
        
    Returns:
        SettingsWindow instance
    """
    window = show_settings_at_section('advanced', settings_manager, on_settings_changed)
    
    # Set provider if specified
    if provider and window.advanced_section:
        provider_map = {'openai': 0, 'anthropic': 1, 'google': 2}
        if provider.lower() in provider_map:
            window.advanced_section.provider_segment.setSelectedSegment_(
                provider_map[provider.lower()]
            )
            window.advanced_section.providerChanged_(
                window.advanced_section.provider_segment
            )
    
    return window


# Compatibility function for old code
def show_settings_dialog(service=None):
    """
    Legacy compatibility function
    
    Args:
        service: Potter service instance (for backwards compatibility)
    """
    logger.debug("Called legacy show_settings_dialog")
    
    settings_manager = None
    callback = None
    
    if service:
        # Extract settings manager and callback from service
        if hasattr(service, 'settings_manager'):
            settings_manager = service.settings_manager
        if hasattr(service, 'reload_settings'):
            callback = service.reload_settings
    
    return show_settings(settings_manager, callback) 