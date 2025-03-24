#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test the ability to toggle between using project name and original file name
in the template structure.
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

class TestProjectNameToggle(unittest.TestCase):
    """Test toggling between using project name and original file name"""
    
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
        
        # Add files to the folder
        self.file_item1 = QTreeWidgetItem(self.project_folder)
        self.file_item1.setText(0, "normal_file.txt")
        self.file_item1.setData(0, Qt.UserRole, {"type": "file", "name": "normal_file.txt", "path": self.test_file_path})
        
        self.file_item2 = QTreeWidgetItem(self.project_folder)
        self.file_item2.setText(0, "toggle_file.txt")
        self.file_item2.setData(0, Qt.UserRole, {"type": "file", "name": "toggle_file.txt", "path": self.test_file_path})
    
    def tearDown(self):
        # Clean up the editor
        self.editor.close()
    
    def test_toggle_project_name(self):
        """Test toggling between using project name and original file name"""
        # First, set a file to use project name
        result = self.editor._use_project_name_for_file(self.file_item2)
        self.assertTrue(result, "Setting file to use project name should succeed")
        
        # Check that file is marked to use project name
        file_data = self.file_item2.data(0, Qt.UserRole)
        self.assertTrue(file_data.get('uses_project_name', False), "File should be marked to use project name")
        self.assertEqual(file_data.get('original_name'), "toggle_file.txt", "Original name should be stored")
        
        # Now toggle back to original name
        result = self.editor._toggle_project_name_for_file(self.file_item2)
        self.assertTrue(result, "Toggling file name should succeed")
        
        # Check that file is no longer using project name
        file_data = self.file_item2.data(0, Qt.UserRole)
        self.assertFalse(file_data.get('uses_project_name', True), "File should no longer be marked to use project name")
        self.assertEqual(self.file_item2.text(0), "toggle_file.txt", "File name should be restored to original")
        
        # Toggle again to use project name
        result = self.editor._toggle_project_name_for_file(self.file_item2)
        self.assertTrue(result, "Toggling file name should succeed")
        
        # Check that file is using project name again
        file_data = self.file_item2.data(0, Qt.UserRole)
        self.assertTrue(file_data.get('uses_project_name', False), "File should be marked to use project name again")
    
    def test_structure_conversion(self):
        """Test converting the structure with toggled file names"""
        # Set one file to use project name
        self.editor._use_project_name_for_file(self.file_item2)
        
        # Convert the structure to data
        converter = StructureConverter(tree_widget=self.editor.tree_widget)
        structure = converter.get_structure()
        
        # Structure should be list of items
        self.assertIsInstance(structure, list, "Structure should be a list")
        
        # Find the project folder
        project_folder = None
        for item in structure:
            if isinstance(item, dict) and item.get('name') == "Project Folder":
                project_folder = item
                break
        
        self.assertIsNotNone(project_folder, "Project folder should be in the structure")
        
        # Check the children of the project folder
        children = project_folder.get('children', [])
        self.assertEqual(len(children), 2, "Project folder should have 2 children")
        
        # Find normal file and toggle file
        normal_file = None
        toggle_file = None
        for child in children:
            if child.get('name') == "normal_file.txt":
                normal_file = child
            elif child.get('uses_project_name', False):
                toggle_file = child
        
        self.assertIsNotNone(normal_file, "Normal file should be in the structure")
        self.assertIsNotNone(toggle_file, "Toggle file should be in the structure")
        
        # Check that toggle file has the uses_project_name flag
        self.assertTrue(toggle_file.get('uses_project_name', False), "Toggle file should have uses_project_name flag")
        
        # Check that original_name is stored
        self.assertEqual(toggle_file.get('original_name'), "toggle_file.txt", "Original name should be stored")
    
    def test_project_creation(self):
        """Test creating a project with toggled file names"""
        # Set one file to use project name
        self.editor._use_project_name_for_file(self.file_item2)
        
        # Convert the structure to data
        converter = StructureConverter(tree_widget=self.editor.tree_widget)
        structure = converter.get_structure()
        
        # Create a temporary output directory
        output_dir = tempfile.mkdtemp()
        try:
            # Create a project builder
            builder = ProjectBuilder(None)
            
            # Create a project with the structure
            project_name = "TestProject123"
            project_path = os.path.join(output_dir, project_name)
            
            # Create placeholders
            placeholders = {"PROJECT_NAME": project_name}
            
            # Process the structure
            os.makedirs(project_path, exist_ok=True)
            for item in structure:
                # Create folders from structure
                if isinstance(item, dict) and item.get('type') == 'folder':
                    folder_name = item.get('name')
                    folder_path = os.path.join(project_path, folder_name)
                    os.makedirs(folder_path, exist_ok=True)
                    
                    # Process children
                    for child in item.get('children', []):
                        if isinstance(child, dict) and child.get('type') == 'file':
                            # Process file based on whether it uses project name
                            if child.get('uses_project_name', False):
                                # Use project name for file
                                extension = ""
                                if 'original_extension' in child:
                                    extension = child.get('original_extension')
                                elif '.' in child.get('name', ''):
                                    name_parts = child.get('name', '').split('.')
                                    extension = f".{name_parts[-1]}"
                                
                                file_name = f"{project_name}{extension}"
                            else:
                                # Use original file name
                                file_name = child.get('name')
                            
                            # Create the file
                            file_path = os.path.join(folder_path, file_name)
                            with open(file_path, 'w') as f:
                                f.write("Test content")
            
            # Check that the normal file exists with its original name
            normal_file_path = os.path.join(project_path, "Project Folder", "normal_file.txt")
            self.assertTrue(os.path.exists(normal_file_path), "Normal file should exist with its original name")
            
            # Check that the toggle file exists with the project name
            toggle_file_path = os.path.join(project_path, "Project Folder", f"{project_name}.txt")
            self.assertTrue(os.path.exists(toggle_file_path), "Toggle file should exist with the project name")
            
        finally:
            # Clean up the output directory
            shutil.rmtree(output_dir)

if __name__ == '__main__':
    unittest.main() 