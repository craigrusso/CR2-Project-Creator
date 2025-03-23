#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Structure Converter Module

This module provides functions for converting between tree widgets and structure representations.
"""

import os
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtCore import Qt


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
        Create a structure representation from the tree widget
        
        Returns:
            list: Structure data
        """
        # Check if tree widget exists
        if not self.tree_widget:
            print("ERROR: No tree widget available")
            return []
        
        # Get the root item
        root = self.tree_widget.invisibleRootItem()
        
        # Initialize the structure
        structure = []
        
        # Process all top-level items
        for i in range(root.childCount()):
            item = root.child(i)
            self._add_item_to_structure(item, structure)
        
        print(f"DEBUG: Created structure with {len(structure)} top-level items")
        return structure
    
    def _add_item_to_structure(self, item, parent_list):
        """
        Add an item to the structure
        
        Args:
            item: Tree widget item
            parent_list: Parent list to add to
        """
        # Get item data
        item_data = item.data(0, Qt.UserRole)
        
        # If no data, try to infer type from children
        if not item_data:
            # If it has children, assume it's a folder
            if item.childCount() > 0:
                item_data = {'type': 'folder', 'name': item.text(0)}
            else:
                # Otherwise, assume it's a file
                item_data = {'type': 'file', 'name': item.text(0)}
        
        # Check type from data
        if isinstance(item_data, dict) and 'type' in item_data:
            if item_data['type'] == 'folder':
                # It's a folder
                folder_name = item.text(0)
                children = []
                
                # Add all children
                for i in range(item.childCount()):
                    self._add_item_to_structure(item.child(i), children)
                
                # Add folder to parent list
                parent_list.append({folder_name: children})
            else:
                # It's a file or other type
                file_name = item.text(0)
                parent_list.append(file_name)
        else:
            # If we can't determine type, add as a file
            file_name = item.text(0)
            parent_list.append(file_name)
    
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
        # Create tree item
        if parent_item:
            folder_item = QTreeWidgetItem(parent_item)
        else:
            folder_item = QTreeWidgetItem(self.tree_widget)
        
        # Set folder properties
        folder_item.setText(0, folder_name)
        folder_item.setData(0, Qt.UserRole, {"type": "folder"})
        
        # If we have file_operations, use it to style the item
        if self.editor and hasattr(self.editor, 'file_operations') and hasattr(self.editor.file_operations, '_create_item'):
            # Use file_operations to create a properly styled item
            styled_item = self.editor.file_operations._create_item(parent_item, folder_name, is_folder=True)
            
            # If a new item was created, we don't need our version
            if styled_item and styled_item != folder_item:
                # Remove our item
                if parent_item:
                    parent_item.removeChild(folder_item)
                else:
                    index = self.tree_widget.indexOfTopLevelItem(folder_item)
                    if index >= 0:
                        self.tree_widget.takeTopLevelItem(index)
                
                return styled_item
        else:
            # Apply styling ourselves
            # Set folder icon
            try:
                from PyQt5.QtGui import QIcon
                
                # Try app/assets/icons/folder.png first
                icon_paths = [
                    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                              "assets", "icons", "folder.png"),
                    "icons/folder.png",
                    os.path.join(os.path.dirname(__file__), "icons", "folder.png")
                ]
                
                folder_icon = None
                for path in icon_paths:
                    if os.path.exists(path):
                        folder_icon = QIcon(path)
                        if not folder_icon.isNull():
                            break
                
                # Use theme icon if file not found
                if folder_icon is None or folder_icon.isNull():
                    folder_icon = QIcon.fromTheme("folder")
                
                # Set icon if we found one
                if folder_icon and not folder_icon.isNull():
                    folder_item.setIcon(0, folder_icon)
                
                # Use bold text for folders
                font = folder_item.font(0)
                font.setBold(True)
                folder_item.setFont(0, font)
                
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
        Process a tree item and its children to generate structure
        
        Args:
            item: The tree item to process
            
        Returns:
            dict or str: The item data in the format expected by the project builder
        """
        if not item:
            return None
        
        # Get the item text
        name = item.text(0)
        
        # Get item data to determine if this is a folder or file
        item_user_data = item.data(0, Qt.UserRole)
        
        # Determine if this is a folder or file
        is_folder = False
        
        # Check data formats in order of preference
        if isinstance(item_user_data, str) and item_user_data == 'folder':
            # Direct string marker
            is_folder = True
        elif isinstance(item_user_data, dict) and 'type' in item_user_data:
            # Dict with type field
            is_folder = item_user_data['type'] == 'folder'
        elif item.childCount() > 0:
            # Has children, must be a folder
            is_folder = True
        
        if is_folder:
            # For folders, use the {folder_name: [children]} format that the project builder expects
            children = []
            for i in range(item.childCount()):
                child_data = self._process_item(item.child(i))
                if child_data:
                    children.append(child_data)
            return {name: children}
        else:
            # For files, just return the name string
            return name

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