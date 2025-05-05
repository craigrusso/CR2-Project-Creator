#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Tests for the Project Type Manager functionality
"""

import sys
import os
import unittest
import tempfile
import shutil
import json
from PyQt5.QtWidgets import QApplication

# Add the project directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.templates.template_manager import TemplateManager
from app.templates.project_type_manager import ProjectTypeManager
from app.ui.structure_editor.category_manager import CategoryManager

class TestProjectTypeManager(unittest.TestCase):
    """Test case for the project type manager functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up the test environment"""
        # Create a QApplication instance for UI tests
        cls.app = QApplication.instance() or QApplication(sys.argv)
        
        # Create a temporary directory for templates
        cls.temp_dir = tempfile.mkdtemp()
        cls.templates_dir = os.path.join(cls.temp_dir, "templates")
        cls.structures_dir = os.path.join(cls.temp_dir, "structures")
        
        # Create the directories
        os.makedirs(cls.templates_dir, exist_ok=True)
        os.makedirs(cls.structures_dir, exist_ok=True)
        
        # Save paths for cleanup
        cls.temp_paths = [cls.temp_dir, cls.templates_dir, cls.structures_dir]
    
    @classmethod
    def tearDownClass(cls):
        """Clean up the test environment"""
        # Remove temporary directories
        for path in cls.temp_paths:
            if os.path.exists(path):
                shutil.rmtree(path)

    def setUp(self):
        """Set up each test"""
        # Create a template manager instance with mock paths
        self.template_manager = TemplateManager()
        self.template_manager.paths = {
            "templates_dir": self.templates_dir,
            "custom_structures_dir": self.structures_dir,
            "template_directories_dir": os.path.join(self.templates_dir, "directories")
        }
        
        # Create a project type manager instance
        self.project_manager = ProjectTypeManager(self.template_manager)
        
        # Clear any existing project types file
        project_types_path = os.path.join(self.templates_dir, "project_types.json")
        if os.path.exists(project_types_path):
            os.remove(project_types_path)

    def test_create_project_type(self):
        """Test creating a new project type"""
        # Add a new project type
        new_type = "Test Category"
        result = self.project_manager.create_project_type(new_type, "Video Editing - Standard")
        self.assertTrue(result, "Failed to create project type")
        
        # Verify it's in the list of project types
        project_types = self.project_manager.get_all_project_types()
        self.assertIn(new_type, project_types, "New project type not found in project types list")
        
        # Check if the project type was saved to disk
        project_types_path = os.path.join(self.templates_dir, "project_types.json")
        self.assertTrue(os.path.exists(project_types_path), "Project types file not created")
        
        # Read the file and verify the project type is there
        with open(project_types_path, 'r') as f:
            saved_types = json.load(f)
        self.assertIn(new_type, saved_types, "New project type not found in saved file")

    def test_load_project_types(self):
        """Test loading project types from file"""
        # Create a project types file
        test_types = {"Category 1": {"structure_name": "Video Editing - Standard", "icon": "📂"}, 
                      "Category 2": {"structure_name": "Motion Graphics - Standard", "icon": "📂"}}
        project_types_path = os.path.join(self.templates_dir, "project_types.json")
        with open(project_types_path, 'w') as f:
            json.dump(test_types, f)
        
        # Create a new project manager to load the file
        project_manager = ProjectTypeManager(self.template_manager)
        
        # Verify all test types are loaded
        project_types = project_manager.get_all_project_types()
        for type_name in test_types.keys():
            self.assertIn(type_name, project_types, f"Project type {type_name} not loaded from file")

    def test_category_dialog(self):
        """Test the category manager dialog"""
        # Create test categories
        test_categories = ["Video Editing", "Motion Graphics", "VFX", "Custom", "Test Category"]
        
        # Create the dialog with test categories
        dialog = CategoryManager(None, test_categories)
        
        # Verify categories are loaded in the list
        self.assertEqual(dialog.category_list.count(), len(test_categories), 
                         "Categories not loaded in dialog")
        
        # Get categories from dialog
        result_categories = dialog.get_categories()
        
        # Verify all categories are returned
        for category in test_categories:
            self.assertIn(category, result_categories, 
                          f"Category {category} not found in result categories")

if __name__ == "__main__":
    unittest.main() 