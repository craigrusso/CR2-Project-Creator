#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import sys
import json
import shutil
import tempfile
import unittest
import zipfile
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the functions to test
from app.core.import_export_manager import export_template, import_template


# Mock QMessageBox class
class MockQMessageBox:
    # Standard button constants
    NoButton = 0
    Yes = 16384  # Same values as in PyQt
    No = 65536
    Ok = 1024
    Cancel = 4194304
    Close = 2097152
    Open = 8388608
    Save = 2048
    Discard = 8192
    
    @classmethod
    def information(cls, *args, **kwargs):
        return None
    
    @classmethod
    def warning(cls, *args, **kwargs):
        return None
    
    @classmethod
    def critical(cls, *args, **kwargs):
        return None
    
    def __init__(self, *args, **kwargs):
        self.text_value = ""
        self.buttons = []
        self.window_title = ""
    
    def setText(self, text):
        self.text_value = text
    
    def setInformativeText(self, text):
        self.informative_text = text
    
    def setStandardButtons(self, buttons):
        self.buttons = buttons
    
    def setDefaultButton(self, button):
        self.default_button = button
    
    def setWindowTitle(self, title):
        self.window_title = title
    
    def exec_(self):
        return 0  # Simulate clicking "No"


# Add patches for QMessageBox
@patch('app.core.import_export_manager.QMessageBox', MockQMessageBox)
@patch('app.core.import_export_manager.QMessageBox.information', MockQMessageBox.information)
@patch('app.core.import_export_manager.QMessageBox.critical', MockQMessageBox.critical)
@patch('app.core.import_export_manager.QMessageBox.warning', MockQMessageBox.warning)
class TestTemplateImportExport(unittest.TestCase):
    """Test the template import/export functionality with a focus on file handling"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for the test
        self.temp_dir = tempfile.mkdtemp()
        self.export_dir = os.path.join(self.temp_dir, "exports")
        os.makedirs(self.export_dir, exist_ok=True)
        
        # Create cache dir
        self.cache_dir = os.path.join(self.temp_dir, "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Create templates dir
        self.templates_dir = os.path.join(self.temp_dir, "templates")
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Create custom structures dir
        self.structures_dir = os.path.join(self.temp_dir, "structures")
        os.makedirs(self.structures_dir, exist_ok=True)
        
        # Template information
        self.template_name = "Test Template"
        self.template_path = os.path.join(self.templates_dir, "test_template.json")
        
        # Create test files
        self.test_files_dir = os.path.join(self.temp_dir, "test_files")
        os.makedirs(self.test_files_dir, exist_ok=True)
        
        # Create test files with content
        self.test_file1 = os.path.join(self.test_files_dir, "test1.txt")
        with open(self.test_file1, 'w') as f:
            f.write("This is test file 1")
        
        self.test_file2 = os.path.join(self.test_files_dir, "subfolder", "test2.txt")
        os.makedirs(os.path.dirname(self.test_file2), exist_ok=True)
        with open(self.test_file2, 'w') as f:
            f.write("This is test file 2 in a subfolder")
        
        # Create a mock file cache manager
        self.mock_file_cache_manager = MagicMock()
        self.mock_file_cache_manager.cache_dir = self.cache_dir
        self.mock_file_cache_manager.cache_file.side_effect = self._mock_cache_file
        
        # Create a template with files
        self.template = {
            "name": self.template_name,
            "category": "Test",
            "description": "Test template for import/export",
            "structure_name": f"Template_{self.template_name.replace(' ', '_')}",
            "structure": [
                {"name": "Folder1", "type": "folder", "children": [
                    {"name": "test1.txt", "type": "file"}
                ]},
                {"name": "subfolder", "type": "folder", "children": [
                    {"name": "test2.txt", "type": "file"}
                ]}
            ],
            "files": [
                {
                    "file_name": "test1.txt",
                    "folder": "Folder1/",
                    "original_path": self.test_file1,
                    "cached_path": os.path.join(self.cache_dir, self.template_name.replace(" ", "_"), "Folder1", "test1.txt"),
                    "file_type": "txt",
                    "size": os.path.getsize(self.test_file1),
                    "is_binary": False,
                    "path": "Folder1/test1.txt"
                },
                {
                    "file_name": "test2.txt",
                    "folder": "subfolder/",
                    "original_path": self.test_file2,
                    "cached_path": os.path.join(self.cache_dir, self.template_name.replace(" ", "_"), "subfolder", "test2.txt"),
                    "file_type": "txt",
                    "size": os.path.getsize(self.test_file2),
                    "is_binary": False,
                    "path": "subfolder/test2.txt"
                }
            ],
            "cached_path": self.cache_dir,
            "path": self.test_files_dir
        }
        
        # Ensure cache directories exist
        os.makedirs(os.path.join(self.cache_dir, self.template_name.replace(" ", "_"), "Folder1"), exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, self.template_name.replace(" ", "_"), "subfolder"), exist_ok=True)
        
        # Copy files to cache
        shutil.copy2(self.test_file1, os.path.join(self.cache_dir, self.template_name.replace(" ", "_"), "Folder1", "test1.txt"))
        shutil.copy2(self.test_file2, os.path.join(self.cache_dir, self.template_name.replace(" ", "_"), "subfolder", "test2.txt"))
        
        # Save template to file
        with open(self.template_path, 'w') as f:
            json.dump(self.template, f, indent=2)
        
        # Create a mock app for testing
        self.mock_app = MagicMock()
        self.mock_app.template_manager.get_template_by_name.return_value = self.template
        self.mock_app.template_manager.edit_template.return_value = True
        self.mock_app.template_manager.file_cache_manager = self.mock_file_cache_manager
        self.mock_app.template_manager.paths = {
            "templates_dir": self.templates_dir,
            "custom_structures_dir": self.structures_dir,
            "cache_dir": self.cache_dir
        }
        self.mock_app.app_version = "1.0.0"
    
    def tearDown(self):
        """Clean up after test"""
        # Remove temporary directories
        shutil.rmtree(self.temp_dir)
    
    def _mock_cache_file(self, file_path, template_name, folder_path='', **kwargs):
        """Mock implementation of cache_file for testing"""
        if not os.path.exists(file_path):
            return None
        
        # Create directory structure in cache
        cache_dir = os.path.join(self.cache_dir, template_name)
        if folder_path:
            cache_dir = os.path.join(cache_dir, folder_path)
        
        os.makedirs(cache_dir, exist_ok=True)
        
        # Get filename and destination path
        filename = os.path.basename(file_path)
        dest_path = os.path.join(cache_dir, filename)
        
        # Copy file to cache
        shutil.copy2(file_path, dest_path)
        
        return dest_path
    
    @patch('app.core.import_export_manager.QFileDialog.getSaveFileName')
    def test_export_template_with_files(self, mock_get_save_file_name):
        """Test exporting a template with files"""
        # Mock QFileDialog.getSaveFileName to return a predetermined path
        export_zip_path = os.path.join(self.export_dir, f"{self.template_name}.zip")
        mock_get_save_file_name.return_value = (export_zip_path, "ZIP Files (*.zip)")
        
        # Call export_template with include_files=True
        export_template(self.mock_app, self.template_name, include_files=True)
        
        # Verify that the ZIP file was created
        self.assertTrue(os.path.exists(export_zip_path), "Export ZIP file was not created")
        
        # Extract the ZIP and examine its contents
        extract_dir = os.path.join(self.export_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(export_zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Check for expected structure and files
        self.assertTrue(os.path.exists(os.path.join(extract_dir, "template_metadata.json")), 
                       "template_metadata.json file is missing")
        
        self.assertTrue(os.path.exists(os.path.join(extract_dir, "template", "template.json")), 
                       "template.json file is missing")
        
        # Check for the files directory
        files_dir = os.path.join(extract_dir, "template", "files")
        self.assertTrue(os.path.exists(files_dir), "Files directory is missing")
        
        # Check if the exported files exist and maintain folder structure
        self.assertTrue(os.path.exists(os.path.join(files_dir, "Folder1", "test1.txt")), 
                       "test1.txt file is missing or in wrong location")
        
        self.assertTrue(os.path.exists(os.path.join(files_dir, "subfolder", "test2.txt")), 
                       "test2.txt file is missing or in wrong location")
        
        # Verify that the exported files have the correct content
        with open(os.path.join(files_dir, "Folder1", "test1.txt"), 'r') as f:
            content = f.read()
            self.assertEqual(content, "This is test file 1", "test1.txt has incorrect content")
        
        with open(os.path.join(files_dir, "subfolder", "test2.txt"), 'r') as f:
            content = f.read()
            self.assertEqual(content, "This is test file 2 in a subfolder", "test2.txt has incorrect content")
        
        # Load the template.json and check if it has the correct structure and file references
        with open(os.path.join(extract_dir, "template", "template.json"), 'r') as f:
            exported_template = json.load(f)
            
            self.assertEqual(exported_template["name"], self.template_name, "Template name doesn't match")
            self.assertTrue("structure" in exported_template, "Structure data missing in exported template")
            self.assertTrue("files" in exported_template, "Files array missing in exported template")
    
    @patch('app.core.import_export_manager.QFileDialog.getOpenFileName')
    @patch('PyQt5.QtWidgets.QInputDialog.getText')
    def test_import_template_with_files(self, mock_input_dialog, mock_get_open_file_name):
        """Test importing a template with files"""
        # First export a template to get a valid ZIP file
        export_zip_path = os.path.join(self.export_dir, f"{self.template_name}.zip")
        with patch('app.core.import_export_manager.QFileDialog.getSaveFileName', return_value=(export_zip_path, "ZIP Files (*.zip)")):
            export_template(self.mock_app, self.template_name, include_files=True)
        
        # Mock QFileDialog.getOpenFileName to return the exported ZIP
        mock_get_open_file_name.return_value = (export_zip_path, "ZIP Files (*.zip)")
        
        # Change the template name to avoid conflicts during import
        import_template_name = f"{self.template_name}_Imported"
        
        # Mock QInputDialog.getText to return a new name
        mock_input_dialog.return_value = (import_template_name, True)
        
        # Call import_template with the exported ZIP
        import_template(self.mock_app, export_zip_path)
        
        # Verify that template_manager.edit_template was called with the imported template
        self.mock_app.template_manager.edit_template.assert_called()
        
        # Get the template data that was passed to edit_template
        imported_template = self.mock_app.template_manager.edit_template.call_args[0][0]
        
        # Check that the imported template has the expected properties
        self.assertEqual(imported_template["name"], import_template_name, "Imported template name doesn't match")
        self.assertTrue("structure" in imported_template, "Structure data missing in imported template")
        self.assertTrue("files" in imported_template, "Files array missing in imported template")
        self.assertTrue("cached_path" in imported_template, "Cached path missing in imported template")
        
        # Check that populate_gallery was called to refresh the UI
        self.mock_app.template_gallery.populate_gallery.assert_called_with(force_refresh=True)
    
    def test_export_then_import_flow(self):
        """Test the complete export and import flow"""
        # Export the template
        export_zip_path = os.path.join(self.export_dir, f"{self.template_name}.zip")
        with patch('app.core.import_export_manager.QFileDialog.getSaveFileName', return_value=(export_zip_path, "ZIP Files (*.zip)")):
            export_template(self.mock_app, self.template_name, include_files=True)
        
        # Verify the export succeeded
        self.assertTrue(os.path.exists(export_zip_path), "Export ZIP file was not created")
        
        # Create a new mock app for import testing
        import_app = MagicMock()
        import_app.template_manager.get_template_by_name.return_value = None  # No existing template
        import_app.template_manager.edit_template.return_value = True
        import_app.template_manager.file_cache_manager = self.mock_file_cache_manager
        import_app.template_manager.paths = {
            "templates_dir": os.path.join(self.temp_dir, "import_templates"),
            "custom_structures_dir": os.path.join(self.temp_dir, "import_structures"),
            "cache_dir": os.path.join(self.temp_dir, "import_cache")
        }
        
        # Create the import directories
        os.makedirs(import_app.template_manager.paths["templates_dir"], exist_ok=True)
        os.makedirs(import_app.template_manager.paths["custom_structures_dir"], exist_ok=True)
        os.makedirs(import_app.template_manager.paths["cache_dir"], exist_ok=True)
        
        # Import the template
        with patch('PyQt5.QtWidgets.QFileDialog.getOpenFileName', return_value=(export_zip_path, "ZIP Files (*.zip)")):
            import_template(import_app, export_zip_path)
        
        # Verify the import succeeded
        import_app.template_manager.edit_template.assert_called()
        
        # Get the imported template data
        imported_template = import_app.template_manager.edit_template.call_args[0][0]
        
        # Verify correct template properties
        self.assertEqual(imported_template["name"], self.template_name, "Imported template name doesn't match")
        self.assertTrue("structure" in imported_template, "Structure missing in imported template")
        self.assertTrue("files" in imported_template, "Files array missing in imported template")
        self.assertTrue("cached_path" in imported_template, "Cache path missing in imported template")
        
        # Verify UI refresh
        import_app.template_gallery.populate_gallery.assert_called_with(force_refresh=True)


if __name__ == "__main__":
    unittest.main() 