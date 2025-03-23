#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script to verify structure conversion and file caching
"""

import unittest
import os
import sys
import shutil
import tempfile
import json
from PyQt5.QtWidgets import QApplication, QTreeWidgetItem
from PyQt5.QtCore import Qt

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import required modules
from app.ui.structure_editor.structure_converter import StructureConverter
from app.ui.ui_components_pyqt import StructureEditor, TemplateDirectoryEditor

class TestStructureConversion(unittest.TestCase):
    """Test case for verifying structure conversion and file caching"""
    
    @classmethod
    def setUpClass(cls):
        # Create QApplication instance
        cls.app = QApplication.instance() or QApplication(sys.argv)
        
        # Create temporary directories
        cls.temp_dir = tempfile.mkdtemp()
        cls.template_dir = os.path.join(cls.temp_dir, "template")
        cls.test_files_dir = os.path.join(cls.temp_dir, "test_files")
        cls.cache_dir = os.path.join(cls.temp_dir, "cache", "template")
        
        # Create directories
        os.makedirs(cls.template_dir, exist_ok=True)
        os.makedirs(cls.test_files_dir, exist_ok=True)
        os.makedirs(cls.cache_dir, exist_ok=True)
        
        # Create sample files and directories
        test_subdir = os.path.join(cls.test_files_dir, "subdir")
        os.makedirs(test_subdir, exist_ok=True)
        
        # Create files in test_files_dir
        with open(os.path.join(cls.test_files_dir, "test1.txt"), "w") as f:
            f.write("Test file 1 content")
        
        with open(os.path.join(cls.test_files_dir, "test2.txt"), "w") as f:
            f.write("Test file 2 content")
        
        # Create files in subdir
        with open(os.path.join(test_subdir, "nested1.txt"), "w") as f:
            f.write("Nested file 1 content")
        
        with open(os.path.join(test_subdir, "nested2.txt"), "w") as f:
            f.write("Nested file 2 content")
        
        # Create nested subfolders
        nested_subdir = os.path.join(test_subdir, "nested_subdir")
        os.makedirs(nested_subdir, exist_ok=True)
        
        with open(os.path.join(nested_subdir, "deeply_nested.txt"), "w") as f:
            f.write("Deeply nested file content")
    
    @classmethod
    def tearDownClass(cls):
        # Clean up temporary directory
        shutil.rmtree(cls.temp_dir)
    
    def test_structure_converter(self):
        """Test the StructureConverter's _process_item method"""
        # Create a tree structure manually
        from PyQt5.QtWidgets import QTreeWidget
        
        # Create tree widget
        tree = QTreeWidget()
        
        # Create converter with this tree
        converter = StructureConverter(tree_widget=tree)
        
        # Create root item
        root = QTreeWidgetItem(tree)
        root.setText(0, "Project Root")
        root.setData(0, Qt.UserRole, "folder")
        
        # Add folder with children
        folder1 = QTreeWidgetItem(root)
        folder1.setText(0, "Folder1")
        folder1.setData(0, Qt.UserRole, "folder")
        
        # Add file to folder1
        file1 = QTreeWidgetItem(folder1)
        file1.setText(0, "file1.txt")
        file1.setData(0, Qt.UserRole, "file")
        
        # Add nested folder
        folder2 = QTreeWidgetItem(folder1)
        folder2.setText(0, "Folder2")
        folder2.setData(0, Qt.UserRole, "folder")
        
        # Add file to folder2
        file2 = QTreeWidgetItem(folder2)
        file2.setText(0, "file2.txt")
        file2.setData(0, Qt.UserRole, "file")
        
        # Process the structure
        structure = converter.get_structure()
        
        # Print the structure for debugging
        print(f"Generated structure: {json.dumps(structure, indent=2)}")
        
        # Verify structure format
        self.assertEqual(len(structure), 1, "Structure should have one top-level item")
        
        # Check the structure format - it has Project Root as the top level
        project_root_item = structure[0]
        self.assertTrue(isinstance(project_root_item, dict), "Top item should be a dictionary")
        self.assertTrue("Project Root" in project_root_item, "Project Root should be the key")
        
        # Get contents of Project Root
        project_root_children = project_root_item["Project Root"]
        self.assertTrue(isinstance(project_root_children, list), "Project Root children should be a list")
        self.assertEqual(len(project_root_children), 1, "Project Root should have 1 child")
        
        # Get Folder1
        folder1_item = project_root_children[0]
        self.assertTrue(isinstance(folder1_item, dict), "Folder1 item should be a dictionary")
        self.assertTrue("Folder1" in folder1_item, "Folder1 should be the key")
        
        # Get contents of Folder1
        folder1_children = folder1_item["Folder1"]
        self.assertTrue(isinstance(folder1_children, list), "Folder1 children should be a list")
        self.assertEqual(len(folder1_children), 2, "Folder1 should have 2 children")
        
        # Check for file1.txt and Folder2
        found_file1 = False
        found_folder2 = False
        folder2_item = None
        
        for item in folder1_children:
            if isinstance(item, str) and item == "file1.txt":
                found_file1 = True
            elif isinstance(item, dict) and "Folder2" in item:
                found_folder2 = True
                folder2_item = item
        
        self.assertTrue(found_file1, "file1.txt should be in Folder1")
        self.assertTrue(found_folder2, "Folder2 should be in Folder1")
        
        # Check Folder2's content
        if folder2_item:
            folder2_children = folder2_item["Folder2"]
            self.assertTrue(isinstance(folder2_children, list), "Folder2 children should be a list")
            self.assertEqual(len(folder2_children), 1, "Folder2 should have 1 child")
            self.assertEqual(folder2_children[0], "file2.txt", "file2.txt should be in Folder2")
    
    def test_file_caching(self):
        """Test file caching during drag and drop operations"""
        # Create editor with template path
        editor = TemplateDirectoryEditor()
        editor.template_path = self.template_dir
        
        # Get the root item
        if editor.structure_tree.topLevelItemCount() == 0:
            root_item = QTreeWidgetItem(editor.structure_tree)
            root_item.setText(0, "Project Root")
            root_item.setData(0, Qt.UserRole, "folder")
        else:
            root_item = editor.structure_tree.topLevelItem(0)
        
        # Process the test directory
        editor._process_dropped_directory(self.test_files_dir, root_item)
        
        # Get the structure cache directory
        templates_dir = os.path.dirname(os.path.dirname(self.template_dir))
        cache_dir = os.path.join(templates_dir, "cache", "template")
        
        # Verify files were cached with correct structure
        self.assertTrue(os.path.exists(cache_dir), "Cache directory should exist")
        
        # Check for test_files_dir in cache
        test_files_dir_cache = os.path.join(cache_dir, os.path.basename(self.test_files_dir))
        
        # Check for test1.txt and test2.txt
        test1_path = os.path.join(cache_dir, os.path.basename(self.test_files_dir), "test1.txt")
        test2_path = os.path.join(cache_dir, os.path.basename(self.test_files_dir), "test2.txt")
        
        # Check for subdir and its files
        subdir_path = os.path.join(cache_dir, os.path.basename(self.test_files_dir), "subdir")
        nested1_path = os.path.join(subdir_path, "nested1.txt")
        nested2_path = os.path.join(subdir_path, "nested2.txt")
        
        # Check for nested_subdir and its file
        nested_subdir_path = os.path.join(subdir_path, "nested_subdir")
        deeply_nested_path = os.path.join(nested_subdir_path, "deeply_nested.txt")
        
        # Verify all paths exist
        self.assertTrue(os.path.exists(test1_path), f"test1.txt not found at {test1_path}")
        self.assertTrue(os.path.exists(test2_path), f"test2.txt not found at {test2_path}")
        self.assertTrue(os.path.exists(nested1_path), f"nested1.txt not found at {nested1_path}")
        self.assertTrue(os.path.exists(nested2_path), f"nested2.txt not found at {nested2_path}")
        self.assertTrue(os.path.exists(deeply_nested_path), f"deeply_nested.txt not found at {deeply_nested_path}")
        
        # Check that the file contents are correct
        with open(test1_path, "r") as f:
            content = f.read()
            self.assertEqual(content, "Test file 1 content", "Content of test1.txt is incorrect")
        
        with open(deeply_nested_path, "r") as f:
            content = f.read()
            self.assertEqual(content, "Deeply nested file content", "Content of deeply_nested.txt is incorrect")
        
        # Create a structure converter for the editor and get the structure
        converter = StructureConverter(tree_widget=editor.structure_tree)
        structure = converter.get_structure()
        
        # Print the structure for debugging
        print(f"Editor structure: {json.dumps(structure, indent=2)}")
        
        # Verify structure format
        self.assertTrue(len(structure) > 0, "Editor structure should not be empty")

    def test_nested_structure_conversion(self):
        """Test converting a nested structure with multiple levels"""
        # Create a tree widget to test
        from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
        tree = QTreeWidget()
        
        # Create a root item
        root_item = QTreeWidgetItem(tree)
        root_item.setText(0, "Project Root")
        root_item.setData(0, Qt.UserRole, {"type": "folder", "name": "Project Root"})
        
        # Create first level folder
        folder1 = QTreeWidgetItem(root_item)
        folder1.setText(0, "Level1")
        folder1.setData(0, Qt.UserRole, {"type": "folder", "name": "Level1"})
        
        # Create second level folder
        folder2 = QTreeWidgetItem(folder1)
        folder2.setText(0, "Level2")
        folder2.setData(0, Qt.UserRole, {"type": "folder", "name": "Level2"})
        
        # Create third level folder
        folder3 = QTreeWidgetItem(folder2)
        folder3.setText(0, "Level3")
        folder3.setData(0, Qt.UserRole, {"type": "folder", "name": "Level3"})
        
        # Add a file to each level
        file1 = QTreeWidgetItem(root_item)
        file1.setText(0, "root_file.txt")
        file1.setData(0, Qt.UserRole, {"type": "file", "name": "root_file.txt"})
        
        file2 = QTreeWidgetItem(folder1)
        file2.setText(0, "level1_file.txt")
        file2.setData(0, Qt.UserRole, {"type": "file", "name": "level1_file.txt"})
        
        file3 = QTreeWidgetItem(folder2)
        file3.setText(0, "level2_file.txt")
        file3.setData(0, Qt.UserRole, {"type": "file", "name": "level2_file.txt"})
        
        file4 = QTreeWidgetItem(folder3)
        file4.setText(0, "level3_file.txt")
        file4.setData(0, Qt.UserRole, {"type": "file", "name": "level3_file.txt"})
        
        # Create a structure converter
        converter = StructureConverter(tree_widget=tree)
        
        # Get the structure
        structure = converter.get_structure()
        
        # Print for debugging
        print("Generated nested structure:", json.dumps(structure, indent=2))
        
        # Verify the structure format
        self.assertEqual(len(structure), 1, "Structure should have one top-level item")
        self.assertTrue("Project Root" in structure[0], "First item should be Project Root")
        
        # Get contents of Project Root
        project_root_children = structure[0]["Project Root"]
        self.assertEqual(len(project_root_children), 2, "Project Root should have 2 children")
        
        # Find Level1 folder and the file
        level1_found = False
        root_file_found = False
        
        for item in project_root_children:
            if isinstance(item, dict) and "Level1" in item:
                level1_found = True
                # Check Level1 contents
                level1_children = item["Level1"]
                self.assertEqual(len(level1_children), 2, "Level1 should have 2 children")
                
                # Find Level2 folder and level1 file
                level2_found = False
                level1_file_found = False
                
                for child in level1_children:
                    if isinstance(child, dict) and "Level2" in child:
                        level2_found = True
                        # Check Level2 contents
                        level2_children = child["Level2"]
                        self.assertEqual(len(level2_children), 2, "Level2 should have 2 children")
                        
                        # Find Level3 folder and level2 file
                        level3_found = False
                        level2_file_found = False
                        
                        for l2_child in level2_children:
                            if isinstance(l2_child, dict) and "Level3" in l2_child:
                                level3_found = True
                                # Check Level3 contents
                                level3_children = l2_child["Level3"]
                                self.assertEqual(len(level3_children), 1, "Level3 should have 1 child")
                                self.assertEqual(level3_children[0], "level3_file.txt", "Level3 should contain level3_file.txt")
                            elif l2_child == "level2_file.txt":
                                level2_file_found = True
                        
                        self.assertTrue(level3_found, "Level3 folder should be found in Level2")
                        self.assertTrue(level2_file_found, "level2_file.txt should be found in Level2")
                    elif child == "level1_file.txt":
                        level1_file_found = True
                
                self.assertTrue(level2_found, "Level2 folder should be found in Level1")
                self.assertTrue(level1_file_found, "level1_file.txt should be found in Level1")
            elif item == "root_file.txt":
                root_file_found = True
        
        self.assertTrue(level1_found, "Level1 folder should be found in Project Root")
        self.assertTrue(root_file_found, "root_file.txt should be found in Project Root")

if __name__ == "__main__":
    unittest.main() 