#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Dialog windows for the application - This file now simply imports and re-exports
functions from the refactored modules.
"""

# Import from refactored modules
from app.dialogs.structure_dialogs import (
    preview_structure,
    populate_structure_tree,
    edit_template_structure,
    import_template_structure,
    preview_template_structure
)

from app.dialogs.batch_operations import (
    show_batch_results,
    handle_batch_projects
)

from app.dialogs.info_dialogs import (
    show_about,
    show_tutorial
)

from app.dialogs.preferences_dialog import (
    show_preferences_dialog
)

from app.dialogs.template_management import (
    show_edit_template,
    create_basic_info_tab,
    create_structure_tab,
    show_manage_templates,
    view_structure,
    delete_structure,
    edit_template,
    delete_template,
    import_template,
    create_folder,
    rename_folder,
    delete_folder
)

from app.dialogs.file_operations import (
    process_dropped_file,
    process_dropped_directory,
    add_file_to_tree
)

# Re-export all functions for backward compatibility
__all__ = [
    'preview_structure',
    'populate_structure_tree',
    'edit_template_structure',
    'import_template_structure',
    'preview_template_structure',
    'show_batch_results',
    'handle_batch_projects',
    'show_about',
    'show_tutorial',
    'show_preferences_dialog',
    'show_edit_template',
    'create_basic_info_tab',
    'create_structure_tab',
    'show_manage_templates',
    'view_structure',
    'delete_structure',
    'edit_template',
    'delete_template',
    'import_template',
    'create_folder',
    'rename_folder',
    'delete_folder',
    'process_dropped_file',
    'process_dropped_directory',
    'add_file_to_tree'
]