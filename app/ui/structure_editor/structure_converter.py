#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Structure Converter Module

This module provides functions for converting between tree widgets and structure representations.
"""

import os
import json
from pathlib import Path
from PyQt5.QtWidgets import QTreeWidgetItem, QApplication, QStyle
from PyQt5.QtCore import Qt

# Import StructureUtils
try:
    from app.utils.structure_utils import StructureUtils
except ImportError:
    # Fallback if not available
    class StructureUtils:
        @staticmethod
        def normalize_structure(structure):
            return structure
            
        @staticmethod
        def normalize_item(item):
            return item

# Import BinaryFileHandler
try:
    from app.utils.binary_file_handler import BinaryFileHandler
except ImportError:
    # Fallback if not available
    class BinaryFileHandler:
        @staticmethod
        def is_binary_file(file_path):
            return False
            
        @staticmethod
        def encode_binary_file(file_path):
            return None
            
        @staticmethod
        def should_embed_binary_file(file_path, max_size_kb=500):
            return False

class StructureConverter:
    """Handles conversion between tree widget and structure data formats"""
    
    def __init__(self, tree_widget=None, editor=None):
        """
        Initialize the structure converter
        
        Args:
            tree_widget: The QTreeWidget to use
            editor: The parent editor instance
        """
        self.editor = editor
        
        # Initialize the tree widget reference
        self.tree_widget = tree_widget
        
        # If no tree_widget provided but editor has one, try to get it
        if not self.tree_widget and editor:
            if hasattr(editor, 'tree_widget'):
                self.tree_widget = editor.tree_widget
                print("DEBUG: StructureConverter using tree_widget from editor")
            elif hasattr(editor, 'tree'):
                self.tree_widget = editor.tree
                print("DEBUG: StructureConverter using tree from editor")
                
        if self.tree_widget:
            print("DEBUG: StructureConverter initialized with tree widget")
        else:
            print("WARNING: StructureConverter initialized without tree widget")
    
    def create_empty_structure(self):
        """
        Create an empty structure in the tree widget
        
        Returns:
            list: Empty structure list
        """
        # Make sure we have a tree widget
        if not self.tree_widget:
            if self.editor and hasattr(self.editor, 'tree'):
                self.tree_widget = self.editor.tree
                print("DEBUG: StructureConverter retrieved tree from editor for empty structure")
            else:
                print("ERROR: No tree widget available for creating empty structure")
                return []
        
        # Clear the tree
        self.tree_widget.clear()
        
        print("DEBUG: Created empty structure")
        return []
    
    def create_structure_from_tree(self):
        """
        Create a structure from the tree widget
        
        Returns:
            list: The structure data
        """
        if not self.tree_widget:
            print("DEBUG: No tree widget available")
            return []
            
        structure = []
        root = self.tree_widget.invisibleRootItem()
        
        # Process all top-level items
        for i in range(root.childCount()):
            item = root.child(i)
            self._add_item_to_structure(item, structure)
            
        print(f"DEBUG: Generated structure with {len(structure)} items")
        
        # Normalize the structure using StructureUtils
        normalized_structure = StructureUtils.normalize_structure(structure)
        
        return normalized_structure
    
    def _add_item_to_structure(self, item, parent_list):
        """
        Add an item to the structure
        
        Args:
            item: Tree widget item
            parent_list: Parent list to add the item to
            
        Returns:
            dict: Item structure or None if it should be skipped
        """
        # Skip None items
        if item is None:
            print(f"DEBUG: Skipping None item")
            return None
        
        # Get item data and type
        item_data = item.data(0, Qt.UserRole) or {}
        item_type = item_data.get('type', None)
        
        # If type is not specified in data, infer it from child count
        if not item_type:
            item_type = 'folder' if item.childCount() > 0 else 'file'
        
        if item_type == 'folder':
            # Handle folder
            folder_name = item_data.get('name', item.text(0))
            
            # Skip folders with empty names, arrays or placeholder names
            if not folder_name or folder_name == '[]' or folder_name == 'name' or folder_name == '':
                print(f"DEBUG: Skipping folder with empty/invalid name: {folder_name}")
                return None
            
            # Convert folder_name to string if it's a list
            if isinstance(folder_name, list):
                # Only use first item if it exists and is not empty
                if len(folder_name) > 0 and folder_name[0]:
                    folder_name = str(folder_name[0])
                else:
                    print(f"DEBUG: Skipping folder with empty name array: {folder_name}")
                    return None
            
            # Ensure folder_name is a string
            folder_name = str(folder_name)
            
            # Create folder structure
            folder_structure = {
                'name': folder_name,
                'type': 'folder'
            }
            
            # Add path if available
            if 'path' in item_data:
                folder_structure['path'] = item_data.get('path')
            
            # Process children
            children = []
            for i in range(item.childCount()):
                child_item = item.child(i)
                child_structure = self._add_item_to_structure(child_item, children)
                if child_structure:
                    children.append(child_structure)
            
            # Add children list if there are any
            if children:
                folder_structure['children'] = children
            
            # Don't add empty folders unless specifically allowed
            if not children and not self.keep_empty_folders:
                print(f"DEBUG: Skipping empty folder: {folder_name}")
                return None
            
            # Add to parent list
            return folder_structure
            
        elif item_type == 'file':
            # Add a file
            file_name = item_data.get('name', item.text(0))
            file_path = item_data.get('path', '')
            is_binary = item_data.get('is_binary', False)
            original_path = item_data.get('original_path', '')
            cached_path = item_data.get('cached_path', '')
            
            # Skip items with empty name arrays or values or name placeholders
            if not file_name or file_name == [] or file_name == 'name' or file_name == '' or (isinstance(file_name, list) and len(file_name) == 0):
                print(f"DEBUG: Skipping file with empty/invalid name: {item_data}")
                return None
            
            # Ensure file_name is a string, not a list or other data type
            if isinstance(file_name, list):
                if len(file_name) > 0 and file_name[0]:
                    file_name = str(file_name[0])
                else:
                    print(f"DEBUG: Skipping file with empty name array: {item_data}")
                    return None
            
            # Convert file_name to string if it's not already
            file_name = str(file_name)
            
            # Clean up file_name - remove [] if present
            if file_name == '[]':
                print(f"DEBUG: Skipping file with empty name: {item_data}")
                return None
            
            # Ensure is_binary is a boolean
            if isinstance(is_binary, list):
                is_binary = bool(is_binary[0]) if is_binary else False
            elif not isinstance(is_binary, bool):
                is_binary = bool(is_binary)
            
            # Create file structure
            file_structure = {
                'name': file_name,
                'type': 'file',
                'is_binary': is_binary
            }
            
            # Add paths if available - ensure they are strings
            if original_path:
                file_structure['original_path'] = str(original_path) if not isinstance(original_path, list) else (str(original_path[0]) if original_path else '')
            
            if file_path and file_path != original_path:
                file_structure['path'] = str(file_path) if not isinstance(file_path, list) else (str(file_path[0]) if file_path else '')
            
            if cached_path:
                file_structure['cached_path'] = str(cached_path) if not isinstance(cached_path, list) else (str(cached_path[0]) if cached_path else '')
            
            # Add file content if available
            if 'content' in item_data:
                content = item_data.get('content')
                if content is not None:
                    file_structure['content'] = str(content) if not isinstance(content, list) else (str(content[0]) if content else '')
            
            # Add binary data if available
            if 'data' in item_data:
                data = item_data.get('data')
                if data:
                    file_structure['data'] = data
            
            # Add cached hash if available
            if 'cache_hash' in item_data:
                cache_hash = item_data.get('cache_hash')
                if cache_hash:
                    file_structure['cache_hash'] = str(cache_hash) if not isinstance(cache_hash, list) else (str(cache_hash[0]) if cache_hash else '')
            
            # Skip items that have empty values or [] as their value for any field
            for key, val in list(file_structure.items()):
                if val == [] or val == '[]' or (isinstance(val, list) and len(val) == 0):
                    print(f"DEBUG: Removing empty array for key {key} in file structure")
                    file_structure.pop(key)
            
            return file_structure
        
        # Unknown item type
        print(f"DEBUG: Skipping unknown item type: {item_type}")
        return None
    
    def load_structure(self, structure):
        """
        Load a structure into the tree widget
        
        Args:
            structure: The structure data to load
        """
        # Make sure we have a tree widget
        if not self.tree_widget:
            if self.editor and hasattr(self.editor, 'tree'):
                self.tree_widget = self.editor.tree
                print("DEBUG: StructureConverter retrieved tree from editor")
            else:
                print("ERROR: No tree widget available for StructureConverter")
                return
        
        # Clear the tree
        self.tree_widget.clear()
        
        # If we have no structure data, return
        if not structure:
            print("DEBUG: No structure data to load")
            return
        
        print(f"DEBUG: Loading structure of type {type(structure)} with content: {structure[:5] if isinstance(structure, list) else 'non-list'}")
        
        # Normalize the structure format
        normalized_structure = self._normalize_structure_format(structure)
        
        print(f"DEBUG: Normalized structure: {normalized_structure[:5] if normalized_structure else 'empty'}")
        
        # Process each item in the structure
        for item in normalized_structure:
            self._add_structure_item_to_tree(item, None)
            print(f"DEBUG: Added item to tree: {item}")
        
        # Expand all items
        self.tree_widget.expandAll()
        
        # Apply icons to all items if possible
        self._apply_icons_to_tree()
        
        # Verify structure was loaded by checking tree items
        root = self.tree_widget.invisibleRootItem()
        print(f"DEBUG: After loading, tree has {root.childCount()} top-level items")
        
        return True
    
    def _apply_icons_to_tree(self):
        """Apply proper icons to all items in the tree"""
        # Get default icons
        from .utils import get_file_icon_for_type
        
        # Get the tree root
        root = self.tree_widget.invisibleRootItem()
        
        # Process all items
        for i in range(root.childCount()):
            item = root.child(i)
            self._apply_icon_to_item(item)
    
    def _apply_icon_to_item(self, item):
        """Apply proper icon to an item and its children recursively"""
        if not item:
            return
            
        # Get item data
        item_data = item.data(0, Qt.UserRole)
        
        # If no data available, infer from text and children
        if not item_data:
            if item.childCount() > 0:
                # Assume it's a folder if it has children
                item_data = {'type': 'folder', 'name': item.text(0)}
            else:
                # Assume it's a file otherwise
                item_data = {'type': 'file', 'name': item.text(0)}
            item.setData(0, Qt.UserRole, item_data)
        
        # Apply icon based on type
        if isinstance(item_data, dict) and 'type' in item_data:
            if item_data['type'] == 'folder':
                # Use standard folder icon
                from PyQt5.QtGui import QIcon
                item.setIcon(0, QIcon.fromTheme("folder"))
            else:
                # Use file type icon
                from .utils import get_file_icon_for_type
                item.setIcon(0, get_file_icon_for_type(item_data.get('name', '')))
        
        # Process children recursively
        for i in range(item.childCount()):
            self._apply_icon_to_item(item.child(i))
        
    def _add_structure_item_to_tree(self, item, parent_item):
        """
        Add a structure item to the tree
        
        Args:
            item: Structure item (can be a string or dict)
            parent_item: Parent tree widget item
        """
        # Filter out hidden files and .DS_Store
        if isinstance(item, str):
            # Skip hidden files and macOS special files
            if item.startswith('.') or item == '.DS_Store':
                return None
                
        # Debug visibility of tree widget
        if not self.tree_widget:
            print("ERROR: _add_structure_item_to_tree called with no tree_widget")
            return None
        
        result_item = None
        
        # Handle different item types
        if isinstance(item, dict):
            # Check for the type-name-children format first (newer format)
            if 'type' in item and 'name' in item:
                # This is the newer format with explicit type and name
                if item['type'] == 'folder':
                    # Create folder item
                    folder_name = item['name']
                    # Handle case where folder_name is a list
                    if isinstance(folder_name, list):
                        folder_name = str(folder_name)
                    
                    # Create new tree item with proper parent
                    if parent_item is None:
                        tree_item = QTreeWidgetItem(self.tree_widget)
                        print(f"DEBUG: Added folder '{folder_name}' as top-level item")
                    else:
                        tree_item = QTreeWidgetItem(parent_item)
                        print(f"DEBUG: Added folder '{folder_name}' as child of '{parent_item.text(0)}'")
                    
                    tree_item.setText(0, folder_name)
                    
                    # Set user data
                    folder_data = {'type': 'folder', 'name': folder_name}
                    tree_item.setData(0, Qt.UserRole, folder_data)
                    
                    # Set folder icon
                    from PyQt5.QtGui import QIcon
                    tree_item.setIcon(0, QIcon.fromTheme("folder"))
                    
                    # Add children if they exist
                    if 'children' in item and isinstance(item['children'], list):
                        for child in item['children']:
                            self._add_structure_item_to_tree(child, tree_item)
                    
                    result_item = tree_item
                else:
                    # It's a file
                    file_name = item['name']
                    # Handle case where file_name is a list
                    if isinstance(file_name, list):
                        file_name = str(file_name)
                    
                    # Create new tree item with proper parent
                    if parent_item is None:
                        tree_item = QTreeWidgetItem(self.tree_widget)
                        print(f"DEBUG: Added file '{file_name}' as top-level item")
                    else:
                        tree_item = QTreeWidgetItem(parent_item)
                        print(f"DEBUG: Added file '{file_name}' as child of '{parent_item.text(0)}'")
                    
                    tree_item.setText(0, file_name)
                    
                    # Set user data
                    file_data = {'type': 'file', 'name': file_name}
                    tree_item.setData(0, Qt.UserRole, file_data)
                    
                    # Set file icon
                    from .utils import get_file_icon_for_type
                    tree_item.setIcon(0, get_file_icon_for_type(file_name))
                    
                    result_item = tree_item
                
                return result_item
                
            # Check for the {folder_name: children} format (older format)
            if len(item) == 1:
                # It's a folder
                for folder_name, children in item.items():
                    # Skip if folder name is empty or hidden
                    if not folder_name or folder_name.startswith('.') or folder_name == '.DS_Store':
                        continue
                        
                    # Handle case where folder_name is a list
                    if isinstance(folder_name, list):
                        folder_name = str(folder_name)
                        
                    # Create tree item with proper parent
                    if parent_item is None:
                        tree_item = QTreeWidgetItem(self.tree_widget)
                        print(f"DEBUG: Added folder '{folder_name}' as top-level item (old format)")
                    else:
                        tree_item = QTreeWidgetItem(parent_item)
                        print(f"DEBUG: Added folder '{folder_name}' as child of '{parent_item.text(0)}' (old format)")
                    
                    tree_item.setText(0, folder_name)
                    
                    # Set user data
                    folder_data = {'type': 'folder', 'name': folder_name}
                    tree_item.setData(0, Qt.UserRole, folder_data)
                    
                    # Set folder icon
                    from PyQt5.QtGui import QIcon
                    tree_item.setIcon(0, QIcon.fromTheme("folder"))
                    
                    # Filter and add children
                    if isinstance(children, list):
                        # Filter out hidden items
                        filtered_children = [
                            child for child in children 
                            if not (isinstance(child, str) and (child.startswith('.') or child == '.DS_Store'))
                        ]
                        
                        # Add children
                        for child in filtered_children:
                            self._add_structure_item_to_tree(child, tree_item)
                    
                    result_item = tree_item
            else:
                # It's some other kind of dictionary - create a folder for each key
                for key, value in item.items():
                    # Skip hidden keys
                    if key.startswith('.') or key == '.DS_Store':
                        continue
                    
                    # Handle case where key is a list
                    if isinstance(key, list):
                        key = str(key)
                        
                    # Create a folder with proper parent
                    if parent_item is None:
                        folder_item = QTreeWidgetItem(self.tree_widget)
                        print(f"DEBUG: Added folder '{key}' as top-level item (dict format)")
                    else:
                        folder_item = QTreeWidgetItem(parent_item)
                        print(f"DEBUG: Added folder '{key}' as child of '{parent_item.text(0)}' (dict format)")
                    
                    folder_item.setText(0, key)
                    
                    # Set user data
                    folder_data = {'type': 'folder', 'name': key}
                    folder_item.setData(0, Qt.UserRole, folder_data)
                    
                    # Set folder icon
                    from PyQt5.QtGui import QIcon
                    folder_item.setIcon(0, QIcon.fromTheme("folder"))
                    
                    # Add children
                    if isinstance(value, list):
                        for child in value:
                            self._add_structure_item_to_tree(child, folder_item)
                    elif isinstance(value, dict):
                        self._add_structure_item_to_tree(value, folder_item)
                    
                    result_item = folder_item
        else:
            # It's a file - skip if hidden
            file_name = str(item)
            if file_name.startswith('.') or file_name == '.DS_Store':
                return None
                
            # Create tree item with proper parent
            if parent_item is None:
                tree_item = QTreeWidgetItem(self.tree_widget)
                print(f"DEBUG: Added file '{file_name}' as top-level item (string format)")
            else:
                tree_item = QTreeWidgetItem(parent_item)
                print(f"DEBUG: Added file '{file_name}' as child of '{parent_item.text(0)}' (string format)")
            
            tree_item.setText(0, file_name)
            
            # Set user data
            file_data = {'type': 'file', 'name': file_name}
            tree_item.setData(0, Qt.UserRole, file_data)
            
            # Set file icon using utility function
            from .utils import get_file_icon_for_type
            tree_item.setIcon(0, get_file_icon_for_type(file_name))
            
            result_item = tree_item
            
        return result_item

    def _add_structure_item(self, item_data, parent_item):
        """
        Add an item from structure data to the tree
        
        Args:
            item_data: Item data (can be string, dict, or special format)
            parent_item: Parent tree item (or None for root)
            
        Returns:
            QTreeWidgetItem: The created tree item
        """
        # Handle different item formats
        if isinstance(item_data, str):
            # Simple string item (file)
            return self._add_file_item(item_data, parent_item)
        elif isinstance(item_data, dict):
            # Dictionary item (folder with children or file with attributes)
            
            # First check if it's the special format {"type": "...", "name": "...", "children": [...]}
            if "type" in item_data and "name" in item_data:
                if item_data.get("type") == "folder":
                    # Create folder item
                    folder_item = self._create_folder_item(item_data["name"], parent_item)
                    
                    # Process children if they exist
                    if "children" in item_data and isinstance(item_data["children"], list):
                        for child in item_data["children"]:
                            self._add_structure_item(child, folder_item)
                    
                    return folder_item
                else:
                    # Create file item
                    return self._add_file_item(item_data["name"], parent_item)
            
            # Check for {"folder_name": [children]} format
            elif len(item_data) == 1:
                folder_name = list(item_data.keys())[0]
                children = list(item_data.values())[0]
                
                # Create folder item
                folder_item = self._create_folder_item(folder_name, parent_item)
                
                # Process children if they exist
                if isinstance(children, list):
                    for child in children:
                        self._add_structure_item(child, folder_item)
                
                return folder_item
            else:
                # Unexpected format, create a file with the data as JSON
                import json
                return self._add_file_item(f"data_{len(item_data)}.json", parent_item)
        else:
            # Unexpected type, create generic item
            return self._add_file_item(f"item_{type(item_data).__name__}", parent_item)

    def _create_folder_item(self, folder_name, parent_item):
        """
        Create a folder item in the tree
        
        Args:
            folder_name: Name of the folder
            parent_item: Parent tree item (or None for root)
            
        Returns:
            QTreeWidgetItem: The created folder item
        """
        # If we have file_operations, use it if available
        if self.editor and hasattr(self.editor, 'file_operations') and hasattr(self.editor.file_operations, 'add_folder'):
            if folder_name:
                # This will show a dialog, so only use if folder_name is not provided
                # and we want to prompt the user
                return self.editor.file_operations.add_folder(parent_item)
        
        # Create the folder item
        if parent_item:
            folder_item = QTreeWidgetItem(parent_item)
        else:
            folder_item = QTreeWidgetItem(self.tree_widget)
        
        # Set folder name and mark as folder
        folder_item.setText(0, folder_name)
        folder_item.setData(0, Qt.UserRole, {"type": "folder"})
        
        # Set folder icon
        try:
            # First try using QApplication standard icons (most reliable)
            folder_icon = QApplication.style().standardIcon(QStyle.SP_DirIcon)
            folder_item.setIcon(0, folder_icon)
            
            # Use bold text for folders
            font = folder_item.font(0)
            font.setBold(True)
            folder_item.setFont(0, font)
            
            # Make folder editable
            folder_item.setFlags(folder_item.flags() | Qt.ItemIsEditable)
            
        except Exception as e:
            print(f"ERROR setting folder icon: {e}")
        
        # Return the folder item
        return folder_item

    def _add_file_item(self, file_name, parent_item):
        """
        Add a file item to the tree
        
        Args:
            file_name: Name of the file
            parent_item: Parent tree item (or None for root)
            
        Returns:
            QTreeWidgetItem: The created file item
        """
        # If we have file_operations, use it
        if self.editor and hasattr(self.editor, 'file_operations') and hasattr(self.editor.file_operations, 'add_file'):
            return self.editor.file_operations.add_file(parent_item, file_name)
        
        # Create tree item
        if parent_item:
            file_item = QTreeWidgetItem(parent_item)
        else:
            file_item = QTreeWidgetItem(self.tree_widget)
        
        # Set file properties
        file_item.setText(0, file_name)
        file_item.setData(0, Qt.UserRole, {"type": "file"})
        
        # Set file icon
        try:
            # Get file icon from utils or use standard icon
            from .utils import get_file_icon_for_type
            file_icon = get_file_icon_for_type(file_name)
            
            # If no icon was found, use standard file icon
            if file_icon.isNull():
                file_icon = QApplication.style().standardIcon(QStyle.SP_FileIcon)
                
            file_item.setIcon(0, file_icon)
        except Exception as e:
            print(f"ERROR setting file icon: {e}")
            
            # Fallback to standard file icon
            try:
                file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
            except:
                pass  # Skip icon if even this fails
        
        # Set item to be editable
        file_item.setFlags(file_item.flags() | Qt.ItemIsEditable)
        
        # Return the file item
        return file_item

    def load_template(self, template_name):
        """
        Load a template structure by name
        
        Args:
            template_name: Name of the template
            
        Returns:
            list: The structure data
        """
        if not template_name:
            return None
            
        # First check if we have a parent with template_manager
        template_manager = None
        tree_parent = self.tree_widget.parent()
        while tree_parent and not template_manager:
            if hasattr(tree_parent, 'template_manager'):
                template_manager = tree_parent.template_manager
            tree_parent = tree_parent.parent()
            
        if not template_manager:
            # Try to get main window template manager
            from PyQt5.QtWidgets import QApplication
            main_window = QApplication.activeWindow()
            if hasattr(main_window, 'template_manager'):
                template_manager = main_window.template_manager
            
        if template_manager:
            # Try to get the structure
            structure = template_manager.get_structure(template_name)
            return structure
        
        # No template manager or structure not found
        return None

    def accept(self):
        """Handle dialog acceptance"""
        # Nothing special to do here
        pass

    def get_structure(self):
        """
        Get the current structure from the tree widget
        
        Returns:
            list: The structure as a list of dictionaries
        """
        try:
            if not self.tree_widget:
                print("ERROR: No tree widget available")
                return []
            
            structure = []
            # Get the root item
            root = self.tree_widget.invisibleRootItem()
            
            # Debug top-level items
            print(f"DEBUG: get_structure - tree has {root.childCount()} top-level items")
            for i in range(root.childCount()):
                item_text = root.child(i).text(0)
                print(f"DEBUG: Top-level item {i}: {item_text}")
            
            # Process each top-level item
            for i in range(root.childCount()):
                item = root.child(i)
                item_data = self._process_item(item)
                if item_data:
                    structure.append(item_data)
            
            print(f"DEBUG: Generated structure with {len(structure)} items")
            return structure
        except Exception as e:
            print(f"ERROR generating structure: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _process_item(self, item):
        """
        Process a single tree widget item into a structure item
        
        Args:
            item: The tree widget item to process
            
        Returns:
            dict or None: Processed structure item or None if invalid
        """
        if not item:
            return None
            
        # Get basic info
        name = item.text(0)
        if not name:
            print("WARNING: Empty name in structure item")
            return None
            
        # Get item data if available
        item_user_data = item.data(0, Qt.UserRole)
        
        # Determine if it's a folder
        is_folder = False
        if isinstance(item_user_data, dict) and 'type' in item_user_data:
            is_folder = item_user_data.get('type') == 'folder'
        else:
            # Try to guess by checking for children
            is_folder = item.childCount() > 0
            
        # If this is a folder, process all children
        if is_folder:
            # Create a folder object
            folder_item = {
                'name': name,
                'type': 'folder'
            }
            
            # Process children
            children = []
            for i in range(item.childCount()):
                child_item = item.child(i)
                child_data = self._process_item(child_item)
                if child_data:
                    children.append(child_data)
                    
            # Add children to folder
            if children:
                folder_item['children'] = children
                
            return folder_item
        else:
            # This is a file
            # Check for project name placeholder flag or rename flag
            if isinstance(item_user_data, dict):
                rename_flag = item_user_data.get('rename_flag', False)
                uses_project_name = item_user_data.get('uses_project_name', False)
                
                if rename_flag or uses_project_name:
                    # Get the original filename - use this as the actual name field
                    original_name = item_user_data.get('original_name', name)
                    
                    # Create file item with both flags set for compatibility
                    # IMPORTANT: 'name' field stores the original filename, not the placeholder
                    file_item = {
                        'name': original_name,  # Store original filename
                        'type': 'file',
                        'rename_flag': True,  # Always set rename_flag to true
                        'uses_project_name': True  # Keep uses_project_name for backward compatibility
                    }
                    
                    # Include any other useful file metadata from the item_user_data
                    for key in ['path', 'original_path', 'is_binary', 'cached_path', 'original_name', 'original_extension']:
                        if key in item_user_data:
                            file_item[key] = item_user_data[key]
                    
                    # Ensure original_path is set if path is available but original_path isn't
                    if 'path' in item_user_data and item_user_data['path'] and 'original_path' not in file_item:
                        file_item['original_path'] = item_user_data['path']
                    
                    return file_item
            
            # Regular file without placeholder
            file_item = {
                'name': name,
                'type': 'file'
            }
            
            # Include any other useful file metadata from the item_user_data
            if isinstance(item_user_data, dict):
                for key in ['path', 'original_path', 'is_binary', 'cached_path', 'rename_flag', 'uses_project_name', 
                           'original_name', 'original_extension']:
                    if key in item_user_data:
                        file_item[key] = item_user_data[key]
                        
                # Ensure original_path is set if path is available but original_path isn't
                if 'path' in item_user_data and item_user_data['path'] and 'original_path' not in file_item:
                    file_item['original_path'] = item_user_data['path']
            
            # If we have the original_path, add it directly to the structure
            if 'original_path' in file_item and file_item['original_path']:
                print(f"DEBUG: File {name} has original_path: {file_item['original_path']}")
            
            return file_item

    def _normalize_structure_format(self, structure):
        """
        Normalize the structure format to a consistent format for the tree widget
        
        Args:
            structure: The structure data to normalize
            
        Returns:
            list: Normalized structure list
        """
        print(f"DEBUG: Normalizing structure format: {type(structure)}")
        
        if not structure:
            print("DEBUG: Empty structure, returning empty list")
            return []
            
        # If structure is already a list, assume it's in the right format
        if isinstance(structure, list):
            # Check if it has the expected format
            for item in structure:
                if isinstance(item, dict) and ('name' in item or 'type' in item):
                    # Format appears to be the newer style with name/type keys
                    # We want to preserve this format, not convert it to tree format
                    print(f"DEBUG: Structure appears to be in newer format with {len(structure)} items")
                    return structure
            
            # If we get here, it's either empty or in the old format
            # For old format, we'll convert to the new format
            print(f"DEBUG: Converting old format structure with {len(structure)} items to new format")
            result = []
            for item in structure:
                if isinstance(item, dict) and len(item) == 1:
                    # This is a folder in old format {folder_name: children}
                    folder_name = list(item.keys())[0]
                    children = list(item.values())[0]
                    
                    folder_item = {
                        'name': folder_name,
                        'type': 'folder'
                    }
                    
                    if children and isinstance(children, list):
                        # Recursively normalize children
                        folder_item['children'] = self._normalize_structure_format(children)
                    
                    result.append(folder_item)
                elif isinstance(item, str):
                    # This is a file
                    result.append({
                        'name': item,
                        'type': 'file'
                    })
                else:
                    # Unknown format, preserve as is
                    result.append(item)
            
            print(f"DEBUG: Normalized structure has {len(result)} items")
            return result
        
        # Handle dictionary format (could be nested)
        if isinstance(structure, dict):
            if 'directories' in structure:
                # This is the full structure format
                return self._normalize_structure_format(structure['directories'])
                
            # Check if this is already in the new format
            if 'name' in structure and 'type' in structure:
                # This is a single item in the new format
                return [structure]
                
            # Convert the dict to a list format
            result = []
            for key, value in structure.items():
                if isinstance(value, dict) or isinstance(value, list):
                    # This is a folder with children
                    folder_item = {
                        'name': key,
                        'type': 'folder',
                        'children': self._normalize_structure_format(value)
                    }
                    result.append(folder_item)
                else:
                    # This is a file
                    result.append({
                        'name': key,
                        'type': 'file'
                    })
            return result
        
        # Fallback - return an empty list
        print("WARNING: Unrecognized structure format, returning empty list")
        return []
        
    def _convert_to_tree_format(self, structure):
        """
        Convert structure with name/type keys to tree format
        
        Args:
            structure: Structure data with name/type format
            
        Returns:
            list: Converted structure in tree format
        """
        # This method is largely deprecated in favor of using the newer format directly
        # We keep it for backward compatibility when needed
        print("DEBUG: Converting structure using _convert_to_tree_format (deprecated)")
        
        if not structure:
            return []
            
        result = []
        
        for item in structure:
            if not isinstance(item, dict):
                # If it's a string, treat as a file
                if isinstance(item, str):
                    result.append(item)
                continue
                
            name = item.get('name', '')
            item_type = item.get('type', 'file')
            
            # Handle case where name is a list
            if isinstance(name, list):
                name = str(name)
            
            if item_type == 'folder' or item_type == 'directory':
                # This is a folder
                children = item.get('children', [])
                
                # If there are no children, create an empty folder
                if not children:
                    result.append({name: []})
                    continue
                    
                # Convert children recursively
                converted_children = self._convert_to_tree_format(children) if children else []
                
                # Add as dictionary with folder name as key and children as value
                folder_entry = {name: converted_children}
                result.append(folder_entry)
            else:
                # This is a file
                result.append(name)
                
        return result 

    def verify_structure(self):
        """
        Diagnostic method to verify the current structure in the tree widget
        
        Returns:
            dict: Information about the current structure
        """
        if not self.tree_widget:
            return {"error": "No tree widget available"}
            
        root = self.tree_widget.invisibleRootItem()
        top_level_count = root.childCount()
        
        items_info = []
        for i in range(top_level_count):
            item = root.child(i)
            item_info = {
                "name": item.text(0),
                "has_children": item.childCount() > 0,
                "child_count": item.childCount(),
                "user_data": str(item.data(0, Qt.UserRole))
            }
            items_info.append(item_info)
            
        result = {
            "top_level_count": top_level_count,
            "items": items_info
        }
        
        print(f"DEBUG: Structure verification: {result}")
        return result 

    def tree_to_structure(self):
        """
        Convert the tree to a structure format
        
        Returns:
            dict: Structure dictionary
        """
        if not self.tree_widget:
            print("ERROR: tree_to_structure called with no tree_widget available")
            return {}
            
        # Create empty structure
        structure = {}
        
        # Process top-level items
        root = self.tree_widget.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            self._add_item_to_structure(structure, item)
            
        return structure
        
    def _add_item_to_structure(self, structure, item):
        """
        Add an item to the structure
        
        Args:
            structure: Structure dictionary to add to
            item: Tree item to add
        """
        # Get item data
        item_data = item.data(0, Qt.UserRole)
        
        # If no data, infer from text
        if not item_data:
            if item.childCount() > 0:
                item_data = {'type': 'folder', 'name': item.text(0)}
            else:
                item_data = {'type': 'file', 'name': item.text(0)}
                
        # Create normalized format
        if isinstance(item_data, dict):
            item_type = item_data.get('type', 'file' if item.childCount() == 0 else 'folder')
            item_name = item_data.get('name', item.text(0))
            
            normalized_item = {
                'type': item_type,
                'name': item_name
            }
            
            # Add path information for files
            if item_type == 'file':
                # Add original path if available
                if 'original_path' in item_data:
                    normalized_item['original_path'] = item_data['original_path']
                
                # Add cache path if available
                if 'cache_path' in item_data:
                    normalized_item['cache_path'] = item_data['cache_path']
                
                # Add binary flag if available
                if 'is_binary' in item_data:
                    normalized_item['is_binary'] = item_data['is_binary']
            
            # Handle children for folders
            if item_type == 'folder' and item.childCount() > 0:
                children = []
                for i in range(item.childCount()):
                    child_item = item.child(i)
                    
                    # Skip hidden files
                    child_text = child_item.text(0)
                    if child_text.startswith('.') or child_text == '.DS_Store':
                        continue
                        
                    # Get child data
                    child_data = child_item.data(0, Qt.UserRole)
                    
                    if not child_data:
                        if child_item.childCount() > 0:
                            child_data = {'type': 'folder', 'name': child_item.text(0)}
                        else:
                            child_data = {'type': 'file', 'name': child_item.text(0)}
                    
                    # Create child structure
                    child_structure = {}
                    self._add_item_to_structure(child_structure, child_item)
                    
                    # Add to children list
                    if child_structure:
                        children.append(next(iter(child_structure.values())))
                        
                normalized_item['children'] = children
            
            # Add to structure
            if item.parent() is None or item.parent() == self.tree_widget.invisibleRootItem():
                # Top level item
                structure[item_name] = normalized_item
            else:
                # Child item
                structure[item.text(0)] = normalized_item 