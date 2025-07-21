#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Item Operations Module
Handles tree item manipulation, display updates, and project name modes
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor


class ItemOperations:
    """Handles tree item manipulation and display updates"""
    
    def __init__(self, tree_widget=None):
        """Initialize item operations handler"""
        self.tree_widget = tree_widget
        
    def set_tree_widget(self, tree_widget):
        """Set or update the tree widget reference"""
        self.tree_widget = tree_widget

    def set_project_name_mode(self, item, mode):
        """Set project name mode for a file"""
        if not item:
            return
        
        # Get current item data
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        
        # Store original name if not already stored
        if 'original_name' not in item_data:
            item_data['original_name'] = item.text(0)
        
        # Clear custom pattern data first - this is key to fixing the issue
        self._clear_all_custom_pattern_data(item_data)
        
        # Update the project name mode
        item_data['project_name_mode'] = mode
        item_data['uses_project_name'] = True
        item_data['rename_flag'] = True
        
        # Update the tree item data
        item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Update the display name
        self.update_project_name_display(item, mode)
        
        # Update visual styling
        self.update_item_display(item)
        
        print(f"DEBUG: Set {mode} mode for {item.text(0)} (cleared custom patterns)")

    def _clear_all_custom_pattern_data(self, item_data):
        """Clear all custom pattern related data from item data"""
        # Remove all custom pattern related keys
        pattern_keys = [
            'pattern', 'uses_custom_pattern', 'custom_options', 
            'separator', 'separator_type', 'custom_separator',
            'date_format_text', 'time_format_text', 'date_format', 'time_format'
        ]
        
        for key in pattern_keys:
            item_data.pop(key, None)
        
        print(f"DEBUG: Cleared custom pattern data keys: {pattern_keys}")

    def switch_from_pattern_to_project_name(self, item, mode='replace'):
        """Switch an item from custom pattern back to project name mode
        
        This is the key method to solve the user's issue - it completely
        clears custom pattern data and switches to project name mode.
        """
        if not item:
            return False
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        
        # Store original name if not already stored
        if 'original_name' not in item_data:
            item_data['original_name'] = item.text(0)
        
        # Completely clear all custom pattern data
        self._clear_all_custom_pattern_data(item_data)
        
        # Set project name mode
        item_data['project_name_mode'] = mode
        item_data['uses_project_name'] = True
        item_data['rename_flag'] = True
        
        # Update the tree item data
        item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Update the display name
        self.update_project_name_display(item, mode)
        
        # Update visual styling
        self.update_item_display(item)
        
        print(f"DEBUG: Successfully switched item from custom pattern to project name mode: {mode}")
        return True

    def update_item_display(self, item):
        """Update the visual display of an item based on its properties"""
        if not item:
            return
        
        try:
            item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
            
            # Apply styling based on item properties
            if item_data.get('uses_custom_pattern'):
                # Custom pattern files - purple and italic
                font = item.font(0)
                font.setItalic(True)
                item.setFont(0, font)
                item.setForeground(0, QBrush(QColor("#9A4AFF")))  # Purple for custom patterns
            elif item_data.get('uses_project_name') or item_data.get('rename_flag'):
                # Project name files - blue and italic
                font = item.font(0)
                font.setItalic(True)
                item.setFont(0, font)
                item.setForeground(0, QBrush(QColor("#4A9BFF")))  # Blue for project name
            else:
                # Reset to normal styling
                font = item.font(0)
                font.setItalic(False)
                item.setFont(0, font)
                
                # Reset color to default
                item.setForeground(0, QBrush())
                
        except (RuntimeError, AttributeError) as e:
            print(f"DEBUG: Error updating item display: {e}")

    def update_project_name_display(self, item, mode):
        """Update the display name of an item based on project name mode"""
        if not item:
            return
        
        try:
            item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
            original_name = item_data.get('original_name', item.text(0))
            
            # Split filename into base and extension
            name_parts = original_name.rsplit('.', 1)
            if len(name_parts) == 2:
                base_name, extension = name_parts
                extension = '.' + extension
            else:
                base_name = original_name
                extension = ''
            
            # Create the display name based on mode
            placeholder = "${PROJECT_NAME}"
            separator = "_"
            
            if mode == 'replace':
                display_name = f"{placeholder}{extension}"
            elif mode == 'prepend':
                display_name = f"{placeholder}{separator}{base_name}{extension}"
            elif mode == 'append':
                display_name = f"{base_name}{separator}{placeholder}{extension}"
            else:
                # Default to replace
                display_name = f"{placeholder}{extension}"
            
            # Update the display
            item.setText(0, display_name)
            print(f"DEBUG: Updated display name to: {display_name}")
            
        except (RuntimeError, AttributeError) as e:
            print(f"DEBUG: Error updating project name display: {e}")

    def apply_pattern_to_item(self, item, pattern_data):
        """Apply custom pattern to item"""
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
        
        # Update visual styling
        self.update_item_display(item)

    def get_item_original_name(self, item):
        """Get the original name of an item"""
        if not item:
            return ""
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        return item_data.get('original_name', item.text(0))

    def set_item_original_name(self, item, original_name):
        """Set the original name of an item"""
        if not item:
            return
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        item_data['original_name'] = original_name
        item.setData(0, Qt.ItemDataRole.UserRole, item_data)

    def reset_item_to_original(self, item):
        """Reset an item to its original name and styling"""
        if not item:
            return
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        original_name = item_data.get('original_name', item.text(0))
        
        # Reset display name
        item.setText(0, original_name)
        
        # Clear ALL flags and pattern data
        item_data['uses_project_name'] = False
        item_data['uses_custom_pattern'] = False
        item_data['rename_flag'] = False
        
        # Clear all pattern-specific data more thoroughly
        self._clear_all_custom_pattern_data(item_data)
        
        # Also clear project name specific data
        project_name_keys = ['project_name_mode', 'custom_separator', 'original_extension']
        for key in project_name_keys:
            item_data.pop(key, None)
        
        item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Reset visual styling
        self.update_item_display(item)
        
        print(f"DEBUG: Reset item to original name: {original_name}")

    def is_item_modified(self, item):
        """Check if an item has been modified from its original state"""
        if not item:
            return False
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        return (item_data.get('uses_project_name', False) or 
                item_data.get('uses_custom_pattern', False) or 
                item_data.get('rename_flag', False))

    def is_item_using_custom_pattern(self, item):
        """Check if an item is currently using a custom pattern"""
        if not item:
            return False
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        return item_data.get('uses_custom_pattern', False) and item_data.get('pattern')

    def is_item_using_project_name(self, item):
        """Check if an item is currently using project name mode"""
        if not item:
            return False
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        return (item_data.get('uses_project_name', False) or 
                item_data.get('rename_flag', False)) and not item_data.get('uses_custom_pattern', False)

    def get_item_type(self, item):
        """Get the type of an item (file or folder)"""
        if not item:
            return None
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        return item_data.get('type')

    def is_folder_item(self, item):
        """Check if an item is a folder"""
        if not item:
            return False
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        return item_data.get('type') == 'folder' or item.childCount() > 0

    def is_file_item(self, item):
        """Check if an item is a file"""
        if not item:
            return False
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        return item_data.get('type') == 'file'

    def get_item_file_type(self, item):
        """Get the file type of an item"""
        if not item:
            return None
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        return item_data.get('file_type')

    def set_item_data(self, item, key, value):
        """Set a data value for an item"""
        if not item:
            return
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        item_data[key] = value
        item.setData(0, Qt.ItemDataRole.UserRole, item_data)

    def get_item_data(self, item, key, default=None):
        """Get a data value from an item"""
        if not item:
            return default
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        return item_data.get(key, default) 