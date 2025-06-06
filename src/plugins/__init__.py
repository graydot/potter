#!/usr/bin/env python3
"""
Plugins Package
Plugin Architecture for Potter application
"""

from .plugin_manager import PluginManager
from .plugin_interface import PluginInterface, PluginContext
from .plugin_registry import PluginRegistry

__all__ = [
    'PluginManager',
    'PluginInterface',
    'PluginContext', 
    'PluginRegistry'
] 