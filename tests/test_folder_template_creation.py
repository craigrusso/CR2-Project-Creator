#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script for template creation while in a folder.
Tests that a new template created while in a folder view is automatically added to that folder.
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime
import unittest
from unittest.mock import MagicMock, patch
import pytest

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder
from app.core.config_manager import get_templates_path, get_settings_path


class TestTemplateInFolderCreation(unittest.TestCase):
    """Test case for template creation while in a folder"""
    
    def setUp(self):
        """Set up the test environment"""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.templates_dir = os.path.join(self.temp_dir, "templates")
        self.cache_dir = os.path.join(self.temp_dir, "cache")
        
        # Create test directories
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Create a template manager with our test directories
        self.template_manager = TemplateManager()
        # Override the template manager's paths
        self.template_manager.paths = {
            "templates_dir": self.templates_dir,
            "templates_cache_dir": self.cache_dir,
            "custom_structures_dir": os.path.join(self.temp_dir, "structures")
        }
        
        # Initialize the folders dict
        self.template_manager.folders = {}
        
    def tearDown(self):
        """Clean up after the test"""
        shutil.rmtree(self.temp_dir)
    
    def test_add_template_in_folder(self):
        """Test that a template created while in a folder is added to that folder"""
        # Create a mock app and gallery
        mock_app = MagicMock()
        mock_app.template_manager = self.template_manager
        
        # Create a test folder
        test_folder = "TestFolder"
        self.template_manager.add_folder(test_folder)
        self.assertTrue(test_folder in self.template_manager.folders, f"Failed to create folder {test_folder}")
        
        # Create a test template
        test_template_name = "TestTemplate"
        
        # Mock the save_template method to avoid actually saving files
        with patch.object(self.template_manager, 'save_template', return_value=True):
            # Mock the get_template_by_name method to return our test template
            with patch.object(self.template_manager, 'get_template_by_name') as mock_get_template:
                # Create a simple template data structure
                test_template = {
                    "name": test_template_name,
                    "description": "Test template",
                    "category": "Test",
                    "type": "Standard"
                }
                mock_get_template.return_value = test_template
                
                # Mock show_edit_template to avoid UI interaction
                with patch('app.dialogs.dialog_windows_pyqt.show_edit_template'):
                    # Call _on_add_template method - this is what we're testing
                    # We need to make os.path.exists return True for the import_path
                    with patch('os.path.exists', return_value=True):
                        # Mock QInputDialog.getText to return our test template name
                        with patch('PyQt5.QtWidgets.QInputDialog.getText', return_value=(test_template_name, True)):
                            # Import the gallery class directly to avoid circular imports
                            # from app.templates.template_gallery_ui_pyqt import TemplateListItem
                            
                            # Create a mock gallery with our properties
                            gallery = MagicMock()
                            gallery.app = mock_app
                            gallery.template_manager = self.template_manager
                            gallery.current_folder = test_folder
                            gallery.populate_gallery = MagicMock()
                            
                            # Call the method directly
                            # TemplateListItem._on_add_template(gallery)
        
        # Check if the template was added to the folder
        self.assertIn(test_template_name, self.template_manager.folders[test_folder], 
                     f"Template {test_template_name} was not added to folder {test_folder}")
        
        print(f"SUCCESS: Template {test_template_name} was correctly added to folder {test_folder}")


if __name__ == "__main__":
    unittest.main() 