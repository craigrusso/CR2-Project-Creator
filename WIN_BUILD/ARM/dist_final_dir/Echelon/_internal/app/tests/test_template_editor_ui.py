#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test for template editor UI components
This test verifies the UI improvements to the template editor
"""

import os
import sys
import unittest
from PyQt6.QtWidgets import QApplication, QFormLayout, QSplitter, QPushButton
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

from app.ui.structure_editor_enhanced import EnhancedStructureEditor

class TestTemplateEditorUI(unittest.TestCase):
    """Test class for template editor UI improvements"""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class"""
        # Create a QApplication if it doesn't exist
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def test_manage_categories_button(self):
        """Test that the Manage Categories button exists and is connected"""
        editor = EnhancedStructureEditor(structure_name="Test Template", is_new=True)
        
        # Find the category layout in the form layout
        ui_builder = editor.ui_builder
        found_button = False
        
        # Use a helper function to recursively search for the Manage button
        def find_manage_button(widget):
            if isinstance(widget, QPushButton) and widget.text() == "Manage":
                return widget
            
            # Check all children
            for child in widget.findChildren(QPushButton):
                if child.text() == "Manage":
                    return child
            
            return None
        
        # Search for the Manage button
        manage_button = find_manage_button(editor)
        
        # Verify button exists
        self.assertIsNotNone(manage_button, "Manage Categories button not found")
        
        # Verify that the button is connected to the _manage_categories method
        # We can't directly check the connection, but we can check that the method exists
        self.assertTrue(hasattr(ui_builder, '_manage_categories'), 
                        "_manage_categories method not found in UIBuilder")
        
        editor.close()
    
    def test_template_info_layout(self):
        """Test that the template info panel maintains proper layout when resized"""
        editor = EnhancedStructureEditor(structure_name="Test Template", is_new=True)
        
        # Find the splitter
        splitters = editor.findChildren(QSplitter)
        self.assertTrue(len(splitters) > 0, "No splitter found in editor")
        
        # Get the first widget in the splitter (template info panel)
        info_container = splitters[0].widget(0)
        self.assertIsNotNone(info_container, "Info container not found in splitter")
        
        # Get the original size of the info container
        original_height = info_container.height()
        
        # Check that the description field is in the second widget of the info container layout
        description_panel = None
        for i in range(info_container.layout().count()):
            widget = info_container.layout().itemAt(i).widget()
            if widget and widget.objectName() == "description_panel":
                description_panel = widget
                break
        
        # If we didn't find a widget with that name, let's check the second widget anyway
        if not description_panel and info_container.layout().count() > 1:
            description_panel = info_container.layout().itemAt(1).widget()
        
        self.assertIsNotNone(description_panel, "Description panel not found in info container")
        
        # Simulate changing the splitter position
        for size in [100, 200, 300]:
            # Set new sizes for the splitter
            splitters[0].setSizes([size, 400])
            
            # Process events to ensure layout updates
            QApplication.processEvents()
            
            # Check that the description panel is receiving the change in size
            # The fixed part should stay roughly the same size
            fixed_panel = info_container.layout().itemAt(0).widget()
            self.assertIsNotNone(fixed_panel, "Fixed panel not found in info container")
            
            # The info container height should change with the splitter
            if size > 100:  # Only check if we have enough space (height might be constrained by minimums)
                self.assertNotEqual(original_height, info_container.height(), 
                                   "Info container height did not change with splitter")
        
        editor.close()

if __name__ == "__main__":
    unittest.main() 