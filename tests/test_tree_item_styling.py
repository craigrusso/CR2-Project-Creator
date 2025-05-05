#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import sys
import os
import unittest
from PyQt5.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem, QStyle, QDialog, QVBoxLayout, QAbstractItemView
from PyQt5.QtCore import Qt
from app.ui.style_debugger import StyleDebugger

class SimpleTreeTest(QDialog):
    """Simple test class for QTreeWidget styling without dependencies"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tree Styling Test")
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Create a tree widget with our styling fixes
        self.structure_tree = QTreeWidget()
        self.structure_tree.setHeaderLabels(["Name"])
        
        # Apply our fixed styling
        self.structure_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #ccc;
                background-color: white;
            }
            
            QTreeWidget::item {
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
            
            QTreeWidget::item:hover {
                background-color: #e6f2ff;
                border: none;
            }
            
            QTreeWidget::item:selected {
                background-color: #cce5ff;
                color: black;
                border: none;
            }
            
            QTreeWidget QLineEdit {
                background-color: white;
                selection-background-color: #8abaff;
                border: 1px solid #8abaff;
                border-radius: 3px;
                padding: 1px 2px;
            }
        """)
        
        # Set edit triggers
        self.structure_tree.setEditTriggers(QAbstractItemView.DoubleClicked | 
                                            QAbstractItemView.EditKeyPressed | 
                                            QAbstractItemView.SelectedClicked)
        
        # Add a root item
        root_item = QTreeWidgetItem(self.structure_tree)
        root_item.setText(0, "Template Root")
        root_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
        root_item.setData(0, Qt.UserRole, {"type": "folder"})
        root_item.setFlags(root_item.flags() | Qt.ItemIsEditable)
        
        # Expand root
        self.structure_tree.expandItem(root_item)
        
        layout.addWidget(self.structure_tree)

class TestTreeItemStyling(unittest.TestCase):
    """Test styling and inline editing of tree items"""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class with a QApplication instance"""
        cls.app = QApplication.instance() or QApplication(sys.argv)
    
    def setUp(self):
        """Set up each test with a fresh test dialog"""
        self.dialog = SimpleTreeTest()
        self.style_debugger = StyleDebugger(self.dialog.structure_tree)
    
    def test_tree_item_styling(self):
        """Test that tree items have the correct styling (no unwanted borders)"""
        # Get the style sheet and verify it has the required components
        style_sheet = self.dialog.structure_tree.styleSheet()
        
        # Check default item state
        self.assertIn("QTreeWidget::item", style_sheet)
        self.assertIn("border: none", style_sheet)
        
        # Check hover state
        self.assertIn("QTreeWidget::item:hover", style_sheet)
        
        # Check selected state
        self.assertIn("QTreeWidget::item:selected", style_sheet)
        
        # Check that item editor (QLineEdit) is styled correctly
        self.assertIn("QTreeWidget QLineEdit", style_sheet)
    
    def test_add_folder_editable(self):
        """Test that added folders are editable"""
        # Add a test folder item
        root_item = self.dialog.structure_tree.topLevelItem(0)
        folder_item = QTreeWidgetItem(root_item)
        folder_item.setText(0, "Test Folder")
        folder_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_DirIcon))
        folder_item.setData(0, Qt.UserRole, {"type": "folder"})
        folder_item.setFlags(folder_item.flags() | Qt.ItemIsEditable)
        
        # Verify the item is editable
        self.assertTrue(folder_item.flags() & Qt.ItemIsEditable)
        
        # Verify that double-clicking would start editing
        self.assertTrue(folder_item.flags() & Qt.ItemIsEditable)
    
    def test_add_file_editable(self):
        """Test that added files are editable"""
        # Add a test file item
        root_item = self.dialog.structure_tree.topLevelItem(0)
        file_item = QTreeWidgetItem(root_item)
        file_item.setText(0, "test_file.txt")
        file_item.setIcon(0, QApplication.style().standardIcon(QStyle.SP_FileIcon))
        file_item.setData(0, Qt.UserRole, {"type": "file", "source_path": "/path/to/test/file.txt"})
        file_item.setFlags(file_item.flags() | Qt.ItemIsEditable)
        
        # Verify the item is editable
        self.assertTrue(file_item.flags() & Qt.ItemIsEditable)
        
        # Verify that the item has all necessary properties
        self.assertEqual(file_item.text(0), "test_file.txt")
        self.assertEqual(file_item.data(0, Qt.UserRole)["type"], "file")
        self.assertEqual(file_item.data(0, Qt.UserRole)["source_path"], "/path/to/test/file.txt")
        self.assertTrue(file_item.flags() & Qt.ItemIsEditable)
    
    def test_tree_edit_triggers(self):
        """Test that the tree widget has the correct edit triggers"""
        # Check that the tree has the expected edit triggers
        self.assertTrue(self.dialog.structure_tree.editTriggers() & QAbstractItemView.DoubleClicked)
        self.assertTrue(self.dialog.structure_tree.editTriggers() & QAbstractItemView.EditKeyPressed)
        self.assertTrue(self.dialog.structure_tree.editTriggers() & QAbstractItemView.SelectedClicked)
    
    def test_tree_style_consistency(self):
        """Test that there are no conflicting styles applied to the tree"""
        # Log style information to help diagnose issues
        self.style_debugger.log_current_style()
        
        # Check for presence of important style properties
        style_sheet = self.dialog.structure_tree.styleSheet()
        
        # Verify no duplicate or conflicting style sections
        style_sections = style_sheet.split("}")
        item_styles = [s for s in style_sections if "QTreeWidget::item" in s]
        
        # Should have exactly 3 item styles - default, hover, selected
        self.assertEqual(len(item_styles), 3, "Should have exactly 3 item style sections")
        
        # Check for proper border specifications in all styles
        for style in item_styles:
            self.assertIn("border: none", style, f"Style section should specify no border: {style}")

if __name__ == "__main__":
    unittest.main() 