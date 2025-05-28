#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script for folder drag and drop functionality in the structure editor.
This script simulates the actual drag and drop process to diagnose the folder name issue.
"""

import sys
import os
import tempfile
import shutil
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QLabel, QTreeWidgetItem
from PyQt6.QtCore import Qt, QMimeData, QUrl, QPoint
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

# Create application instance before importing UI components
app = QApplication(sys.argv)

# Import structure editor after QApplication created
from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.ui.structure_editor.drag_drop import DragDropHandler

class FolderDragDropRealTest(QDialog):
    """Test dialog for simulating real folder drag and drop operations"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Folder Drag Drop Simulation Test")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Add test control buttons
        self.status_label = QLabel("Ready to test...")
        layout.addWidget(self.status_label)
        
        test_button = QPushButton("Simulate Drag-Drop")
        test_button.clicked.connect(self.run_test)
        layout.addWidget(test_button)
        
        direct_test_button = QPushButton("Direct Method Test")
        direct_test_button.clicked.connect(self.run_direct_test)
        layout.addWidget(direct_test_button)
        
        print_tree_button = QPushButton("Print Tree Structure")
        print_tree_button.clicked.connect(self.print_tree_structure)
        layout.addWidget(print_tree_button)
        
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
            
        self.status_label.setText(f"Created test directory structure in: {self.test_dir}")
        print(f"Test directory: {self.test_dir}")
        print(f"Top folder path: {self.top_folder}")
    
    def run_test(self):
        """Simulate real drag and drop operation"""
        self.status_label.setText("Simulating drag and drop...")
        
        # Get the handler
        if not hasattr(self.editor, 'drag_drop_handler'):
            self.status_label.setText("ERROR: No drag_drop_handler found")
            return
        
        handler = self.editor.drag_drop_handler
        tree = self.editor.tree_widget
        
        # Create a drop event that mimics a real OS folder drop
        mime_data = QMimeData()
        url = QUrl.fromLocalFile(self.top_folder)
        mime_data.setUrls([url])
        
        # Create a drop position (center of the tree)
        pos = QPoint(tree.width() // 2, tree.height() // 2)
        
        # Create the drop event
        drop_event = QDropEvent(
            pos,
            Qt.DropAction.CopyAction,
            mime_data,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QDropEvent.Drop
        )
        
        # Call the handler's _handle_url_drop method directly
        # This simulates what happens during a real drop
        try:
            handler._handle_url_drop(drop_event)
            self.status_label.setText("Simulated drag-drop operation completed")
            
            # Check the result
            self.print_tree_structure()
        except Exception as e:
            self.status_label.setText(f"ERROR during simulation: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def run_direct_test(self):
        """Test the directory adding method directly for comparison"""
        self.status_label.setText("Testing direct method call...")
        
        # Get the handler
        if not hasattr(self.editor, 'drag_drop_handler'):
            self.status_label.setText("ERROR: No drag_drop_handler found")
            return
        
        handler = self.editor.drag_drop_handler
        tree = self.editor.tree_widget
        
        # Call the add directory method directly
        result = handler._add_directory_to_tree(self.top_folder, tree.invisibleRootItem())
        
        if result:
            # Check if the top folder name is correct
            expected_name = "TopFolder"
            actual_name = result.text(0)
            
            self.status_label.setText(f"DIRECT TEST: Top folder name - Expected: {expected_name}, Got: {actual_name}")
        else:
            self.status_label.setText("DIRECT TEST: Failed - No result from _add_directory_to_tree")
    
    def print_tree_structure(self):
        """Print the current tree structure to analyze issues"""
        tree = self.editor.tree_widget
        root = tree.invisibleRootItem()
        
        # Check if there are any items
        count = root.childCount()
        if count == 0:
            print("No items in tree")
            return
        
        print("\nCurrent Tree Structure:")
        self._print_item_recursive(root, 0)
    
    def _print_item_recursive(self, item, level):
        """Recursively print tree items with their data"""
        indent = "  " * level
        for i in range(item.childCount()):
            child = item.child(i)
            item_name = child.text(0)
            item_data = child.data(0, Qt.ItemDataRole.UserRole)
            
            print(f"{indent}├─ {item_name} ({item_data})")
            self._print_item_recursive(child, level + 1)
    
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
        test_window = FolderDragDropRealTest()
        test_window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 