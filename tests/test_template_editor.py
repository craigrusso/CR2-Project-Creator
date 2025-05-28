#!/usr/bin/env python3
import os
import sys
import unittest
import json
import tempfile
import shutil
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import QApplication, QDialog, QTreeWidgetItem
from PyQt6.QtCore import Qt

from app.ui.structure_editor_enhanced import EnhancedStructureEditor, show_enhanced_structure_editor
from app.templates.template_operations import TemplateOperations
from app.templates.template_manager import TemplateManager

class TestTemplateEditor(unittest.TestCase):
    """Test cases for the Enhanced Structure Editor"""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication once for all tests"""
        cls.app = QApplication.instance() or QApplication(sys.argv)
        
    def setUp(self):
        """Set up test environment before each test"""
        # Create test directory
        self.test_dir = tempfile.mkdtemp()
        
        # Create subdirectories
        self.structures_dir = os.path.join(self.test_dir, "structures")
        self.templates_dir = os.path.join(self.test_dir, "templates")
        os.makedirs(self.structures_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Create a mock template manager
        self.template_manager = MagicMock(spec=TemplateManager)
        self.template_manager.paths = {
            "structures_dir": self.structures_dir,
            "templates_dir": self.templates_dir,
            "custom_structures_dir": self.structures_dir
        }
        
        # Set up basic template data
        self.template_name = "Test Template"
        self.structure_name = f"Template_{self.template_name}"
        
        # Create basic structure data
        self.structure = [
            {"name": "Folder 1", "type": "folder", "children": []},
            {"name": "File 1", "type": "file"}
        ]
        
        # Set up template manager get_structure method
        self.template_manager.get_structure.return_value = self.structure
        
        # Set up template manager get_template_info method
        self.template_info = {
            "name": self.template_name,
            "description": "Test description",
            "tags": ["test", "template"]
        }
        self.template_manager.get_template_info.return_value = self.template_info
        
        # Mock the save methods
        self.template_manager.save_custom_structure.return_value = True
        self.template_manager.save_template_info.return_value = True
        
        # Create a parent widget with the template manager
        self.parent = MagicMock()
        self.parent.template_manager = self.template_manager
        
    def tearDown(self):
        """Clean up after each test"""
        # Remove test directory
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test the initialization of the structure editor"""
        # Create a structure editor with existing template
        editor = EnhancedStructureEditor(
            self.parent,
            structure_name=self.structure_name,
            structure=self.structure
        )
        
        # Check that it initialized with the correct name
        self.assertEqual(editor.template_name, self.template_name)
        self.assertEqual(editor.structure_name, self.structure_name)
        
        # Check window title
        self.assertIn(self.template_name, editor.windowTitle())
        
        # Check that template manager was passed correctly
        self.assertEqual(editor.template_manager, self.template_manager)
        
        # Clean up
        editor.reject()
    
    def test_create_structure_from_tree(self):
        """Test creating a structure from the tree view"""
        # Create a structure editor
        editor = EnhancedStructureEditor(self.parent)
        
        # Add items to tree
        root_item = QTreeWidgetItem(editor.tree)
        root_item.setText(0, "Project Root")
        root_item.setData(0, Qt.ItemDataRole.UserRole, "project_root")
        
        folder_item = QTreeWidgetItem(root_item)
        folder_item.setText(0, "Test Folder")
        folder_item.setData(0, Qt.ItemDataRole.UserRole, "folder")
        
        file_item = QTreeWidgetItem(root_item)
        file_item.setText(0, "Test File")
        file_item.setData(0, Qt.ItemDataRole.UserRole, "file")
        file_item.setData(0, Qt.ItemDataRole.UserRole + 3, True)  # Use project name
        
        # Create structure from tree
        structure = editor.create_structure_from_tree()
        
        # Check structure
        self.assertEqual(len(structure), 2)
        self.assertEqual(structure[0]["name"], "Test Folder")
        self.assertEqual(structure[0]["type"], "folder")
        self.assertEqual(structure[1]["name"], "Test File")
        self.assertEqual(structure[1]["type"], "file")
        self.assertTrue(structure[1].get("use_project_name", False))
        
        # Clean up
        editor.reject()
    
    def test_save_structure(self):
        """Test saving a structure"""
        # Create a structure editor
        editor = EnhancedStructureEditor(self.parent)
        
        # Set template name
        editor.name_input.setText(self.template_name)
        
        # Mock the create_structure_from_tree method
        editor.create_structure_from_tree = MagicMock(return_value=self.structure)
        
        # Save structure
        result = editor.save_structure()
        
        # Check result
        self.assertTrue(result)
        
        # Check that template manager methods were called
        self.template_manager.save_custom_structure.assert_called_with(
            self.template_name, self.structure
        )
        
        # Check template info was saved
        self.template_manager.save_template_info.assert_called()
        
        # Check that dialog result was set
        self.assertEqual(editor.result(), QDialog.Accepted)
        
        # Check that internal state was updated
        self.assertTrue(editor.structure_saved)
        self.assertEqual(editor.original_template_name, self.template_name)
        
        # Clean up
        editor.reject()
    
    def test_update_structure_name_from_template(self):
        """Test updating structure name when template name changes"""
        # Create a structure editor
        editor = EnhancedStructureEditor(self.parent)
        
        # Update structure name
        editor.update_structure_name_from_template("New Template Name")
        
        # Check that structure name was updated
        self.assertEqual(editor.structure_name, "New Template Name")
        
        # Check window title
        self.assertIn("New Template Name", editor.windowTitle())
        
        # Clean up
        editor.reject()
    
    def test_load_structure(self):
        """Test loading a structure"""
        # Create a structure editor
        editor = EnhancedStructureEditor(self.parent)
        
        # Load structure
        result = editor.load_structure(self.structure)
        
        # Check result
        self.assertTrue(result)
        
        # Check tree items
        root = editor.tree.invisibleRootItem()
        self.assertEqual(root.childCount(), 1)
        
        project_root = root.child(0)
        self.assertEqual(project_root.childCount(), 2)
        
        folder_item = project_root.child(0)
        self.assertEqual(folder_item.text(0), "Folder 1")
        self.assertEqual(folder_item.data(0, Qt.ItemDataRole.UserRole), "folder")
        
        file_item = project_root.child(1)
        self.assertEqual(file_item.text(0), "File 1")
        self.assertEqual(file_item.data(0, Qt.ItemDataRole.UserRole), "file")
        
        # Clean up
        editor.reject()
    
    def test_accept_with_save(self):
        """Test accepting dialog with saving"""
        # Create a structure editor
        editor = EnhancedStructureEditor(self.parent)
        
        # Set template name
        editor.name_input.setText(self.template_name)
        
        # Mock the create_structure_from_tree method
        editor.create_structure_from_tree = MagicMock(return_value=self.structure)
        
        # Mock the super().accept method
        with patch.object(QDialog, 'accept') as mock_accept:
            # Call accept
            editor.accept()
            
            # Check that save_structure was called
            self.assertTrue(editor.structure_saved)
            
            # Check that super().accept was called
            mock_accept.assert_called_once()
        
        # Clean up
        editor.reject()
    
    def test_get_current_template_info(self):
        """Test getting current template info"""
        # Create a structure editor
        editor = EnhancedStructureEditor(self.parent)
        
        # Set fields
        editor.name_input.setText(self.template_name)
        editor.description_input.setText("Test description")
        editor.tags_input.setText("tag1, tag2, tag3")
        
        # Get template info
        template_info = editor.get_current_template_info()
        
        # Check result
        self.assertEqual(template_info["name"], self.template_name)
        self.assertEqual(template_info["description"], "Test description")
        self.assertEqual(template_info["tags"], ["tag1", "tag2", "tag3"])
        
        # Clean up
        editor.reject()
    
    def test_show_enhanced_structure_editor(self):
        """Test the show_enhanced_structure_editor function"""
        # Mock EnhancedStructureEditor with a result
        with patch('app.ui.structure_editor_enhanced.EnhancedStructureEditor') as mock_editor_class:
            # Set up mock
            mock_editor = MagicMock()
            mock_editor.exec_.return_value = QDialog.Accepted
            mock_editor.get_result.return_value = {
                'structure_name': self.template_name,
                'structure': self.structure
            }
            mock_editor_class.return_value = mock_editor
            
            # Call function
            success, result_structure, result_name = show_enhanced_structure_editor(
                self.parent, structure_name=self.structure_name
            )
            
            # Check results
            self.assertTrue(success)
            self.assertEqual(result_structure, self.structure)
            self.assertEqual(result_name, self.template_name)

if __name__ == '__main__':
    unittest.main() 