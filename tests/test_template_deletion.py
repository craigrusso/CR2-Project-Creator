#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test the template deletion functionality to ensure templates are fully deleted
and do not reappear when loading templates.
"""

import os
import sys
import unittest
import tempfile
import shutil
import json
import time
from PyQt6.QtWidgets import QApplication

# Add project directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import necessary modules
from app.templates.template_operations import TemplateOperations
from app.templates.template_manager_core import TemplateManagerCore

class TestTemplateDeletion(unittest.TestCase):
    """Test template deletion functionality to ensure templates are properly deleted."""
    
    @classmethod
    def setUpClass(cls):
        # Create QApplication instance if it doesn't exist
        cls.app = QApplication.instance() or QApplication(sys.argv)
    
    def setUp(self):
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create templates directory within temp dir
        self.templates_dir = os.path.join(self.temp_dir, "templates")
        self.structures_dir = os.path.join(self.temp_dir, "structures")
        self.cache_dir = os.path.join(self.temp_dir, "cache")
        
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.structures_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Create a basic template operations instance with our test paths
        self.template_ops = TemplateOperations()
        self.template_ops.paths = {
            "templates_dir": self.templates_dir,
            "custom_structures_dir": self.structures_dir,
            "templates_cache_dir": self.cache_dir
        }
        
        # Create a Template Manager Core instance with our test paths
        self.template_manager = TemplateManagerCore()
        self.template_manager.paths = {
            "templates_dir": self.templates_dir,
            "custom_structures_dir": self.structures_dir,
            "templates_cache_dir": self.cache_dir,
            "template_directories_dir": os.path.join(self.temp_dir, "template_dirs")
        }
    
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)
    
    def create_test_template(self, name="Test Template", structure=None):
        """Helper to create a test template"""
        if structure is None:
            structure = [
                {
                    "type": "folder",
                    "name": "Project Folder",
                    "children": [
                        {
                            "type": "file",
                            "name": "test_file.txt",
                            "original_path": os.path.join(self.temp_dir, "test_file.txt"),
                            "path": os.path.join(self.temp_dir, "test_file.txt")
                        }
                    ]
                }
            ]
        
        # Create test file
        with open(os.path.join(self.temp_dir, "test_file.txt"), 'w') as f:
            f.write("Test file content")
            
        # Save the template
        template_data = {
            "name": name,
            "structure": structure
        }
        success = self.template_ops.save_template(template_data)
        self.assertTrue(success, f"Failed to save test template '{name}'")
        
        # Verify template exists
        template_path = os.path.join(self.templates_dir, f"{name.replace(' ', '_')}.json")
        self.assertTrue(os.path.exists(template_path), f"Template file not created at {template_path}")
        
        return template_path
    
    def test_delete_template_file(self):
        """Test that template file is actually deleted when calling delete_template"""
        # Create a test template
        template_name = "DeleteTest"
        template_path = self.create_test_template(template_name)
        
        # Delete the template
        result = self.template_ops.delete_template(template_name)
        self.assertTrue(result, "Template deletion failed")
        
        # Verify the template file was deleted
        self.assertFalse(os.path.exists(template_path), 
                       f"Template file still exists at {template_path}")
    
    def test_template_manager_delete_template(self):
        """Test that template is completely deleted using template manager"""
        # Create test templates
        template_name1 = "DeleteTest1"
        template_name2 = "DeleteTest2"
        
        self.create_test_template(template_name1)
        self.create_test_template(template_name2)
        
        # Load templates
        self.template_manager.load_templates()
        
        # Verify templates were loaded
        templates_before = [t.get('name') for t in self.template_manager.templates]
        self.assertIn(template_name1, templates_before, "First template not loaded")
        self.assertIn(template_name2, templates_before, "Second template not loaded")
        
        # Delete the first template
        result = self.template_manager.delete_template(template_name1)
        self.assertTrue(result, "Template deletion failed")
        
        # Manually load templates again
        self.template_manager.templates = []  # Clear templates
        self.template_manager.load_templates()
        
        # Verify the deleted template is not loaded but the other one is
        templates_after = [t.get('name') for t in self.template_manager.templates]
        self.assertNotIn(template_name1, templates_after, 
                       f"Deleted template '{template_name1}' still appears after reloading")
        self.assertIn(template_name2, templates_after, "Second template should still be loaded")
    
    def test_template_with_spaces_in_name(self):
        """Test that template with spaces in the name is properly deleted"""
        # Create a test template with spaces in name
        template_name = "Template With Spaces"
        self.create_test_template(template_name)
        
        # Load templates
        self.template_manager.load_templates()
        
        # Verify template was loaded
        templates_before = [t.get('name') for t in self.template_manager.templates]
        self.assertIn(template_name, templates_before, "Template not loaded")
        
        # Delete the template
        result = self.template_manager.delete_template(template_name)
        self.assertTrue(result, "Template deletion failed")
        
        # Manually load templates again
        self.template_manager.templates = []  # Clear templates
        self.template_manager.load_templates()
        
        # Verify the deleted template is not loaded
        templates_after = [t.get('name') for t in self.template_manager.templates]
        self.assertNotIn(template_name, templates_after, 
                       f"Deleted template '{template_name}' still appears after reloading")

if __name__ == '__main__':
    unittest.main() 