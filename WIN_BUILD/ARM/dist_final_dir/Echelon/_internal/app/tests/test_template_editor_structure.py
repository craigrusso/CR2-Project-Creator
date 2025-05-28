#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test for template editor structure functionality
This test verifies that the template editor works properly with the 
modified UI that removed preset functionality
"""

import os
import sys
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

from app.ui.structure_editor_enhanced import EnhancedStructureEditor

class TestTemplateEditorStructure(unittest.TestCase):
    """Test class for template editor structure functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class"""
        # Create a QApplication if it doesn't exist
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def test_editor_creation(self):
        """Test that the editor can be created"""
        editor = EnhancedStructureEditor(structure_name="Test Template", is_new=True)
        self.assertIsNotNone(editor)
        self.assertEqual(editor.template_name, "Test Template")
        editor.close()
    
    def test_add_file_folder(self):
        """Test adding files and folders to the structure"""
        editor = EnhancedStructureEditor(structure_name="Test Template", is_new=True)
        
        # Get initial count
        initial_items = self._count_tree_items(editor)
        
        # Add a folder
        editor.add_folder()
        
        # Check that a folder was added
        self.assertEqual(self._count_tree_items(editor), initial_items + 1)
        
        # Add a file
        editor.add_file()
        
        # Check that a file was added
        self.assertEqual(self._count_tree_items(editor), initial_items + 2)
        
        editor.close()
    
    def test_delete_item(self):
        """Test deleting items from the structure"""
        editor = EnhancedStructureEditor(structure_name="Test Template", is_new=True)
        
        # Add a folder
        editor.add_folder()
        
        # Get count after adding
        items_after_add = self._count_tree_items(editor)
        
        # Select the folder
        editor.tree_widget.setCurrentItem(editor.tree_widget.topLevelItem(0))
        
        # Delete the folder
        editor.delete_selected()
        
        # Check that the folder was deleted
        self.assertEqual(self._count_tree_items(editor), items_after_add - 1)
        
        editor.close()
    
    def test_structure_stats_update(self):
        """Test that structure stats are updated correctly"""
        editor = EnhancedStructureEditor(structure_name="Test Template", is_new=True)
        
        # Get initial stats text
        initial_stats = editor.ui_builder.stats_label.text()
        
        # Add a folder
        editor.add_folder()
        
        # Add a file
        editor.add_file()
        
        # Check that stats were updated
        updated_stats = editor.ui_builder.stats_label.text()
        self.assertNotEqual(initial_stats, updated_stats)
        self.assertIn("2 items", updated_stats)
        self.assertIn("1 folders", updated_stats)
        self.assertIn("1 files", updated_stats)
        
        editor.close()
    
    def _count_tree_items(self, editor):
        """Helper method to count items in the tree"""
        count = 0
        root = editor.tree_widget.invisibleRootItem()
        for i in range(root.childCount()):
            count += 1 + self._count_child_items(root.child(i))
        return count
    
    def _count_child_items(self, item):
        """Helper method to recursively count child items"""
        count = 0
        for i in range(item.childCount()):
            count += 1 + self._count_child_items(item.child(i))
        return count

if __name__ == "__main__":
    unittest.main() 