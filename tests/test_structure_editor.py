#!/usr/bin/env python3
# Tests for the structure editor

import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import QApplication, QTreeWidgetItem, QMessageBox, QWidget
from PyQt5.QtCore import Qt
from app.ui.structure_editor_enhanced import EnhancedStructureEditor

# Create QApplication instance for tests
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

class TestEnhancedStructureEditor(unittest.TestCase):
    """Tests for the EnhancedStructureEditor class"""
    
    def setUp(self):
        """Set up test environment before each test case"""
        # Create a real QWidget as parent instead of MagicMock
        self.parent_widget = QWidget()
        
        # Create a mock app attribute on the parent
        self.parent_widget.app = MagicMock()
        
        # Mock the template_manager property
        self.mock_template_manager = MagicMock()
        self.parent_widget.app.template_manager = self.mock_template_manager
        
        # Create the structure editor with test parameters
        self.editor = EnhancedStructureEditor(
            parent=self.parent_widget,
            structure_name="Template_Test",
            structure=None,
            project_type=None,
            is_new=False
        )
        
        # Mock the QMessageBox.warning
        self.message_patcher = patch('app.ui.structure_editor_enhanced.QMessageBox.warning')
        self.mock_warning = self.message_patcher.start()
        
        # Set up a basic tree structure for testing
        self.editor.tree.clear()
        root = QTreeWidgetItem(self.editor.tree)
        root.setText(0, "Project Root")
        root.setData(0, Qt.UserRole, "folder")
        
        # Add a subfolder
        folder = QTreeWidgetItem(root)
        folder.setText(0, "Test Folder")
        folder.setData(0, Qt.UserRole, "folder")
        
        # Add a file
        file = QTreeWidgetItem(folder)
        file.setText(0, "Test File.txt")
        file.setData(0, Qt.UserRole, "file")
        
    def tearDown(self):
        """Clean up after each test case"""
        self.message_patcher.stop()
        self.editor.close()
        self.parent_widget.close()
        
    def test_save_structure_with_empty_template_name(self):
        """Test save_structure with empty template name"""
        # Set empty template name
        self.editor.template_name_edit.setText("")
        
        # Call save_structure
        self.editor.save_structure()
        
        # Verify warning was shown
        self.mock_warning.assert_called_once()
        args, _ = self.mock_warning.call_args
        self.assertEqual(args[1], "Error")
        self.assertEqual(args[2], "Please enter a template name")
        
    @patch('app.templates.template_operations.TemplateOperations')
    def test_save_structure_with_valid_template_name(self, mock_template_ops_class):
        """Test save_structure with valid template name"""
        # Set up mock TemplateOperations
        mock_template_ops = MagicMock()
        mock_template_ops_class.return_value = mock_template_ops
        mock_template_ops.save_structure.return_value = True
        
        # Set template name
        self.editor.template_name_edit.setText("Test Template")
        
        # Mock extract_structure_from_tree and get_current_template_info
        mock_structure = [
            {"name": "Test Folder", "type": "folder", "children": [
                {"name": "Test File.txt", "type": "file"}
            ]}
        ]
        self.editor.extract_structure_from_tree = MagicMock(return_value=mock_structure)
        self.editor.get_current_template_info = MagicMock(return_value={"description": "Test description"})
        
        # Mock accept method to avoid closing dialog
        self.editor.accept = MagicMock()
        
        # Call save_structure
        self.editor.save_structure()
        
        # Verify template operations were called with correct arguments
        mock_template_ops.save_structure.assert_called_once_with("Template_Test Template", mock_structure)
        mock_template_ops.save_template_info.assert_called_once_with("Test Template", {"description": "Test description"})
        
        # Verify dialog was accepted
        self.editor.accept.assert_called_once()
        
    @patch('app.templates.template_operations.TemplateOperations')
    def test_save_structure_with_existing_template_prefix(self, mock_template_ops_class):
        """Test save_structure with template name that already has Template_ prefix"""
        # Set up mock TemplateOperations
        mock_template_ops = MagicMock()
        mock_template_ops_class.return_value = mock_template_ops
        mock_template_ops.save_structure.return_value = True
        
        # Set template name with prefix
        self.editor.template_name_edit.setText("Template_Existing")
        
        # Mock extract_structure_from_tree and get_current_template_info
        mock_structure = [
            {"name": "Test Folder", "type": "folder", "children": [
                {"name": "Test File.txt", "type": "file"}
            ]}
        ]
        self.editor.extract_structure_from_tree = MagicMock(return_value=mock_structure)
        self.editor.get_current_template_info = MagicMock(return_value={"description": "Test description"})
        
        # Mock accept method to avoid closing dialog
        self.editor.accept = MagicMock()
        
        # Call save_structure
        self.editor.save_structure()
        
        # Verify template operations were called with correct arguments
        mock_template_ops.save_structure.assert_called_once_with("Template_Existing", mock_structure)
        mock_template_ops.save_template_info.assert_called_once_with("Existing", {"description": "Test description"})
        
        # Verify dialog was accepted
        self.editor.accept.assert_called_once()
        
    @patch('app.templates.template_operations.TemplateOperations')
    def test_save_structure_extraction_failure(self, mock_template_ops_class):
        """Test save_structure when structure extraction fails"""
        # Set up mock TemplateOperations
        mock_template_ops = MagicMock()
        mock_template_ops_class.return_value = mock_template_ops
        
        # Set template name
        self.editor.template_name_edit.setText("Test Template")
        
        # Mock extract_structure_from_tree to return None (failure)
        self.editor.extract_structure_from_tree = MagicMock(return_value=None)
        
        # Call save_structure
        self.editor.save_structure()
        
        # Verify warning was shown
        self.mock_warning.assert_called_once()
        args, _ = self.mock_warning.call_args
        self.assertEqual(args[1], "Error")
        self.assertEqual(args[2], "Failed to extract structure from tree")
        
        # Verify template operations were not called
        mock_template_ops.save_structure.assert_not_called()
        
    @patch('app.templates.template_operations.TemplateOperations')
    def test_save_structure_save_failure(self, mock_template_ops_class):
        """Test save_structure when structure save fails"""
        # Set up mock TemplateOperations
        mock_template_ops = MagicMock()
        mock_template_ops_class.return_value = mock_template_ops
        mock_template_ops.save_structure.return_value = False
        
        # Set template name
        self.editor.template_name_edit.setText("Test Template")
        
        # Mock extract_structure_from_tree and get_current_template_info
        mock_structure = [
            {"name": "Test Folder", "type": "folder", "children": [
                {"name": "Test File.txt", "type": "file"}
            ]}
        ]
        self.editor.extract_structure_from_tree = MagicMock(return_value=mock_structure)
        
        # Call save_structure
        self.editor.save_structure()
        
        # Verify warning was shown
        self.mock_warning.assert_called_once()
        args, _ = self.mock_warning.call_args
        self.assertEqual(args[1], "Error")
        self.assertEqual(args[2], "Failed to save structure 'Template_Test Template'")
        
        # Verify template_info operations were not called
        mock_template_ops.save_template_info.assert_not_called()
        
    @patch('app.templates.template_operations.TemplateOperations')
    def test_save_structure_with_exception(self, mock_template_ops_class):
        """Test save_structure when an exception occurs"""
        # Set up mock TemplateOperations to raise an exception
        mock_template_ops = MagicMock()
        mock_template_ops_class.return_value = mock_template_ops
        mock_template_ops.save_structure.side_effect = Exception("Test exception")
        
        # Set template name
        self.editor.template_name_edit.setText("Test Template")
        
        # Mock extract_structure_from_tree and get_current_template_info
        mock_structure = [
            {"name": "Test Folder", "type": "folder", "children": [
                {"name": "Test File.txt", "type": "file"}
            ]}
        ]
        self.editor.extract_structure_from_tree = MagicMock(return_value=mock_structure)
        self.editor.get_current_template_info = MagicMock(return_value={"description": "Test description"})
        
        # Call save_structure
        self.editor.save_structure()
        
        # Verify warning was shown with exception message
        self.mock_warning.assert_called_once()
        args, _ = self.mock_warning.call_args
        self.assertEqual(args[1], "Error")
        self.assertEqual(args[2], "Error saving structure: Test exception")

if __name__ == '__main__':
    unittest.main() 