#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test the dollar sign placeholder handling in project names.
"""

import os
import sys
import tempfile
import shutil
import unittest

# Add parent directory to path to allow importing app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.project_builder import ProjectBuilder

class TestDollarPlaceholder(unittest.TestCase):
    """Test functionality related to dollar sign in project name placeholders."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        # Create a mock template manager (None is sufficient for our tests)
        self.template_manager = None
        # Create the project builder instance
        self.project_builder = ProjectBuilder(self.template_manager)
        # Test project name
        self.project_name = "TestProject123"
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_handle_dollar_placeholder(self):
        """Test the _handle_dollar_placeholder method."""
        # Test cases with different input patterns
        test_cases = [
            # Standard placeholder
            {"input": "${PROJECT_NAME}", "expected": self.project_name},
            # Placeholder with extension
            {"input": "${PROJECT_NAME}.txt", "expected": f"{self.project_name}.txt"},
            # Placeholder at beginning with other text
            {"input": "${PROJECT_NAME}_config", "expected": f"{self.project_name}_config"},
            # Placeholder in middle
            {"input": "prefix_${PROJECT_NAME}_suffix", "expected": f"prefix_{self.project_name}_suffix"},
            # Just $ at beginning
            {"input": "$file.txt", "expected": f"{self.project_name}.txt"},
            # $ without braces 
            {"input": "$PROJECT_NAME.js", "expected": f"{self.project_name}.js"},
            # Multiple extensions
            {"input": "${PROJECT_NAME}.config.json", "expected": f"{self.project_name}.config.json"},
            # Multiple placeholders
            {"input": "${PROJECT_NAME}_${PROJECT_NAME}", "expected": f"{self.project_name}_{self.project_name}"},
        ]
        
        # Run tests for each case
        for case in test_cases:
            result = self.project_builder._handle_dollar_placeholder(case["input"], self.project_name)
            self.assertEqual(result, case["expected"], 
                            f"Failed on input '{case['input']}': expected '{case['expected']}', got '{result}'")
    
    def test_create_structure_with_dollar_placeholder(self):
        """Test creating a folder structure with dollar placeholders."""
        # Create a simple directory structure for testing
        test_structure = [
            "regular_folder",
            "${PROJECT_NAME}_folder",
            "${PROJECT_NAME}.txt",
            "$config.json"
        ]
        
        # Create a project path
        project_path = os.path.join(self.temp_dir, self.project_name)
        os.makedirs(project_path, exist_ok=True)
        
        # Create the folder structure
        self.project_builder._create_folder_structure(project_path, test_structure, self.project_name)
        
        # Debug: List all files in the directory to see what was actually created
        print("\n🔍 DEBUG: Listing all files in the test directory:")
        for root, dirs, files in os.walk(project_path):
            rel_path = os.path.relpath(root, project_path)
            if rel_path == '.':
                rel_path = ''
            print(f"  Directory: {rel_path or '(root)'}")
            for d in dirs:
                print(f"    Folder: {d}")
            for f in files:
                print(f"    File: {f}")
        
        # Manually check for items that should exist
        expected_paths = [
            os.path.join(project_path, "regular_folder"),
            os.path.join(project_path, f"{self.project_name}_folder"),
            os.path.join(project_path, f"{self.project_name}.txt"),
            os.path.join(project_path, f"{self.project_name}.json"),
        ]
        
        for path in expected_paths:
            exists = os.path.exists(path)
            print(f"🔍 DEBUG: Checking path: {path} - Exists: {exists}")
            self.assertTrue(exists, f"Path does not exist: {path}")

if __name__ == "__main__":
    unittest.main() 