#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import sys
import os
import unittest
from PyQt6.QtWidgets import QApplication, QTreeWidgetItem, QTreeWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from app.ui.structure_editor_enhanced import EnhancedStructureEditor

class TestStructureEditorStyling(unittest.TestCase):
    """Tests for consistent styling between Add Template and Edit Template dialogs"""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class with a QApplication instance"""
        cls.app = QApplication.instance() or QApplication(sys.argv)
    
    def test_add_edit_template_styling_consistency(self):
        """Test that Add Template and Edit Template dialogs have consistent styling"""
        # Create an "Add Template" dialog (is_new=True)
        add_dialog = EnhancedStructureEditor(structure_name="", is_new=True)
        
        # Create an "Edit Template" dialog (is_new=False)
        edit_dialog = EnhancedStructureEditor(structure_name="Test_Template", is_new=False)
        
        # Get references to the tree widgets
        add_tree = add_dialog.tree_widget
        edit_tree = edit_dialog.tree_widget
        
        # Verify that both trees exist
        self.assertIsNotNone(add_tree, "Add Template dialog tree widget not found")
        self.assertIsNotNone(edit_tree, "Edit Template dialog tree widget not found")
        
        # Check styling attributes consistency
        self.assertEqual(add_tree.rootIsDecorated(), edit_tree.rootIsDecorated(), 
                         "rootIsDecorated inconsistent between dialogs")
        self.assertEqual(add_tree.itemsExpandable(), edit_tree.itemsExpandable(),
                         "itemsExpandable inconsistent between dialogs")
        self.assertEqual(add_tree.iconSize(), edit_tree.iconSize(),
                         "iconSize inconsistent between dialogs")
        self.assertEqual(add_tree.indentation(), edit_tree.indentation(),
                         "indentation inconsistent between dialogs")
        
        # Check for styling elements in the stylesheet
        add_style = add_tree.styleSheet()
        edit_style = edit_tree.styleSheet()
        
        # Check for branch indicator styling
        self.assertIn("QTreeWidget::branch:has-children:!has-siblings:closed", add_style, 
                      "Branch closed indicator missing in Add Template dialog")
        self.assertIn("QTreeWidget::branch:has-children:!has-siblings:closed", edit_style,
                      "Branch closed indicator missing in Edit Template dialog")
                      
        self.assertIn("QTreeWidget::branch:open:has-children", add_style,
                     "Branch open indicator missing in Add Template dialog")
        self.assertIn("QTreeWidget::branch:open:has-children", edit_style,
                     "Branch open indicator missing in Edit Template dialog")
        
        # Check for item styling
        self.assertIn("QTreeWidget::item:has-children", add_style, 
                     "Folder item styling missing in Add Template dialog")
        self.assertIn("QTreeWidget::item:has-children", edit_style,
                     "Folder item styling missing in Edit Template dialog")
        
        # Verify that tree header is hidden in both dialogs
        self.assertTrue(add_tree.isHeaderHidden(), "Header should be hidden in Add Template dialog")
        self.assertTrue(edit_tree.isHeaderHidden(), "Header should be hidden in Edit Template dialog")
        
        # Clean up
        add_dialog.close()
        edit_dialog.close()

if __name__ == "__main__":
    unittest.main() 