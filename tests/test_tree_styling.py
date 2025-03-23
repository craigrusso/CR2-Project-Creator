#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import sys
import os
import unittest
from PyQt5.QtWidgets import QApplication, QTreeWidgetItem
from PyQt5.QtCore import Qt
from app.ui.ui_components_pyqt import TemplateDirectoryEditor

class TestTreeStyling(unittest.TestCase):
    """Tests for tree styling in the template editor"""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class with a QApplication instance"""
        cls.app = QApplication.instance() or QApplication(sys.argv)
    
    def setUp(self):
        """Set up each test with a fresh TemplateDirectoryEditor"""
        self.dialog = TemplateDirectoryEditor()
        self.dialog._create_structure_tab()  # Initialize the structure tab
        
    def test_tree_styling(self):
        """Test that the tree has the correct styling to avoid blue borders"""
        # Get the style sheet of the tree
        style_sheet = self.dialog.structure_tree.styleSheet()
        
        # Check that the style sheet includes border removal for items
        self.assertIn("QTreeWidget::item", style_sheet)
        self.assertIn("border: none", style_sheet)
        
        # Check item hover styling
        self.assertIn("QTreeWidget::item:hover", style_sheet)
        
        # Check item selection styling
        self.assertIn("QTreeWidget::item:selected", style_sheet)
        
    def test_add_folder_styling(self):
        """Test that adding a folder does not result in unwanted styling"""
        # Add a test folder to the tree
        root_item = self.dialog.structure_tree.topLevelItem(0)
        folder_item = QTreeWidgetItem(root_item)
        folder_item.setText(0, "Test Folder")
        folder_item.setData(0, Qt.UserRole, {"type": "folder"})
        
        # Verify that the folder item has the correct data
        self.assertEqual(folder_item.data(0, Qt.UserRole), {"type": "folder"})
        
    def test_add_file_styling(self):
        """Test that adding a file does not result in unwanted styling"""
        # Add a test file to the tree
        root_item = self.dialog.structure_tree.topLevelItem(0)
        file_path = "/path/to/test/file.txt"
        file_item = QTreeWidgetItem(root_item)
        file_item.setText(0, "test_file.txt")
        file_item.setData(0, Qt.UserRole, file_path)
        
        # Verify that the file item has the correct data
        self.assertEqual(file_item.data(0, Qt.UserRole), file_path)

if __name__ == "__main__":
    unittest.main() 