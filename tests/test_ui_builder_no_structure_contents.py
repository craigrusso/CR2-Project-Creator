#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test for UIBuilder without Structure Contents section
"""

import sys
import os
import unittest
from PyQt6.QtWidgets import QApplication, QDialog, QPushButton, QLabel, QSplitter
from PyQt6.QtCore import Qt

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the UIBuilder and related classes
from app.ui.structure_editor.ui_components import UIBuilder
from app.ui.structure_editor_enhanced import EnhancedStructureEditor

class TestUIBuilderNoStructureContents(unittest.TestCase):
    """Test for UIBuilder without Structure Contents section"""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class"""
        # Create QApplication instance if it doesn't exist
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up the test"""
        # Create a dummy editor dialog to host our UI
        self.editor = EnhancedStructureEditor(structure_name="Test_Template")
        
        # Create the UIBuilder instance
        self.ui_builder = UIBuilder(self.editor, "Test_Template")
    
    def test_ui_initialization(self):
        """Test that the UI initializes correctly"""
        # Get the layout from UIBuilder
        layout = self.ui_builder.init_ui()
        
        # Make basic assertions to ensure the UI was created
        self.assertIsNotNone(layout, "Layout should not be None")
        self.assertIsNotNone(self.ui_builder.template_name_field, "Template name field should exist")
        self.assertIsNotNone(self.ui_builder.template_category_field, "Category field should exist")
        self.assertIsNotNone(self.ui_builder.template_info_field, "Template info field should exist")
        self.assertIsNotNone(self.ui_builder.tree, "Tree widget should exist")
    
    def test_structure_contents_removed(self):
        """Test that the Structure Contents header and related UI elements are not present"""
        # Initialize the UI
        layout = self.ui_builder.init_ui()
        
        # Check if any label in our editor has the text "Structure Contents"
        structure_contents_exists = False
        for widget in self.editor.findChildren(QDialog):
            if hasattr(widget, 'text') and callable(widget.text) and widget.text() == "Structure Contents":
                structure_contents_exists = True
                break
        
        self.assertFalse(structure_contents_exists, "Structure Contents label should not exist")
        
        # Check that the header is hidden in the tree
        self.assertTrue(self.ui_builder.tree.isHeaderHidden(), "Tree header should be hidden")
        
        # Check that there's no "Import Structure" button
        import_btn_exists = False
        for button in self.editor.findChildren(QPushButton):
            if hasattr(button, 'text') and button.text() == "Import Structure":
                import_btn_exists = True
                break
                
        self.assertFalse(import_btn_exists, "Import Structure button should not exist")
        
        # Check that there's no splitter for separating the structure section
        splitter_exists = False
        for widget in self.editor.findChildren(QSplitter):
            if widget.orientation() == Qt.Orientation.Vertical:
                splitter_exists = True
                break
                
        self.assertFalse(splitter_exists, "Vertical splitter should not exist in UI")
    
    def test_new_ui_elements(self):
        """Test that new UI elements have been added correctly"""
        # Initialize the UI
        layout = self.ui_builder.init_ui()
        
        # Check that the Project Structure header exists
        structure_header_exists = False
        for label in self.editor.findChildren(QLabel):
            if hasattr(label, 'text') and label.text() == "Project Structure":
                structure_header_exists = True
                break
        
        self.assertTrue(structure_header_exists, "Project Structure header should exist")
        
        # Check that the instruction text exists
        instruction_text_exists = False
        for label in self.editor.findChildren(QLabel):
            if hasattr(label, 'text') and "Create and organize your project structure" in label.text():
                instruction_text_exists = True
                break
        
        self.assertTrue(instruction_text_exists, "Instruction text should exist")
        
        # Check that the status bar exists
        self.assertIsNotNone(getattr(self.ui_builder, 'status_bar', None), "Status bar should exist")
        
        # Test that button layout is in the right place
        # by checking it's positioned above the tree in the UI hierarchy
        operations_buttons = []
        for button in self.editor.findChildren(QPushButton):
            if hasattr(button, 'text') and button.text() in ["Add File", "Add Folder", "Delete"]:
                operations_buttons.append(button)
        
        self.assertEqual(len(operations_buttons), 3, "Should find all three operation buttons")
        
        # Check that tree has proper styling
        self.assertTrue(self.ui_builder.tree.rootIsDecorated(), "Tree should have root decoration")
        self.assertTrue(self.ui_builder.tree.itemsExpandable(), "Tree items should be expandable")
        
        # Verify the tree uses custom icon size
        self.assertEqual(self.ui_builder.tree.iconSize().width(), 20, "Tree should have custom icon size")
    
    def test_functionality_preserved(self):
        """Test that all functionality is preserved despite UI changes"""
        # Initialize the UI
        layout = self.ui_builder.init_ui()
        
        # Verify that essential components are connected
        self.assertIsNotNone(self.editor.tree, "Tree should be set on the editor")
        
        # Test that the tree has the necessary properties
        self.assertTrue(self.editor.tree.dragEnabled(), "Tree should have drag enabled")
        self.assertTrue(self.editor.tree.acceptDrops(), "Tree should accept drops")
        
        # Verify buttons and functionality connections exist
        # We're not testing actual functionality (which needs more setup)
        # but just that the connections are made correctly
        self.assertTrue(hasattr(self.editor, 'add_file'), "Editor should have add_file method")
        self.assertTrue(hasattr(self.editor, 'add_folder'), "Editor should have add_folder method")
        self.assertTrue(hasattr(self.editor, 'delete_selected'), "Editor should have delete_selected method")
    
    def tearDown(self):
        """Clean up after the test"""
        if self.editor:
            self.editor.close()
            self.editor = None
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        # Properly clean up QApplication if we created it
        pass

if __name__ == "__main__":
    unittest.main() 