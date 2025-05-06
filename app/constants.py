#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Constants module to prevent circular imports
"""

import os
import sys

# Resource path helper
def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller/py2app """
    
    # Determine the base path depending on whether the app is frozen
    if getattr(sys, 'frozen', False):
        # Running frozen/packaged
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller environment
            base_path = sys._MEIPASS
            print(f"DEBUG: Frozen Mode (PyInstaller) - Using base_path: {base_path}")
        else:
            # Assume py2app environment
            # The executable is in Contents/MacOS, resources are in Contents/Resources
            base_path = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", "Resources"))
            print(f"DEBUG: Frozen Mode (py2app) - Using base_path: {base_path}")
            
        final_path = os.path.join(base_path, relative_path)

    else:
        # Running from source (development mode)
        # Base path is the project root (one level up from 'app' directory)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        # Join the project root directly with the relative path provided
        final_path = os.path.join(base_path, relative_path)
        print(f"DEBUG: Development Mode - Using base_path: {base_path}")

    # Debug print for the determined path
    print(f"DEBUG get_resource_path: relative='{relative_path}', final='{final_path}'")

    # Check if the final path exists, provide warning if not
    if not os.path.exists(final_path):
         print(f"WARNING: Resource path does not exist: {final_path}")

    return final_path

# App constants
APP_NAME = "Echelon"
APP_VERSION = "1.0"
APP_BUILD_NUMBER = 255
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