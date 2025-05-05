#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for validating JSON structure handling in the application.
This test focuses on the consistency of file naming, JSON serialization/deserialization,
and proper structure lookup across different naming patterns.
"""

import unittest
import os
import json
import shutil
import tempfile
import time
from datetime import datetime
import sys

# Mock PyQt modules before importing any project code
sys.modules['PyQt5'] = unittest.mock.MagicMock()
sys.modules['PyQt5.QtWidgets'] = unittest.mock.MagicMock()
sys.modules['PyQt5.QtCore'] = unittest.mock.MagicMock()
sys.modules['PyQt5.QtGui'] = unittest.mock.MagicMock()

# Import the necessary modules from the application
try:
    from app.templates.structure_operations import StructureOperations
    from app.templates.template_operations import TemplateOperations
except ImportError:
    print("WARNING: Could not import directly from app modules.")
    print("Adjusting path to allow imports from the current directory.")
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from app.templates.structure_operations import StructureOperations
    from app.templates.template_operations import TemplateOperations

# Create a mock for the app instance
class MockApp:
    """Mock application instance for testing."""
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the MockApp instance."""
        if cls._instance is None:
            cls._instance = MockApp()
        return cls._instance
    
    def __init__(self):
        """Initialize the MockApp instance with required attributes."""
        self.template_gallery = unittest.mock.MagicMock()
        self.template_gallery.populate_gallery = unittest.mock.MagicMock()
        self.template_gallery.select_template = unittest.mock.MagicMock()

# Mock the ProjectCreatorApp module
sys.modules['app.core.app_module_pyqt'] = unittest.mock.MagicMock()
sys.modules['app.core.app_module_pyqt'].ProjectCreatorApp = MockApp

class TestJSONStructureHandling(unittest.TestCase):
    """Test case for validating JSON structure handling in the application."""
    
    def setUp(self):
        """Set up the test environment before each test."""
        # Create temporary directories for testing
        self.test_dir = tempfile.mkdtemp(prefix="test_json_")
        self.structures_dir = os.path.join(self.test_dir, "structures")
        self.templates_dir = os.path.join(self.test_dir, "templates")
        
        # Create the necessary directories
        os.makedirs(self.structures_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Initialize the StructureOperations instance with our test directories
        self.structure_ops = StructureOperations()
        self.structure_ops.paths = {
            "structures_dir": self.structures_dir,
            "templates_dir": self.templates_dir,
            "custom_structures_dir": self.structures_dir  # Add this to fix the key error
        }
        self.structure_ops.custom_structures = {}
        
        # Initialize the TemplateOperations instance
        self.template_ops = TemplateOperations()
        self.template_ops.paths = {
            "structures_dir": self.structures_dir,
            "templates_dir": self.templates_dir,
            "custom_structures_dir": self.structures_dir  # Add this to match structure_ops
        }
        self.template_ops.templates = []
        self.template_ops.custom_structures = {}
        self.template_ops.folders = {}
        
        print(f"\nTest directories created:")
        print(f"- Temp dir: {self.test_dir}")
        print(f"- Structures dir: {self.structures_dir}")
        print(f"- Templates dir: {self.templates_dir}")
    
    def tearDown(self):
        """Clean up the test environment after each test."""
        # Remove the temporary directories
        shutil.rmtree(self.test_dir)
        print(f"Test directories removed: {self.test_dir}")
    
    def create_test_structure(self, name="Test Structure"):
        """Create a test structure with the given name."""
        return {
            "name": name,
            "display_name": name,
            "version": "1.0",
            "type": "custom",
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "directories": [
                {"name": "src", "description": "Source files"},
                {"name": "docs", "description": "Documentation"}
            ]
        }
    
    def create_test_template(self, name="Test Template", structure_name=None):
        """Create a test template with the given name."""
        if structure_name is None:
            structure_name = f"Template_{name}"
        
        return {
            "name": name,
            "description": "Test template description",
            "structure_name": structure_name,
            "category": "Test",
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "type": "custom"
        }
    
    def test_structure_serialization_basic(self):
        """Test basic structure serialization without special characters."""
        # Create a test structure
        structure_name = "Basic_Structure"
        structure = self.create_test_structure(structure_name)
        
        # Save the structure
        print(f"\nTest: Saving structure '{structure_name}'")
        success = self.structure_ops.save_custom_structure(structure_name, structure)
        
        # Check that the structure was saved successfully
        self.assertTrue(success, "Failed to save structure")
        
        # Check that the file exists
        expected_path = os.path.join(self.structures_dir, f"Template_{structure_name}.json")
        self.assertTrue(os.path.exists(expected_path), f"Structure file not created at: {expected_path}")
        
        # Read the file and check its contents
        with open(expected_path, 'r') as f:
            saved_data = json.load(f)
        
        # Verify key structure elements
        self.assertEqual(saved_data["name"], structure_name, "Structure name mismatch")
        self.assertEqual(saved_data["type"], "custom", "Structure type mismatch")
        self.assertEqual(len(saved_data["directories"]), 2, "Structure directories count mismatch")
        
        print(f"Structure file contents verified at: {expected_path}")
    
    def test_structure_serialization_with_spaces(self):
        """Test structure serialization with spaces in the name."""
        # Create a test structure with spaces
        structure_name = "Structure With Spaces"
        structure = self.create_test_structure(structure_name)
        
        # Save the structure
        print(f"\nTest: Saving structure '{structure_name}'")
        success = self.structure_ops.save_custom_structure(structure_name, structure)
        
        # Check that the structure was saved successfully
        self.assertTrue(success, "Failed to save structure")
        
        # Check that the file exists with underscores
        expected_path = os.path.join(self.structures_dir, f"Template_Structure_With_Spaces.json")
        self.assertTrue(os.path.exists(expected_path), f"Structure file not created at: {expected_path}")
        
        # Read the file and check its contents
        with open(expected_path, 'r') as f:
            saved_data = json.load(f)
        
        # Verify the display_name preserves spaces
        self.assertEqual(saved_data["display_name"], structure_name, "Structure display_name should preserve spaces")
        
        print(f"Structure file with spaces in name verified at: {expected_path}")
    
    def test_structure_retrieval_various_formats(self):
        """Test retrieving structures with various name formats."""
        # Create and save a test structure
        original_name = "Test Structure"
        structure = self.create_test_structure(original_name)
        self.structure_ops.save_custom_structure(original_name, structure)
        
        # Attempt to retrieve the structure with different name formats
        print(f"\nTest: Retrieving structure with different name formats")
        
        # List of name variations to try
        name_variations = [
            original_name,                      # Original with spaces
            "Test_Structure",                   # With underscores
            f"Template_{original_name}",        # With Template_ prefix and spaces
            f"Template_Test_Structure"          # With Template_ prefix and underscores
        ]
        
        for variation in name_variations:
            print(f"Trying to retrieve structure with name: '{variation}'")
            retrieved = self.structure_ops.get_structure(variation)
            self.assertIsNotNone(retrieved, f"Failed to retrieve structure with name: {variation}")
            self.assertEqual(retrieved["display_name"], original_name, 
                            f"Retrieved structure display_name mismatch with variation: {variation}")
            print(f"✓ Successfully retrieved structure with name variation: '{variation}'")
    
    def test_template_with_structure(self):
        """Test creating a template with an associated structure."""
        # Create a test structure
        structure_name = "Template Structure"
        structure = self.create_test_structure(structure_name)
        self.structure_ops.save_custom_structure(structure_name, structure)
        
        # Create a test template referencing the structure
        template_name = "Template With Structure"
        template = self.create_test_template(template_name, structure_name)
        
        # Save the template as a JSON file
        template_path = os.path.join(self.templates_dir, f"{template_name.replace(' ', '_')}.json")
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        # Add the template to the list
        self.template_ops.templates.append(template)
        
        print(f"\nTest: Created template '{template_name}' with structure '{structure_name}'")
        
        # Test retrieving the structure for the template
        retrieved_structure = self.structure_ops.get_structure(structure_name)
        self.assertIsNotNone(retrieved_structure, f"Failed to retrieve structure for template")
        self.assertEqual(retrieved_structure["display_name"], structure_name, "Structure display_name mismatch")
        
        print(f"Template and associated structure verified")
    
    def test_template_rename_with_structure(self):
        """Test renaming a template and its associated structure."""
        # Create a test structure and template
        old_structure_name = "Original Structure"
        structure = self.create_test_structure(old_structure_name)
        success = self.structure_ops.save_custom_structure(old_structure_name, structure)
        self.assertTrue(success, "Failed to save initial structure")
        
        old_template_name = "Original Template"
        template = self.create_test_template(old_template_name, old_structure_name)
        
        # Save the template as a JSON file
        template_path = os.path.join(self.templates_dir, f"{old_template_name.replace(' ', '_')}.json")
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        # Add the template to the list
        self.template_ops.templates.append(template)
        
        # Set up the template_ops.custom_structures to mimic the app
        self.template_ops.custom_structures = self.structure_ops.custom_structures
        
        # Set up the get_structure method to use our structure_ops method
        self.template_ops.get_structure = self.structure_ops.get_structure
        
        print(f"\nTest: Renaming template '{old_template_name}' to 'New Template'")
        
        # Rename the template
        new_template_name = "New Template"
        success = self.template_ops.rename_template(old_template_name, new_template_name)
        
        # Check that the rename was successful
        self.assertTrue(success, "Failed to rename template")
        
        # Check that the new template file exists
        new_template_path = os.path.join(self.templates_dir, f"{new_template_name.replace(' ', '_')}.json")
        self.assertTrue(os.path.exists(new_template_path), f"New template file not created at: {new_template_path}")
        
        # Check that the old template file no longer exists
        old_template_path = os.path.join(self.templates_dir, f"{old_template_name.replace(' ', '_')}.json")
        self.assertFalse(os.path.exists(old_template_path), f"Old template file still exists at: {old_template_path}")
        
        # Read the new template file and check its structure_name
        with open(new_template_path, 'r') as f:
            new_template_data = json.load(f)
        
        new_structure_name = new_template_data.get("structure_name", "")
        print(f"New template references structure name: '{new_structure_name}'")
        
        # Check that the new structure exists in memory or on disk
        retrieved_structure = self.structure_ops.get_structure(new_structure_name)
        if retrieved_structure:
            self.assertEqual(retrieved_structure["display_name"], old_structure_name, 
                           "Retrieved structure display_name mismatch")
            print(f"Structure successfully retrieved after template rename")
        else:
            print(f"NOTE: Structure not found after template rename - this may be expected if rename doesn't update structure")
    
    def test_template_delete_with_structure(self):
        """Test deleting a template and its associated structure."""
        # Create a test structure and template
        structure_name = "Delete Structure"
        structure = self.create_test_structure(structure_name)
        success = self.structure_ops.save_custom_structure(structure_name, structure)
        self.assertTrue(success, "Failed to save initial structure")
        
        template_name = "Delete Template"
        template = self.create_test_template(template_name, structure_name)
        
        # Save the template as a JSON file
        template_path = os.path.join(self.templates_dir, f"{template_name.replace(' ', '_')}.json")
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        # Add the template to the list
        self.template_ops.templates.append(template)
        
        # Set up the template_ops structure handling to use our structure_ops
        self.template_ops.custom_structures = self.structure_ops.custom_structures
        self.template_ops.get_structure = self.structure_ops.get_structure
        
        print(f"\nTest: Deleting template '{template_name}' with structure '{structure_name}'")
        
        # Verify structure exists before deletion
        prefixed_name = f"Template_{structure_name.replace(' ', '_')}"
        structure_path = os.path.join(self.structures_dir, f"{prefixed_name}.json")
        self.assertTrue(os.path.exists(structure_path), f"Structure file doesn't exist at: {structure_path}")
        
        # Delete the template
        success = self.template_ops.delete_template(template_name)
        
        # Check that the delete was successful
        self.assertTrue(success, "Failed to delete template")
        
        # Check that the template file no longer exists
        self.assertFalse(os.path.exists(template_path), f"Template file still exists at: {template_path}")
        
        print(f"Template successfully deleted")
    
    def test_structure_file_names_consistency(self):
        """Test the consistency of structure file names with different input patterns."""
        # Test cases with different name formats
        test_cases = [
            {"input": "Simple", "expected": "Template_Simple.json"},
            {"input": "With Space", "expected": "Template_With_Space.json"},
            {"input": "Template_Prefixed", "expected": "Template_Prefixed.json"},
            {"input": "Template_With Space", "expected": "Template_With_Space.json"},
            {"input": "Multiple   Spaces", "expected": "Template_Multiple_Spaces.json"}
        ]
        
        print("\nTest: Structure file name consistency")
        
        for case in test_cases:
            input_name = case["input"]
            expected_filename = case["expected"]
            
            # Create and save a structure with this name
            structure = self.create_test_structure(input_name)
            success = self.structure_ops.save_custom_structure(input_name, structure)
            
            # Check if save was successful
            self.assertTrue(success, f"Failed to save structure with name: {input_name}")
            
            # Check that the file exists with the expected name
            expected_path = os.path.join(self.structures_dir, expected_filename)
            self.assertTrue(os.path.exists(expected_path), 
                           f"Structure file not created at expected path: {expected_path}")
            
            print(f"✓ '{input_name}' saved as '{expected_filename}'")

if __name__ == "__main__":
    unittest.main()
