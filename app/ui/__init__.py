#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
UI components and functionality for the application
"""

# Import main UI components for easy access
from app.ui.app_theme_pyqt import configure_styles, apply_dark_theme_to_template_section
from app.ui.color_scheme_pyqt import colors
from app.ui.ui_components_pyqt import ScrollableFrame, ToolTip, CardFrame, SearchBox, TemplateFileCard

# Import structure editor components
from app.ui.structure_editor_functions import show_enhanced_structure_editor

# Import the enhanced structure editor
try:
    from app.ui.enhanced_structure_editor import EnhancedStructureEditor
except ImportError as e:
    print(f"Warning: Failed to import EnhancedStructureEditor: {e}")

# Import gallery templates handling
try:
    from app.ui.gallery_templates import GalleryTemplates
except ImportError as e:
    print(f"Warning: Failed to import GalleryTemplates: {e}")

# Make all UI modules available for import
__all__ = [
    'configure_styles',
    'apply_dark_theme_to_template_section',
    'colors',
    'ScrollableFrame',
    'ToolTip',
    'CardFrame',
    'SearchBox',
    'TemplateFileCard',
    'show_enhanced_structure_editor',
    'EnhancedStructureEditor',
    'GalleryTemplates'
]
