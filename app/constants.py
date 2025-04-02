#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Constants module to prevent circular imports
"""

import os
import sys

# Resource path helper
def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # When frozen, the base path should be the Resources directory
        executable_dir = os.path.dirname(sys.executable)
        base_path = os.path.normpath(os.path.join(executable_dir, '..', 'Resources'))
        
        # Standard path with app subdirectory
        final_path = os.path.join(base_path, 'app', relative_path)
        
        # Check if file exists at standard path
        if not os.path.exists(final_path):
            # Try with duplicate Resources in path (PyInstaller quirk)
            duplicate_resources_path = os.path.join(base_path, 'Resources', 'app', relative_path)
            if os.path.exists(duplicate_resources_path):
                print(f"DEBUG: Found resource at duplicate Resources path: {duplicate_resources_path}")
                return duplicate_resources_path
                
            # Sanity check if _MEIPASS exists as a fallback
            if hasattr(sys, '_MEIPASS') and sys._MEIPASS != base_path:
                print(f"WARNING: Resource not found at standard path, falling back to _MEIPASS '{sys._MEIPASS}'")
                meipass_path = os.path.join(sys._MEIPASS, 'app', relative_path)
                if os.path.exists(meipass_path):
                    return meipass_path
        
        print(f"DEBUG: Frozen Mode - Using base_path: {base_path}")
        
        # ***** CORRECTED PATH JOIN FOR FROZEN *****
        # Assets are placed inside an 'app' folder within Resources by --add-data
        return final_path

    except Exception as e:
        print(f"DEBUG: get_resource_path exception: {e}")
        # Not frozen - running from source
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) 
        print(f"DEBUG: Development Mode - Using base_path: {base_path}")
        # In development, assets are usually relative to the project root (base_path)
        # under the app directory. Adjust if structure differs.
        final_path = os.path.join(base_path, 'app', relative_path)
        
    # Debug print
    print(f"DEBUG get_resource_path: base='{base_path}', rel='{relative_path}', final='{final_path}'")

    return final_path

# App constants
APP_NAME = "Echelon"
APP_VERSION = "0.95"
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