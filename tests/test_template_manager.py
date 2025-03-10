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

from app.templates.template_manager import TemplateManager

class TestTemplateManager(unittest.TestCase):
    """Test cases for the Template Manager"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for templates
        self.test_dir = os.path.join(os.path.dirname(__file__), 'test_templates')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Create template manager (it uses get_config_paths internally, so we'll patch that)
        with patch('app.templates.template_manager.get_config_paths') as mock_get_paths:
            mock_get_paths.return_value = {
                "templates_dir": os.path.join(self.test_dir, "templates"),
                "custom_structures_dir": os.path.join(self.test_dir, "structures"),
                "template_directories_dir": os.path.join(self.test_dir, "template_directories")
            }
            self.template_manager = TemplateManager()
            
        # Create necessary directories
        os.makedirs(os.path.join(self.test_dir, "templates"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "structures"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "template_directories"), exist_ok=True)
        
        # Create some test templates
        self.test_templates = [
            {
                'name': 'Test Template 1',
                'description': 'Test template for unit testing',
                'icon': '📄',
                'category': 'Testing',
                'folder': 'General',
                'items': [
                    {'type': 'directory', 'name': 'src'},
                    {'type': 'directory', 'name': 'tests'},
                    {'type': 'file', 'name': 'README.md', 'content': '# Test Project'}
                ]
            },
            {
                'name': 'Test Template 2',
                'description': 'Another test template',
                'icon': '🧪',
                'category': 'Development',
                'folder': 'Development',
                'items': [
                    {'type': 'directory', 'name': 'app'},
                    {'type': 'file', 'name': 'main.py', 'content': 'print("Hello, World!")'}
                ]
            }
        ]
        
        # Manually save templates to the templates directory
        for template in self.test_templates:
            filename = template['name'].replace(" ", "_").replace("/", "-").replace("\\", "-")
            file_path = os.path.join(os.path.join(self.test_dir, "templates"), f"{filename}.json")
            with open(file_path, 'w') as f:
                json.dump(template, f)
        
        # Reload templates to make sure they're in memory
        self.template_manager.load_templates()
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove the test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_add_template(self):
        """Test adding a template"""
        # Add a new template
        new_template = {
            'name': 'New Test Template',
            'description': 'A new test template',
            'icon': '🆕',
            'category': 'Testing',
            'folder': 'General',
            'items': [
                {'type': 'file', 'name': 'new_file.txt', 'content': 'New file content'}
            ]
        }
        
        result = self.template_manager.save_template(
            name=new_template['name'],
            category=new_template['category'],
            file_path='',
            structure_type='Standard',
            description=new_template['description']
        )
        self.assertTrue(result, "Failed to add template")
        
        # Check if template was added
        templates = self.template_manager.get_all_templates()
        self.assertEqual(len(templates), 3, "Template was not added correctly")
        
        # Check if template can be retrieved by name
        retrieved = self.template_manager.get_template_by_name('New Test Template')
        self.assertIsNotNone(retrieved, "Could not retrieve template by name")
        self.assertEqual(retrieved['name'], 'New Test Template', "Retrieved template has incorrect name")
    
    def test_update_template(self):
        """Test updating a template"""
        # Get the first test template
        template = self.template_manager.get_template_by_name('Test Template 1')
        
        # Update the template
        template['description'] = 'Updated description'
        result = self.template_manager.update_template(template)
        self.assertTrue(result, "Failed to update template")
        
        # Check if template was updated
        retrieved = self.template_manager.get_template_by_name('Test Template 1')
        self.assertEqual(retrieved['description'], 'Updated description', "Template was not updated correctly")
    
    def test_delete_template(self):
        """Test deleting a template"""
        # Delete the first test template
        result = self.template_manager.delete_template('Test Template 1')
        self.assertTrue(result, "Failed to delete template")
        
        # Check if template was deleted
        retrieved = self.template_manager.get_template_by_name('Test Template 1')
        self.assertIsNone(retrieved, "Template was not deleted correctly")
        
        # Check if only one template remains
        templates = self.template_manager.get_all_templates()
        self.assertEqual(len(templates), 1, "Incorrect number of templates after deletion")
    
    def test_get_templates_by_folder(self):
        """Test getting templates by folder"""
        # First create the folders
        self.template_manager.create_folder('General')
        self.template_manager.create_folder('Development')
        
        # Move templates to their folders
        self.template_manager.move_template_to_folder('Test Template 1', 'General')
        self.template_manager.move_template_to_folder('Test Template 2', 'Development')
        
        # Get templates in the General folder
        templates = self.template_manager.get_templates_in_folder('General')
        self.assertEqual(len(templates), 1, "Incorrect number of templates in the General folder")
        self.assertEqual(templates[0]['name'], 'Test Template 1', "Incorrect template in the General folder")
        
        # Get templates in the Development folder
        templates = self.template_manager.get_templates_in_folder('Development')
        self.assertEqual(len(templates), 1, "Incorrect number of templates in the Development folder")
        self.assertEqual(templates[0]['name'], 'Test Template 2', "Incorrect template in the Development folder")
    
    def test_get_templates_by_category(self):
        """Test getting templates by category"""
        # Get templates in the Testing category
        templates = self.template_manager.filter_templates(category='Testing')
        self.assertEqual(len(templates), 1, "Incorrect number of templates in the Testing category")
        self.assertEqual(templates[0]['name'], 'Test Template 1', "Incorrect template in the Testing category")
        
        # Get templates in the Development category
        templates = self.template_manager.filter_templates(category='Development')
        self.assertEqual(len(templates), 1, "Incorrect number of templates in the Development category")
        self.assertEqual(templates[0]['name'], 'Test Template 2', "Incorrect template in the Development category")
    
    def test_move_template_to_folder(self):
        """Test moving a template to a folder"""
        # First create the folders
        self.template_manager.create_folder('General')
        self.template_manager.create_folder('Development')
        
        # Move the first template to the General folder
        result = self.template_manager.move_template_to_folder('Test Template 1', 'General')
        self.assertTrue(result, "Failed to move template to folder")
        
        # Now move it to the Development folder
        result = self.template_manager.move_template_to_folder('Test Template 1', 'Development')
        self.assertTrue(result, "Failed to move template to folder")
        
        # Check if template was moved
        template = self.template_manager.get_template_by_name('Test Template 1')
        self.assertEqual(template['folder'], 'Development', "Template was not moved to the correct folder")
        
        # Check if both templates are now in the Development folder
        templates = self.template_manager.get_templates_in_folder('Development')
        self.assertEqual(len(templates), 1, "Incorrect number of templates in the Development folder after move")
    
    def test_create_folder(self):
        """Test creating a folder"""
        # Create a new folder
        result = self.template_manager.create_folder('New Folder')
        self.assertTrue(result, "Failed to create folder")
        
        # Check if folder was created
        folders = self.template_manager.get_folders()
        self.assertIn('New Folder', folders, "New folder was not created")
    
    def test_rename_folder(self):
        """Test renaming a folder"""
        # Rename the Development folder
        result = self.template_manager.rename_folder('Development', 'Dev')
        self.assertTrue(result, "Failed to rename folder")
        
        # Check if folder was renamed
        folders = self.template_manager.get_folders()
        self.assertIn('Dev', folders, "Folder was not renamed correctly")
        self.assertNotIn('Development', folders, "Old folder name still exists after rename")
        
        # Check if templates in the folder have been updated
        template = self.template_manager.get_template_by_name('Test Template 2')
        self.assertEqual(template['folder'], 'Dev', "Template folder reference was not updated")
    
    def test_delete_folder(self):
        """Test deleting a folder"""
        # Delete the Development folder
        result = self.template_manager.delete_folder('Development')
        self.assertTrue(result, "Failed to delete folder")
        
        # Check if folder was deleted
        folders = self.template_manager.get_folders()
        self.assertNotIn('Development', folders, "Folder was not deleted")
        
        # Check if templates in the folder have been moved to root
        template = self.template_manager.get_template_by_name('Test Template 2')
        self.assertEqual(template['folder'], '', "Template was not moved to root after folder deletion")

if __name__ == '__main__':
    unittest.main() 