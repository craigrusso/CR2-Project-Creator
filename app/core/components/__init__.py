# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Core application components package
This package contains modular components that make up the main application.
"""

# Import all component classes for easy access
from .main_window import MainWindow
from .layout_manager import LayoutManager
from .menu_builder import MenuBuilder
from .status_manager import StatusManager
from .batch_manager import BatchManager
from .versioning_ui import VersioningUI
from .custom_options_manager import CustomOptionsManager
from .update_manager import UpdateManager
from .recent_files_manager import RecentFilesManager
from .import_export_manager import ImportExportManager

__all__ = [
    'MainWindow',
    'LayoutManager', 
    'MenuBuilder',
    'StatusManager',
    'BatchManager',
    'VersioningUI',
    'CustomOptionsManager',
    'UpdateManager',
    'RecentFilesManager',
    'ImportExportManager'
] 