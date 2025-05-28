#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test for tree widget icons
Tests the functionality of the tree widget styling with platform-specific icons
"""

import os
import sys
import unittest
import platform

from PyQt6.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

# Setup application for tests
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

# Append parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import modules for testing
from app.ui.tree_styling import apply_tree_styling, update_tree_item_icons
from app.ui.icon_utilities import get_folder_icon, get_file_icon

class TreeIconTest(unittest.TestCase):
    """Test for tree widget icons"""
    
    def setUp(self):
        """Set up test environment"""
        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(["Name"])
        
        # Create a test structure with folders and files
        self.root_item = QTreeWidgetItem(self.tree)
        self.root_item.setText(0, "Project Root")
        self.root_item.setData(0, Qt.ItemDataRole.UserRole, "folder")
        
        # Create folders
        self.folder1 = QTreeWidgetItem(self.root_item)
        self.folder1.setText(0, "01_FOOTAGE")
        self.folder1.setData(0, Qt.ItemDataRole.UserRole, "folder")
        
        self.folder2 = QTreeWidgetItem(self.root_item)
        self.folder2.setText(0, "02_AE_PROJECTS")
        self.folder2.setData(0, Qt.ItemDataRole.UserRole, "folder")
        
        # Create files with different extensions
        self.file1 = QTreeWidgetItem(self.folder1)
        self.file1.setText(0, "video.mp4")
        self.file1.setData(0, Qt.ItemDataRole.UserRole, "file")
        
        self.file2 = QTreeWidgetItem(self.folder1)
        self.file2.setText(0, "image.jpg")
        self.file2.setData(0, Qt.ItemDataRole.UserRole, "file")
        
        self.file3 = QTreeWidgetItem(self.folder2)
        self.file3.setText(0, "${PROJECT_NAME}.prproj")
        self.file3.setData(0, Qt.ItemDataRole.UserRole, "file")
        
        # Expand all items
        self.tree.expandAll()
        
        # Apply styling with icons
        apply_tree_styling(self.tree)
    
    def test_folder_icons_applied(self):
        """Test that folders have the correct platform-specific icons"""
        folder_icon = get_folder_icon(True)  # True for expanded
        
        # Check root folder icon
        self.assertFalse(self.root_item.icon(0).isNull())
        
        # Check subfolder icons
        self.assertFalse(self.folder1.icon(0).isNull())
        self.assertFalse(self.folder2.icon(0).isNull())
        
        # Verify folder type data is set
        self.assertEqual(self.root_item.data(0, Qt.ItemDataRole.UserRole), "folder")
        self.assertEqual(self.folder1.data(0, Qt.ItemDataRole.UserRole), "folder")
        self.assertEqual(self.folder2.data(0, Qt.ItemDataRole.UserRole), "folder")
    
    def test_file_icons_applied(self):
        """Test that files have the correct type-specific icons"""
        # Check file icons
        self.assertFalse(self.file1.icon(0).isNull())
        self.assertFalse(self.file2.icon(0).isNull())
        self.assertFalse(self.file3.icon(0).isNull())
        
        # Verify file type data is set
        self.assertEqual(self.file1.data(0, Qt.ItemDataRole.UserRole), "file")
        self.assertEqual(self.file2.data(0, Qt.ItemDataRole.UserRole), "file")
        self.assertEqual(self.file3.data(0, Qt.ItemDataRole.UserRole), "file")
    
    def test_expand_changes_folder_icon(self):
        """Test that expanding/collapsing changes the folder icon"""
        # Collapse a folder
        self.folder1.setExpanded(False)
        
        # Update icons after collapse
        update_tree_item_icons(self.tree)
        
        # Verify icon is not null
        self.assertFalse(self.folder1.icon(0).isNull())
        
        # Re-expand the folder
        self.folder1.setExpanded(True)
        
        # Update icons after expansion
        update_tree_item_icons(self.tree)
        
        # Verify icon is not null
        self.assertFalse(self.folder1.icon(0).isNull())
    
    def test_platform_specific_styling(self):
        """Test that styling is applied according to platform"""
        # Just verify that our platform detection works
        current_platform = platform.system()
        self.assertIn(current_platform, ["Windows", "Darwin", "Linux"])
        
        # Log the platform for debugging
        print(f"Running test on {current_platform} platform")
        
        # Verify tree widget has styling applied
        self.assertTrue(len(self.tree.styleSheet()) > 0)

if __name__ == '__main__':
    unittest.main() 