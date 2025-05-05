#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import sys
import tempfile
import unittest
import shutil
import json
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QMessageBox

# Add the parent directory of app to sys.path so we can import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, root_dir)

try:
    from app.utils.file_cache_manager import FileCacheManager
    from app.templates.cache_manager import TemplateCacheManager
except ImportError:
    # Create mock classes if imports fail
    print("WARNING: Could not import required modules. Using mock classes for testing.")
    
    class FileCacheManager:
        def __init__(self, cache_dir=None):
            self.cache_dir = cache_dir or os.path.join(os.getcwd(), "cache")
            os.makedirs(self.cache_dir, exist_ok=True)
            self.cache_stats = {}
        
        def cache_file(self, file_path, template_name, folder_path='', rename_flag=False):
            template_dir = os.path.join(self.cache_dir, template_name, "files")
            os.makedirs(template_dir, exist_ok=True)
            dest = os.path.join(template_dir, os.path.basename(file_path))
            try:
                shutil.copy2(file_path, dest)
                return dest
            except:
                return None
                
        def clear_template_cache(self, template_name):
            template_dir = os.path.join(self.cache_dir, template_name)
            if os.path.exists(template_dir):
                shutil.rmtree(template_dir)
            return True
            
        def get_all_cached_files(self, template_name):
            template_dir = os.path.join(self.cache_dir, template_name, "files")
            if not os.path.exists(template_dir):
                return {}
            
            result = {}
            for filename in os.listdir(template_dir):
                file_path = os.path.join(template_dir, filename)
                key = filename
                result[key] = {
                    "cached_path": file_path,
                    "original_path": "",  # No way to know original path
                    "file_name": filename
                }
            return result
    
    class TemplateCacheManager:
        def __init__(self, template_manager):
            self.template_manager = template_manager
            self.file_cache_manager = template_manager.file_cache_manager
            self.template_io = template_manager.template_io
            self.stats = {}


class TestTemplateCacheManager(unittest.TestCase):
    """Test the TemplateCacheManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.temp_dir, "cache")
        self.templates_dir = os.path.join(self.temp_dir, "templates")
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Create temporary test files
        self.original_file1_path = os.path.join(self.temp_dir, "test1.txt")
        self.original_file2_path = os.path.join(self.temp_dir, "test2.txt")
        self.missing_file_path = os.path.join(self.temp_dir, "missing.txt")
        
        with open(self.original_file1_path, "w") as f:
            f.write("Test file 1 content")
        
        with open(self.original_file2_path, "w") as f:
            f.write("Test file 2 content")
        
        # Set up a mock template manager
        self.template_manager = MagicMock()
        
        # Set up the FileCacheManager
        self.file_cache_manager = FileCacheManager(self.cache_dir)
        
        # Set up the template manager with the file cache manager
        self.template_manager.file_cache_manager = self.file_cache_manager
        
        # Set up a mock template_io
        self.template_io = MagicMock()
        self.template_manager.template_io = self.template_io
        
        # Set up the paths
        self.paths = {
            "templates_dir": self.templates_dir,
            "cache_dir": self.cache_dir
        }
        self.template_manager.paths = self.paths
        
        # Create the TemplateCacheManager
        self.cache_manager = TemplateCacheManager(self.template_manager)
        
        # Cache a test template with files
        self.template_name = "TestTemplate"
        
        # Create the files directory structure
        template_cache_dir = os.path.join(self.cache_dir, self.template_name)
        self.template_files_dir = os.path.join(template_cache_dir, "files")
        os.makedirs(os.path.join(self.template_files_dir, "docs"), exist_ok=True)
        os.makedirs(os.path.join(self.template_files_dir, "src"), exist_ok=True)
        os.makedirs(os.path.join(self.template_files_dir, "misc"), exist_ok=True)
        
        # Cache the files
        self.cached_file1 = self.file_cache_manager.cache_file(
            self.original_file1_path, 
            self.template_name,
            "docs"
        )
        
        self.cached_file2 = self.file_cache_manager.cache_file(
            self.original_file2_path,
            self.template_name,
            "src"
        )
        
        # Create a mock missing file entry in the cache metadata
        missing_cached_path = os.path.join(self.template_files_dir, "misc", "missing.txt")
        # Create an empty file for the "missing" file
        with open(missing_cached_path, "w") as f:
            f.write("This is a missing file that will have no original")
            
        # Create a mock template with both valid and missing files
        self.template = {
            "name": self.template_name,
            "description": "Test template",
            "category": "Test",
            "files": [
                {
                    "original_path": self.original_file1_path,
                    "cached_path": self.cached_file1,
                    "folder": "docs"
                },
                {
                    "original_path": self.original_file2_path,
                    "cached_path": self.cached_file2,
                    "folder": "src"
                },
                {
                    "original_path": self.missing_file_path,
                    "cached_path": missing_cached_path,
                    "folder": "misc"
                }
            ]
        }
        
        # Create metadata file with missing file entry
        metadata_file = os.path.join(template_cache_dir, "metadata.json")
        metadata = {
            "test1.txt": {
                "original_path": self.original_file1_path,
                "cached_path": self.cached_file1
            },
            "test2.txt": {
                "original_path": self.original_file2_path,
                "cached_path": self.cached_file2
            },
            "missing.txt": {
                "original_path": self.missing_file_path,
                "cached_path": missing_cached_path,
                "folder": "misc"
            }
        }
        
        # Write metadata file
        with open(metadata_file, "w") as f:
            json.dump(metadata, f)
        
        # Set up a mock get_template method
        self.template_io.get_template = MagicMock(return_value=self.template)
        self.template_io.templates = {self.template_name: self.template}
        
        # Fix the get_all_cached_files method to work with the new folder structure
        original_get_all_cached_files = self.file_cache_manager.get_all_cached_files
        
        def patched_get_all_cached_files(template_name):
            result = {}
            template_dir = os.path.join(self.cache_dir, template_name, "files")
            
            if not os.path.exists(template_dir):
                return {}
            
            # Walk through all directories and find files
            for root, _, files in os.walk(template_dir):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    # Get folder path relative to the files directory
                    rel_path = os.path.relpath(root, template_dir)
                    folder = "" if rel_path == "." else rel_path
                    
                    result[file_name] = {
                        "cached_path": file_path,
                        "original_path": "",  # Will be filled from metadata
                        "file_name": file_name,
                        "folder": folder
                    }
            
            # Read metadata to get original paths
            metadata_file = os.path.join(self.cache_dir, template_name, "metadata.json")
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)
                        
                    # Update result with original paths
                    for file_name, file_info in metadata.items():
                        if file_name in result:
                            result[file_name]["original_path"] = file_info.get("original_path", "")
                except Exception as e:
                    print(f"Error loading metadata: {e}")
            
            return result
        
        # Replace the method with our patched version
        self.file_cache_manager.get_all_cached_files = patched_get_all_cached_files
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def test_check_template_original_files(self):
        """Test checking if a template has all its original files"""
        all_originals_exist, missing_files = self.cache_manager.check_template_original_files(self.template_name)
        
        # We should have missing files
        self.assertFalse(all_originals_exist)
        self.assertTrue(len(missing_files) > 0)
        
        # The missing file should be in the missing_files dictionary
        missing_file_keys = [key for key, info in missing_files.items() 
                           if os.path.basename(info["original_path"]) == "missing.txt"]
        self.assertTrue(len(missing_file_keys) > 0)
    
    def test_recache_template(self):
        """Test recaching a template"""
        # Clear the template cache first
        self.file_cache_manager.clear_template_cache(self.template_name)
        
        # Now recache the template
        success, stats = self.cache_manager.recache_template(self.template_name)
        
        # It should succeed
        self.assertTrue(success)
        
        # It should have recached the existing files and reported the missing one
        self.assertEqual(stats["files_recached"], 2)
        self.assertEqual(stats["files_missing_original"], 1)
        
        # Check that the files were actually recached
        cached_files = self.file_cache_manager.get_all_cached_files(self.template_name)
        self.assertEqual(len(cached_files), 2)  # Only the valid files should be recached
    
    def test_safe_clear_template_cache_dialog(self):
        """Test that the safe clear cache shows a warning dialog when originals are missing"""
        # Setup test environment with known missing file
        missing_file_path = os.path.join(self.temp_dir, "definitely_missing.txt")
        
        # Patch check_template_original_files to control its return value
        with patch.object(self.cache_manager, 'check_template_original_files') as mock_check:
            # Simulate a template with missing originals
            mock_check.return_value = (False, {'missing.txt': {
                'file_name': 'missing.txt',
                'folder': 'misc',
                'original_path': missing_file_path
            }})
            
            # Patch QMessageBox.warning to control its return value
            with patch('PyQt5.QtWidgets.QMessageBox.warning') as mock_warning:
                # Simulate user clicking "Yes"
                mock_warning.return_value = QMessageBox.Yes
                
                # Also mock clear_template_cache to verify it gets called
                with patch.object(self.file_cache_manager, 'clear_template_cache') as mock_clear:
                    mock_clear.return_value = True
                    
                    # Call the method we're testing
                    success, info = self.cache_manager.safe_clear_template_cache(self.template_name)
                    
                    # Verify the warning dialog was shown
                    self.assertTrue(mock_warning.called)
                    
                    # Verify clear_template_cache was called after user clicked Yes
                    self.assertTrue(mock_clear.called)
                    
                    # Verify the operation was successful
                    self.assertTrue(success)
                    self.assertTrue(info["cleared"])
                    self.assertTrue(info["warning_shown"])
    
    def test_find_all_templates_with_missing_originals(self):
        """Test finding all templates with missing original files"""
        templates_with_missing = self.cache_manager.find_all_templates_with_missing_originals()
        
        # Our test template should be in the result
        self.assertIn(self.template_name, templates_with_missing)
        
        # It should have the missing file info
        missing_files = templates_with_missing[self.template_name]
        missing_file_keys = [key for key, info in missing_files.items() 
                           if os.path.basename(info["original_path"]) == "missing.txt"]
        self.assertTrue(len(missing_file_keys) > 0)


class TestCacheDirectoryStructure(unittest.TestCase):
    """Test the folder structure consistency in cache management"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.temp_dir, "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Create the FileCacheManager
        self.file_cache_manager = FileCacheManager(self.cache_dir)
        
        # Create test folders and files
        self.test_files_dir = os.path.join(self.temp_dir, "test_files")
        os.makedirs(self.test_files_dir, exist_ok=True)
        
        # Create test files in different folders
        # File 1: No folder
        self.file1_path = os.path.join(self.test_files_dir, "file1.txt")
        with open(self.file1_path, "w") as f:
            f.write("Test file 1 content")
            
        # File 2: In a folder
        self.folder1_path = os.path.join(self.test_files_dir, "folder1")
        os.makedirs(self.folder1_path, exist_ok=True)
        self.file2_path = os.path.join(self.folder1_path, "file2.txt")
        with open(self.file2_path, "w") as f:
            f.write("Test file 2 content")
            
        # File 3: In a nested folder
        self.nested_folder_path = os.path.join(self.folder1_path, "nested")
        os.makedirs(self.nested_folder_path, exist_ok=True)
        self.file3_path = os.path.join(self.nested_folder_path, "file3.txt")
        with open(self.file3_path, "w") as f:
            f.write("Test file 3 content")
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def test_cache_folder_structure(self):
        """Test that files are cached with the correct folder structure"""
        template_name = "TestTemplate"
        
        # Cache file 1 (no folder)
        cached_file1 = self.file_cache_manager.cache_file(
            self.file1_path, 
            template_name,
            ""  # No folder
        )
        
        # Cache file 2 (with folder)
        cached_file2 = self.file_cache_manager.cache_file(
            self.file2_path,
            template_name,
            "folder1"
        )
        
        # Cache file 3 (with nested folder)
        cached_file3 = self.file_cache_manager.cache_file(
            self.file3_path,
            template_name,
            "folder1/nested"
        )
        
        # Check the structure
        template_cache_dir = os.path.join(self.cache_dir, template_name)
        files_dir = os.path.join(template_cache_dir, "files")
        
        # Verify the files directory exists
        self.assertTrue(os.path.exists(files_dir), "Files directory should exist")
        
        # Verify file 1 is directly in the files directory
        expected_file1_path = os.path.join(files_dir, "file1.txt")
        self.assertTrue(os.path.exists(expected_file1_path), "File 1 should be in files directory")
        
        # Verify file 2 is in the folder1 subdirectory
        folder1_dir = os.path.join(files_dir, "folder1")
        expected_file2_path = os.path.join(folder1_dir, "file2.txt")
        self.assertTrue(os.path.exists(folder1_dir), "folder1 directory should exist")
        self.assertTrue(os.path.exists(expected_file2_path), "File 2 should be in folder1 directory")
        
        # Verify file 3 is in the nested subdirectory
        nested_dir = os.path.join(folder1_dir, "nested")
        expected_file3_path = os.path.join(nested_dir, "file3.txt")
        self.assertTrue(os.path.exists(nested_dir), "Nested directory should exist")
        self.assertTrue(os.path.exists(expected_file3_path), "File 3 should be in nested directory")
        
        # Verify cache paths are correct
        self.assertEqual(cached_file1, expected_file1_path, "Cache path for file 1 is incorrect")
        self.assertEqual(cached_file2, expected_file2_path, "Cache path for file 2 is incorrect")
        self.assertEqual(cached_file3, expected_file3_path, "Cache path for file 3 is incorrect")
    
    def test_recache_preserves_structure(self):
        """Test that recaching preserves the proper folder structure"""
        # This test simulates what the TemplateCacheManager.recache_template method does
        
        template_name = "RecacheTest"
        
        # First, cache files with the proper structure
        original_file1 = self.file_cache_manager.cache_file(
            self.file1_path, 
            template_name,
            ""  # No folder
        )
        
        original_file2 = self.file_cache_manager.cache_file(
            self.file2_path,
            template_name,
            "folder1"
        )
        
        # Clear the cache
        self.file_cache_manager.clear_template_cache(template_name)
        
        # Now recache the files
        recached_file1 = self.file_cache_manager.cache_file(
            self.file1_path, 
            template_name,
            ""  # No folder
        )
        
        recached_file2 = self.file_cache_manager.cache_file(
            self.file2_path,
            template_name,
            "folder1"
        )
        
        # Check that the paths follow the expected structure
        template_cache_dir = os.path.join(self.cache_dir, template_name)
        files_dir = os.path.join(template_cache_dir, "files")
        
        # Verify recached paths
        expected_file1_path = os.path.join(files_dir, "file1.txt")
        expected_file2_path = os.path.join(files_dir, "folder1", "file2.txt")
        
        self.assertEqual(recached_file1, expected_file1_path, "Recached path for file 1 is incorrect")
        self.assertEqual(recached_file2, expected_file2_path, "Recached path for file 2 is incorrect")


if __name__ == "__main__":
    unittest.main() 