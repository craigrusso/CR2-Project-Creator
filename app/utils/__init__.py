# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Utility modules
"""

# Import from utils.py
from app.utils.utils import (
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

# Import from file operations
from app.utils.file_operations import FileOperationsHandler, BinaryFileHandler

# Import from template utils
from app.utils.template_utils import (
    validate_template_name,
    format_template_name,
    get_structure_file_extension,
    get_structure_file_extensions,
    parse_structure_data
)

# Import from security
from app.utils.security import (
    SecurityBookmarkManager,
    save_security_bookmarks,
    load_security_bookmarks
)

# Import from cache
from app.utils.cache import FileCacheManager, CachePreferences

# Export commonly used functions and classes
__all__ = [
    # Basic utils
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
    
    # File operations
    'FileOperationsHandler',
    'BinaryFileHandler',
    
    # Template utils
    'validate_template_name',
    'format_template_name',
    'get_structure_file_extension',
    'get_structure_file_extensions',
    'parse_structure_data',
    
    # Security
    'SecurityBookmarkManager',
    'save_security_bookmarks',
    'load_security_bookmarks',
    
    # Cache
    'FileCacheManager',
    'CachePreferences'
]
