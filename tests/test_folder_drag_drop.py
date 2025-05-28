#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script for folder drag and drop functionality in the structure editor.
This script validates the folder name preservation when dragging folders.
"""

import sys
import os
import tempfile
import shutil
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QMimeData, QUrl, QPoint
from PyQt6.QtTest import QTest
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

# Create application instance before importing UI components
app = QApplication(sys.argv)

# Import structure editor after QApplication created
from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.ui.structure_editor.drag_drop import DragDropHandler

class FolderDragDropTest(QDialog):
    """Test dialog for folder drag and drop testing"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Folder Drag Drop Test")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Add test control buttons
        self.status_label = QLabel("Ready to test...")
        layout.addWidget(self.status_label)
        
        test_button = QPushButton("Run Drag Drop Test")
        test_button.clicked.connect(self.run_test)
        layout.addWidget(test_button)
        
        # Create structure editor for testing
        self.editor = EnhancedStructureEditor(
            structure_name="Test_DragDrop",
            is_new=True
        )
        layout.addWidget(self.editor)
        
        # Set up test directories
        self.setup_test_dirs()
    
    def setup_test_dirs(self):
        """Set up test directories for drag and drop testing"""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        
        # Create a test folder structure
        self.top_folder = os.path.join(self.test_dir, "TopFolder")
        os.makedirs(self.top_folder)
        
        # Create subfolders and files
        os.makedirs(os.path.join(self.top_folder, "SubFolder1"))
        os.makedirs(os.path.join(self.top_folder, "SubFolder2"))
        
        # Create some test files
        with open(os.path.join(self.top_folder, "file1.txt"), "w") as f:
            f.write("Test file 1")
        
        with open(os.path.join(self.top_folder, "SubFolder1", "file2.txt"), "w") as f:
            f.write("Test file 2")
            
        self.status_label.setText(f"Created test directory: {self.test_dir}")
    
    def run_test(self):
        """Run the drag and drop test"""
        self.status_label.setText("Running test...")
        
        # Get the drag drop handler from the editor
        handler = None
        if hasattr(self.editor, 'drag_drop_handler'):
            handler = self.editor.drag_drop_handler
        
        if not handler:
            self.status_label.setText("ERROR: Could not find drag_drop_handler")
            return
        
        # Test adding a directory
        tree_widget = self.editor.tree_widget
        root_item = tree_widget.invisibleRootItem()
        
        # Debug print of folder structure
        print(f"Top folder path: {self.top_folder}")
        print(f"Top folder name: {os.path.basename(self.top_folder)}")
        
        # Test adding a directory
        result = handler._add_directory_to_tree(self.top_folder, root_item)
        
        if result:
            # Check if the top folder name is correct
            expected_name = "TopFolder"
            actual_name = result.text(0)
            print(f"Expected folder name: {expected_name}")
            print(f"Actual folder name: {actual_name}")
            
            if actual_name == expected_name:
                self.status_label.setText(f"SUCCESS: Top folder name is correct: {actual_name}")
            else:
                self.status_label.setText(f"FAILURE: Top folder name is incorrect. Expected: {expected_name}, Got: {actual_name}")
            
            # Check if subfolders exist
            subfolder_names = []
            for i in range(result.childCount()):
                child = result.child(i)
                subfolder_names.append(child.text(0))
            
            expected_subfolders = ["SubFolder1", "SubFolder2", "file1.txt"]
            if any(name in subfolder_names for name in ["SubFolder1", "SubFolder2"]):
                self.status_label.setText(f"{self.status_label.text()}\nSubfolders found: {', '.join(subfolder_names)}")
            else:
                self.status_label.setText(f"{self.status_label.text()}\nERROR: No expected subfolders found. Got: {', '.join(subfolder_names)}")
                
            # Verify folder data in UserRole
            folder_data = result.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(folder_data, dict):
                print(f"Folder data: {folder_data}")
                if folder_data.get("name") == expected_name:
                    self.status_label.setText(f"{self.status_label.text()}\nFolder data name is correct: {folder_data.get('name')}")
                else:
                    self.status_label.setText(f"{self.status_label.text()}\nERROR: Folder data name is incorrect. Expected: {expected_name}, Got: {folder_data.get('name')}")
            else:
                self.status_label.setText(f"{self.status_label.text()}\nERROR: No folder data found or invalid format")
        else:
            self.status_label.setText("FAILURE: No result from _add_directory_to_tree")
    
    def closeEvent(self, event):
        """Clean up test directories on close"""
        try:
            shutil.rmtree(self.test_dir)
            print(f"Removed test directory: {self.test_dir}")
        except Exception as e:
            print(f"Error removing test directory: {e}")
        event.accept()

if __name__ == "__main__":
    try:
        test_window = FolderDragDropTest()
        test_window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 