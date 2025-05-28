#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test the rename_flag functionality for file renaming during project creation.
This tests that files are properly renamed when rename_flag is set, and verifies
backward compatibility with uses_project_name.
"""

import os
import sys
import unittest
import tempfile
import shutil
import json
from PyQt6.QtWidgets import QApplication, QTreeWidgetItem
from PyQt6.QtCore import Qt

# Add project directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import necessary modules
from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.ui.structure_editor.structure_converter import StructureConverter
from app.core.project_builder import ProjectBuilder

class TestRenameFlag(unittest.TestCase):
    """Test the rename_flag functionality for file renaming."""
    
    @classmethod
    def setUpClass(cls):
        # Create QApplication instance if it doesn't exist
        cls.app = QApplication.instance() or QApplication(sys.argv)
        
        # Create a temporary directory for test files
        cls.temp_dir = tempfile.mkdtemp()
        
        # Create test file
        cls.test_file_path = os.path.join(cls.temp_dir, "test_file.txt")
        with open(cls.test_file_path, 'w') as f:
            f.write("Test file content")
    
    @classmethod
    def tearDownClass(cls):
        # Clean up temporary directory
        shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        # Create an enhanced structure editor for each test
        self.editor = EnhancedStructureEditor(
            parent=None,
            structure_name="Test_Template",
            is_new=True,
            structure=None,
            project_type=None
        )
        self.editor.template_name = "Test_Template"
        
        # Create test structure
        self.root_item = self.editor.tree_widget.invisibleRootItem()
        
        # Add a root folder
        self.project_folder = QTreeWidgetItem(self.root_item)
        self.project_folder.setText(0, "Project Folder")
        self.project_folder.setData(0, Qt.ItemDataRole.UserRole, {"type": "folder", "name": "Project Folder"})
        
        # Add files to the folder with specific names for testing
        self.file_item1 = QTreeWidgetItem(self.project_folder)
        self.file_item1.setText(0, "regular_file.txt")
        self.file_item1.setData(0, Qt.ItemDataRole.UserRole, {"type": "file", "name": "regular_file.txt", "path": self.test_file_path})
        
        self.file_item2 = QTreeWidgetItem(self.project_folder)
        self.file_item2.setText(0, "renamed_file.prproj")
        self.file_item2.setData(0, Qt.ItemDataRole.UserRole, {"type": "file", "name": "renamed_file.prproj", "path": self.test_file_path})
        
        self.file_item3 = QTreeWidgetItem(self.project_folder)
        self.file_item3.setText(0, "legacy_file.txt")
        self.file_item3.setData(0, Qt.ItemDataRole.UserRole, {"type": "file", "name": "legacy_file.txt", "path": self.test_file_path})
    
    def tearDown(self):
        # Clean up the editor
        self.editor.close()
    
    def test_rename_flag_prioritized(self):
        """Test that rename_flag is prioritized over uses_project_name."""
        # Set up item data with different flag combinations
        item_data = self.file_item2.data(0, Qt.ItemDataRole.UserRole)
        item_data['rename_flag'] = True
        item_data['uses_project_name'] = False  # uses_project_name is false but rename_flag is true
        item_data['original_name'] = "renamed_file.prproj"
        self.file_item2.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Convert to structure
        converter = StructureConverter(tree_widget=self.editor.tree_widget)
        structure = converter.get_structure()
        
        # Find the item in the structure
        file_item = None
        project_folder = structure[0]  # First item should be our project folder
        for child in project_folder.get('children', []):
            if child.get('name') == "renamed_file.prproj":
                file_item = child
                break
                
        self.assertIsNotNone(file_item, "File item not found in structure")
        
        # Verify both flags are set correctly in the structure
        self.assertTrue(file_item.get('rename_flag', False), "rename_flag should be true")
        
        # Create a temporary output directory for the test project
        output_dir = tempfile.mkdtemp()
        try:
            # Create a project builder
            project_builder = ProjectBuilder(None)
            
            # Create a project with the structure
            project_name = "TestProject123"
            placeholders = {"PROJECT_NAME": project_name}
            
            # Process the structure
            project_path = os.path.join(output_dir, project_name)
            os.makedirs(project_path, exist_ok=True)
            
            # Process the structure to create the project
            project_builder._create_folder_structure(project_path, structure, placeholders)
            
            # Check that the file with rename_flag=True exists with the project name
            renamed_file_path = os.path.join(project_path, "Project Folder", f"{project_name}.prproj")
            self.assertTrue(os.path.exists(renamed_file_path), 
                           "File should exist with the project name due to rename_flag=True")
                           
        finally:
            # Clean up the output directory
            shutil.rmtree(output_dir)
    
    def test_uses_project_name_backward_compatibility(self):
        """Test backward compatibility with uses_project_name."""
        # Set up item data with only uses_project_name set
        item_data = self.file_item3.data(0, Qt.ItemDataRole.UserRole)
        item_data['uses_project_name'] = True  # Only uses_project_name is true
        item_data['rename_flag'] = False  # Explicitly set rename_flag to false
        item_data['original_name'] = "legacy_file.txt"
        self.file_item3.setData(0, Qt.ItemDataRole.UserRole, item_data)
        
        # Convert to structure
        converter = StructureConverter(tree_widget=self.editor.tree_widget)
        structure = converter.get_structure()
        
        # Create a temporary output directory for the test project
        output_dir = tempfile.mkdtemp()
        try:
            # Create a project builder
            project_builder = ProjectBuilder(None)
            
            # Create a project with the structure
            project_name = "LegacyTest"
            placeholders = {"PROJECT_NAME": project_name}
            
            # Process the structure
            project_path = os.path.join(output_dir, project_name)
            os.makedirs(project_path, exist_ok=True)
            
            # Process the structure to create the project
            project_builder._create_folder_structure(project_path, structure, placeholders)
            
            # Check that the file with uses_project_name=True but rename_flag=False 
            # still gets renamed for backward compatibility
            legacy_file_path = os.path.join(project_path, "Project Folder", f"{project_name}.txt")
            self.assertTrue(os.path.exists(legacy_file_path), 
                           "File should be renamed based on uses_project_name for backward compatibility")
                           
        finally:
            # Clean up the output directory
            shutil.rmtree(output_dir)
    
    def test_toggling_sets_both_flags(self):
        """Test that toggling project name sets both flags correctly."""
        # Toggle project name on
        self.editor._toggle_project_name_for_file(self.file_item1)
        
        # Check that both flags are set
        item_data = self.file_item1.data(0, Qt.ItemDataRole.UserRole)
        self.assertTrue(item_data.get('rename_flag', False),
                      "rename_flag should be set when toggling on")
        self.assertTrue(item_data.get('uses_project_name', False),
                      "uses_project_name should be set when toggling on")
        
        # Toggle project name off
        self.editor._toggle_project_name_for_file(self.file_item1)
        
        # Check that both flags are cleared
        item_data = self.file_item1.data(0, Qt.ItemDataRole.UserRole)
        self.assertFalse(item_data.get('rename_flag', True),
                       "rename_flag should be cleared when toggling off")
        self.assertFalse(item_data.get('uses_project_name', True),
                       "uses_project_name should be cleared when toggling off")

if __name__ == '__main__':
    unittest.main() 