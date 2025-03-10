#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import sys
import json
import shutil
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path so we can import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.structure_manager import StructureManager

class TestStructureManager(unittest.TestCase):
    """Test cases for the Structure Manager"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for structures
        self.test_dir = os.path.join(os.path.dirname(__file__), 'test_structures')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Create structure manager with the test directory
        self.structure_manager = StructureManager(structures_dir=self.test_dir)
        
        # Create some test structures directly in the structures directory
        self.test_structures = [
            {
                'name': 'Test Structure 1',
                'items': [
                    {'type': 'directory', 'name': 'src'},
                    {'type': 'directory', 'name': 'tests'},
                    {'type': 'file', 'name': 'README.md', 'content': '# Test Project'}
                ]
            },
            {
                'name': 'Test Structure 2',
                'items': [
                    {'type': 'directory', 'name': 'app'},
                    {'type': 'file', 'name': 'main.py', 'content': 'print("Hello, World!")'}
                ]
            }
        ]
        
        # Manually save structures to files
        for structure in self.test_structures:
            filename = structure['name'].replace(" ", "_").replace("/", "-").replace("\\", "-")
            file_path = os.path.join(self.test_dir, f"{filename}.json")
            with open(file_path, 'w') as f:
                json.dump(structure, f, indent=2)
        
        # Reload structures to make sure they're in memory
        self.structure_manager.load_structures()
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove the test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_add_structure(self):
        """Test adding a structure"""
        # Add a new structure
        new_structure = {
            'name': 'New Test Structure',
            'items': [
                {'type': 'file', 'name': 'new_file.txt', 'content': 'New file content'}
            ]
        }
        
        result = self.structure_manager.add_structure(new_structure)
        self.assertTrue(result, "Failed to add structure")
        
        # Check if structure was added
        structures = self.structure_manager.get_all_structures()
        self.assertEqual(len(structures), 3, "Structure was not added correctly")
        
        # Check if structure can be retrieved by name
        retrieved = self.structure_manager.get_structure_by_name('New Test Structure')
        self.assertIsNotNone(retrieved, "Could not retrieve structure by name")
        self.assertEqual(retrieved['name'], 'New Test Structure', "Retrieved structure has incorrect name")
    
    def test_update_structure(self):
        """Test updating a structure"""
        # Get the first test structure
        structure = self.structure_manager.get_structure_by_name('Test Structure 1')
        
        # Add a new item to the structure
        structure['items'].append({'type': 'file', 'name': 'CHANGELOG.md', 'content': '# Changelog'})
        
        # Update the structure
        result = self.structure_manager.update_structure(structure)
        self.assertTrue(result, "Failed to update structure")
        
        # Check if structure was updated
        retrieved = self.structure_manager.get_structure_by_name('Test Structure 1')
        self.assertEqual(len(retrieved['items']), 4, "Structure was not updated correctly")
        self.assertEqual(retrieved['items'][3]['name'], 'CHANGELOG.md', "New item not added correctly")
    
    def test_delete_structure(self):
        """Test deleting a structure"""
        # Delete the first test structure
        result = self.structure_manager.delete_structure('Test Structure 1')
        self.assertTrue(result, "Failed to delete structure")
        
        # Check if structure was deleted
        retrieved = self.structure_manager.get_structure_by_name('Test Structure 1')
        self.assertIsNone(retrieved, "Structure was not deleted correctly")
        
        # Check if only one structure remains
        structures = self.structure_manager.get_all_structures()
        self.assertEqual(len(structures), 1, "Incorrect number of structures after deletion")
    
    def test_get_structure_names(self):
        """Test getting structure names"""
        # Get all structure names
        names = self.structure_manager.get_structure_names()
        self.assertEqual(len(names), 2, "Incorrect number of structure names")
        self.assertIn('Test Structure 1', names, "First structure name not found")
        self.assertIn('Test Structure 2', names, "Second structure name not found")
    
    def test_get_structure_by_name(self):
        """Test getting a structure by name"""
        # Get structure by name
        structure = self.structure_manager.get_structure_by_name('Test Structure 1')
        self.assertIsNotNone(structure, "Structure not found by name")
        self.assertEqual(structure['name'], 'Test Structure 1', "Retrieved structure has incorrect name")
        self.assertEqual(len(structure['items']), 3, "Retrieved structure has incorrect number of items")
    
    def test_structure_exists(self):
        """Test checking if a structure exists"""
        # Check if existing structures exist
        self.assertTrue(self.structure_manager.structure_exists('Test Structure 1'), "Existing structure not found")
        self.assertTrue(self.structure_manager.structure_exists('Test Structure 2'), "Existing structure not found")
        
        # Check if non-existent structure does not exist
        self.assertFalse(self.structure_manager.structure_exists('Non-existent Structure'), "Non-existent structure found")
    
    def test_duplicate_structure(self):
        """Test duplicating a structure"""
        # Duplicate the first structure
        result = self.structure_manager.duplicate_structure('Test Structure 1', 'Duplicated Structure')
        self.assertTrue(result, "Failed to duplicate structure")
        
        # Check if structure was duplicated
        duplicated = self.structure_manager.get_structure_by_name('Duplicated Structure')
        self.assertIsNotNone(duplicated, "Duplicated structure not found")
        self.assertEqual(duplicated['name'], 'Duplicated Structure', "Duplicated structure has incorrect name")
        self.assertEqual(len(duplicated['items']), 3, "Duplicated structure has incorrect number of items")
        
        # Check if original structure still exists
        original = self.structure_manager.get_structure_by_name('Test Structure 1')
        self.assertIsNotNone(original, "Original structure not found after duplication")
        
        # Check if we now have 3 structures total
        structures = self.structure_manager.get_all_structures()
        self.assertEqual(len(structures), 3, "Incorrect number of structures after duplication")
    
    def test_import_export_structure(self):
        """Test importing and exporting a structure"""
        # Export a structure to a file
        export_path = os.path.join(self.test_dir, 'exported_structure.json')
        structure = self.structure_manager.get_structure_by_name('Test Structure 1')
        
        with open(export_path, 'w') as f:
            json.dump(structure, f)
        
        # Delete the structure
        self.structure_manager.delete_structure('Test Structure 1')
        
        # Import the structure back
        with open(export_path, 'r') as f:
            imported_structure = json.load(f)
        
        result = self.structure_manager.add_structure(imported_structure)
        self.assertTrue(result, "Failed to import structure")
        
        # Check if structure was imported correctly
        retrieved = self.structure_manager.get_structure_by_name('Test Structure 1')
        self.assertIsNotNone(retrieved, "Imported structure not found")
        self.assertEqual(retrieved['name'], 'Test Structure 1', "Imported structure has incorrect name")
        self.assertEqual(len(retrieved['items']), 3, "Imported structure has incorrect number of items")

if __name__ == '__main__':
    unittest.main() 