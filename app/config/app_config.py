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

# Resource path helper removed - moved to app/utils.py

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

# App constants
APP_BUILD_NUMBER = 255 # Make sure this reflects the current build

# --- API Endpoints --- 
DEFAULT_GET_PUBLIC_DOWNLOADS_URL = "https://www.cr2creative.com/api/downloads/public" # Default URL

# --- Default Paths ---
DEFAULT_STRUCTURES_PATH = "Default Project Structures"
DEFAULT_TEMPLATES_PATH = "Project Templates"

# --- Update Check --- 
UPDATE_CHECK_INTERVAL_SECONDS = 14 * 24 * 60 * 60 # Check every 14 days
