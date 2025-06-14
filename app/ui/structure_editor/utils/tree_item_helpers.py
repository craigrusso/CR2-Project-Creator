#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Tree Item Helpers

Utility functions for working with QTreeWidgetItem objects in the structure editor.
Extracted from the monolithic file_operations.py for better organization.
"""

from PyQt6.QtWidgets import QTreeWidgetItem
from PyQt6.QtCore import Qt
from .file_type_detector import FileTypeDetector


class TreeItemHelpers:
    """Utility functions for tree widget item operations"""
    
    @staticmethod
    def create_file_item(parent_item, file_name, file_type=None, original_path=None):
        """Create a new file tree item with proper data"""
        # Create the tree item
        if parent_item:
            file_item = QTreeWidgetItem(parent_item)
        else:
            # This would need the tree widget passed in, but for now we'll handle it in the caller
            raise ValueError("Parent item required for file creation")

        file_item.setText(0, file_name)
        
        # Set item data
        item_data = {
            'name': file_name,
            'type': 'file',
            'file_type': file_type or FileTypeDetector.get_file_type_from_extension(file_name)
        }
        
        if original_path:
            item_data['original_path'] = original_path
            # Binary detection would be handled by BinaryFileHandler
        
        file_item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Expand parent if needed
        if parent_item:
            parent_item.setExpanded(True)
        
        return file_item
    
    @staticmethod
    def create_folder_item(parent_item, folder_name):
        """Create a new folder tree item with proper data"""
        # Create the tree item
        if parent_item:
            folder_item = QTreeWidgetItem(parent_item)
        else:
            # This would need the tree widget passed in, but for now we'll handle it in the caller
            raise ValueError("Parent item required for folder creation")

        folder_item.setText(0, folder_name)
        
        # Set item data
        item_data = {
            'name': folder_name,
            'type': 'folder'
        }
        
        folder_item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Expand parent if needed
        if parent_item:
            parent_item.setExpanded(True)
        
        return folder_item
    
    @staticmethod
    def get_item_data(item):
        """Safely get item data from a tree widget item"""
        if not item:
            return {}
        
        try:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            return data if isinstance(data, dict) else {}
        except:
            return {}
    
    @staticmethod
    def set_item_data(item, data):
        """Safely set item data on a tree widget item"""
        if not item or not isinstance(data, dict):
            return False
        
        try:
            item.setData(0, Qt.ItemDataRole.UserRole, data)
            return True
        except:
            return False
    
    @staticmethod
    def is_folder_item(item):
        """Check if an item represents a folder"""
        data = TreeItemHelpers.get_item_data(item)
        return data.get('type') == 'folder' or item.childCount() > 0
    
    @staticmethod
    def is_file_item(item):
        """Check if an item represents a file"""
        data = TreeItemHelpers.get_item_data(item)
        return data.get('type') == 'file'
    
    @staticmethod
    def get_item_path(item):
        """Get the full path of an item within the tree structure"""
        if not item:
            return ""
        
        path_parts = []
        current = item
        
        while current:
            path_parts.insert(0, current.text(0))
            current = current.parent()
        
        return "/".join(path_parts)
    
    @staticmethod
    def find_item_by_name(tree_widget, name, item_type=None):
        """Find an item in the tree by name and optionally by type"""
        if not tree_widget:
            return None
        
        def search_recursive(parent):
            for i in range(parent.childCount()):
                child = parent.child(i)
                if child.text(0) == name:
                    if item_type is None:
                        return child
                    
                    data = TreeItemHelpers.get_item_data(child)
                    if data.get('type') == item_type:
                        return child
                
                # Search in children
                result = search_recursive(child)
                if result:
                    return result
            return None
        
        # Search from root
        for i in range(tree_widget.topLevelItemCount()):
            root_item = tree_widget.topLevelItem(i)
            if root_item.text(0) == name:
                if item_type is None:
                    return root_item
                
                data = TreeItemHelpers.get_item_data(root_item)
                if data.get('type') == item_type:
                    return root_item
            
            # Search in children
            result = search_recursive(root_item)
            if result:
                return result
        
        return None 