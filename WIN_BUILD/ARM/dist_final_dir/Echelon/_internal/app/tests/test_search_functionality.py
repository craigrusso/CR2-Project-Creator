#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test for the search functionality in the Structure Editor
"""

import sys
import os
import unittest
from PyQt6.QtWidgets import QApplication, QTreeWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

# Add the parent directory to the sys.path to properly import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the class we want to test
from app.ui.structure_editor.ui_components import UIBuilder
from app.ui.structure_editor_enhanced import EnhancedStructureEditor

class TestSearchFunctionality(unittest.TestCase):
    """Test search functionality in the structure editor"""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment"""
        # Create a QApplication instance if not already exists
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up the test case"""
        # Create an editor instance for testing
        self.editor = EnhancedStructureEditor(None, "Test_Template", True)
        
        # Get references to the components
        self.ui_builder = self.editor.ui_builder
        self.search_field = self.ui_builder.search_field
        self.tree = self.ui_builder.tree
        
        # Add some items to the tree for testing
        self.root_item = QTreeWidgetItem(self.tree)
        self.root_item.setText(0, "RootFolder")
        
        # Add a folder
        self.folder_item = QTreeWidgetItem(self.root_item)
        self.folder_item.setText(0, "TestFolder")
        
        # Add some files
        self.file_item1 = QTreeWidgetItem(self.folder_item)
        self.file_item1.setText(0, "test_file.txt")
        
        self.file_item2 = QTreeWidgetItem(self.root_item)
        self.file_item2.setText(0, "config.json")
        
        self.file_item3 = QTreeWidgetItem(self.root_item)
        self.file_item3.setText(0, "README.md")
    
    def test_search_filtering(self):
        """Test that search filtering works properly"""
        # All items should be visible initially
        self.assertFalse(self.root_item.isHidden())
        self.assertFalse(self.folder_item.isHidden())
        self.assertFalse(self.file_item1.isHidden())
        self.assertFalse(self.file_item2.isHidden())
        self.assertFalse(self.file_item3.isHidden())
        
        # Search for "test"
        self.search_field.setText("test")
        
        # Give time for the filter to process
        QTest.qWait(100)
        
        # TestFolder and test_file.txt should be visible, others hidden
        self.assertFalse(self.root_item.isHidden())  # Root should stay visible
        self.assertFalse(self.folder_item.isHidden())  # Contains "test"
        self.assertFalse(self.file_item1.isHidden())  # Contains "test"
        self.assertTrue(self.file_item2.isHidden())  # Doesn't contain "test"
        self.assertTrue(self.file_item3.isHidden())  # Doesn't contain "test"
        
        # Clear search
        self.search_field.clear()
        
        # Give time for the filter to process
        QTest.qWait(100)
        
        # All items should be visible again
        self.assertFalse(self.root_item.isHidden())
        self.assertFalse(self.folder_item.isHidden())
        self.assertFalse(self.file_item1.isHidden())
        self.assertFalse(self.file_item2.isHidden())
        self.assertFalse(self.file_item3.isHidden())
    
    def test_clear_search_method(self):
        """Test that the _clear_search method works properly"""
        # Enter some search text
        self.search_field.setText("config")
        
        # Give time for the filter to process
        QTest.qWait(100)
        
        # Verify that filtering occurred
        self.assertTrue(self.folder_item.isHidden())  # Doesn't contain "config"
        self.assertFalse(self.file_item2.isHidden())  # Contains "config"
        
        # Call the clear search method directly
        self.ui_builder._clear_search()
        
        # Give time for the filter to process
        QTest.qWait(100)
        
        # Verify that all items are visible again
        self.assertFalse(self.root_item.isHidden())
        self.assertFalse(self.folder_item.isHidden())
        self.assertFalse(self.file_item1.isHidden())
        self.assertFalse(self.file_item2.isHidden())
        self.assertFalse(self.file_item3.isHidden())
        
        # Verify that search field is empty
        self.assertEqual(self.search_field.text(), "")
    
    def tearDown(self):
        """Clean up after the test"""
        self.editor.close()
        self.editor.deleteLater()

if __name__ == "__main__":
    unittest.main() 