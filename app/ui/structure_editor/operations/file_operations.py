#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Basic File Operations Module
Handles basic file and folder operations: add, delete, rename
"""

import os
from PyQt6.QtWidgets import (
    QTreeWidgetItem, QInputDialog, QLineEdit, QMessageBox, QDialog, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

# Import our utilities
from ..utils.file_type_detector import FileTypeDetector


class BasicFileOperations:
    """Handles basic file and folder operations"""
    
    def __init__(self, tree_widget=None):
        """Initialize basic file operations handler"""
        self.tree_widget = tree_widget
        self.file_detector = FileTypeDetector()
        
    def set_tree_widget(self, tree_widget):
        """Set or update the tree widget reference"""
        self.tree_widget = tree_widget

    def add_file(self, parent_item=None, file_name=None, file_type=None):
        """Add an existing file to the structure, ensuring it's placed under the correct parent."""
        if not self.tree_widget:
            print("ERROR: No tree widget available")
            return None

        # 1. Determine the correct parent item using logic identical to add_folder.
        selected = self.tree_widget.selectedItems()
        actual_parent_item = None
        parent_name_for_debug = "Root Level"

        if selected:
            item = selected[0]
            # If the selected item is a folder, it becomes the parent.
            item_data = item.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(item_data, dict) and item_data.get('type') == "folder":
                actual_parent_item = item
                parent_name_for_debug = actual_parent_item.text(0)

        # If no folder was selected, the parent becomes the invisible root item.
        if actual_parent_item is None:
            actual_parent_item = self.tree_widget.invisibleRootItem()

        # 2. Open system file picker dialog to select an existing file.
        file_path, _ = QFileDialog.getOpenFileName(
            self.tree_widget,
            "Select File to Add to Template Structure",
            "",  # Start in default directory
            "All Files (*)"
        )
        
        if not file_path:
            return None  # User cancelled
        
        # 3. Process the selected file.
        file_name = os.path.basename(file_path)
        file_type = self.file_detector.get_file_type_from_extension(file_name)
        
        # 4. Create the file item in the tree under the correct parent.
        file_item = self._add_file_item(actual_parent_item, file_name, file_type, file_path)
        
        if file_item:
            from ..handlers.binary_file_handler import BinaryFileHandler
            data = file_item.data(0, Qt.ItemDataRole.UserRole) or {}
            data['is_binary'] = BinaryFileHandler.is_binary_file(file_path)
            data['original_path'] = file_path
            file_item.setData(0, Qt.ItemDataRole.UserRole, data)
            
            # This styling needs to be applied after the item is created and added.
            try:
                from app.ui.tree_styling import update_item_icon
                update_item_icon(file_item)
            except ImportError:
                print("Could not import update_item_icon for immediate styling.")

            print(f"DEBUG: Added file '{file_name}' to parent '{parent_name_for_debug}'")
        
        return file_item

    def _add_file_item(self, parent_item, file_name, file_type=None, original_path=None):
        """Internal method to add a file item to the tree"""
        if not self.tree_widget:
            return None

        # Create the tree item
        if parent_item:
            file_item = QTreeWidgetItem(parent_item)
        else:
            file_item = QTreeWidgetItem(self.tree_widget)

        file_item.setText(0, file_name)
        
        # Set item data
        item_data = {
            'name': file_name,
            'type': 'file',
            'file_type': file_type or self.file_detector.get_file_type_from_extension(file_name)
        }
        
        if original_path:
            item_data['original_path'] = original_path
            # Import binary file handler for checking
            from ..handlers.binary_file_handler import BinaryFileHandler
            item_data['is_binary'] = BinaryFileHandler.is_binary_file(original_path)
        
        file_item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Set display text without emoji icons
        file_item.setText(0, file_name)
        
        # Expand parent if needed
        if parent_item:
            parent_item.setExpanded(True)
        
        print(f"DEBUG: Added file '{file_name}' to tree")
        return file_item

    def add_folder(self, parent_item=None, folder_name=None):
        """Add a new folder to the structure"""
        if not self.tree_widget:
            print("ERROR: No tree widget available")
            return None

        # Get folder name from user if not provided
        if not folder_name:
            from PyQt6.QtWidgets import QInputDialog
            text, ok = QInputDialog.getText(
                self.tree_widget, 
                'Add Folder', 
                'Enter folder name:'
            )
            if ok and text.strip():
                folder_name = text.strip()
            else:
                return None

        # Create the tree item
        if parent_item:
            folder_item = QTreeWidgetItem(parent_item)
        else:
            folder_item = QTreeWidgetItem(self.tree_widget)

        folder_item.setText(0, folder_name)
        
        # Set item data
        item_data = {
            'name': folder_name,
            'type': 'folder'
        }
        folder_item.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Set proper folder icon immediately
        try:
            from app.ui.icon_utilities import get_folder_icon
            folder_item.setIcon(0, get_folder_icon(False))  # Initially collapsed
        except ImportError:
            # Fallback to standard icon
            from PyQt6.QtWidgets import QApplication, QStyle
            folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
        
        # Make folder editable
        folder_item.setFlags(folder_item.flags() | Qt.ItemFlag.ItemIsEditable)
        
        # Expand parent if needed
        if parent_item:
            parent_item.setExpanded(True)
        
        # Expand the new folder
        folder_item.setExpanded(True)
        
        # Force immediate icon refresh to ensure proper system folder icon
        try:
            from app.ui.tree_styling import update_item_icon
            update_item_icon(folder_item)
        except ImportError:
            pass
        
        print(f"DEBUG: Added folder '{folder_name}' to tree with proper icon")
        return folder_item

    def delete_selected(self):
        """Delete the selected items"""
        if not self.tree_widget:
            return

        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            return

        # Confirm deletion
        count = len(selected_items)
        item_text = "item" if count == 1 else "items"
        
        reply = QMessageBox.question(
            self.tree_widget,
            "Confirm Deletion",
            f"Are you sure you want to delete the selected {count} {item_text}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for item in selected_items:
                # Get parent before deletion
                parent = item.parent()
                
                # Remove the item
                if parent:
                    parent.removeChild(item)
                else:
                    index = self.tree_widget.indexOfTopLevelItem(item)
                    if index >= 0:
                        self.tree_widget.takeTopLevelItem(index)
                
                print(f"DEBUG: Deleted item '{item.text(0)}'")

    def rename_item(self, item):
        """Rename the selected item"""
        if not item:
            return
        
        # Get current name (remove emoji prefix if present)
        current_text = item.text(0)
        if " " in current_text and any(current_text.startswith(emoji) for emoji in ["🎬", "🎵", "🖼️", "📄", "📊", "📽️", "📦", "💻"]):
            current_name = current_text.split(" ", 1)[1]
        else:
            current_name = current_text
        
        # Get new name from user
        text, ok = QInputDialog.getText(
            self.tree_widget,
            'Rename Item',
            'Enter new name:',
            QLineEdit.EchoMode.Normal,
            current_name
        )
        
        if ok and text.strip() and text.strip() != current_name:
            new_name = text.strip()
            
            # Update item data
            data = item.data(0, Qt.ItemDataRole.UserRole) or {}
            data['name'] = new_name
            item.setData(0, Qt.ItemDataRole.UserRole, data)
            
            # Update display text without emoji icons
            item.setText(0, new_name)
            
            print(f"DEBUG: Renamed item to '{new_name}'") 