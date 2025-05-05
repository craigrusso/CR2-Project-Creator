#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import unittest
import os
import shutil
import tempfile
import zipfile
import json
from unittest.mock import MagicMock, patch

from app.core.import_export_manager import export_template
from app.utils.cache.file_cache_manager import FileCacheManager

class TestTemplateExport(unittest.TestCase):
    """Test the template export functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.template_dir = os.path.join(self.temp_dir, "templates")
        self.cache_dir = os.path.join(self.temp_dir, "cache")
        self.export_dir = os.path.join(self.temp_dir, "export")
        self.test_files_dir = os.path.join(self.temp_dir, "test_files")
        
        # Create directories
        os.makedirs(self.template_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.export_dir, exist_ok=True)
        os.makedirs(self.test_files_dir, exist_ok=True)
        
        # Create test files
        self.original_file1_path = os.path.join(self.test_files_dir, "test_file1.txt")
        self.original_file2_path = os.path.join(self.test_files_dir, "test_file2.py")
        self.original_subfolder_path = os.path.join(self.test_files_dir, "subfolder")
        os.makedirs(self.original_subfolder_path, exist_ok=True)
        self.original_file3_path = os.path.join(self.original_subfolder_path, "test_file3.json")
        
        # Write content to test files
        with open(self.original_file1_path, 'w') as f:
            f.write("This is test file 1")
        with open(self.original_file2_path, 'w') as f:
            f.write("print('This is test file 2')")
        with open(self.original_file3_path, 'w') as f:
            f.write('{"key": "This is test file 3"}')
        
        # Cache some files
        self.cache_manager = FileCacheManager(self.cache_dir)
        self.template_name = "TestTemplate"
        
        # Cache test files
        self.cached_file1 = self.cache_manager.cache_file(
            self.original_file1_path, 
            self.template_name, 
            "docs"
        )
        self.cached_file2 = self.cache_manager.cache_file(
            self.original_file2_path,
            self.template_name,
            "src"
        )
        self.cached_file3 = self.cache_manager.cache_file(
            self.original_file3_path,
            self.template_name,
            "config"
        )
        
        # Create a mock template
        self.template = {
            "name": self.template_name,
            "description": "Test template for export",
            "created": 1234567890,
            "modified": 1234567890,
            "category": "Test",
            "type": "Standard",
            "path": self.test_files_dir,
            "cached_path": self.cache_dir,
            "files": [
                {
                    "file_name": "test_file1.txt",
                    "original_path": self.original_file1_path,
                    "cached_path": self.cached_file1,
                    "folder": "docs",
                    "file_type": "document",
                    "file_size": os.path.getsize(self.original_file1_path)
                },
                {
                    "file_name": "test_file2.py",
                    "original_path": self.original_file2_path,
                    "cached_path": self.cached_file2,
                    "folder": "src",
                    "file_type": "code",
                    "file_size": os.path.getsize(self.original_file2_path)
                },
                {
                    "file_name": "test_file3.json",
                    "original_path": self.original_file3_path,
                    "cached_path": self.cached_file3,
                    "folder": "config",
                    "file_type": "code",
                    "file_size": os.path.getsize(self.original_file3_path)
                }
            ],
            "structure": [
                {
                    "type": "folder",
                    "name": "docs",
                    "children": [
                        "test_file1.txt"
                    ]
                },
                {
                    "type": "folder",
                    "name": "src",
                    "children": [
                        "test_file2.py"
                    ]
                },
                {
                    "type": "folder",
                    "name": "config",
                    "children": [
                        "test_file3.json"
                    ]
                }
            ]
        }
        
        # Save template to a file
        self.template_file_path = os.path.join(self.template_dir, f"{self.template_name}.json")
        with open(self.template_file_path, 'w') as f:
            json.dump(self.template, f, indent=2)
        
        # Create a mock app for testing
        self.mock_app = MagicMock()
        self.mock_app.template_manager.get_template_by_name.return_value = self.template
    
    def tearDown(self):
        """Clean up after test"""
        # Remove temporary directories
        shutil.rmtree(self.temp_dir)
    
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
        
        # Check that the files directory exists
        files_dir = os.path.join(extract_dir, "template", "files")
        self.assertTrue(os.path.exists(files_dir), "Files directory is missing")
        
        # Check for specific files with their expected folder structure
        self.assertTrue(os.path.exists(os.path.join(files_dir, "docs", "test_file1.txt")), 
                        "test_file1.txt is missing from docs folder")
        self.assertTrue(os.path.exists(os.path.join(files_dir, "src", "test_file2.py")), 
                        "test_file2.py is missing from src folder")
        self.assertTrue(os.path.exists(os.path.join(files_dir, "config", "test_file3.json")), 
                        "test_file3.json is missing from config folder")
        
        # Verify file contents
        with open(os.path.join(files_dir, "docs", "test_file1.txt"), 'r') as f:
            self.assertEqual(f.read(), "This is test file 1", "Content of test_file1.txt is incorrect")
        
        with open(os.path.join(files_dir, "src", "test_file2.py"), 'r') as f:
            self.assertEqual(f.read(), "print('This is test file 2')", "Content of test_file2.py is incorrect")
        
        with open(os.path.join(files_dir, "config", "test_file3.json"), 'r') as f:
            self.assertEqual(f.read(), '{"key": "This is test file 3"}', "Content of test_file3.json is incorrect")
    
    @patch('app.core.import_export_manager.QFileDialog.getSaveFileName')
    def test_export_template_without_files(self, mock_get_save_file_name):
        """Test exporting a template without files"""
        # Mock QFileDialog.getSaveFileName to return a predetermined path
        export_zip_path = os.path.join(self.export_dir, f"{self.template_name}_no_files.zip")
        mock_get_save_file_name.return_value = (export_zip_path, "ZIP Files (*.zip)")
        
        # Call export_template with include_files=False
        export_template(self.mock_app, self.template_name, include_files=False)
        
        # Verify that the ZIP file was created
        self.assertTrue(os.path.exists(export_zip_path), "Export ZIP file was not created")
        
        # Extract the ZIP and examine its contents
        extract_dir = os.path.join(self.export_dir, "extracted_no_files")
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(export_zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Check for expected structure
        self.assertTrue(os.path.exists(os.path.join(extract_dir, "template_metadata.json")), 
                        "template_metadata.json file is missing")
        
        self.assertTrue(os.path.exists(os.path.join(extract_dir, "template", "template.json")), 
                        "template.json file is missing")
        
        # Check metadata to ensure it correctly indicates no files included
        with open(os.path.join(extract_dir, "template_metadata.json"), 'r') as f:
            metadata = json.load(f)
            self.assertFalse(metadata.get('includes_files', True), 
                            "Metadata incorrectly indicates that files are included")
        
        # Verify files directory doesn't contain any files (if it exists at all)
        files_dir = os.path.join(extract_dir, "template", "files")
        if os.path.exists(files_dir):
            self.assertEqual(len(os.listdir(files_dir)), 0, 
                            "Files directory should be empty when include_files=False")
    
    @patch('app.core.import_export_manager.QFileDialog.getSaveFileName')
    def test_export_template_with_missing_original_files(self, mock_get_save_file_name):
        """Test exporting a template with missing original files (should fall back to cache)"""
        # Mock QFileDialog.getSaveFileName to return a predetermined path
        export_zip_path = os.path.join(self.export_dir, f"{self.template_name}_fallback.zip")
        mock_get_save_file_name.return_value = (export_zip_path, "ZIP Files (*.zip)")
        
        # Modify the template to have invalid original paths but valid cached paths
        self.template["files"][0]["original_path"] = "/nonexistent/path/test_file1.txt"
        self.template["files"][1]["original_path"] = "/nonexistent/path/test_file2.py"
        self.template["files"][2]["original_path"] = "/nonexistent/path/test_file3.json"
        self.template["path"] = "/nonexistent/path"
        
        # Update the mock to use our modified template
        self.mock_app.template_manager.get_template_by_name.return_value = self.template
        
        # Call export_template with include_files=True
        export_template(self.mock_app, self.template_name, include_files=True)
        
        # Verify that the ZIP file was created
        self.assertTrue(os.path.exists(export_zip_path), "Export ZIP file was not created")
        
        # Extract the ZIP and examine its contents
        extract_dir = os.path.join(self.export_dir, "extracted_fallback")
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(export_zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Check for expected structure and files - should fall back to using cached files
        files_dir = os.path.join(extract_dir, "template", "files")
        
        # Since we're testing fallback to cache, we should find the files even though original paths are invalid
        self.assertTrue(os.path.exists(os.path.join(files_dir, "docs", "test_file1.txt")) or
                        os.path.exists(os.path.join(files_dir, "test_file1.txt")), 
                        "test_file1.txt is missing after fallback to cache")
        
        self.assertTrue(os.path.exists(os.path.join(files_dir, "src", "test_file2.py")) or
                        os.path.exists(os.path.join(files_dir, "test_file2.py")), 
                        "test_file2.py is missing after fallback to cache")
        
        self.assertTrue(os.path.exists(os.path.join(files_dir, "config", "test_file3.json")) or
                        os.path.exists(os.path.join(files_dir, "test_file3.json")), 
                        "test_file3.json is missing after fallback to cache")

if __name__ == '__main__':
    unittest.main() 