#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Import Operations Module
Handles importing files and directories into the structure
"""

import os
from PyQt6.QtWidgets import QFileDialog, QMessageBox

# Import our utilities
from ..utils.file_type_detector import FileTypeDetector
from ..handlers.binary_file_handler import BinaryFileHandler


class ImportOperations:
    """Handles file and directory import operations"""
    
    def __init__(self, tree_widget=None, basic_operations=None):
        """Initialize import operations handler"""
        self.tree_widget = tree_widget
        self.basic_operations = basic_operations
        self.file_detector = FileTypeDetector()
        self.binary_handler = BinaryFileHandler()
        
    def set_tree_widget(self, tree_widget):
        """Set or update the tree widget reference"""
        self.tree_widget = tree_widget
        
    def set_basic_operations(self, basic_operations):
        """Set the basic operations handler reference"""
        self.basic_operations = basic_operations

    def import_directory(self, target_item=None):
        """Import a directory structure"""
        if not self.tree_widget:
            return

        # Get directory from user
        dir_path = QFileDialog.getExistingDirectory(
            self.tree_widget,
            "Select Directory to Import",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if not dir_path:
            return
        
        try:
            # Import the directory contents
            self._import_directory_contents(dir_path, target_item)
            print(f"DEBUG: Successfully imported directory: {dir_path}")
        except Exception as e:
            QMessageBox.critical(
                self.tree_widget,
                "Import Error",
                f"Failed to import directory:\n{str(e)}"
            )

    def _import_directory_contents(self, dir_path, parent_item):
        """Recursively import directory contents"""
        if not self.basic_operations:
            print("ERROR: No basic operations handler available")
            return
            
        try:
            for item_name in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item_name)
                
                if os.path.isdir(item_path):
                    # Create folder item using basic operations
                    folder_item = self.basic_operations.add_folder(parent_item, item_name)
                    # Recursively import subdirectory
                    self._import_directory_contents(item_path, folder_item)
                else:
                    # Create file item using basic operations
                    file_type = self.file_detector.get_file_type_from_extension(item_path)
                    self.basic_operations._add_file_item(parent_item, item_name, file_type, item_path)
                    
        except Exception as e:
            print(f"ERROR: Failed to import directory contents: {e}")
            raise

    def import_file(self, target_item=None):
        """Import a single file"""
        if not self.tree_widget:
            return

        # Get file from user
        file_path, _ = QFileDialog.getOpenFileName(
            self.tree_widget,
            "Select File to Import",
            "",
            "All Files (*)"
        )
        
        if not file_path:
            return
        
        if not self.basic_operations:
            print("ERROR: No basic operations handler available")
            return
        
        try:
            file_name = os.path.basename(file_path)
            file_type = self.file_detector.get_file_type_from_extension(file_path)
            
            # Add the file item using basic operations
            self.basic_operations._add_file_item(target_item, file_name, file_type, file_path)
            print(f"DEBUG: Successfully imported file: {file_name}")
            
        except Exception as e:
            QMessageBox.critical(
                self.tree_widget,
                "Import Error",
                f"Failed to import file:\n{str(e)}"
            )

    def is_binary_file(self, file_path):
        """Check if a file is binary"""
        return self.binary_handler.is_binary_file(file_path)
        
    def get_file_type_from_extension(self, file_path):
        """Get file type from extension"""
        return self.file_detector.get_file_type_from_extension(file_path)
        
    def should_embed_binary_file(self, file_path, max_size_kb=500):
        """Check if a binary file should be embedded based on size"""
        return self.binary_handler.should_embed_binary_file(file_path, max_size_kb) 