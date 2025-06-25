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
from PyQt6.QtCore import Qt, QObject
from PyQt6.QtGui import QIcon

# Import our utilities
from ..utils.file_type_detector import FileTypeDetector


class BasicFileOperations(QObject):
    """Handles basic file and folder operations"""
    
    def __init__(self, tree_widget=None):
        """Initialize basic file operations handler"""
        super().__init__()
        self.tree_widget = tree_widget
        self.file_detector = FileTypeDetector()
        
    def set_tree_widget(self, tree_widget):
        """Set or update the tree widget reference"""
        self.tree_widget = tree_widget

    def add_file(self, parent_item=None, file_name=None, file_type=None):
        """Add a new file to the structure"""
        if not self.tree_widget:
            print("ERROR: No tree widget available")
            return None
        
        # Determine the correct parent for the new file
        if parent_item is None:
            selected = self.tree_widget.selectedItems()
            if selected:
                item = selected[0]
                item_data = item.data(0, Qt.ItemDataRole.UserRole)
                
                # Check if the selected item is a folder
                is_folder = (item.childCount() > 0 or 
                             (isinstance(item_data, dict) and item_data.get('type') == 'folder'))

                if is_folder:
                    parent_item = item  # Use the selected folder as the parent
                else:
                    parent_item = item.parent()  # Use the parent of the selected file
            
            # If still no parent, default to the root
            if parent_item is None:
                parent_item = self.tree_widget.invisibleRootItem()

        # Get file path(s) from user
        file_paths, _ = QFileDialog.getOpenFileNames(
            self.tree_widget,
            'Select File(s) to Add',
            os.path.expanduser("~"),
            'All Files (*.*)'
        )
        
        if not file_paths:
            return None  # User cancelled
        
        created_items = []
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            
            # Create the new file item
            file_item = QTreeWidgetItem()
            file_item.setText(0, file_name)
            file_item.setText(1, "file")  # Set type in column 1
            
            # Add to the determined parent
            parent_item.addChild(file_item)
            
            # Store metadata in the item
            item_data = {
                'name': file_name,
                'type': 'file',
                'original_path': file_path,
                'is_binary': FileTypeDetector.is_binary_file(file_path)
            }
            file_item.setData(0, Qt.ItemDataRole.UserRole, item_data)
            created_items.append(file_item)

        # Expand the parent to make the new file(s) visible
        if parent_item is not self.tree_widget.invisibleRootItem():
            parent_item.setExpanded(True)
        
        return created_items

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

        # Set both column texts
        folder_item.setText(0, folder_name)
        folder_item.setText(1, "folder")  # Set the type column
        
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