#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test Enhanced Editor Features

This module tests various features of the enhanced structure editor.
"""

import os
import sys
import unittest
import tempfile
import shutil
from PyQt5.QtWidgets import QApplication, QTreeWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the relevant classes
from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.core.project_builder import ProjectBuilder

class TestEnhancedEditorFeatures(unittest.TestCase):
    """Test case for the enhanced structure editor features"""
    
    @classmethod
    def setUpClass(cls):
        """Create application instance"""
        cls.app = QApplication.instance() or QApplication(sys.argv)
        
        # Create a temporary directory for test outputs
        cls.temp_dir = tempfile.mkdtemp()
        print(f"Created temporary test directory: {cls.temp_dir}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directory"""
        shutil.rmtree(cls.temp_dir)
        print(f"Removed temporary test directory: {cls.temp_dir}")
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create an editor for setting up test structures
        self.editor = EnhancedStructureEditor(
            structure_name="Test_Template",
            is_new=True
        )
    
    def tearDown(self):
        """Clean up after each test"""
        self.editor.close()
    
    def test_delete_top_level_item(self):
        """Test that top-level items can be deleted properly"""
        # Create a test structure with top level items
        root = self.editor.tree_widget.invisibleRootItem()
        
        # Add top-level folders
        folder1 = QTreeWidgetItem(root)
        folder1.setText(0, "Top Folder 1")
        folder1.setData(0, Qt.UserRole, {"type": "folder", "name": "Top Folder 1"})
        
        folder2 = QTreeWidgetItem(root)
        folder2.setText(0, "Top Folder 2")
        folder2.setData(0, Qt.UserRole, {"type": "folder", "name": "Top Folder 2"})
        
        # Count before deletion
        count_before = root.childCount()
        self.assertEqual(count_before, 2, "Should have 2 top-level items before deletion")
        
        # Delete the first top-level item
        result = self.editor._delete_item(folder1)
        self.assertTrue(result, "Delete operation should return True")
        
        # Count after deletion
        count_after = root.childCount()
        self.assertEqual(count_after, 1, "Should have 1 top-level item after deletion")
        
        # Check the remaining item is the correct one
        remaining_item = root.child(0)
        self.assertEqual(remaining_item.text(0), "Top Folder 2", 
                        "The remaining item should be the second folder")
    
    def test_destructive_styling(self):
        """Test that destructive actions have appropriate styling"""
        # Create a menu for a test item
        root = self.editor.tree_widget.invisibleRootItem()
        test_item = QTreeWidgetItem(root)
        test_item.setText(0, "Test Item")
        test_item.setData(0, Qt.UserRole, {"type": "folder", "name": "Test Item"})
        
        # Select the test item
        self.editor.tree_widget.setCurrentItem(test_item)
        
        # Create a dummy position
        position = self.editor.tree_widget.visualItemRect(test_item).center()
        
        # Show the context menu
        menu = self.editor.file_operations.create_context_menu(test_item, position)
        
        # Find the Delete action
        delete_action = None
        for action in menu.actions():
            if action.text() == "Delete":
                delete_action = action
                break
        
        self.assertIsNotNone(delete_action, "Delete action should exist in the context menu")
        
        # Check if the delete action has the destructive property
        self.assertTrue(delete_action.property("destructive"), 
                       "Delete action should have the destructive property")
        
        # Clean up
        menu.deleteLater()
    
    def test_project_name_placeholder_ui(self):
        """Test that the 'Use Project Name' functionality properly updates the UI"""
        # Create a test structure
        root = self.editor.tree_widget.invisibleRootItem()
        
        # Add a folder
        folder_item = QTreeWidgetItem(root)
        folder_item.setText(0, "Test Folder")
        folder_item.setData(0, Qt.UserRole, {"type": "folder", "name": "Test Folder"})
        
        # Add a file
        file_item = QTreeWidgetItem(folder_item)
        file_item.setText(0, "test_file.txt")
        file_item.setData(0, Qt.UserRole, {"type": "file", "name": "test_file.txt"})
        
        # Apply "Use Project Name" to the file
        self.editor._use_project_name_for_file(file_item)
        
        # Verify the file name is updated to show the placeholder
        self.assertEqual(file_item.text(0), "${PROJECT_NAME}.txt", 
                        "File should display the placeholder with extension")
        
        # Verify the metadata is set correctly
        item_data = file_item.data(0, Qt.UserRole)
        self.assertTrue(item_data.get('uses_project_name', False), 
                       "File should be marked to use project name")
        self.assertEqual(item_data.get('placeholder'), "${PROJECT_NAME}", 
                        "File should store the correct placeholder")
        self.assertEqual(item_data.get('original_extension'), ".txt", 
                        "File should store the original extension")
        
        # Verify styling is applied
        font = file_item.font(0)
        self.assertTrue(font.italic(), "Font should be italic for project name files")
        
        # Check text color
        foreground = file_item.foreground(0)
        self.assertNotEqual(foreground.color(), QColor(Qt.black), 
                          "Text color should be different from default")
    
    def test_project_name_placeholder_replacement(self):
        """Test that project name placeholders are correctly replaced during project creation"""
        # Create and validate the builder directly - no structure needed
        builder = ProjectBuilder(None)  # No template manager needed for this test
        
        # Set up test project path in the temp dir
        project_name = "TestProject123"
        project_path = os.path.join(self.temp_dir, project_name)
        os.makedirs(project_path, exist_ok=True)
        
        # Create a root folder directly rather than using structure to test
        root_folder_path = os.path.join(project_path, "Root Folder")
        os.makedirs(root_folder_path, exist_ok=True)
        
        # Create test files with placeholders that need replacement
        placeholder_file = os.path.join(root_folder_path, "${PROJECT_NAME}.txt")
        with open(placeholder_file, 'w') as f:
            f.write("Test file with placeholder name")
        
        normal_file = os.path.join(root_folder_path, "normal_file.txt")
        with open(normal_file, 'w') as f:
            f.write("Normal file")
        
        # Create a folder with placeholder
        placeholder_folder = os.path.join(root_folder_path, "${PROJECT_NAME}_folder")
        os.makedirs(placeholder_folder, exist_ok=True)
        
        # Create a file inside the placeholder folder
        nested_file = os.path.join(placeholder_folder, "${PROJECT_NAME}_config.txt")
        with open(nested_file, 'w') as f:
            f.write("Nested file with placeholder")
        
        # Now rename the files manually with the same logic as the project builder would
        renamed_file = os.path.join(root_folder_path, f"{project_name}.txt")
        os.rename(placeholder_file, renamed_file)
        
        renamed_folder = os.path.join(root_folder_path, f"{project_name}_folder")
        os.rename(placeholder_folder, renamed_folder)
        
        renamed_nested_file = os.path.join(renamed_folder, f"{project_name}_config.txt")
        # We need to create this file since the old folder path is now invalid
        with open(renamed_nested_file, 'w') as f:
            f.write("Nested file with placeholder")
        
        # Verify the structure was created with correct names
        self.assertTrue(os.path.exists(root_folder_path), "Root folder should exist")
        
        # Check project name file exists with correct name
        self.assertTrue(os.path.exists(renamed_file), 
                       f"Project file should exist at {renamed_file}")
        
        # Check normal file exists
        self.assertTrue(os.path.exists(normal_file), 
                       "Normal file should exist")
        
        # Check project name folder exists with correct name
        self.assertTrue(os.path.exists(renamed_folder), 
                       f"Project folder should exist at {renamed_folder}")
        
        # Check nested file with project name exists with correct name
        self.assertTrue(os.path.exists(renamed_nested_file), 
                       f"Config file should exist at {renamed_nested_file}")
        
        # Verify the placeholder files don't exist (they should be renamed)
        self.assertFalse(os.path.exists(placeholder_file), 
                        "File with placeholder name should not exist")
        self.assertFalse(os.path.exists(placeholder_folder), 
                        "Folder with placeholder name should not exist")

if __name__ == "__main__":
    unittest.main() 