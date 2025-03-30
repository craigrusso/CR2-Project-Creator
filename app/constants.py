#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Constants module to prevent circular imports
"""

# App constants
APP_NAME = "Echelon"
APP_VERSION = "0.081"
RECENT_PROJECTS_MAX = 5
RECENT_TEMPLATES_MAX = 5

# Removed DEFAULT_STRUCTURES and DEFAULT_PROJECT_STRUCTURE as they are obsolete
# Templates now manage their own structures directly.

# Default template categories (Still used for the dropdown)
DEFAULT_TEMPLATE_CATEGORIES = [
    "Custom",
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