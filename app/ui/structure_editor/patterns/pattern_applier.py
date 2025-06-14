#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Pattern Applier Module
Handles core pattern application logic for custom naming patterns
"""

import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor


class PatternApplier:
    """Handles core pattern application logic"""
    
    def __init__(self, tree_widget=None, item_operations=None):
        """Initialize pattern applier"""
        self.tree_widget = tree_widget
        self.item_operations = item_operations
        
    def set_tree_widget(self, tree_widget):
        """Set or update the tree widget reference"""
        self.tree_widget = tree_widget
        
    def set_item_operations(self, item_operations):
        """Set the item operations handler reference"""
        self.item_operations = item_operations

    def apply_pattern_to_item(self, item, pattern_data):
        """Apply custom pattern to item"""
        if not item:
            return
            
        data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        
        # Store original name if not already stored
        if 'original_name' not in data:
            data['original_name'] = item.text(0)
        
        # Update data with pattern information
        data.update(pattern_data)
        data['uses_custom_pattern'] = True
        data['rename_flag'] = True
        # Clear conflicting flags
        data['uses_project_name'] = False
        
        item.setData(0, Qt.ItemDataRole.UserRole, data)
        
        # Update display to show the pattern
        if pattern_data.get('pattern'):
            # Display the pattern as-is for template editing
            item.setText(0, pattern_data['pattern'])
            
            # Apply styling to indicate this item uses a custom pattern
            font = item.font(0)
            font.setItalic(True)
            item.setFont(0, font)
            
            # Use a different color for custom pattern files
            item.setForeground(0, QBrush(QColor("#9A4AFF")))  # Purple for custom patterns
            
            print(f"DEBUG: Applied custom pattern '{pattern_data['pattern']}' to item '{data.get('original_name', item.text(0))}'")
        
        # Update visual styling using item operations if available
        if self.item_operations:
            self.item_operations.update_item_display(item)

    def copy_folder_children(self, source_folder, target_folder):
        """Copy all children from source folder to target folder"""
        if not source_folder or not target_folder:
            return
            
        for i in range(source_folder.childCount()):
            source_child = source_folder.child(i)
            source_data = source_child.data(0, Qt.ItemDataRole.UserRole) or {}
            
            # Create new child item
            from PyQt6.QtWidgets import QTreeWidgetItem
            new_child = QTreeWidgetItem(target_folder)
            
            # Copy data and set proper display text
            source_name = source_data.get('name', source_child.text(0))
            # Clean any existing icons from the name
            if ' ' in source_name and any(source_name.startswith(icon) for icon in ['🎬', '🎵', '🖼️', '📄', '📊', '📽️', '📦', '💻']):
                source_name = source_name.split(' ', 1)[1]
            
            # Set display text without emoji icons
            new_child.setText(0, source_name)
            
            new_child.setData(0, Qt.ItemDataRole.UserRole, source_data.copy())
            
            # Set proper icon and properties based on item type
            child_type = source_data.get('type', 'file')
            if child_type == 'folder':
                # Set proper folder icon
                try:
                    from app.ui.icon_utilities import get_folder_icon
                    new_child.setIcon(0, get_folder_icon(False))  # Initially collapsed
                except ImportError:
                    # Fallback to standard icon
                    from PyQt6.QtWidgets import QApplication, QStyle
                    new_child.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
                
                # Make folder editable
                new_child.setFlags(new_child.flags() | Qt.ItemFlag.ItemIsEditable)
                
                # Recursively copy if this child is also a folder
                if source_child.childCount() > 0:
                    self.copy_folder_children(source_child, new_child)
            else:
                # Set proper file icon
                try:
                    from app.ui.icon_utilities import get_file_icon
                    new_child.setIcon(0, get_file_icon(source_name))
                except ImportError:
                    # Fallback to standard icon
                    from PyQt6.QtWidgets import QApplication, QStyle
                    new_child.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
                
                # Make file editable
                new_child.setFlags(new_child.flags() | Qt.ItemFlag.ItemIsEditable)
            
            # Force immediate icon refresh
            try:
                from app.ui.tree_styling import update_item_icon
                update_item_icon(new_child)
            except ImportError:
                pass

    def get_item_base_name_and_extension(self, item):
        """Extract base name and extension from an item"""
        if not item:
            return "", ""
            
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        original_name = item_data.get('original_name', item.text(0))
        
        # Clean original name of any existing icons or prefixes
        if ' ' in original_name and any(original_name.startswith(icon) for icon in ['🎬', '🎵', '🖼️', '📄', '📊', '📽️', '📦', '💻']):
            original_name = original_name.split(' ', 1)[1]
        
        # Extract base name and extension
        if '.' in original_name:
            base_name, extension = os.path.splitext(original_name)
            return base_name, extension
        else:
            return original_name, ""

    def create_new_item(self, parent_item, name, item_type='file', original_data=None):
        """Create a new tree item with proper setup"""
        if not self.tree_widget:
            return None
            
        from PyQt6.QtWidgets import QTreeWidgetItem
        
        # Create new tree item
        if parent_item:
            new_item = QTreeWidgetItem(parent_item)
        else:
            new_item = QTreeWidgetItem(self.tree_widget)
        
        new_item.setText(0, name)
        
        # Set proper icon and properties based on item type
        if item_type == 'folder':
            # Set proper folder icon
            try:
                from app.ui.icon_utilities import get_folder_icon
                new_item.setIcon(0, get_folder_icon(False))  # Initially collapsed
            except ImportError:
                # Fallback to standard icon
                from PyQt6.QtWidgets import QApplication, QStyle
                new_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
            
            # Make folder editable
            new_item.setFlags(new_item.flags() | Qt.ItemFlag.ItemIsEditable)
        else:
            # Set proper file icon
            try:
                from app.ui.icon_utilities import get_file_icon
                new_item.setIcon(0, get_file_icon(name))
            except ImportError:
                # Fallback to standard icon
                from PyQt6.QtWidgets import QApplication, QStyle
                new_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
            
            # Make file editable
            new_item.setFlags(new_item.flags() | Qt.ItemFlag.ItemIsEditable)
        
        # Set item data
        if original_data:
            new_data = original_data.copy()
            new_data['name'] = name
            new_item.setData(0, Qt.ItemDataRole.UserRole, new_data)
        
        # Force immediate icon refresh
        try:
            from app.ui.tree_styling import update_item_icon
            update_item_icon(new_item)
        except ImportError:
            pass
        
        return new_item

    def expand_parent_if_needed(self, item):
        """Expand parent item if it has children"""
        if not item:
            return
            
        parent_item = item.parent()
        if parent_item:
            parent_item.setExpanded(True)

    def refresh_tree_widget(self):
        """Refresh the tree widget display"""
        if self.tree_widget:
            self.tree_widget.update()

    def clean_item_name(self, name):
        """Clean item name of emoji icons and prefixes"""
        if not name:
            return ""
            
        # Clean any existing icons from the name
        if ' ' in name and any(name.startswith(icon) for icon in ['🎬', '🎵', '🖼️', '📄', '📊', '📽️', '📦', '💻']):
            return name.split(' ', 1)[1]
        
        return name

    def get_item_type(self, item):
        """Get the type of an item (file or folder)"""
        if not item:
            return 'file'
            
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        return item_data.get('type', 'file')

    def ensure_original_name_stored(self, item):
        """Ensure the original name is stored in item data"""
        if not item:
            return
            
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        if 'original_name' not in item_data:
            item_data['original_name'] = self.clean_item_name(item.text(0))
            item.setData(0, Qt.ItemDataRole.UserRole, item_data) 