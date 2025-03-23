# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Utility modules
"""

# Import key utility functions
from app.utils.utils import (
    get_config_paths,
    load_json_file,
    save_json_file,
    load_config,
    save_config,
    load_recent_projects,
    save_recent_projects,
    load_recent_templates,
    save_recent_templates,
    add_to_recent_projects,
    open_folder,
    create_readme_file,
    truncate_path
)
from app.utils.integration import integrate_enhanced_templates, patch_app_file
from app.utils.file_operations import FileOperationsHandler

# Export file operations
__all__ = [
    'get_config_paths',
    'load_json_file',
    'save_json_file',
    'load_config',
    'save_config',
    'load_recent_projects',
    'save_recent_projects',
    'load_recent_templates',
    'save_recent_templates',
    'add_to_recent_projects',
    'open_folder',
    'create_readme_file',
    'truncate_path',
    'integrate_enhanced_templates',
    'patch_app_file',
    'FileOperationsHandler'
]
