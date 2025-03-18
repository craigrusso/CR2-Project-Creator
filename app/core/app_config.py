#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import platform
import json

# Import colors from our centralized color scheme - PyQt version
from app.ui.color_scheme_pyqt import colors, APP_COLORS
# Import all necessary constants from constants.py
from app.constants import (
    APP_NAME, APP_VERSION, RECENT_PROJECTS_MAX, RECENT_TEMPLATES_MAX,
    DEFAULT_STRUCTURES, PROJECT_TYPE_TO_STRUCTURE, DEFAULT_TEMPLATE_CATEGORIES
)

# Config file locations
def get_config_paths():
    """Get paths for configuration files and directories"""
    config_dir = os.path.join(os.path.expanduser("~"), ".echelon")
    
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
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
    
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
