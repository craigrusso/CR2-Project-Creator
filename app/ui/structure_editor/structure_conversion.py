#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Structure Conversion Module for the Enhanced Structure Editor
Contains functions for converting between tree widget items and structure data
"""

import os
from PyQt5.QtWidgets import QTreeWidgetItem, QApplication, QStyle
from PyQt5.QtCore import Qt

from .utils import get_file_icon_for_type, _count_structure_items

class StructureConverter:
    """Converts between tree widgets and structure data"""
    
    def __init__(self, editor):
        """
        Initialize the structure converter
        
        Args:
            editor: Reference to the parent editor
        """
        self.editor = editor
        self.tree = getattr(editor, 'tree', None)
    
    def create_structure_from_tree(self):
        """
        Create a structure representation from the current tree
        
        Returns:
            list: Structure data as a list
        """
        # Check if we have a tree
        if not self.tree:
            print("Error: No tree widget available")
            return []
        
        # Get the root item
        root = self.tree.invisibleRootItem()
        
        # Create an empty structure
        structure = []
        
        # Add all top-level items to the structure
        for i in range(root.childCount()):
            item = root.child(i)
            
            # Extract the item type
            item_type = item.data(0, Qt.UserRole + 1)
            
            if item_type == "folder" or not item_type:
                # Handle folder
                folder_name = item.text(0)
                children = []
                
                # Add all children
                self._add_child_items_to_structure(item, children)
                
                # Add the folder to the structure
                structure.append({folder_name: children})
            elif item_type == "file":
                # Handle file
                file_name = item.text(0)
                structure.append(file_name)
        
        return structure
    
    def _add_child_items_to_structure(self, parent_item, structure):
        """
        Add child items to the structure
        
        Args:
            parent_item: Parent tree item
            structure: Structure to add items to
        """
        # Add all children
        for i in range(parent_item.childCount()):
            item = parent_item.child(i)
            
            # Extract the item type
            item_type = item.data(0, Qt.UserRole + 1)
            
            if item_type == "folder" or not item_type:
                # Handle folder
                folder_name = item.text(0)
                children = []
                
                # Add all children
                self._add_child_items_to_structure(item, children)
                
                # Add the folder to the structure
                structure.append({folder_name: children})
            elif item_type == "file":
                # Handle file
                file_name = item.text(0)
                structure.append(file_name)
    
    def extract_structure_from_tree(self):
        """
        Extract a structure from the tree view
        
        Returns:
            list: Extracted structure
        """
        if not self.tree:
            return []
            
        root = self.tree.invisibleRootItem()
        result = []
        
        # Process all top-level items
        for i in range(root.childCount()):
            item = root.child(i)
            result.append(self._extract_item(item))
            
        return result
    
    def _extract_item(self, item):
        """
        Extract an item from the tree view
        
        Args:
            item: Tree item to extract
            
        Returns:
            dict or str: Extracted item
        """
        if item.childCount() > 0:
            # This is a folder
            folder_name = item.text(0)
            children = []
            
            # Extract all children
            for i in range(item.childCount()):
                child = item.child(i)
                children.append(self._extract_item(child))
                
            return {folder_name: children}
        else:
            # This is a file
            file_name = item.text(0)
            return file_name
    
    def load_structure(self, structure):
        """
        Load a structure into the tree
        
        Args:
            structure: Structure to load
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        if not self.tree:
            print("Error: No tree widget available")
            return False
            
        # Clear the tree
        self.tree.clear()
        
        # Check if we have a structure
        if not structure:
            print("Warning: Empty structure provided")
            self.create_new_structure()
            return True
            
        # Create the project root item
        root_name = "Project Root"
        root_item = QTreeWidgetItem(self.tree)
        root_item.setText(0, root_name)
        root_item.setData(0, Qt.UserRole + 1, "folder")  # Mark as folder
        
        # Try to get the root folder
        root_folder = None
        for item in structure:
            if isinstance(item, dict) and root_name in item:
                root_folder = item
                break
                
        # If we found a root folder, use its children
        root_children = []
        if root_folder:
            root_children = root_folder[root_name]
        else:
            # Use the entire structure as children of the root
            root_children = structure
            
        # Add all children to the root item
        for item in root_children:
            self._add_item_to_tree(root_item, item)
            
        # Expand the root item
        root_item.setExpanded(True)
        
        return True
    
    def _add_item_to_tree(self, parent_item, item_data):
        """
        Add an item to the tree
        
        Args:
            parent_item: Parent tree item
            item_data: Item data
            
        Returns:
            QTreeWidgetItem: The newly created item
        """
        # Skip invalid items
        if item_data is None:
            print(f"DEBUG: Skipping None item")
            return None
            
        # Handle different structure formats 
        try:
            if isinstance(item_data, dict):
                # Dictionary with a single key (folder)
                for folder_name, children in item_data.items():
                    # Ensure folder_name is a string
                    if not isinstance(folder_name, str):
                        print(f"WARNING: Folder name is not a string: {folder_name}")
                        folder_name = str(folder_name)
                        
                    # Create folder item
                    folder_item = QTreeWidgetItem(parent_item)
                    folder_item.setText(0, folder_name)
                    folder_item.setData(0, Qt.UserRole + 1, "folder")  # Mark as folder
                    
                    # Set folder icon if available
                    if hasattr(self.editor, 'folder_icon'):
                        folder_item.setIcon(0, self.editor.folder_icon)
                    
                    # Add children only if they exist
                    if children and isinstance(children, list):
                        for child in children:
                            if child is not None:  # Skip None values
                                self._add_item_to_tree(folder_item, child)
                    
                    return folder_item
                    
            elif isinstance(item_data, str):
                # String (file)
                file_name = item_data
                
                # Create file item
                file_item = QTreeWidgetItem(parent_item)
                file_item.setText(0, file_name)
                file_item.setData(0, Qt.UserRole + 1, "file")  # Mark as file
                
                # Set file icon if available
                if hasattr(self.editor, '_get_file_icon_for_type'):
                    file_icon = self.editor._get_file_icon_for_type(file_name)
                    file_item.setIcon(0, file_icon)
                
                return file_item
                
            elif isinstance(item_data, list):
                # For lists passed directly to this method, create a folder
                print(f"WARNING: Received list directly in _add_item_to_tree: {item_data}")
                
                # Create a generic folder
                folder_item = QTreeWidgetItem(parent_item)
                folder_item.setText(0, "Folder")
                folder_item.setData(0, Qt.UserRole + 1, "folder")  # Mark as folder
                
                # Add all items in the list
                for child in item_data:
                    if child is not None:  # Skip None values
                        self._add_item_to_tree(folder_item, child)
                
                return folder_item
                
            else:
                print(f"WARNING: Unknown item type: {type(item_data)}")
                
                # Try to convert to string
                try:
                    item_str = str(item_data)
                    file_item = QTreeWidgetItem(parent_item)
                    file_item.setText(0, item_str)
                    file_item.setData(0, Qt.UserRole + 1, "file")  # Mark as file
                    return file_item
                except:
                    print(f"ERROR: Could not convert {item_data} to string")
                    return None
                    
        except Exception as e:
            print(f"ERROR in _add_item_to_tree: {e}")
            print(f"Item data: {item_data}")
            return None
            
        return None
    
    def create_new_structure(self):
        """
        Create a new blank structure
        
        Returns:
            bool: True if created successfully, False otherwise
        """
        if not self.tree:
            print("Error: No tree widget available")
            return False
            
        # Clear the tree
        self.tree.clear()
        
        # Create the project root item
        root_item = QTreeWidgetItem(self.tree)
        root_item.setText(0, "Project Root")
        root_item.setData(0, Qt.UserRole + 1, "folder")  # Mark as folder
        
        # Add default folders
        default_folders = ["Footage", "Audio", "Graphics", "Exports"]
        
        for folder_name in default_folders:
            folder_item = QTreeWidgetItem(root_item)
            folder_item.setText(0, folder_name)
            folder_item.setData(0, Qt.UserRole + 1, "folder")  # Mark as folder
            
            # Set folder icon if available
            if hasattr(self.editor, 'folder_icon'):
                folder_item.setIcon(0, self.editor.folder_icon)
        
        # Expand the root item
        root_item.setExpanded(True)
        
        return True 