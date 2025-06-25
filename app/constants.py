#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Constants module to prevent circular imports
"""

import os
import sys

def get_resource_path(relative_path):
    """
    Get the correct resource path for both development and frozen environments.
    
    Args:
        relative_path (str): Path relative to the application root
        
    Returns:
        str: Absolute path to the resource
    """
    # Determine if the application is frozen (PyInstaller)
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # If frozen, use the _MEIPASS attribute provided by PyInstaller
        base_path = sys._MEIPASS
    else:
        # If running in development, use the script directory
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    # Return the absolute path to the resource
    return os.path.join(base_path, relative_path)

# App constants
APP_NAME = "Echelon"
APP_VERSION_NUMBER = "1.0"
APP_BUILD_NUMBER = "278"
APP_RELEASE_STAGE = "Stable"
USER_UPDATE_CHANNEL_PREFERENCE = "Stable"
RECENT_PROJECTS_MAX = 5
RECENT_TEMPLATES_MAX = 5

# Removed DEFAULT_STRUCTURES and DEFAULT_PROJECT_STRUCTURE as they are obsolete
# Templates now manage their own structures directly.

# Default template categories (Still used for the dropdown)
DEFAULT_TEMPLATE_CATEGORIES = [
    "Custom",
    "Examples",
    "Video Editing",
    "Motion Graphics",
    "VFX",
    "Web Development",
    "General" # Keep General as a fallback? Or remove?
]

# Reserved filenames (cross-platform)
RESERVED_FILENAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}

# PROJECT_TYPE_TO_STRUCTURE removed as it depended on obsolete DEFAULT_STRUCTURES 