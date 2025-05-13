#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Icon Utilities Module
Provides centralized icon handling with platform-specific icons for files and folders
"""

import os
import platform
from PyQt5.QtWidgets import QApplication, QStyle, QFileIconProvider
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QFileInfo, QSize
from app.constants import get_resource_path
from app.ui.color_scheme_pyqt import APP_COLORS

class IconProvider:
    """Centralized icon provider for the application"""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists"""
        if cls._instance is None:
            cls._instance = super(IconProvider, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the icon provider with platform-specific settings"""
        if self._initialized:
            return
            
        self._initialized = True
        self._system = platform.system()
        self._icon_provider = QFileIconProvider()
        
        # Initialize file type mappings with distinct icons
        self._init_file_type_mappings()
        
        # Platform-specific folder icons
        self._folder_icon = None
        self._folder_open_icon = None
        self._init_platform_specific_folder_icons()
    
    def _init_file_type_mappings(self):
        """Initialize file type mappings with distinct icons"""
        # File type constants - more distinct icons than QFileIconProvider
        self.VIDEO_ICON = QApplication.style().standardIcon(QStyle.SP_MediaPlay)
        self.AUDIO_ICON = QApplication.style().standardIcon(QStyle.SP_MediaVolume)
        self.IMAGE_ICON = QApplication.style().standardIcon(QStyle.SP_DesktopIcon)
        self.DOC_ICON = QApplication.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        self.CODE_ICON = QApplication.style().standardIcon(QStyle.SP_FileDialogContentsView)
        self.ADOBE_ICON = QApplication.style().standardIcon(QStyle.SP_FileLinkIcon)
        self.GENERIC_FILE_ICON = QApplication.style().standardIcon(QStyle.SP_FileIcon)
        
        # Extension to icon mappings
        self._extension_mappings = {
            # Video files
            '.mp4': self.VIDEO_ICON, '.mov': self.VIDEO_ICON, '.avi': self.VIDEO_ICON, 
            '.mkv': self.VIDEO_ICON, '.mxf': self.VIDEO_ICON, '.webm': self.VIDEO_ICON, 
            '.wmv': self.VIDEO_ICON, '.flv': self.VIDEO_ICON,
            
            # Audio files
            '.mp3': self.AUDIO_ICON, '.wav': self.AUDIO_ICON, '.aac': self.AUDIO_ICON, 
            '.flac': self.AUDIO_ICON, '.ogg': self.AUDIO_ICON, '.m4a': self.AUDIO_ICON, 
            '.aif': self.AUDIO_ICON, '.aiff': self.AUDIO_ICON,
            
            # Image files
            '.jpg': self.IMAGE_ICON, '.jpeg': self.IMAGE_ICON, '.png': self.IMAGE_ICON, 
            '.gif': self.IMAGE_ICON, '.bmp': self.IMAGE_ICON, '.tiff': self.IMAGE_ICON, 
            '.tif': self.IMAGE_ICON, '.svg': self.IMAGE_ICON,
            
            # Document files
            '.pdf': self.DOC_ICON, '.doc': self.DOC_ICON, '.docx': self.DOC_ICON, 
            '.txt': self.DOC_ICON, '.rtf': self.DOC_ICON, '.xls': self.DOC_ICON, 
            '.xlsx': self.DOC_ICON, '.ppt': self.DOC_ICON, '.pptx': self.DOC_ICON,
            
            # Code files
            '.py': self.CODE_ICON, '.js': self.CODE_ICON, '.html': self.CODE_ICON, 
            '.css': self.CODE_ICON, '.json': self.CODE_ICON, '.xml': self.CODE_ICON, 
            '.cpp': self.CODE_ICON, '.c': self.CODE_ICON, '.h': self.CODE_ICON, 
            '.java': self.CODE_ICON,
            
            # Adobe project files
            '.prproj': self.ADOBE_ICON, '.aep': self.ADOBE_ICON, '.aepx': self.ADOBE_ICON, 
            '.psd': self.ADOBE_ICON, '.ai': self.ADOBE_ICON, '.indd': self.ADOBE_ICON
        }
    
    def _init_platform_specific_folder_icons(self):
        """Initialize platform-specific folder icons"""
        # Default folder icons
        self._folder_icon = QApplication.style().standardIcon(QStyle.SP_DirIcon)
        self._folder_open_icon = QApplication.style().standardIcon(QStyle.SP_DirOpenIcon)
        
        # Use platform-specific folder colors to match OS expectations
        if self._system == "Darwin":  # macOS
            folder_color = APP_COLORS.get('macos_folder_icon', '#3897F0')
        else:  # Windows and others - use golden folder color
            folder_color = APP_COLORS.get('folder_icon', '#E8BA36')
            
        # Check for system-specific folder icons first
        system_name = self._system.lower()
        
        # Updated paths to the platform-specific icons directory
        platform_folder_path = get_resource_path(f'app/assets/icons/platform/folder_{system_name}.png')
        if os.path.exists(platform_folder_path):
            self._folder_icon = QIcon(platform_folder_path)
            print(f"DEBUG: Using platform-specific folder icon: {platform_folder_path}")
        else:
            print(f"DEBUG: Using system standard folder icon (no custom icon found at {platform_folder_path})")
            
        platform_folder_open_path = get_resource_path(f'app/assets/icons/platform/folder_open_{system_name}.png')
        if os.path.exists(platform_folder_open_path):
            self._folder_open_icon = QIcon(platform_folder_open_path)
            print(f"DEBUG: Using platform-specific open folder icon: {platform_folder_open_path}")
        else:
            print(f"DEBUG: Using system standard open folder icon (no custom icon found)")
    
    def get_folder_icon(self, is_open=False):
        """Get platform-specific folder icon"""
        return self._folder_open_icon if is_open else self._folder_icon
    
    def get_file_icon(self, filename):
        """
        Get the appropriate icon for a file based on its extension
        
        Args:
            filename (str): Name or path of the file
            
        Returns:
            QIcon: Icon for the file type
        """
        # Extract file extension
        _, ext = os.path.splitext(filename.lower())
        
        # Check for project name placeholders
        is_project_file = '{PROJECT_NAME}' in filename and '.' in filename
        if is_project_file:
            # Extract extension from project file
            parts = filename.split('.')
            if len(parts) > 1:
                ext = '.' + parts[-1].split()[0]  # Get extension before any emoji
        
        # Check if we have a pre-defined icon for this extension
        if ext in self._extension_mappings:
            return self._extension_mappings[ext]
        
        # Use system file icon provider as fallback
        try:
            # For project name files, create a temporary extension for the icon provider
            if is_project_file:
                temp_file = f"temp{ext}"
                file_info = QFileInfo(temp_file)
            else:
                file_info = QFileInfo(filename)
                
            system_icon = self._icon_provider.icon(file_info)
            if not system_icon.isNull():
                return system_icon
        except Exception as e:
            print(f"Error getting file icon: {e}")
        
        # Last resort - use generic file icon
        return self.GENERIC_FILE_ICON

# Global convenience functions
def get_folder_icon(is_open=False):
    """Get platform-specific folder icon"""
    return IconProvider().get_folder_icon(is_open)

def get_file_icon(filename):
    """Get icon for file type"""
    return IconProvider().get_file_icon(filename) 