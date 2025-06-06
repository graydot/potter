#!/usr/bin/env python3
"""
Settings Dialogs Package
Contains all dialog components for settings
"""

from .prompt_dialog import PromptDialog
from .permissions_dialog import PermissionsDialog
from .common_dialogs import CommonDialogs

__all__ = [
    'PromptDialog',
    'PermissionsDialog',
    'CommonDialogs'
]
