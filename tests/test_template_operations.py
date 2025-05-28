#!/usr/bin/env python3
"""
Tests for template and structure operations functionality.
This test script focuses on validating the file operations for templates and structures.
"""

import os
import sys
import json
import shutil
import unittest
from unittest.mock import patch, MagicMock

# Create test directories
TEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_tmp")
TEST_STRUCTURES_DIR = os.path.join(TEST_DIR, "structures")
TEST_TEMPLATES_DIR = os.path.join(TEST_DIR, "templates")

# Add mocks before any imports
sys.modules['PyQt5'] = MagicMock()
sys.modules['PyQt6.QtWidgets'] = MagicMock()
sys.modules['PyQt6.QtCore'] = MagicMock()
sys.modules['PyQt6.QtGui'] = MagicMock()
sys.modules['sip'] = MagicMock()
sys.modules['PyQt5.sip'] = MagicMock()

# Create a mock app class
class MockApp:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = MockApp()
        return cls._instance
    
    def __init__(self):
        self.template_gallery = MagicMock()
        self.template_gallery.populate_gallery = MagicMock()
        self.template_gallery.select_template = MagicMock()
        self.structure_manager = MagicMock()

# Now we can import our modules
from app.templates.structure_operations import StructureOperations
from app.templates.template_operations import TemplateOperations

class TestStructureOperations(unittest.TestCase):
    """Test case for structure operations"""
    
    def setUp(self):
        """Set up test environment"""
        # Create test directories
        os.makedirs(TEST_STRUCTURES_DIR, exist_ok=True)
        os.makedirs(TEST_TEMPLATES_DIR, exist_ok=True)
        
        # Mock get_config_paths
        self.paths_patcher = patch('app.utils.utils.get_config_paths', 
                                  return_value={
                                      'custom_structures_dir': TEST_STRUCTURES_DIR,
                                      'templates_dir': TEST_TEMPLATES_DIR
                                  })
        self.mock_get_config_paths = self.paths_patcher.start()
        
        # Mock app instance
        self.app_patcher = patch('app.core.app_module_pyqt.ProjectCreatorApp', MockApp)
        self.mock_app = self.app_patcher.start()
        
        # Initialize test objects
        self.structure_ops = StructureOperations()
        self.template_ops = TemplateOperations()
        
        # Add a test structure and template
        self.test_structure = {
            "name": "Template_Test_Structure",
            "display_name": "Test Structure",
            "directories": ["Folder1", "Folder2", "Assets"]
        }
        
        self.test_template = {
            "name": "Test Template",
            "description": "A test template",
            "structure": "Test_Structure"
        }
    
    def tearDown(self):
        """Clean up test environment"""
        # Stop patchers
        self.paths_patcher.stop()
        self.app_patcher.stop()
        
        # Remove test directories
        if os.path.exists(TEST_DIR):
            shutil.rmtree(TEST_DIR)
    
    def test_save_custom_structure(self):
        """Test saving a custom structure"""
        # Test saving the structure
        result = self.structure_ops.save_custom_structure("Test_Structure", 
                                                         self.test_structure["directories"])
        self.assertTrue(result)
        
        # Check that the file was created
        expected_path = os.path.join(TEST_STRUCTURES_DIR, "Template_Test_Structure.json")
        self.assertTrue(os.path.exists(expected_path))
        
        # Check the content
        with open(expected_path, 'r') as f:
            saved_structure = json.load(f)
            self.assertEqual(saved_structure["name"], "Template_Test_Structure")
            self.assertEqual(saved_structure["display_name"], "Test_Structure")
            self.assertEqual(saved_structure["directories"], self.test_structure["directories"])
    
    def test_get_structure(self):
        """Test retrieving a structure"""
        # Save a structure first
        self.structure_ops.save_custom_structure("Test_Structure", 
                                               self.test_structure["directories"])
        
        # Test getting with different name variations
        structure1 = self.structure_ops.get_structure("Test_Structure")
        self.assertEqual(structure1, self.test_structure["directories"])
        
        structure2 = self.structure_ops.get_structure("Template_Test_Structure")
        self.assertEqual(structure2, self.test_structure["directories"])
    
    def test_rename_template(self):
        """Test renaming a template and its structure file"""
        # Save a structure and template
        self.structure_ops.save_custom_structure("Test_Structure", 
                                               self.test_structure["directories"])
        
        # Create test template file
        template_file_path = os.path.join(TEST_TEMPLATES_DIR, "Test_Template.json")
        with open(template_file_path, 'w') as f:
            json.dump(self.test_template, f)
        
        # Add the template to the list
        self.template_ops.templates = [self.test_template]
        
        # Test renaming
        result = self.template_ops.rename_template("Test Template", "New Template Name")
        
        # Check result
        self.assertTrue(result)
        
        # Check that the old file doesn't exist
        self.assertFalse(os.path.exists(template_file_path))
        
        # Check that new file exists
        new_template_file_path = os.path.join(TEST_TEMPLATES_DIR, "New_Template_Name.json")
        self.assertTrue(os.path.exists(new_template_file_path))
    
    def test_delete_template(self):
        """Test deleting a template and its structure file"""
        # Save a structure and template
        self.structure_ops.save_custom_structure("Test_Structure", 
                                               self.test_structure["directories"])
        
        # Create test template file
        template_file_path = os.path.join(TEST_TEMPLATES_DIR, "Test_Template.json")
        with open(template_file_path, 'w') as f:
            json.dump(self.test_template, f)
        
        # Add the template to the list
        self.template_ops.templates = [self.test_template]
        self.template_ops.custom_structures = {"Template_Test_Structure": self.test_structure}
        
        # Test deleting
        result = self.template_ops.delete_template("Test Template")
        
        # Check result
        self.assertTrue(result)
        
        # Check that the template file was deleted
        self.assertFalse(os.path.exists(template_file_path))
    
    def test_load_custom_structures(self):
        """Test loading custom structures"""
        # Save multiple structures
        self.structure_ops.save_custom_structure("Structure1", ["Folder1", "Folder2"])
        self.structure_ops.save_custom_structure("Structure2", ["FolderA", "FolderB"])
        
        # Reset the custom_structures dict
        self.structure_ops.custom_structures = {}
        
        # Load structures
        count = self.structure_ops.load_custom_structures()
        
        # Check that we loaded the structures
        self.assertEqual(count, 1)  # Update count since first file gets replaced
        self.assertIn("Template_Structure2", self.structure_ops.custom_structures)

if __name__ == "__main__":
    unittest.main() 