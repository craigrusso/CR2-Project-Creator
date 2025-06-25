#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
File Type Detection Utility

Handles file type detection, categorization, and related constants.
Extracted from the monolithic file_operations.py for better organization.
"""

import os
from PyQt6.QtWidgets import QApplication, QStyle
from PyQt6.QtGui import QIcon

# Constants for file types
FILE_TYPES = {
    'video': ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg', '.3gp', '.prproj'],
    'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.aiff'],
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg'],
    'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
    'spreadsheet': ['.xls', '.xlsx', '.csv', '.ods'],
    'presentation': ['.ppt', '.pptx', '.odp'],
    'archive': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'script': ['.py', '.js', '.html', '.css', '.xml', '.json'],
    'cad': ['.dwg', '.dxf', '.stp', '.step', '.iges', '.igs'],
    'other': []
}


class FileTypeDetector:
    """Utility class for detecting and categorizing file types"""
    
    @staticmethod
    def get_file_type_from_extension(file_path):
        """Determine file type from extension"""
        ext = os.path.splitext(file_path.lower())[1]
        
        for file_type, extensions in FILE_TYPES.items():
            if ext in extensions:
                return file_type
        return 'other'
    
    @staticmethod
    def get_file_icon(file_type):
        """Get appropriate icon for file type"""
        icon_map = {
            'video': '🎬',
            'audio': '🎵',
            'image': '🖼️',
            'document': '📄',
            'spreadsheet': '📊',
            'presentation': '📽️',
            'archive': '📦',
            'script': '💻',
            'folder': '',
            'other': '📄'
        }
        return icon_map.get(file_type, '📄')
    
    @staticmethod
    def get_available_categories():
        """Get list of available file type categories (excluding 'other')"""
        categories = list(FILE_TYPES.keys())
        if 'other' in categories:
            categories.remove('other')
        return categories
    
    @staticmethod
    def is_supported_extension(file_path):
        """Check if file extension is in our supported types"""
        return FileTypeDetector.get_file_type_from_extension(file_path) != 'other'

    @staticmethod
    def is_binary_file(file_path):
        """
        Check if a file is binary or text.
        
        Args:
            file_path (str): The path to the file.
            
        Returns:
            bool: True if the file is likely binary, False otherwise.
        """
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' in chunk
        except IOError:
            return False

def get_folder_icon(is_expanded=False) -> QIcon:
    """
    Returns the appropriate folder icon (open or closed).
    
    Args:
        is_expanded (bool): Whether the folder is expanded.
        
    Returns:
        QIcon: The folder icon.
    """
    if is_expanded:
        return QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon)
    else:
        return QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon) 