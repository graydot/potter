#!/usr/bin/env python3
"""
Core Plugins Package
Built-in plugins for Potter application
"""

from .text_processing_plugin import TextFormatterPlugin, TextValidatorPlugin

__all__ = [
    'TextFormatterPlugin',
    'TextValidatorPlugin'
] 