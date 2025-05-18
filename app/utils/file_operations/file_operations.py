#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative
"""
File Operations Handler

Provides utilities for handling file operations in the application
"""

import os
import json
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal


class FileOperationsHandler(QObject):
    """Handler for file operations with signal support"""
    
    # Signals
    file_loaded = pyqtSignal(str, object)  # file_path, content
    file_saved = pyqtSignal(str)  # file_path
    
    def __init__(self, parent=None, debug=False):
        """Initialize the file operations handler"""
        super().__init__(parent)
        self.parent = parent
        self.debug = debug
    
    def load_json_file(self, file_path=None, show_dialog=True):
        """
        Load a JSON file and emit a signal with the content
        
        Args:
            file_path: Path to the file to load (optional)
            show_dialog: Whether to show a file dialog if no path is provided
            
        Returns:
            tuple: (success, content)
        """
        try:
            # If no file path and show_dialog is True, show a file dialog
            if not file_path and show_dialog:
                file_path, _ = QFileDialog.getOpenFileName(
                    self.parent,
                    "Load JSON File",
                    "",
                    "JSON Files (*.json);;All Files (*)"
                )
                
                if not file_path:
                    return False, None
            
            # if self.debug:
            #     print(f"FileOperationsHandler: Loading file from {file_path}")
            
            # Load the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            # Emit signal
            self.file_loaded.emit(file_path, content)
            
            return True, content
        except Exception as e:
            print(f"Error loading file: {e}")
            if self.parent:
                QMessageBox.warning(
                    self.parent,
                    "Error",
                    f"Failed to load file: {e}"
                )
            return False, None
    
    def save_json_file(self, data, file_path=None, show_dialog=True):
        """
        Save JSON data to a file
        
        Args:
            data: The data to save
            file_path: Path to save the file to (optional)
            show_dialog: Whether to show a file dialog if no path is provided
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # If no file path and show_dialog is True, show a file dialog
            if not file_path and show_dialog:
                file_path, _ = QFileDialog.getSaveFileName(
                    self.parent,
                    "Save JSON File",
                    "",
                    "JSON Files (*.json);;All Files (*)"
                )
                
                if not file_path:
                    return False
            
            # if self.debug:
            #     print(f"FileOperationsHandler: Saving file to {file_path}")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Save the file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            # Emit signal
            self.file_saved.emit(file_path)
            
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            if self.parent:
                QMessageBox.warning(
                    self.parent,
                    "Error",
                    f"Failed to save file: {e}"
                )
            return False
    
    def import_file(self, target_dir, file_path=None, show_dialog=True):
        """
        Import a file to a target directory
        
        Args:
            target_dir: Directory to import the file to
            file_path: Path of the file to import (optional)
            show_dialog: Whether to show a file dialog if no path is provided
            
        Returns:
            tuple: (success, imported_file_path)
        """
        try:
            # If no file path and show_dialog is True, show a file dialog
            if not file_path and show_dialog:
                file_path, _ = QFileDialog.getOpenFileName(
                    self.parent,
                    "Import File",
                    "",
                    "All Files (*)"
                )
                
                if not file_path:
                    return False, None
            
            # Ensure target directory exists
            os.makedirs(target_dir, exist_ok=True)
            
            # Get the file name
            file_name = os.path.basename(file_path)
            target_path = os.path.join(target_dir, file_name)
            
            # Copy the file
            import shutil
            shutil.copy2(file_path, target_path)
            
            return True, target_path
        except Exception as e:
            print(f"Error importing file: {e}")
            if self.parent:
                QMessageBox.warning(
                    self.parent,
                    "Error",
                    f"Failed to import file: {e}"
                )
            return False, None 