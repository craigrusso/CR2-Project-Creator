#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Versioning Applier Module
Handles versioning pattern application for files and folders
"""

import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTreeWidgetItem


class VersioningApplier:
    """Handles versioning pattern application"""
    
    def __init__(self, tree_widget=None, pattern_applier=None):
        """Initialize versioning applier"""
        self.tree_widget = tree_widget
        self.pattern_applier = pattern_applier
        
    def set_tree_widget(self, tree_widget):
        """Set or update the tree widget reference"""
        self.tree_widget = tree_widget
        
    def set_pattern_applier(self, pattern_applier):
        """Set the pattern applier reference"""
        self.pattern_applier = pattern_applier

    def apply_versioning_to_item(self, item, versioning_data):
        """Apply versioning configuration to item"""
        if not item or not self.tree_widget:
            print("DEBUG: apply_versioning_to_item - missing item or tree widget")
            return
            
        print(f"DEBUG: Applying versioning to item: {item.text(0)}")
        print(f"DEBUG: Versioning data: {versioning_data}")
        
        # Get parent item
        parent_item = item.parent()
        
        # Get original item data
        original_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        original_name = original_data.get('name', item.text(0))
        item_type = original_data.get('type', 'file')
        
        # Clean original name of any existing icons or prefixes if available
        if 'name' in original_data:
            original_name = original_data['name']
            if ' ' in original_name and any(original_name.startswith(icon) for icon in ['🎬', '🎵', '🖼️', '📄', '📊', '📽️', '📦', '💻']):
                original_name = original_name.split(' ', 1)[1]
                original_data['original_name'] = original_name
        
        # Ensure we have original_name stored for future reference
        if 'original_name' not in original_data:
            original_data['original_name'] = original_name
        
        # Extract base name and extension
        if '.' in original_name:
            base_name, extension = os.path.splitext(original_name)
        else:
            base_name = original_name
            extension = '.txt' if item_type == 'file' else ''  # Default extension for files
        
        # Get versioning parameters
        format_text = versioning_data.get('versioning_format', 'v01, v02, v03...')
        start_num = versioning_data.get('versioning_start', 1)
        count = versioning_data.get('versioning_count', 5)
        
        # Generate version strings and create new items
        created_items = []
        
        for i in range(count):
            version_num = start_num + i
            
            # Generate version string based on format
            version_str = self._generate_version_string(format_text, version_num)
            
            # Create new filename
            new_filename = f"{base_name}_{version_str}{extension}"
            
            # Create new tree item
            if i == 0:
                # Update the first item (original item)
                new_item = item
                new_item.setText(0, new_filename)
            else:
                # Create additional items
                new_item = self._create_versioned_item(parent_item, new_filename, item_type, item)
            
            # Copy and update item data
            new_data = original_data.copy()
            new_data.update(versioning_data)
            new_data['name'] = new_filename
            new_data['original_name'] = original_name  # Keep reference to original
            new_data['version_number'] = version_num
            new_data['version_string'] = version_str
            
            new_item.setData(0, Qt.ItemDataRole.UserRole, new_data)
            
            # Set display text without emoji icons
            new_item.setText(0, new_filename)
            
            # Force immediate icon refresh to ensure proper system icons
            try:
                from app.ui.tree_styling import update_item_icon
                update_item_icon(new_item)
            except ImportError:
                pass
            
            created_items.append(new_item)
            print(f"DEBUG: Created versioned {item_type}: {new_filename} with proper icon")
        
        # Expand parent if needed
        if parent_item:
            parent_item.setExpanded(True)
        
        print(f"DEBUG: Successfully created {len(created_items)} versioned files")

    def _generate_version_string(self, format_text, version_num):
        """Generate version string based on format"""
        if format_text.startswith("v0"):
            return f"v{version_num:02d}"
        elif format_text.startswith("V0"):
            return f"V{version_num:02d}"
        elif format_text.startswith("_v"):
            return f"_v{version_num}"
        elif format_text.startswith("_V"):
            return f"_V{version_num}"
        elif format_text.startswith("(v0"):
            return f"(v{version_num:02d})"
        elif format_text.startswith("00"):
            return f"{version_num:03d}"
        elif format_text.startswith("_00"):
            return f"_{version_num:03d}"
        else:
            return f"v{version_num:02d}"

    def _create_versioned_item(self, parent_item, filename, item_type, original_item):
        """Create a new versioned item"""
        if parent_item:
            new_item = QTreeWidgetItem(parent_item)
        else:
            new_item = QTreeWidgetItem(self.tree_widget)
        
        new_item.setText(0, filename)
        
        # Set proper icon and properties based on item type
        if item_type == 'folder':
            # Set proper folder icon immediately
            try:
                from app.ui.icon_utilities import get_folder_icon
                new_item.setIcon(0, get_folder_icon(False))  # Initially collapsed
            except ImportError:
                # Fallback to standard icon
                from PyQt6.QtWidgets import QApplication, QStyle
                new_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
            
            # Make folder editable
            new_item.setFlags(new_item.flags() | Qt.ItemFlag.ItemIsEditable)
            
            # Copy all children to the new folder if it's a folder
            if original_item.childCount() > 0 and self.pattern_applier:
                self.pattern_applier.copy_folder_children(original_item, new_item)
        else:
            # Set proper file icon
            try:
                from app.ui.icon_utilities import get_file_icon
                new_item.setIcon(0, get_file_icon(filename))
            except ImportError:
                # Fallback to standard icon
                from PyQt6.QtWidgets import QApplication, QStyle
                new_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
            
            # Make file editable
            new_item.setFlags(new_item.flags() | Qt.ItemFlag.ItemIsEditable)
        
        return new_item

    def apply_versioning_to_folder(self, folder_item, versioning_data):
        """Apply versioning to all files in a folder"""
        if not folder_item:
            return
        
        print(f"DEBUG: Applying versioning to folder: {folder_item.text(0)}")
        
        # Find all file items in the folder
        file_items = []
        for i in range(folder_item.childCount()):
            child = folder_item.child(i)
            child_data = child.data(0, Qt.ItemDataRole.UserRole) or {}
            if child_data.get('type') == 'file':
                file_items.append(child)
        
        # Apply versioning to each file
        for file_item in file_items:
            self.apply_versioning_to_item(file_item, versioning_data)
        
        print(f"DEBUG: Applied versioning to {len(file_items)} files in folder")

    def get_version_info(self, item):
        """Get version information from an item"""
        if not item:
            return None
            
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        return {
            'version_number': item_data.get('version_number'),
            'version_string': item_data.get('version_string'),
            'original_name': item_data.get('original_name'),
            'versioning_format': item_data.get('versioning_format'),
            'versioning_start': item_data.get('versioning_start'),
            'versioning_count': item_data.get('versioning_count')
        }

    def is_versioned_item(self, item):
        """Check if an item is versioned"""
        if not item:
            return False
            
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        return 'version_number' in item_data

    def get_versioned_siblings(self, item):
        """Get all versioned siblings of an item"""
        if not item:
            return []
            
        parent = item.parent()
        if not parent:
            parent = self.tree_widget.invisibleRootItem()
        
        siblings = []
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        original_name = item_data.get('original_name')
        
        if not original_name:
            return []
        
        for i in range(parent.childCount()):
            sibling = parent.child(i)
            sibling_data = sibling.data(0, Qt.ItemDataRole.UserRole) or {}
            if (sibling_data.get('original_name') == original_name and 
                'version_number' in sibling_data):
                siblings.append(sibling)
        
        return siblings

    def remove_versioning(self, item):
        """Remove versioning from an item and its siblings"""
        if not item:
            return
            
        # Get all versioned siblings
        versioned_items = self.get_versioned_siblings(item)
        
        if not versioned_items:
            return
        
        # Keep only the first item and restore its original name
        first_item = versioned_items[0]
        item_data = first_item.data(0, Qt.ItemDataRole.UserRole) or {}
        original_name = item_data.get('original_name', first_item.text(0))
        
        # Restore original name
        first_item.setText(0, original_name)
        
        # Clear versioning data
        version_keys = ['version_number', 'version_string', 'versioning_format', 
                       'versioning_start', 'versioning_count']
        for key in version_keys:
            item_data.pop(key, None)
        
        first_item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Remove other versioned items
        for versioned_item in versioned_items[1:]:
            parent = versioned_item.parent()
            if parent:
                parent.removeChild(versioned_item)
            else:
                index = self.tree_widget.indexOfTopLevelItem(versioned_item)
                if index >= 0:
                    self.tree_widget.takeTopLevelItem(index)
        
        print(f"DEBUG: Removed versioning, restored to: {original_name}") 