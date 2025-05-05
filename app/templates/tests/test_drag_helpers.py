#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Tests for drag_helpers module functionality.
"""

import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure path includes the app directory
test_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(os.path.dirname(os.path.dirname(test_dir)))
sys.path.insert(0, app_dir)

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QByteArray, QMimeData, Qt
from PyQt5.QtGui import QPixmap

try:
    # Create a QApplication instance if one doesn't exist
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
except Exception as e:
    print(f"Error initializing QApplication: {e}")
    exit(1)

# Import the module under test
from app.templates.drag_helpers import create_drag_pixmap, setup_drag_mime_data
from app.templates.drag_helpers import TEMPLATE_NAMES_MIME_TYPE, TEMPLATE_MULTI_DRAG_MIME_TYPE


class TestDragHelpers(unittest.TestCase):
    """Test cases for drag_helpers module"""
    
    def setUp(self):
        """Set up test environment before each test"""
        self.widget = QWidget()
        self.widget.resize(100, 100)
        
        # Mock templates
        self.template1 = {"name": "Template 1", "category": "Test"}
        self.template2 = {"name": "Template 2", "category": "Test"}
        self.templates = [self.template1, self.template2]
        
    def tearDown(self):
        """Clean up after each test"""
        self.widget = None
    
    def test_create_drag_pixmap_single(self):
        """Test creating a drag pixmap for a single item"""
        pixmap = create_drag_pixmap(self.widget, item_count=1)
        
        # Basic validation
        self.assertIsInstance(pixmap, QPixmap)
        self.assertFalse(pixmap.isNull())
        
        # For single items, the size should be about the same as the widget
        # plus a small padding
        self.assertTrue(pixmap.width() >= self.widget.width())
        self.assertTrue(pixmap.height() >= self.widget.height())
    
    def test_create_drag_pixmap_multiple(self):
        """Test creating a drag pixmap with a count indicator"""
        pixmap = create_drag_pixmap(self.widget, item_count=5)
        
        # Basic validation
        self.assertIsInstance(pixmap, QPixmap)
        self.assertFalse(pixmap.isNull())
        
        # Size assertions similar to single item test
        self.assertTrue(pixmap.width() >= self.widget.width())
        self.assertTrue(pixmap.height() >= self.widget.height())
    
    def test_setup_drag_mime_data_single(self):
        """Test setting up MIME data for a single template"""
        mime_data = QMimeData()
        template_names = setup_drag_mime_data([self.template1], mime_data)
        
        # Verify returned template names
        self.assertEqual(len(template_names), 1)
        self.assertEqual(template_names[0], "Template 1")
        
        # Verify MIME data content
        self.assertTrue(mime_data.hasText())
        self.assertEqual(mime_data.text(), "Template 1")
        
        # Verify our custom MIME type was set
        self.assertTrue(mime_data.hasFormat(TEMPLATE_NAMES_MIME_TYPE))
        
        # Verify no multi-drag flag for single template
        self.assertFalse(mime_data.hasFormat(TEMPLATE_MULTI_DRAG_MIME_TYPE))
    
    def test_setup_drag_mime_data_multiple(self):
        """Test setting up MIME data for multiple templates"""
        mime_data = QMimeData()
        template_names = setup_drag_mime_data(self.templates, mime_data)
        
        # Verify returned template names
        self.assertEqual(len(template_names), 2)
        self.assertEqual(template_names[0], "Template 1")
        self.assertEqual(template_names[1], "Template 2")
        
        # Verify MIME data content
        self.assertTrue(mime_data.hasText())
        self.assertEqual(mime_data.text(), "Template 1\nTemplate 2")
        
        # Verify our custom MIME types were set
        self.assertTrue(mime_data.hasFormat(TEMPLATE_NAMES_MIME_TYPE))
        self.assertTrue(mime_data.hasFormat(TEMPLATE_MULTI_DRAG_MIME_TYPE))
    
    def test_setup_drag_mime_data_string_templates(self):
        """Test handling string template names"""
        mime_data = QMimeData()
        template_names = setup_drag_mime_data(["Template A", "Template B"], mime_data)
        
        # Verify returned template names
        self.assertEqual(len(template_names), 2)
        self.assertEqual(template_names[0], "Template A")
        self.assertEqual(template_names[1], "Template B")
        
        # Verify MIME data content
        self.assertTrue(mime_data.hasText())
        self.assertEqual(mime_data.text(), "Template A\nTemplate B")


if __name__ == '__main__':
    unittest.main() 