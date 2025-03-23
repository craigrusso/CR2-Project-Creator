#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Comprehensive test for structure editor functionality
Tests the delete and Use Project Name functionality
"""

import sys
import os
import unittest
from PyQt5.QtWidgets import QApplication, QTreeWidgetItem, QMenu, QAction
from PyQt5.QtCore import Qt, QEvent, QPoint
from PyQt5.QtTest import QTest
from PyQt5.QtGui import QKeyEvent, QContextMenuEvent

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module to test
from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.ui.structure_editor.file_operations import FileOperations

class TestStructureEditorFunctionality(unittest.TestCase):
    """Comprehensive test for structure editor functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class"""
        # Create Qt application
        cls.app = QApplication.instance() or QApplication(sys.argv)
    
    def setUp(self):
        """Set up each test"""
        # Create the structure editor
        self.editor = EnhancedStructureEditor(
            structure_name="Test_Template",
            is_new=True
        )
        
        # Add a file and folder to test
        self.root_item = self.editor.tree_widget.invisibleRootItem()
        
        # Create a folder
        self.folder_item = QTreeWidgetItem(self.root_item)
        self.folder_item.setText(0, "Test Folder")
        self.folder_item.setData(0, Qt.UserRole, {"type": "folder", "name": "Test Folder"})
        
        # Add files to the folder
        self.file_item1 = QTreeWidgetItem(self.folder_item)
        self.file_item1.setText(0, "test_file1.txt")
        self.file_item1.setData(0, Qt.UserRole, {"type": "file", "name": "test_file1.txt"})
        
        self.file_item2 = QTreeWidgetItem(self.folder_item)
        self.file_item2.setText(0, "test_file2.txt")
        self.file_item2.setData(0, Qt.UserRole, {"type": "file", "name": "test_file2.txt"})
        
        # Add a folder in the folder
        self.subfolder_item = QTreeWidgetItem(self.folder_item)
        self.subfolder_item.setText(0, "Subfolder")
        self.subfolder_item.setData(0, Qt.UserRole, {"type": "folder", "name": "Subfolder"})
        
        # Expand the folder
        self.folder_item.setExpanded(True)
        
    def tearDown(self):
        """Clean up after each test"""
        self.editor.close()
        
    def test_delete_folder_using_menu(self):
        """Test deleting a folder using the context menu"""
        # Select the folder
        self.editor.tree_widget.setCurrentItem(self.folder_item)
        
        # Call the delete_item method directly
        result = self.editor._delete_item(self.folder_item)
        
        # Check result
        self.assertTrue(result, "Delete operation should return True")
        
        # Check that the folder was removed
        root_count = self.root_item.childCount()
        self.assertEqual(root_count, 0, "Root should have no children after folder deletion")
        
    def test_delete_file_using_key(self):
        """Test deleting a file using the Delete key"""
        # Select the file
        self.editor.tree_widget.setCurrentItem(self.file_item1)
        
        # Get initial count
        initial_count = self.folder_item.childCount()
        self.assertEqual(initial_count, 3, "Folder should have 3 children initially")
        
        # Create a delete key event
        delete_event = QKeyEvent(QEvent.KeyPress, Qt.Key_Delete, Qt.NoModifier)
        
        # Send the event
        self.editor._handle_key_press(delete_event)
        
        # Check that the file was deleted
        final_count = self.folder_item.childCount()
        self.assertEqual(final_count, 2, "Folder should have 2 children after file deletion")
        
    def test_use_project_name(self):
        """Test using project name for a file"""
        # Select the file
        self.editor.tree_widget.setCurrentItem(self.file_item2)
        
        # Call the method directly
        self.editor._use_project_name_for_file(self.file_item2)
        
        # Check that the file now uses the project name
        file_data = self.file_item2.data(0, Qt.UserRole)
        self.assertTrue(file_data.get('uses_project_name', False), "File should be marked to use project name")
        
        # Check the file name has been updated
        self.assertEqual(self.file_item2.text(0), "Test_Template.txt", "File name should be updated to use the template name")
        
        # Check styling is applied (font is italic)
        self.assertTrue(self.file_item2.font(0).italic(), "Font should be italic for files using project name")
        
    def test_file_operations_delete(self):
        """Test deletion using the FileOperations class"""
        # Select the file
        self.editor.tree_widget.setCurrentItem(self.file_item1)
        
        # Call the delete_selected method in file_operations
        result = self.editor.file_operations.delete_selected()
        
        # Check that the method returns True
        self.assertTrue(result, "FileOperations.delete_selected should return True when deletion is successful")
        
        # Check that the file was deleted
        final_count = self.folder_item.childCount()
        self.assertEqual(final_count, 2, "Folder should have 2 children after file deletion")
        
    def test_file_operations_use_project_name(self):
        """Test use project name using the FileOperations class"""
        # Select the file
        self.editor.tree_widget.setCurrentItem(self.file_item2)
        
        # Call the _use_project_name_for_file method in file_operations
        result = self.editor.file_operations._use_project_name_for_file(self.file_item2)
        
        # Check that the method returns True
        self.assertTrue(result, "FileOperations._use_project_name_for_file should return True when successful")
        
        # Check that the file now uses the project name
        file_data = self.file_item2.data(0, Qt.UserRole)
        self.assertTrue(file_data.get('uses_project_name', False), "File should be marked to use project name")
        
        # Check the file name has been updated
        self.assertEqual(self.file_item2.text(0), "Test_Template.txt", "File name should be updated to use the template name")

if __name__ == "__main__":
    unittest.main() 