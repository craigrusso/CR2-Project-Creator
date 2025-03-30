#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import platform
import json
import sys

# Import colors from our centralized color scheme - PyQt version
from app.ui.color_scheme_pyqt import colors, APP_COLORS
# Import all necessary constants from constants.py
from app.constants import (
    APP_NAME, APP_VERSION, RECENT_PROJECTS_MAX, RECENT_TEMPLATES_MAX,
    DEFAULT_TEMPLATE_CATEGORIES
)

# Config file locations
def get_config_paths():
    """Get paths for configuration files and directories"""
    # Get home directory in a cross-platform way
    home_dir = os.path.expanduser("~")
    
    # Fallback if expanduser doesn't work
    if not os.path.exists(home_dir):
        if platform.system() == "Windows":
            home_drive = os.environ.get('HOMEDRIVE')
            home_path = os.environ.get('HOMEPATH')
            if home_drive and home_path:
                home_dir = os.path.join(home_drive, home_path)
            else:
                home_dir = os.getcwd()
        else:
            home_dir = os.environ.get('HOME', os.getcwd())
    
    config_dir = os.path.join(home_dir, ".echelon")
    
    paths = {
        "config_dir": config_dir,
        "config_file": os.path.join(config_dir, "config.json"),
        "recent_projects_file": os.path.join(config_dir, "recent_projects.json"),
        "recent_templates_file": os.path.join(config_dir, "recent_templates.json"),
        "templates_dir": os.path.join(config_dir, "templates"),
        "custom_structures_dir": os.path.join(config_dir, "structures"),
        "template_directories_dir": os.path.join(config_dir, "template_directories")
    }
    
    # Create directories if they don't exist
    for dir_path in [config_dir, paths["templates_dir"], paths["custom_structures_dir"], paths["template_directories_dir"]]:
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        except Exception as e:
            print(f"Warning: Could not create directory {dir_path}: {e}")
            # Try to use a temporary directory as fallback
            if dir_path == config_dir:
                temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_config")
                try:
                    os.makedirs(temp_dir, exist_ok=True)
                    paths["config_dir"] = temp_dir
                    # Update all other paths
                    for key in paths:
                        if key != "config_dir":
                            paths[key] = paths[key].replace(config_dir, temp_dir)
                except:
                    print(f"Critical error: Unable to create any config directory")
    
    return paths

# Platform-specific DPI handling
def setup_dpi_awareness():
    """Configure DPI settings for the application"""
    if platform.system() == "Windows":
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(2)
        except ImportError:
            pass

# Sample templates for the gallery
SAMPLE_TEMPLATES = [
    {"name": "Basic Video Edit", "category": "Video Editing", "icon": "🎬", "description": "Standard timeline with basic folders"},
    {"name": "Interview Setup", "category": "Video Editing", "icon": "🎙️", "description": "Multicam interview template"},
    {"name": "Motion Graphics Intro", "category": "Motion Graphics", "icon": "✨", "description": "Animated intro template"},
    {"name": "Logo Animation", "category": "Motion Graphics", "icon": "🔄", "description": "3D logo reveal"},
    {"name": "Photo Album", "category": "Design", "icon": "📷", "description": "Multi-page photo layout"},
    {"name": "Podcast Setup", "category": "Audio", "icon": "🎧", "description": "Podcast editing template"},
    {"name": "Social Media Pack", "category": "Design", "icon": "📱", "description": "Templates for various platforms"},
    {"name": "Custom Empty", "category": "Custom", "icon": "📂", "description": "Start with a blank template"}
]
