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
    
    # Debug output to help troubleshoot path issues
    print(f"[DEBUG] get_resource_path called for: {relative_path}")
    print(f"[DEBUG] Current working directory: {os.getcwd()}")
    
    try:
        # Get base path for bundled app or development
        if getattr(sys, 'frozen', False):
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            # py2app stores resources relative to the app bundle
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller
                base_path = sys._MEIPASS
                print(f"[DEBUG] Using PyInstaller path: {base_path}")
            else:
                # py2app
                base_path = os.path.abspath(os.path.dirname(os.path.dirname(sys.executable)))
                print(f"[DEBUG] Using py2app path: {base_path}")
        else:
            # Dev mode - try different approaches to find the right base path
            base_path = os.path.abspath(os.path.dirname(__file__))
            print(f"[DEBUG] Using script directory path: {base_path}")
            
            # If we're in a subdirectory and need to go up to project root
            if relative_path.startswith("app/") and os.path.basename(base_path) == "app":
                # We're already in the app directory, strip "app/" from relative_path
                relative_path = relative_path[4:]
                print(f"[DEBUG] Adjusted relative path to: {relative_path}")
            elif relative_path.startswith("app/") and not os.path.basename(base_path) == "app":
                # We need to find the project root that contains app/
                current_dir = base_path
                while os.path.basename(current_dir) != "app" and os.path.dirname(current_dir) != current_dir:
                    # Go up one directory level
                    parent_dir = os.path.dirname(current_dir)
                    if os.path.exists(os.path.join(parent_dir, "app")):
                        base_path = parent_dir
                        print(f"[DEBUG] Found project root at: {base_path}")
                        break
                    current_dir = parent_dir
        
        # Try both paths to see which one works
        resource_path = os.path.join(base_path, relative_path)
        if not os.path.exists(resource_path) and relative_path.startswith("app/"):
            # Try without app/ prefix
            alt_path = os.path.join(base_path, relative_path[4:])
            if os.path.exists(alt_path):
                resource_path = alt_path
                print(f"[DEBUG] Using alternative resource path: {resource_path}")
        
        print(f"[DEBUG] Final resource path: {resource_path}")
        print(f"[DEBUG] Path exists: {os.path.exists(resource_path)}")
        return resource_path
    except Exception as e:
        print(f"[ERROR] Error in get_resource_path: {str(e)}")
        # Fallback to simple path resolution
        return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)

# App constants
APP_NAME = "Echelon"
APP_VERSION = "1.0"
APP_BUILD_NUMBER = 261
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