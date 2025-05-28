#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test case for drag and drop file handling in template editor
"""

import unittest
import os
import sys
import shutil
import tempfile
import json
from PyQt6.QtWidgets import QApplication, QTreeWidgetItem, QStyle
from PyQt6.QtCore import Qt, QMimeData, QUrl, QPoint
from PyQt6.QtTest import QTest
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import required classes
from app.ui.ui_components_pyqt import TemplateDirectoryEditor
from app.templates.template_manager import TemplateManager

class TestDragDropFileHandling(unittest.TestCase):
    """Test case for verifying file drag and drop functionality"""
    
    @classmethod
    def setUpClass(cls):
        # Create QApplication instance
        cls.app = QApplication.instance() or QApplication(sys.argv)
        
        # Create temporary directories for testing
        cls.temp_dir = tempfile.mkdtemp()
        cls.template_dir = os.path.join(cls.temp_dir, "template")
        cls.test_files_dir = os.path.join(cls.temp_dir, "test_files")
        cls.cache_dir = os.path.join(cls.temp_dir, "cache")
        
        # Create directories
        os.makedirs(cls.template_dir, exist_ok=True)
        os.makedirs(cls.test_files_dir, exist_ok=True)
        os.makedirs(cls.cache_dir, exist_ok=True)
        
        # Create test files
        with open(os.path.join(cls.test_files_dir, "test_file.txt"), "w") as f:
            f.write("This is a test file")
        
        # Create test folder structure
        test_subdir = os.path.join(cls.test_files_dir, "subdir")
        os.makedirs(test_subdir, exist_ok=True)
        with open(os.path.join(test_subdir, "nested_file.txt"), "w") as f:
            f.write("This is a nested file")
    
    @classmethod
    def tearDownClass(cls):
        # Clean up temporary directory
        shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        # Create template editor for testing
        self.editor = TemplateDirectoryEditor()
        self.editor.template_path = self.template_dir
        
        # This is where files will actually be cached
        templates_dir = os.path.dirname(os.path.dirname(self.template_dir))
        self.actual_cache_dir = os.path.join(templates_dir, "cache", "template")
        # Make sure the cache directory exists
        os.makedirs(self.actual_cache_dir, exist_ok=True)
        
        # Make structure tree accessible
        self.tree = self.editor.structure_tree
        
        # Make sure the root item exists
        if self.tree.topLevelItemCount() == 0:
            root_item = QTreeWidgetItem(self.tree)
            root_item.setText(0, "Project Root")
            root_item.setData(0, Qt.ItemDataRole.UserRole, "folder")
            root_item.setExpanded(True)
    
    def test_process_dropped_directory(self):
        """Test processing a dropped directory"""
        # Get the root item
        root_item = self.tree.topLevelItem(0)
        
        # Process the test directory
        self.editor._process_dropped_directory(self.test_files_dir, root_item)
        
        # Verify that items were added to the tree
        self.assertTrue(root_item.childCount() > 0, "No items were added to the tree")
        
        # Find the test_files directory in the tree
        test_files_item = None
        for i in range(root_item.childCount()):
            item = root_item.child(i)
            if item.text(0) == os.path.basename(self.test_files_dir):
                test_files_item = item
                break
        
        self.assertIsNotNone(test_files_item, "Test files directory not found in tree")
        
        # Verify that child items were added
        self.assertTrue(test_files_item.childCount() > 0, "No child items were added")
        
        # Check that both the file and subfolder were added
        has_file = False
        has_subdir = False
        for i in range(test_files_item.childCount()):
            item = test_files_item.child(i)
            if item.text(0) == "test_file.txt":
                has_file = True
            elif item.text(0) == "subdir":
                has_subdir = True
        
        self.assertTrue(has_file, "Test file not found in tree")
        self.assertTrue(has_subdir, "Subdirectory not found in tree")
        
        # Create a mock implementation of _get_structure_from_tree for testing
        def get_structure_from_tree():
            """Mock implementation of _get_structure_from_tree for testing"""
            result = []
            root = self.tree.topLevelItem(0)
            
            # Process each child of the root
            for i in range(root.childCount()):
                child = root.child(i)
                build_structure_from_item(child, result)
            
            return result
            
        def build_structure_from_item(item, parent_list):
            """Mock implementation of _build_structure_from_item for testing"""
            # Check if this is a folder or file based on user data
            is_file = item.data(0, Qt.ItemDataRole.UserRole) == "file"
            
            if is_file:
                # It's a file, add as a simple string
                parent_list.append(item.text(0))
            else:
                # It's a folder - empty or with children
                if item.childCount() > 0:
                    # Folder with children
                    folder_dict = {item.text(0): []}
                    for i in range(item.childCount()):
                        build_structure_from_item(item.child(i), folder_dict[item.text(0)])
                    parent_list.append(folder_dict)
                else:
                    # Empty folder
                    parent_list.append({item.text(0): []})
        
        # Use our mock implementation to get the structure
        structure = get_structure_from_tree()
        
        # Print the structure for debugging
        print(f"Generated structure: {json.dumps(structure, indent=2)}")
        
        # Verify the structure format
        self.assertTrue(len(structure) > 0, "Empty structure generated")
        
        # Check that the structure uses the correct format
        found_test_dir = False
        for item in structure:
            if isinstance(item, dict) and os.path.basename(self.test_files_dir) in item:
                found_test_dir = True
                # Check the content of the test dir in the structure
                contents = item[os.path.basename(self.test_files_dir)]
                self.assertTrue(isinstance(contents, list), "Contents are not a list")
                
                # Verify that both the file and directory are in the structure
                file_found = False
                subdir_found = False
                for content_item in contents:
                    if isinstance(content_item, str) and content_item == "test_file.txt":
                        file_found = True
                    elif isinstance(content_item, dict) and "subdir" in content_item:
                        subdir_found = True
                
                self.assertTrue(file_found, "File not found in structure")
                self.assertTrue(subdir_found, "Subdirectory not found in structure")
        
        self.assertTrue(found_test_dir, "Test directory not found in structure")
        
        # Check if file was copied to cache
        print(f"Checking cache at: {self.actual_cache_dir}")
        if os.path.exists(self.actual_cache_dir):
            print(f"Cache directory exists. Contents: {os.listdir(self.actual_cache_dir)}")
            
            # Check for test_file.txt
            self.assertTrue(os.path.exists(os.path.join(self.actual_cache_dir, "test_file.txt")), 
                           "File was not copied to the cache directory")
        else:
            self.fail(f"Cache directory does not exist: {self.actual_cache_dir}")

if __name__ == "__main__":
    unittest.main() 