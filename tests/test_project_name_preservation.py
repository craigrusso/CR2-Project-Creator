#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test the preservation of original filenames in templates when using the 'Use Project Name' feature.
Verifies that the original filename is preserved in the JSON structure, and that
the project name is correctly applied during project creation.
"""

import os
import sys
import unittest
import tempfile
import shutil
import json
from PyQt5.QtWidgets import QApplication, QTreeWidgetItem
from PyQt5.QtCore import Qt

# Add project directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import necessary modules
from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.ui.structure_editor.structure_converter import StructureConverter
from app.core.project_builder import ProjectBuilder

class TestProjectNamePreservation(unittest.TestCase):
    """Test that original filenames are preserved in templates when using project name substitution"""
    
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
        self.project_folder.setData(0, Qt.UserRole, {"type": "folder", "name": "Project Folder"})
        
        # Add files to the folder with specific names for testing
        self.file_item1 = QTreeWidgetItem(self.project_folder)
        self.file_item1.setText(0, "original_file.txt")
        self.file_item1.setData(0, Qt.UserRole, {"type": "file", "name": "original_file.txt", "path": self.test_file_path})
        
        self.file_item2 = QTreeWidgetItem(self.project_folder)
        self.file_item2.setText(0, "project_name_file.prproj")
        self.file_item2.setData(0, Qt.UserRole, {"type": "file", "name": "project_name_file.prproj", "path": self.test_file_path})
    
    def tearDown(self):
        # Clean up the editor
        self.editor.close()
    
    def test_original_name_preserved_in_structure(self):
        """Test that the original filename is preserved in the structure data"""
        # Set the file to use project name
        self.editor._use_project_name_for_file(self.file_item2)
        
        # Convert to structure
        converter = StructureConverter(tree_widget=self.editor.tree_widget)
        structure = converter.get_structure()
        
        # Find the file in the structure
        file_item = None
        project_folder = structure[0]  # First item should be our project folder
        for child in project_folder.get('children', []):
            if child.get('uses_project_name', False):
                file_item = child
                break
                
        self.assertIsNotNone(file_item, "File with uses_project_name flag not found in structure")
        
        # Check that the name field still contains the original filename
        self.assertEqual(file_item.get('name'), "project_name_file.prproj", 
                        "Original filename should be preserved in the name field")
        
        # Check that the uses_project_name flag is set
        self.assertTrue(file_item.get('uses_project_name', False),
                      "uses_project_name flag should be set")
                      
        # Convert structure to JSON and back to simulate saving and loading template
        structure_json = json.dumps(structure)
        loaded_structure = json.loads(structure_json)
        
        # Find the file in the loaded structure
        loaded_file_item = None
        loaded_project_folder = loaded_structure[0]
        for child in loaded_project_folder.get('children', []):
            if child.get('uses_project_name', False):
                loaded_file_item = child
                break
                
        self.assertIsNotNone(loaded_file_item, "File with uses_project_name flag not found in loaded structure")
        
        # Check that the name field still contains the original filename after JSON conversion
        self.assertEqual(loaded_file_item.get('name'), "project_name_file.prproj", 
                        "Original filename should be preserved after JSON conversion")
    
    def test_project_creation_with_preserved_names(self):
        """Test that project creation correctly applies the project name while preserving the original name in structure"""
        # Set the file to use project name
        self.editor._use_project_name_for_file(self.file_item2)
        
        # Set data on file_item1 to ensure it doesn't use project name
        item_data1 = self.file_item1.data(0, Qt.UserRole)
        item_data1['uses_project_name'] = False
        item_data1['rename_flag'] = False
        self.file_item1.setData(0, Qt.UserRole, item_data1)
        
        # Convert to structure
        converter = StructureConverter(tree_widget=self.editor.tree_widget)
        structure = converter.get_structure()
        
        # Create a temporary output directory for the test project
        output_dir = tempfile.mkdtemp()
        try:
            # Create a project builder
            builder = ProjectBuilder(None)
            
            # Create a project with the structure
            project_name = "TestProject123"
            placeholders = {"PROJECT_NAME": project_name}
            
            # Process the structure
            project_path = os.path.join(output_dir, project_name)
            os.makedirs(project_path, exist_ok=True)
            
            # Process the structure to create the project
            builder._create_folder_structure(project_path, structure, placeholders)
            
            # Check that the file with uses_project_name=True exists with the project name
            project_name_file_path = os.path.join(project_path, "Project Folder", f"{project_name}.prproj")
            self.assertTrue(os.path.exists(project_name_file_path), 
                           "File should exist with the project name")
                           
            # Verify the original name is still in the structure data
            for item in structure:
                if item.get('name') == "Project Folder":
                    for child in item.get('children', []):
                        if child.get('uses_project_name', False):
                            self.assertEqual(child.get('name'), "project_name_file.prproj",
                                          "Original filename should still be in the structure data")
                            
        finally:
            # Clean up the output directory
            shutil.rmtree(output_dir)
            
    def test_toggling_preserves_original_name(self):
        """Test that toggling between project name and original name preserves the original name"""
        # Set the file to use project name
        self.editor._use_project_name_for_file(self.file_item2)
        
        # Get the item data
        item_data = self.file_item2.data(0, Qt.UserRole)
        self.assertTrue(item_data.get('uses_project_name', False),
                      "uses_project_name flag should be set")
        
        # Check the visual display shows the placeholder
        self.assertEqual(self.file_item2.text(0), "${PROJECT_NAME}.prproj",
                        "Display should show the placeholder")
        
        # Original name should be stored in the data
        self.assertEqual(item_data.get('original_name'), "project_name_file.prproj",
                        "Original name should be stored in the data")
        
        # Toggle back to original name
        self.editor._toggle_project_name_for_file(self.file_item2)
        
        # Get updated item data
        item_data = self.file_item2.data(0, Qt.UserRole)
        self.assertFalse(item_data.get('uses_project_name', True),
                       "uses_project_name flag should be turned off")
        
        # Display should show original name
        self.assertEqual(self.file_item2.text(0), "project_name_file.prproj",
                        "Display should show the original name")
        
        # Toggle back to project name
        self.editor._toggle_project_name_for_file(self.file_item2)
        
        # Get updated item data
        item_data = self.file_item2.data(0, Qt.UserRole)
        self.assertTrue(item_data.get('uses_project_name', False),
                      "uses_project_name flag should be set again")
        
        # Display should show placeholder
        self.assertEqual(self.file_item2.text(0), "${PROJECT_NAME}.prproj",
                        "Display should show the placeholder again")

    def test_rename_flag_matches_uses_project_name(self):
        """Test that rename_flag is set to true when uses_project_name is set to true"""
        # Set the file to use project name
        self.editor._use_project_name_for_file(self.file_item2)
        
        # Get the item data
        item_data = self.file_item2.data(0, Qt.UserRole)
        
        # Check that uses_project_name is set to true
        self.assertTrue(item_data.get('uses_project_name', False),
                      "uses_project_name flag should be set")
        
        # Check that rename_flag is also set to true
        self.assertTrue(item_data.get('rename_flag', False),
                      "rename_flag should be set when uses_project_name is set")
        
        # Toggle back to original name
        self.editor._toggle_project_name_for_file(self.file_item2)
        
        # Get updated item data
        item_data = self.file_item2.data(0, Qt.UserRole)
        
        # Check that uses_project_name is set to false
        self.assertFalse(item_data.get('uses_project_name', True),
                       "uses_project_name flag should be turned off")
        
        # Check that rename_flag is also set to false
        self.assertFalse(item_data.get('rename_flag', True),
                       "rename_flag should be false when uses_project_name is false")
        
        # Toggle back to project name
        self.editor._toggle_project_name_for_file(self.file_item2)
        
        # Get updated item data
        item_data = self.file_item2.data(0, Qt.UserRole)
        
        # Check that both flags are set to true again
        self.assertTrue(item_data.get('uses_project_name', False),
                      "uses_project_name flag should be set again")
        self.assertTrue(item_data.get('rename_flag', False),
                      "rename_flag should be set again")

    def test_flags_preserved_in_template_json(self):
        """Test that both uses_project_name and rename_flag are properly saved and loaded from template JSON"""
        # Set up a temporary directory for the test
        test_dir = tempfile.mkdtemp()
        try:
            # Set the file to use project name
            self.editor._use_project_name_for_file(self.file_item2)
            
            # Get item data
            item_data = self.file_item2.data(0, Qt.UserRole)
            
            # Verify both flags are set
            self.assertTrue(item_data.get('uses_project_name', False), 
                           "uses_project_name should be set to true")
            self.assertTrue(item_data.get('rename_flag', False), 
                           "rename_flag should be set to true")
            
            # Convert to structure and save to JSON file
            converter = StructureConverter(tree_widget=self.editor.tree_widget)
            structure = converter.get_structure()
            
            # Save structure to JSON file
            json_path = os.path.join(test_dir, "test_template.json")
            with open(json_path, 'w') as f:
                template = {
                    "name": "Test Template",
                    "structure": structure,
                    "description": "Test template with project name flags"
                }
                json.dump(template, f, indent=2)
            
            # Load the JSON back
            with open(json_path, 'r') as f:
                loaded_template = json.load(f)
            
            # Find the file in the loaded structure
            loaded_file_item = None
            loaded_structure = loaded_template['structure']
            
            # Navigate the structure to find our file
            project_folder = loaded_structure[0]  # First item should be our project folder
            for child in project_folder.get('children', []):
                if child.get('type') == 'file' and child.get('uses_project_name', False):
                    loaded_file_item = child
                    break
                    
            self.assertIsNotNone(loaded_file_item, "Could not find file with uses_project_name flag in loaded template")
            
            # Verify both flags are preserved in the loaded JSON
            self.assertTrue(loaded_file_item.get('uses_project_name', False), 
                           "uses_project_name flag should be preserved in template JSON")
            self.assertTrue(loaded_file_item.get('rename_flag', False), 
                           "rename_flag flag should be preserved in template JSON")
            
            # Verify original_name is also preserved
            self.assertEqual(loaded_file_item.get('name'), "project_name_file.prproj",
                           "Original file name should be preserved in JSON")
                           
        finally:
            # Clean up the temporary directory
            shutil.rmtree(test_dir)

if __name__ == '__main__':
    unittest.main() 