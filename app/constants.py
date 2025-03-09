#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Constants module to prevent circular imports
"""

# App constants
APP_NAME = "CR2 Creative Pro"
APP_VERSION = "2.1"
RECENT_PROJECTS_MAX = 5
RECENT_TEMPLATES_MAX = 5

# Default structures
DEFAULT_STRUCTURES = {
    "Basic": ["images", "scripts", "styles", "docs"],
    "Web Project": ["css", "js", "images", "fonts", "libs"],
    "Python App": ["src", "tests", "docs", "data"],
    "Node.js": ["src", "public", "routes", "models", "views", "controllers"],
    "Mobile App": ["assets", "lib", "screens", "models", "services"]
}

# Default template categories
DEFAULT_TEMPLATE_CATEGORIES = [
    "Web Development",
    "Mobile Apps",
    "Desktop Applications",
    "Data Science",
    "Game Development"
]

# Project types
PROJECT_TYPE_TO_STRUCTURE = {
    "Standard": "Basic",
    "standard": "Basic",
    "Web": "Web Project",
    "Python": "Python App",
    "Node.js": "Node.js",
    "Mobile": "Mobile App"
} 