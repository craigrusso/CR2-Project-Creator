#!/usr/bin/env python3
import os
import sys
import unittest
import json
import tempfile
import shutil
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox
from PyQt5.QtCore import Qt

from app.templates.template_operations import TemplateOperations
from app.templates.template_manager import TemplateManager
from app.core.import_export_manager import export_template

class TestDirectoryTemplate(unittest.TestCase):
    """Test cases for directory template caching functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication once for all tests"""
        cls.app = QApplication.instance() or QApplication(sys.argv)
        
    def setUp(self):
        """Set up test environment before each test"""
        # Create temp directories
        self.test_dir = tempfile.mkdtemp()
        self.templates_dir = os.path.join(self.test_dir, "templates")
        self.templates_cache_dir = os.path.join(self.templates_dir, "cache")
        self.structures_dir = os.path.join(self.test_dir, "structures")
        
        # Create the directories
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.templates_cache_dir, exist_ok=True)
        os.makedirs(self.structures_dir, exist_ok=True)
        
        # Create test project directory structure
        self.test_project_dir = os.path.join(self.test_dir, "test_project")
        os.makedirs(self.test_project_dir, exist_ok=True)
        
        # Create a few subdirectories
        self.src_dir = os.path.join(self.test_project_dir, "src")
        self.components_dir = os.path.join(self.src_dir, "components")
        self.assets_dir = os.path.join(self.test_project_dir, "assets")
        
        os.makedirs(self.src_dir, exist_ok=True)
        os.makedirs(self.components_dir, exist_ok=True)
        os.makedirs(self.assets_dir, exist_ok=True)
        
        # Create a .git directory that should be excluded
        self.git_dir = os.path.join(self.test_project_dir, ".git")
        self.git_hooks_dir = os.path.join(self.git_dir, "hooks")
        self.git_objects_dir = os.path.join(self.git_dir, "objects")
        
        os.makedirs(self.git_dir, exist_ok=True)
        os.makedirs(self.git_hooks_dir, exist_ok=True)
        os.makedirs(self.git_objects_dir, exist_ok=True)
        
        # Create some test files in each directory
        # Main files
        with open(os.path.join(self.test_project_dir, "README.md"), 'w') as f:
            f.write("# Project for {{PROJECT_NAME}}\nThis is a test project.")
            
        with open(os.path.join(self.test_project_dir, "package.json"), 'w') as f:
            f.write('{"name": "{{PROJECT_NAME}}", "version": "1.0.0"}')
        
        # Source files
        with open(os.path.join(self.src_dir, "index.js"), 'w') as f:
            f.write('console.log("Welcome to {{PROJECT_NAME}}");')
            
        with open(os.path.join(self.components_dir, "Component.js"), 'w') as f:
            f.write('export const Component = () => <div>{{PROJECT_NAME}}</div>;')
        
        # Create binary files that should be excluded
        with open(os.path.join(self.assets_dir, "image.jpg"), 'wb') as f:
            f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00')
        
        # Create git files that should be excluded
        with open(os.path.join(self.git_dir, "config"), 'w') as f:
            f.write("[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n")
            
        with open(os.path.join(self.git_hooks_dir, "pre-commit.sample"), 'w') as f:
            f.write("#!/bin/sh\nexit 0\n")
            
        with open(os.path.join(self.git_objects_dir, "hash123"), 'wb') as f:
            f.write(b'\x00\x01\x02\x03\x04')
        
        # Create a manager with our test paths
        self.template_manager = TemplateManager()
        self.template_manager.paths = {
            "templates_dir": self.templates_dir,
            "custom_structures_dir": self.structures_dir,
            "templates_cache_dir": self.templates_cache_dir
        }
        
        # Mock template operations to use our template manager
        self.template_ops = TemplateOperations()
        self.template_ops.paths = self.template_manager.paths
        self.template_ops.templates = []
        
        # Create a fake app for export testing
        self.app_mock = MagicMock()
        self.app_mock.template_manager = self.template_manager
        
    def tearDown(self):
        """Clean up after each test"""
        # Remove temp directory
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_import_directory_and_cache(self):
        """Test importing a directory correctly caches files and excludes .git"""
        # Import the test project directory
        template_name = "Directory Template"
        result = self.template_ops.import_template_file(self.test_project_dir, template_name, "Web")
        
        # Check that import was successful
        self.assertTrue(result, "Import template directory failed")
        
        # Verify template was created and added to list
        self.assertEqual(len(self.template_ops.templates), 1, "Template was not added to list")
        template = self.template_ops.templates[0]
        
        # Check template metadata
        self.assertEqual(template["name"], template_name)
        self.assertEqual(template["path"], self.test_project_dir)
        self.assertTrue("cached_path" in template, "Template missing cached_path")
        self.assertFalse(template.get("is_single_file", True), "Template is incorrectly marked as single file")
        
        # Verify cache directory exists and contains files
        cache_dir = template["cached_path"]
        self.assertTrue(os.path.exists(cache_dir), "Cache directory not created")
        
        # Check that .git directory was NOT cached
        git_cache_dir = os.path.join(cache_dir, ".git")
        self.assertFalse(os.path.exists(git_cache_dir), ".git directory was incorrectly cached")
        
        # Check that binary files were NOT cached
        image_cache = os.path.join(cache_dir, "assets", "image.jpg")
        self.assertFalse(os.path.exists(image_cache), "Binary image file was incorrectly cached")
        
        # Check that text files WITH template variables WERE cached
        readme_cache = os.path.join(cache_dir, "README.md")
        self.assertTrue(os.path.exists(readme_cache), "README.md with template variables not cached")
        
        package_cache = os.path.join(cache_dir, "package.json")
        self.assertTrue(os.path.exists(package_cache), "package.json with template variables not cached")
        
        index_cache = os.path.join(cache_dir, "src", "index.js")
        self.assertTrue(os.path.exists(index_cache), "src/index.js with template variables not cached")
        
        component_cache = os.path.join(cache_dir, "src", "components", "Component.js")
        self.assertTrue(os.path.exists(component_cache), "src/components/Component.js with template variables not cached")
        
        # Store the template for other tests
        self.test_template = template
        
    def test_export_directory_template(self):
        """Test exporting a directory template"""
        # First import and cache a directory template
        self.test_import_directory_and_cache()
        
        # Make sure our template has the correct metadata
        template = self.test_template
        self.assertFalse(template.get("is_single_file", True), "Template is incorrectly marked as single file")
        
        # We'll patch app_version attribute to avoid JSON serialization issues
        self.app_mock.app_version = "1.0.0"
        
        # Set up mocks for all file operations to avoid actual operations
        with patch('app.core.import_export_manager.QFileDialog.getSaveFileName') as mock_save_dialog, \
             patch('app.core.import_export_manager.QMessageBox.information') as mock_info, \
             patch('app.core.import_export_manager.QMessageBox.warning') as mock_warning, \
             patch('app.core.import_export_manager.QMessageBox.critical') as mock_critical, \
             patch('app.core.import_export_manager.tempfile.TemporaryDirectory'), \
             patch('app.core.import_export_manager.os.path.exists', return_value=True), \
             patch('app.core.import_export_manager.os.makedirs'), \
             patch('app.core.import_export_manager.open', create=True), \
             patch('app.core.import_export_manager.json.dump'), \
             patch('app.core.import_export_manager.shutil.copy2'), \
             patch('app.core.import_export_manager.shutil.copytree'), \
             patch('app.core.import_export_manager.zipfile.ZipFile', create=True) as mock_zipfile:
            
            # Configure the file dialog mock to return a path
            export_path = os.path.join(self.test_dir, "exported_template.zip")
            mock_save_dialog.return_value = (export_path, "ZIP Files (*.zip)")
            
            # Mock app.template_manager.get_template_by_name to return our template
            self.app_mock.template_manager.get_template_by_name = MagicMock(return_value=template)
            
            # Call the function we're testing
            export_template(self.app_mock, template["name"], include_files=True)
            
            # Verify required calls were made
            mock_save_dialog.assert_called_once()
            mock_info.assert_called_once()
            mock_warning.assert_not_called()
            mock_critical.assert_not_called()
            
            # Verify zipfile creation
            mock_zipfile.assert_called_once()
            
            # Check that copy operations occurred - since we're mocking files
            # we just verify that copy2 was called at least once for our cached files
            copy_calls = shutil.copy2.mock_calls
            self.assertGreater(len(copy_calls), 0, "No copy operations performed")
            
            # Since our test doesn't actually create real files, we can't test
            # the exact content of the zip file, but we can verify the process ran

if __name__ == '__main__':
    unittest.main() 