#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Integration test for folder drag and drop functionality.
This test verifies that folder names are preserved properly during drag and drop operations,
and that the complete folder hierarchy is maintained.
"""

import sys
import os
import tempfile
import shutil
import time
import unittest
from PyQt5.QtWidgets import QApplication, QTreeWidgetItem
from PyQt5.QtCore import Qt, QMimeData, QUrl, QPoint
from PyQt5.QtGui import QDropEvent

# Create application instance before importing UI components
app = QApplication(sys.argv)

# Import structure editor after QApplication created
from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.ui.structure_editor.drag_drop import DragDropHandler

class DragDropIntegrationTest(unittest.TestCase):
    """Test case for folder drag and drop integration testing"""
    
    def setUp(self):
        """Set up test environment"""
        # Create test directory structure
        self.test_dir = tempfile.mkdtemp()
        print(f"Test directory: {self.test_dir}")
        
        # Create test folder structure
        self.top_folder = os.path.join(self.test_dir, "TopFolder")
        os.makedirs(self.top_folder)
        
        # Create nested subfolders to verify hierarchy is preserved
        self.subfolder1 = os.path.join(self.top_folder, "SubFolder1")
        self.subfolder2 = os.path.join(self.top_folder, "SubFolder2")
        self.nested_folder = os.path.join(self.subfolder1, "NestedFolder")
        
        os.makedirs(self.subfolder1)
        os.makedirs(self.subfolder2)
        os.makedirs(self.nested_folder)
        
        # Create test files at different levels
        with open(os.path.join(self.top_folder, "root_file.txt"), "w") as f:
            f.write("Root level file")
        
        with open(os.path.join(self.subfolder1, "sub1_file.txt"), "w") as f:
            f.write("Subfolder 1 file")
            
        with open(os.path.join(self.nested_folder, "nested_file.txt"), "w") as f:
            f.write("Nested folder file")
        
        with open(os.path.join(self.subfolder2, "sub2_file.txt"), "w") as f:
            f.write("Subfolder 2 file")
            
        # Create the editor
        self.editor = EnhancedStructureEditor(
            structure_name="Test_DragDrop",
            is_new=True
        )
        
    def tearDown(self):
        """Clean up test resources"""
        # Remove test directory
        try:
            shutil.rmtree(self.test_dir)
            print(f"Removed test directory: {self.test_dir}")
        except Exception as e:
            print(f"Error removing test directory: {e}")
    
    def test_folder_name_preserved(self):
        """Test that top folder name is preserved when dropping a folder"""
        # Simulate drag-drop operation
        handler = self.editor.drag_drop_handler
        tree = self.editor.tree_widget
        
        # Create a drop event for the top folder
        mime_data = QMimeData()
        url = QUrl.fromLocalFile(self.top_folder)
        mime_data.setUrls([url])
        
        # Drop position (center of tree)
        pos = QPoint(tree.width() // 2, tree.height() // 2)
        
        # Create and execute drop event
        drop_event = QDropEvent(
            pos,
            Qt.CopyAction,
            mime_data,
            Qt.LeftButton,
            Qt.NoModifier,
            QDropEvent.Drop
        )
        
        # Process the drop
        handler._handle_url_drop(drop_event)
        
        # Verify results
        self._verify_folder_structure(tree)
    
    def test_direct_method_call(self):
        """Test directly calling the add_directory_to_tree method"""
        handler = self.editor.drag_drop_handler
        tree = self.editor.tree_widget
        
        # Add directory directly
        added_item = handler._add_directory_to_tree(self.top_folder, tree.invisibleRootItem())
        
        # Verify the top folder was added with correct name
        self.assertIsNotNone(added_item, "No item was added")
        self.assertEqual(added_item.text(0), "TopFolder", 
                         f"Top folder name mismatch: expected 'TopFolder', got '{added_item.text(0)}'")
        
        # Verify the full structure
        self._verify_folder_structure(tree)
    
    def _verify_folder_structure(self, tree):
        """Verify the folder structure was added correctly"""
        root = tree.invisibleRootItem()
        
        # Find the top folder
        top_folder_item = None
        for i in range(root.childCount()):
            item = root.child(i)
            if item.text(0) == "TopFolder":
                top_folder_item = item
                break
        
        # Verify top folder exists
        self.assertIsNotNone(top_folder_item, "TopFolder was not found in the tree")
        
        # Verify subfolder structure
        subfolder_names = []
        for i in range(top_folder_item.childCount()):
            subfolder_names.append(top_folder_item.child(i).text(0))
        
        self.assertIn("SubFolder1", subfolder_names, "SubFolder1 not found")
        self.assertIn("SubFolder2", subfolder_names, "SubFolder2 not found")
        self.assertIn("root_file.txt", subfolder_names, "root_file.txt not found")
        
        # Find SubFolder1 item
        subfolder1_item = None
        for i in range(top_folder_item.childCount()):
            item = top_folder_item.child(i)
            if item.text(0) == "SubFolder1":
                subfolder1_item = item
                break
        
        # Verify SubFolder1 contents
        self.assertIsNotNone(subfolder1_item, "SubFolder1 item not found")
        
        subfolder1_contents = []
        for i in range(subfolder1_item.childCount()):
            subfolder1_contents.append(subfolder1_item.child(i).text(0))
        
        self.assertIn("NestedFolder", subfolder1_contents, "NestedFolder not found")
        self.assertIn("sub1_file.txt", subfolder1_contents, "sub1_file.txt not found")
        
        # Find NestedFolder item
        nested_folder_item = None
        for i in range(subfolder1_item.childCount()):
            item = subfolder1_item.child(i)
            if item.text(0) == "NestedFolder":
                nested_folder_item = item
                break
        
        # Verify NestedFolder contents
        self.assertIsNotNone(nested_folder_item, "NestedFolder item not found")
        
        nested_contents = []
        for i in range(nested_folder_item.childCount()):
            nested_contents.append(nested_folder_item.child(i).text(0))
        
        self.assertIn("nested_file.txt", nested_contents, "nested_file.txt not found")
        
        # Find SubFolder2 item
        subfolder2_item = None
        for i in range(top_folder_item.childCount()):
            item = top_folder_item.child(i)
            if item.text(0) == "SubFolder2":
                subfolder2_item = item
                break
        
        # Verify SubFolder2 contents
        self.assertIsNotNone(subfolder2_item, "SubFolder2 item not found")
        
        subfolder2_contents = []
        for i in range(subfolder2_item.childCount()):
            subfolder2_contents.append(subfolder2_item.child(i).text(0))
        
        self.assertIn("sub2_file.txt", subfolder2_contents, "sub2_file.txt not found")
    
    def _print_tree_structure(self, tree):
        """Print the current tree structure for debugging"""
        root = tree.invisibleRootItem()
        print("\nTree Structure:")
        self._print_item_recursive(root, 0)
    
    def _print_item_recursive(self, item, level):
        """Recursively print tree items"""
        indent = "  " * level
        for i in range(item.childCount()):
            child = item.child(i)
            item_text = child.text(0)
            item_data = child.data(0, Qt.UserRole)
            print(f"{indent}├─ {item_text} ({item_data})")
            self._print_item_recursive(child, level + 1)

if __name__ == "__main__":
    unittest.main() 