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
from app.templates.template_io import TemplateIO
from app.templates.template_structure_ops import TemplateStructureOps
from app.utils.file_cache_manager import FileCacheManager

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
        
        # Create TemplateIO instance for direct save/delete
        self.file_cache_manager = FileCacheManager(self.cache_dir)
        self.structure_ops = TemplateStructureOps({
            "custom_structures_dir": self.structures_dir,
            "templates_dir": self.templates_dir
        })
        self.template_io = TemplateIO({
            "templates_dir": self.templates_dir,
            "custom_structures_dir": self.structures_dir
        }, self.file_cache_manager, self.structure_ops)
    
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
            
        # Save the template using TemplateIO
        template_data = {
            "name": name,
            "structure": structure
        }
        success = self.template_io.save_template(template_data)
        self.assertTrue(success, f"Failed to save test template '{name}'")
        
        # Verify template exists
        from app.templates.template_utils import sanitize_filename
        template_path = os.path.join(self.templates_dir, f"{sanitize_filename(name)}.json")
        self.assertTrue(os.path.exists(template_path), f"Template file not created at {template_path}")
        
        return template_path
    
    def test_delete_template_file(self):
        """Test that template file is actually deleted when calling delete_template"""
        # Create a test template
        template_name = "DeleteTest"
        template_path = self.create_test_template(template_name)
        
        # Delete the template
        result = self.template_io.delete_template(template_name)
        self.assertTrue(result, "Template deletion failed")
        
        # Verify the template file was deleted
        self.assertFalse(os.path.exists(template_path), 
                       f"Template file still exists at {template_path}")
    
    def test_template_manager_delete_template(self):
        """Test that template is completely deleted using template manager (now using TemplateIO)"""
        # Create test templates
        template_name1 = "DeleteTest1"
        template_name2 = "DeleteTest2"
        
        self.create_test_template(template_name1)
        self.create_test_template(template_name2)
        
        # Load templates
        self.template_io.load_templates()
        templates_before = list(self.template_io.templates.keys())
        self.assertIn(template_name1, templates_before, "First template not loaded")
        self.assertIn(template_name2, templates_before, "Second template not loaded")
        
        # Delete the first template
        result = self.template_io.delete_template(template_name1)
        if isinstance(result, tuple):
            result = result[0]
        self.assertTrue(result, "Template deletion failed")
        
        # Reload templates
        self.template_io.load_templates()
        templates_after = list(self.template_io.templates.keys())
        self.assertNotIn(template_name1, templates_after, f"Deleted template '{template_name1}' still appears after reloading")
        self.assertIn(template_name2, templates_after, "Second template should still be loaded")
    
    def test_template_with_spaces_in_name(self):
        """Test that template with spaces in the name is properly deleted (now using TemplateIO)"""
        template_name = "Template With Spaces"
        self.create_test_template(template_name)
        
        # Load templates
        self.template_io.load_templates()
        templates_before = list(self.template_io.templates.keys())
        self.assertIn(template_name, templates_before, "Template not loaded")
        
        # Delete the template
        result = self.template_io.delete_template(template_name)
        if isinstance(result, tuple):
            result = result[0]
        self.assertTrue(result, "Template deletion failed")
        
        # Reload templates
        self.template_io.load_templates()
        templates_after = list(self.template_io.templates.keys())
        self.assertNotIn(template_name, templates_after, f"Deleted template '{template_name}' still appears after reloading")
    
    def test_template_with_apostrophe_in_name(self):
        """Test that template with an apostrophe in the name is properly deleted (now using TemplateIO)"""
        template_name = "Craig's Template"
        self.create_test_template(template_name)
        
        # Load templates
        self.template_io.load_templates()
        templates_before = list(self.template_io.templates.keys())
        self.assertIn(template_name, templates_before, "Template with apostrophe not loaded")
        
        # Delete the template
        result = self.template_io.delete_template(template_name)
        if isinstance(result, tuple):
            result = result[0]
        self.assertTrue(result, "Template deletion failed for apostrophe name")
        
        # Reload templates
        self.template_io.load_templates()
        templates_after = list(self.template_io.templates.keys())
        self.assertNotIn(template_name, templates_after, f"Deleted template '{template_name}' still appears after reloading")

if __name__ == '__main__':
    unittest.main() 