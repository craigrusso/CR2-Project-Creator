#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Structure Editor Package
Contains modular components for the Enhanced Structure Editor
"""

# Export module components - avoid circular imports
from .core import StructureEditorCore
from .structure_conversion import StructureConverter
from .ui_components import UIBuilder
from .file_operations import FileOperations
from .template_handler import TemplateHandler
from .drag_drop import DragDropHandler
from .manager_dialog import StructureManagerDialog
from .utils import _count_structure_items, get_file_icon_for_type, is_built_in_structure

# For backward compatibility and easier importing
__all__ = [
    'StructureEditorCore',
    'StructureConverter',
    'UIBuilder',
    'FileOperations',
    'TemplateHandler',
    'DragDropHandler',
    'StructureManagerDialog',
    '_count_structure_items',
    'get_file_icon_for_type',
    'is_built_in_structure'
] 