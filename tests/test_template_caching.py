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

from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox
from PyQt6.QtCore import Qt

from app.templates.template_operations import TemplateOperations
from app.templates.template_manager import TemplateManager
from app.core.import_export_manager import export_template

class TestTemplateCaching(unittest.TestCase):
    """Test cases for template caching and export functionality"""
    
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
        
        # Create test files
        self.test_file_dir = os.path.join(self.test_dir, "test_files")
        os.makedirs(self.test_file_dir, exist_ok=True)
        
        # Create a sample test file
        self.test_file = os.path.join(self.test_file_dir, "test_template.txt")
        with open(self.test_file, 'w') as f:
            f.write("This is a test template file with {{PROJECT_NAME}} placeholder.")
        
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
        
    def test_import_file_and_cache(self):
        """Test importing a file creates proper cache"""
        # Import the test file
        template_name = "Test Template"
        result = self.template_ops.import_template_file(self.test_file, template_name, "Text")
        
        # Check that import was successful
        self.assertTrue(result, "Import template file failed")
        
        # Verify template was created and added to list
        self.assertEqual(len(self.template_ops.templates), 1, "Template was not added to list")
        template = self.template_ops.templates[0]
        
        # Check template metadata
        self.assertEqual(template["name"], template_name)
        self.assertEqual(template["path"], self.test_file)
        self.assertTrue("cached_path" in template, "Template missing cached_path")
        
        # Check that caching flag is set correctly
        self.assertTrue(template.get("should_cache_files", False), 
                        "should_cache_files flag not set to True")
        
        # Verify cache directory exists and contains the file
        cache_dir = template["cached_path"]
        self.assertTrue(os.path.exists(cache_dir), "Cache directory not created")
        
        # Check if file was cached
        cached_files = os.listdir(cache_dir)
        self.assertTrue(len(cached_files) > 0, "No files were cached")
        
        # Verify the content of the cached file
        cached_file = os.path.join(cache_dir, os.path.basename(self.test_file))
        self.assertTrue(os.path.exists(cached_file), "File not found in cache directory")
        
        # Check content
        with open(cached_file, 'r') as f:
            content = f.read()
        self.assertIn("{{PROJECT_NAME}}", content, "Cached file content is incorrect")
        
        # Store the template for other tests to use
        self.test_template = template
    
    def test_export_template(self):
        """Test exporting a template with cached files"""
        # First import and cache a template
        self.test_import_file_and_cache()
        
        # Create a real template object instead of a MagicMock
        # to avoid JSON serialization issues
        template = self.test_template
        
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

if __name__ == '__main__':
    unittest.main() 