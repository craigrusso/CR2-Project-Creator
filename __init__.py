#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Project Creator Tool - A tool for creating project structures from templates.
"""

__version__ = "1.0.0"
__author__ = "Craig P. Russo / CR2 Creative"

# Import key components for easier access if needed
from app.core.app_config import APP_NAME, APP_VERSION_NUMBER
from app.core.app_module import ProjectCreatorApp
from app.core.project_builder import ProjectBuilder
from app.templates.template_manager import TemplateManager 