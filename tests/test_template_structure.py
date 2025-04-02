#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test that templates without structure are properly handled
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import from app
from app.core.project_builder import ProjectBuilder
from app.core.project_operations import template_has_structure

class TestTemplateStructure(unittest.TestCase):
    """Test template structure validation and handling"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_builder = ProjectBuilder(None)
    
    def test_template_has_structure(self):
        """Test the template_has_structure function"""
        # Test with empty template
        self.assertFalse(template_has_structure(None))
        self.assertFalse(template_has_structure({}))
        
        # Test with template without structure
        template_no_structure = {
            'name': 'Test Template',
            'description': 'Template without structure'
        }
        self.assertFalse(template_has_structure(template_no_structure))
        
        # Test with template with empty structure
        template_empty_structure = {
            'name': 'Empty Structure',
            'structure': {}
        }
        self.assertFalse(template_has_structure(template_empty_structure))
        
        # Test with template with empty folders
        template_empty_folders = {
            'name': 'Empty Folders',
            'structure': {
                'folders': {}
            }
        }
        self.assertFalse(template_has_structure(template_empty_folders))
        
        # Test with template with valid dict structure
        template_valid_dict = {
            'name': 'Valid Dict',
            'structure': {
                'folders': {
                    'src': {},
                    'docs': {}
                }
            }
        }
        self.assertTrue(template_has_structure(template_valid_dict))
        
        # Test with template with valid list structure
        template_valid_list = {
            'name': 'Valid List',
            'structure': [
                {
                    'type': 'folder',
                    'name': 'src',
                    'children': []
                }
            ]
        }
        self.assertTrue(template_has_structure(template_valid_list))
    
    def test_create_project_with_no_structure(self):
        """Test creating a project with a template that has no structure"""
        # Create a test template with no structure
        template_no_structure = {
            'name': 'No Structure Template',
            'description': 'Template without structure',
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'files': []  # Empty files array
        }
        
        # Try to create project
        result, info = self.project_builder.create_project(
            project_name="TestNoStructure",
            output_dir=self.temp_dir,
            template_file=template_no_structure
        )
        
        # Verify result - should be success but with no_structure flag
        self.assertTrue(result)
        self.assertTrue(isinstance(info, dict))
        self.assertTrue(info.get('no_structure', False))
        
        # Verify project directory exists
        project_dir = info.get('project_dir')
        self.assertTrue(os.path.exists(project_dir))
        
        # Verify no default folders were created
        self.assertFalse(os.path.exists(os.path.join(project_dir, 'src')))
        self.assertFalse(os.path.exists(os.path.join(project_dir, 'docs')))
        self.assertFalse(os.path.exists(os.path.join(project_dir, 'resources')))
    
    def test_create_project_with_structure(self):
        """Test creating a project with a template that has structure"""
        # Create a test template with structure
        template_with_structure = {
            'name': 'With Structure Template',
            'description': 'Template with structure',
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'structure': {
                'folders': {
                    'src': {},
                    'docs': {},
                    'resources': {}
                }
            },
            'files': []  # Empty files array
        }
        
        # Try to create project
        result, info = self.project_builder.create_project(
            project_name="TestWithStructure",
            output_dir=self.temp_dir,
            template_file=template_with_structure
        )
        
        # Verify result
        self.assertTrue(result)
        
        # Get project path (may be a string or dict with project_dir)
        if isinstance(info, dict):
            project_dir = info.get('project_dir')
            # Verify it doesn't have no_structure flag
            self.assertFalse(info.get('no_structure', False))
        else:
            project_dir = info
        
        # Verify project directory exists
        self.assertTrue(os.path.exists(project_dir))
        
        # Verify folders were created
        self.assertTrue(os.path.exists(os.path.join(project_dir, 'src')))
        self.assertTrue(os.path.exists(os.path.join(project_dir, 'docs')))
        self.assertTrue(os.path.exists(os.path.join(project_dir, 'resources')))
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove temporary directory and its contents
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()

 