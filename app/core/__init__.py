#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Core application modules
"""

# Import key modules - PyQt version
from app.core.app_module_pyqt import ProjectCreatorApp
from app.core.app_config import APP_NAME, APP_VERSION
from app.core.project_builder import ProjectBuilder

# Import core modules for easier access
from app.core.structure_manager import StructureManager

# Version
__version__ = "1.0.0"
