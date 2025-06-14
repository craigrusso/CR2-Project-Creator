#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Date Applier Module
Handles date sequence pattern application for files and folders
"""

import os
from datetime import datetime, timedelta
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTreeWidgetItem


class DateApplier:
    """Handles date sequence pattern application"""
    
    def __init__(self, tree_widget=None, pattern_applier=None, item_operations=None):
        """Initialize date applier"""
        self.tree_widget = tree_widget
        self.pattern_applier = pattern_applier
        self.item_operations = item_operations
        
    def set_tree_widget(self, tree_widget):
        """Set or update the tree widget reference"""
        self.tree_widget = tree_widget
        
    def set_pattern_applier(self, pattern_applier):
        """Set the pattern applier reference"""
        self.pattern_applier = pattern_applier
        
    def set_item_operations(self, item_operations):
        """Set the item operations reference"""
        self.item_operations = item_operations

    def apply_date_sequence_to_item(self, item, date_data):
        """Apply date sequence configuration to item"""
        if not item or not self.tree_widget:
            print("DEBUG: apply_date_sequence_to_item - missing item or tree widget")
            return
            
        print(f"DEBUG: Applying date sequence to item: {item.text(0)}")
        print(f"DEBUG: Date data: {date_data}")
        
        # Get parent item
        parent_item = item.parent()
        
        # Get original item data
        original_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        original_name = original_data.get('name', item.text(0))
        item_type = original_data.get('type', 'file')
        
        # Clean original name of any existing icons or prefixes
        if ' ' in original_name and any(original_name.startswith(icon) for icon in ['🎬', '🎵', '🖼️', '📄', '📊', '📽️', '📦', '💻']):
            original_name = original_name.split(' ', 1)[1]
        
        # Ensure we have original_name stored for future reference
        if 'original_name' not in original_data:
            original_data['original_name'] = original_name
        
        # Extract date sequence data
        date_format = date_data.get('date_format', 'YYYY-MM-DD')
        start_date = date_data.get('date_start')
        end_date = date_data.get('date_end')
        interval_value = date_data.get('date_interval_value', 1)
        interval_type = date_data.get('date_interval_type', 'Days')
        
        # Parse original filename/foldername to get base name and extension
        base_name = original_name
        extension = ""
        if item_type == 'file' and '.' in original_name:
            base_name, extension = original_name.rsplit('.', 1)
            extension = '.' + extension
        
        current_date = start_date
        created_items = []
        item_index = 0
        
        # Create items for each date in the sequence (limit to 10 for performance)
        while current_date <= end_date and len(created_items) < 10:
            # Format date string
            date_str = self._format_date_string(current_date, date_format)
            
            # Create new name with date
            new_name = f"{base_name}_{date_str}{extension}"
            
            # Create new tree item
            if item_index == 0:
                # Update the first item (original item)
                new_item = item
                new_item.setText(0, new_name)
            else:
                # Create additional items
                new_item = self._create_date_item(parent_item, new_name, item_type, item)
            
            # Copy and update item data - ensure all data is JSON serializable
            new_data = original_data.copy()
            
            # Only copy JSON-serializable fields from date_data
            json_safe_date_data = {
                'date_format': date_data.get('date_format'),
                'date_start_iso': date_data.get('date_start_iso'),
                'date_end_iso': date_data.get('date_end_iso'),
                'date_interval_value': date_data.get('date_interval_value'),
                'date_interval_type': date_data.get('date_interval_type'),
                'uses_date_sequence': date_data.get('uses_date_sequence'),
                'rename_flag': date_data.get('rename_flag')
            }
            
            new_data.update(json_safe_date_data)
            new_data['name'] = new_name
            new_data['original_name'] = original_name  # Keep reference to original
            new_data['date_sequence_index'] = item_index
            new_data['date_sequence_date'] = current_date.isoformat()  # Convert to string
            
            # Set data on the tree item
            new_item.setData(0, Qt.ItemDataRole.UserRole, new_data)
            
            # If the original item had project name settings, apply them to the date sequence name
            if original_data.get('uses_project_name') and item_type == 'file' and self.item_operations:
                # Apply project name to the date-sequenced filename
                mode = original_data.get('project_name_mode', 'prepend')
                self.item_operations.update_project_name_display(new_item, mode)
                # Update visual styling
                self.item_operations.update_item_display(new_item)
            else:
                # Set display text without emoji icons
                new_item.setText(0, new_name)
            
            # Force immediate icon refresh to ensure proper system icons
            try:
                from app.ui.tree_styling import update_item_icon
                update_item_icon(new_item)
            except ImportError:
                pass
            
            created_items.append(new_item)
            print(f"DEBUG: Created date sequence {item_type}: {new_name} with proper icon")
            
            # Move to next date
            current_date = self._calculate_next_date(current_date, interval_value, interval_type)
            item_index += 1
        
        print(f"DEBUG: Successfully created {len(created_items)} date sequence {item_type}s")
        
        # Expand parent if it has children
        if parent_item:
            parent_item.setExpanded(True)
        
        # Refresh the tree widget
        if self.tree_widget:
            self.tree_widget.update()

    def _format_date_string(self, date, date_format):
        """Format date string based on format"""
        if date_format == "YYYY-MM-DD":
            return date.strftime("%Y-%m-%d")
        elif date_format == "YYYYMMDD":
            return date.strftime("%Y%m%d")
        elif date_format == "MM-DD-YYYY":
            return date.strftime("%m-%d-%Y")
        elif date_format == "DD-MM-YYYY":
            return date.strftime("%d-%m-%Y")
        elif date_format == "YYYY_MM_DD":
            return date.strftime("%Y_%m_%d")
        elif date_format == "MM_DD_YYYY":
            return date.strftime("%m_%d_%Y")
        elif date_format == "DD_MM_YYYY":
            return date.strftime("%d_%m_%Y")
        elif date_format == "YYYY.MM.DD":
            return date.strftime("%Y.%m.%d")
        elif date_format == "MM.DD.YYYY":
            return date.strftime("%m.%d.%Y")
        elif date_format == "DD.MM.YYYY":
            return date.strftime("%d.%m.%Y")
        else:
            return date.strftime("%Y-%m-%d")  # Default format

    def _calculate_next_date(self, current_date, interval_value, interval_type):
        """Calculate the next date in the sequence"""
        if interval_type == "Days":
            return current_date + timedelta(days=interval_value)
        elif interval_type == "Weeks":
            return current_date + timedelta(weeks=interval_value)
        elif interval_type == "Months":
            # Approximate month calculation
            return current_date + timedelta(days=interval_value * 30)
        else:
            return current_date + timedelta(days=interval_value)

    def _create_date_item(self, parent_item, name, item_type, original_item):
        """Create a new date sequence item"""
        if parent_item:
            new_item = QTreeWidgetItem(parent_item)
        else:
            new_item = QTreeWidgetItem(self.tree_widget)
        
        new_item.setText(0, name)
        
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
            
            # Copy all children to the new folder
            if original_item.childCount() > 0 and self.pattern_applier:
                self.pattern_applier.copy_folder_children(original_item, new_item)
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
        
        return new_item

    def apply_date_sequence_to_folder(self, folder_item, date_data):
        """Apply date sequence to all files in a folder"""
        if not folder_item:
            return
        
        print(f"DEBUG: Applying date sequence to folder: {folder_item.text(0)}")
        
        # Find all file items in the folder
        file_items = []
        for i in range(folder_item.childCount()):
            child = folder_item.child(i)
            child_data = child.data(0, Qt.ItemDataRole.UserRole) or {}
            if child_data.get('type') == 'file':
                file_items.append(child)
        
        # Apply date sequence to each file
        for file_item in file_items:
            self.apply_date_sequence_to_item(file_item, date_data)
        
        print(f"DEBUG: Applied date sequence to {len(file_items)} files in folder")

    def get_date_sequence_info(self, item):
        """Get date sequence information from an item"""
        if not item:
            return None
            
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        return {
            'date_sequence_index': item_data.get('date_sequence_index'),
            'date_sequence_date': item_data.get('date_sequence_date'),
            'original_name': item_data.get('original_name'),
            'date_format': item_data.get('date_format'),
            'date_start_iso': item_data.get('date_start_iso'),
            'date_end_iso': item_data.get('date_end_iso'),
            'date_interval_value': item_data.get('date_interval_value'),
            'date_interval_type': item_data.get('date_interval_type')
        }

    def is_date_sequence_item(self, item):
        """Check if an item is part of a date sequence"""
        if not item:
            return False
            
        item_data = item.data(0, Qt.ItemDataRole.UserRole) or {}
        return 'date_sequence_index' in item_data

    def get_date_sequence_siblings(self, item):
        """Get all date sequence siblings of an item"""
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
                'date_sequence_index' in sibling_data):
                siblings.append(sibling)
        
        return siblings

    def remove_date_sequence(self, item):
        """Remove date sequence from an item and its siblings"""
        if not item:
            return
            
        # Get all date sequence siblings
        date_items = self.get_date_sequence_siblings(item)
        
        if not date_items:
            return
        
        # Keep only the first item and restore its original name
        first_item = date_items[0]
        item_data = first_item.data(0, Qt.ItemDataRole.UserRole) or {}
        original_name = item_data.get('original_name', first_item.text(0))
        
        # Restore original name
        first_item.setText(0, original_name)
        
        # Clear date sequence data
        date_keys = ['date_sequence_index', 'date_sequence_date', 'date_format',
                    'date_start_iso', 'date_end_iso', 'date_interval_value', 
                    'date_interval_type', 'uses_date_sequence']
        for key in date_keys:
            item_data.pop(key, None)
        
        first_item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Remove other date sequence items
        for date_item in date_items[1:]:
            parent = date_item.parent()
            if parent:
                parent.removeChild(date_item)
            else:
                index = self.tree_widget.indexOfTopLevelItem(date_item)
                if index >= 0:
                    self.tree_widget.takeTopLevelItem(index)
        
        print(f"DEBUG: Removed date sequence, restored to: {original_name}")

    def validate_date_range(self, start_date, end_date):
        """Validate that the date range is reasonable"""
        if not start_date or not end_date:
            return False, "Start and end dates are required"
        
        if start_date > end_date:
            return False, "Start date must be before end date"
        
        # Check if the range is too large (more than 2 years)
        if (end_date - start_date).days > 730:
            return False, "Date range is too large (maximum 2 years)"
        
        return True, ""

    def calculate_sequence_count(self, start_date, end_date, interval_value, interval_type):
        """Calculate how many items will be created in the sequence"""
        if not start_date or not end_date:
            return 0
        
        current_date = start_date
        count = 0
        
        while current_date <= end_date and count < 100:  # Safety limit
            count += 1
            current_date = self._calculate_next_date(current_date, interval_value, interval_type)
        
        return count 