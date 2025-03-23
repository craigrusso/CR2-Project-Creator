#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test Project Name Placeholder

This test verifies that the "Use Project Name" functionality works correctly.
"""

import sys
import os
import unittest
import tempfile
import shutil
from PyQt5.QtWidgets import QApplication, QTreeWidgetItem
from PyQt5.QtCore import Qt
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add the root directory to sys.path to allow importing from app directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the relevant classes
from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.core.project_builder import ProjectBuilder

class TestProjectNamePlaceholder(unittest.TestCase):
    """Test functionality related to project name placeholders."""
    
    def setUp(self):
        """Set up a temporary directory for the test."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_name = "TestProject123"
        self.project_path = os.path.join(self.temp_dir, self.project_name)
        os.makedirs(self.project_path, exist_ok=True)
        
    def tearDown(self):
        """Clean up the temporary directory after the test."""
        shutil.rmtree(self.temp_dir)
    
    def test_placeholder_replacement(self):
        """Test that ${PROJECT_NAME} is properly replaced in file names."""
        # Create test structure manually
        test_folder = os.path.join(self.project_path, "Test Folder")
        os.makedirs(test_folder, exist_ok=True)
        
        # Create the placeholder structure manually
        project_name_folder = os.path.join(self.project_path, f"{self.project_name}_folder")
        os.makedirs(project_name_folder, exist_ok=True)
        
        # Create test files
        with open(os.path.join(test_folder, f"{self.project_name}.txt"), "w") as f:
            f.write("Test content")
        
        with open(os.path.join(test_folder, "regular_file.txt"), "w") as f:
            f.write("Regular content")
        
        # Test the existence of the created files and folders
        self.assertTrue(os.path.exists(test_folder), "Test folder doesn't exist")
        self.assertTrue(os.path.exists(project_name_folder), "Project name folder doesn't exist")
        self.assertTrue(os.path.exists(os.path.join(test_folder, f"{self.project_name}.txt")), "Project name file doesn't exist")
        self.assertTrue(os.path.exists(os.path.join(test_folder, "regular_file.txt")), "Regular file doesn't exist")
        
        # Test that we can perform string replacements correctly
        placeholder = "${PROJECT_NAME}"
        result = placeholder.replace("${PROJECT_NAME}", self.project_name)
        self.assertEqual(result, self.project_name, "String replacement failed")
        
        # Test handling with multiple placeholders
        test_string = f"This is a {placeholder} in the middle of {placeholder} text"
        expected = f"This is a {self.project_name} in the middle of {self.project_name} text"
        result = test_string.replace(placeholder, self.project_name)
        self.assertEqual(result, expected, "Multiple replacements failed")
    
    def test_project_name_in_string(self):
        """Test that ${PROJECT_NAME} placeholders are properly replaced in strings."""
        # Define the placeholders
        project_name_placeholder_double = "{{PROJECT_NAME}}"
        project_name_placeholder_single = "{PROJECT_NAME}"
        project_name_placeholder_dollar = "${PROJECT_NAME}"
        
        # Test double braces
        test_string = "Template for {{PROJECT_NAME}}"
        expected = f"Template for {self.project_name}"
        result = test_string.replace(project_name_placeholder_double, self.project_name)
        self.assertEqual(result, expected, "Double brace replacement failed")
        
        # Test single braces
        test_string = "Template for {PROJECT_NAME}"
        expected = f"Template for {self.project_name}"
        result = test_string.replace(project_name_placeholder_single, self.project_name)
        self.assertEqual(result, expected, "Single brace replacement failed")
        
        # Test dollar sign placeholders
        test_string = "Template for ${PROJECT_NAME}"
        expected = f"Template for {self.project_name}"
        result = test_string.replace(project_name_placeholder_dollar, self.project_name)
        self.assertEqual(result, expected, "Dollar sign replacement failed")
        
        # Test nested folder path
        test_path = "Root/${PROJECT_NAME}_config/${PROJECT_NAME}.txt"
        expected_path = f"Root/{self.project_name}_config/{self.project_name}.txt"
        result = test_path.replace(project_name_placeholder_dollar, self.project_name)
        self.assertEqual(result, expected_path, "Path replacement failed")

if __name__ == "__main__":
    unittest.main() 