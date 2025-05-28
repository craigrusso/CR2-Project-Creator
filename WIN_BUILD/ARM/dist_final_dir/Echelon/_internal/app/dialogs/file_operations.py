#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
File and directory operation utilities for dialog windows.
"""

import os
from PyQt6.QtWidgets import (QTreeWidgetItem, QStyle, QApplication)
from PyQt6.QtCore import Qt

def process_dropped_file(file_path, parent_item):
    """Process a file dropped onto the tree"""
    # Get the filename
    file_name = os.path.basename(file_path)
    
    # Skip hidden files on Mac
    if file_name.startswith('.'):
        return None
        
    # Create a file item
    file_item = QTreeWidgetItem(parent_item, [file_name, "File"])
    file_item.setData(0, Qt.ItemDataRole.UserRole, file_path)  # Store the original path
    
    # Auto-expand the parent
    parent_item.setExpanded(True)
    
    return file_item

def process_dropped_directory(dir_path, parent_item):
    """Process a directory dropped onto the tree"""
    # Create a folder item for this directory
    dir_name = os.path.basename(os.path.normpath(dir_path))
    
    # Skip .DS_Store and other hidden Mac files
    if dir_name.startswith('.'):
        print(f"DEBUG: Skipping hidden Mac directory in recursive function: {dir_name}")
        return None
            
    # Add the directory to the tree
    folder_item = QTreeWidgetItem(parent_item)
    folder_item.setText(0, dir_name)
    folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
    folder_item.setExpanded(True)
    
    # Add all subdirectories and files
    try:
        for item in sorted(os.listdir(dir_path)):
            # Skip hidden files on Mac
            if item.startswith('.'):
                continue
                
            item_path = os.path.join(dir_path, item)
            if os.path.isdir(item_path):
                # Recursively add subdirectory
                process_dropped_directory(item_path, folder_item)
            else:
                # Add file
                add_file_to_tree(item_path, folder_item)
    except Exception as e:
        print(f"DEBUG: Error processing directory contents in recursive function: {e}")
            
    return folder_item

def add_file_to_tree(file_path, parent_item):
    """Add a file to the tree"""
    file_name = os.path.basename(file_path)
    
    # Skip hidden files on Mac
    if file_name.startswith('.'):
        print(f"DEBUG: Skipping hidden Mac file in recursive function: {file_name}")
        return None
            
    # Create a file item
    file_item = QTreeWidgetItem(parent_item)
    file_item.setText(0, file_name)
    file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
    file_item.setData(0, Qt.ItemDataRole.UserRole, file_path)  # Store the original path
    
    # Auto-expand the parent
    parent_item.setExpanded(True)
    
    return file_item
