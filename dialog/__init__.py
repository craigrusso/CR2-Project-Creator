#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Dialog modules for Project Creator
"""

# Import key dialog functions
from dialog.batch_dialog import show_batch_create, show_batch_results
from dialog.about_dialog import show_about
from dialog.preferences_dialog import show_preferences
from dialog.preview_dialog import preview_structure
from dialog.tutorial_dialog import show_tutorial
from dialog.template_dialogs import (
    edit_template_dialog,
    create_new_category,
    create_new_folder,
    manage_templates_dialog,
    import_template,
    delete_selected_template,
    edit_selected_template
)
from dialog.template_management_dialog import manage_templates_dialog
from dialog.folder_dialog import create_new_folder
from dialog.category_dialog import create_new_category
from dialog.template_edit_dialog import edit_template_dialog

# Export all public functions
__all__ = [
    'show_batch_create',
    'show_batch_results',
    'show_about',
    'show_preferences',
    'preview_structure',
    'show_tutorial',
    'edit_template_dialog',
    'create_new_category',
    'create_new_folder',
    'manage_templates_dialog',
    'import_template',
    'delete_selected_template',
    'edit_selected_template'
] 