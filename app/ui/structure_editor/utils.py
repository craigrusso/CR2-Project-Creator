#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Utility functions for the structure editor
"""

import os
from PyQt5.QtWidgets import QStyle, QFileIconProvider
from PyQt5.QtCore import QFileInfo
import mimetypes

def _count_structure_items(structure):
    """
    Count the number of items in a structure
    This was the missing method causing the crash
    
    Args:
        structure (list): The structure to count items in
        
    Returns:
        int: Total number of items in the structure
    """
    count = 0
    
    # Base case: empty structure
    if not structure:
        return 0
    
    for item in structure:
        count += 1  # Count this item
        
        # If item is a dictionary
        if isinstance(item, dict):
            # If it has the standard format with children
            if "children" in item and isinstance(item["children"], list):
                count += _count_structure_items(item["children"])
            # If it's in the alternative format with a folder name as the key
            elif len(item) == 1 and isinstance(list(item.values())[0], list):
                count += _count_structure_items(list(item.values())[0])
    
    return count

def get_file_icon_for_type(file_path):
    """
    Get the appropriate icon for a file based on its extension
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        QIcon: Icon for the file type
    """
    from PyQt5.QtWidgets import QApplication
    
    # Initialize mime types if not already initialized
    if not mimetypes.inited:
        mimetypes.init()
    
    # Get file extension
    _, ext = os.path.splitext(file_path.lower())
    
    # Handle special file types
    if ext in ['.prproj', '.aep', '.aepx']:
        return QApplication.style().standardIcon(QStyle.SP_FileLinkIcon)
    elif ext in ['.mp4', '.mov', '.avi', '.mxf']:
        return QApplication.style().standardIcon(QStyle.SP_MediaPlay)
    elif ext in ['.psd', '.ai', '.png', '.jpg', '.jpeg', '.tif', '.tiff']:
        return QApplication.style().standardIcon(QStyle.SP_FileDialogContentsView)
    elif ext in ['.wav', '.mp3', '.aac', '.m4a']:
        return QApplication.style().standardIcon(QStyle.SP_MediaVolume)
    elif ext in ['.txt', '.md', '.rtf']:
        return QApplication.style().standardIcon(QStyle.SP_FileDialogDetailedView)
    
    # Use system file icon provider for other types
    try:
        provider = QFileIconProvider()
        file_info = QFileInfo(file_path)
        return provider.icon(file_info)
    except:
        # Fallback to generic file icon
        return QApplication.style().standardIcon(QStyle.SP_FileIcon)

def is_built_in_structure(structure_name):
    """
    Check if a structure is a built-in structure
    
    Args:
        structure_name (str): Name of the structure
        
    Returns:
        bool: True if it's a built-in structure, False otherwise
    """
    # Known built-in structure prefixes
    built_in_prefixes = [
        "Video Editing",
        "Photo Editing",
        "VFX",
        "Motion Graphics",
        "Audio Production",
        "3D",
    ]
    
    # Check if the structure name starts with any of the built-in prefixes
    if structure_name:
        for prefix in built_in_prefixes:
            if structure_name.startswith(prefix):
                return True
    
    return False 