#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import platform
import json

# Import colors from our centralized color scheme - PyQt version
from app.ui.color_scheme_pyqt import colors, APP_COLORS
from app.constants import APP_NAME, APP_VERSION, RECENT_PROJECTS_MAX, RECENT_TEMPLATES_MAX, DEFAULT_STRUCTURES, PROJECT_TYPE_TO_STRUCTURE, DEFAULT_TEMPLATE_CATEGORIES

# App constants
APP_NAME = "CR2 Creative Pro"
APP_VERSION = "2.1"
RECENT_PROJECTS_MAX = 5
RECENT_TEMPLATES_MAX = 5

# Color scheme is now imported from color_scheme.py

# Config file locations
def get_config_paths():
    """Get paths for configuration files and directories"""
    config_dir = os.path.join(os.path.expanduser("~"), ".cr2creator")
    
    paths = {
        "config_dir": config_dir,
        "config_file": os.path.join(config_dir, "config.json"),
        "recent_projects_file": os.path.join(config_dir, "recent_projects.json"),
        "recent_templates_file": os.path.join(config_dir, "recent_templates.json"),
        "templates_dir": os.path.join(config_dir, "templates"),
        "custom_structures_dir": os.path.join(config_dir, "structures")
    }
    
    # Create directories if they don't exist
    for dir_path in [config_dir, paths["templates_dir"], paths["custom_structures_dir"]]:
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

# Default template categories
DEFAULT_TEMPLATE_CATEGORIES = ["Video Editing", "Motion Graphics", "Design", "Audio", "Custom"]

# Default project structure templates
DEFAULT_STRUCTURES = {
    "standard": [
        {"01_PREMIER_PROJECT": [
            {"01_FOOTAGE": []}
        ]},
        {"02_AE_PROJECTS": []},
        {"03_AE_RENDERS": []},
        {"04_DELIVERY": []},
        {"05_MUSIC": []},
        {"06_AAFs": []},
        {"07_VOs": []},
        {"08_AUDITION_FILES": [
            {"01_AUDITION_SESSIONS": []},
            {"02_AUDITION_FILES": []},
            {"03_MIX_PRINTS": []}
        ]}
    ],
    "video": [
        {"01_PREMIER_PROJECT": [
            {"01_RAW_FOOTAGE": []},
            {"02_SORTED_FOOTAGE": []},
            {"03_GRAPHICS": []}
        ]},
        {"02_AE_PROJECTS": []},
        {"03_AE_RENDERS": []},
        {"04_DELIVERY": [
            {"01_DRAFTS": []},
            {"02_FINALS": []}
        ]},
        {"05_MUSIC": []},
        {"06_SFX": []},
        {"07_VOs": []},
        {"08_AUDITION_FILES": [
            {"01_AUDITION_SESSIONS": []},
            {"02_AUDITION_FILES": []},
            {"03_MIX_PRINTS": []}
        ]},
        {"09_DOCUMENTS": []},
        {"10_BACKUPS": []}
    ],
    "motion": [
        {"01_AE_PROJECTS": []},
        {"02_C4D_PROJECTS": []},
        {"03_RENDERS": [
            {"01_PREVIEWS": []},
            {"02_FINALS": []}
        ]},
        {"04_ASSETS": [
            {"01_IMAGES": []},
            {"02_VIDEOS": []},
            {"03_AUDIO": []},
            {"04_3D_MODELS": []}
        ]},
        {"05_REFERENCE": []},
        {"06_DELIVERY": []},
        {"07_BACKUPS": []}
    ],
    "design": [
        {"01_PHOTOSHOP_PROJECTS": []},
        {"02_ILLUSTRATOR_PROJECTS": []},
        {"03_INDESIGN_PROJECTS": []},
        {"04_ASSETS": [
            {"01_IMAGES": []},
            {"02_FONTS": []},
            {"03_LOGOS": []}
        ]},
        {"05_REFERENCE": []},
        {"06_EXPORTS": [
            {"01_WEB": []},
            {"02_PRINT": []}
        ]},
        {"07_CLIENT_FEEDBACK": []},
        {"08_FINALS": []}
    ],
    "audio": [
        {"01_AUDITION_SESSIONS": []},
        {"02_RAW_AUDIO": []},
        {"03_EDITED_AUDIO": []},
        {"04_MUSIC": []},
        {"05_SFX": []},
        {"06_RENDERS": [
            {"01_DRAFTS": []},
            {"02_FINALS": []}
        ]},
        {"07_REFERENCES": []},
        {"08_DOCUMENTS": []}
    ]
}

# Map project types to structure keys
PROJECT_TYPE_TO_STRUCTURE = {
    "Standard": "standard",
    "Video Editing": "video",
    "Motion Graphics": "motion",
    "Design": "design",
    "Audio": "audio"
}

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
