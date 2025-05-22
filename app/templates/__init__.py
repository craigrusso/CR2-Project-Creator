# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Template management modules
"""

# Import key template modules - PyQt version
from app.templates.template_manager import TemplateManager
# Import the operations modules for direct access if needed
from app.templates.template_manager_core import TemplateManagerCore
from app.templates.template_operations import TemplateOperations
from app.templates.structure_operations import StructureOperations
from app.templates.folder_operations import FolderOperations
from app.templates.ui_operations import UIOperations

from app.templates.templates import (
    # Legacy functions - some still used
    populate_template_gallery,  # Redirects to refactored gallery
    get_template_file,
    clear_template_file,
    clear_structure_template,
    rename_current_template,
    rename_template_file
)

# Migration helper for upgrade path
from app.templates.template_manager_migration import TemplateManagerMigration

# Use refactored template card
from app.templates.components import TemplateCard

# from app.templates.template_copier_pyqt import TemplateCopier # Commented out
# from app.templates.template_importer_pyqt import TemplateImporter # Commented out

__all__ = [
    "TemplateManager",
    "TemplateManagerCore",
    "TemplateOperations",
    "StructureOperations",
    "FolderOperations",
    "UIOperations",
    "populate_template_gallery",
    "get_template_file",
    "clear_template_file",
    "clear_structure_template",
    "rename_current_template",
    "rename_template_file",
    "TemplateManagerMigration",
    "TemplateCard",
    # "TemplateCopier", # Commented out
    # "TemplateImporter", # Commented out
]
