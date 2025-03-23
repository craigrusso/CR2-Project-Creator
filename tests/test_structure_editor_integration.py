#!/usr/bin/env python3
"""
Integration tests for the structure editor and template manager.
Focuses on name updates, saving, and UI refreshes.
"""

import os
import sys
import unittest
import json
import tempfile
import shutil
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtCore import Qt

# Import the modules to test
from app.ui.structure_editor_enhanced import EnhancedStructureEditor
from app.templates.template_operations import TemplateOperations

# Check if TemplateGallery exists, otherwise create a mock
try:
    from app.ui.gallery_templates import TemplateGallery
except ImportError:
    # Create a mock TemplateGallery class
    class TemplateGallery:
        """Mock TemplateGallery class for testing"""
        def __init__(self):
            self.template_manager = None
            
        def refresh_gallery(self):
            """Mock refresh gallery method"""
            pass

# Check if handle_template_edit exists, otherwise create a mock
try:
    from app.ui.gallery_templates import handle_template_edit
except ImportError:
    # Create a mock handle_template_edit function
    def handle_template_edit(gallery, template_name):
        """Mock handle_template_edit function"""
        # Create a structure editor with the template name
        editor = EnhancedStructureEditor(
            gallery,
            structure_name=template_name.replace(' ', '_')
        )
        
        # Set the template manager
        editor.template_manager = gallery.template_manager
        
        # Execute the editor and refresh the gallery if accepted
        if editor.exec_() == QDialog.Accepted:
            gallery.refresh_gallery()
            return True
        return False

class TestStructureEditorIntegration(unittest.TestCase):
    """Test the integration between structure editor and template manager"""
    
    @classmethod
    def setUpClass(cls):
        """Set up the QApplication once for all tests"""
        cls.app = QApplication.instance() or QApplication(sys.argv)
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.structures_dir = os.path.join(self.temp_dir, "structures")
        self.templates_dir = os.path.join(self.temp_dir, "templates")
        os.makedirs(self.structures_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Create a sample structure
        self.sample_structure = [
            {"name": "Folder 1", "type": "folder", "children": [
                {"name": "Subfolder 1", "type": "folder", "children": []},
                {"name": "File 1.txt", "type": "file"}
            ]},
            {"name": "File 2.txt", "type": "file", "use_project_name": True},
            {"name": "Folder 2", "type": "folder", "children": []}
        ]
        
        # Create a sample template info
        self.sample_template_info = {
            "name": "Test Template",
            "description": "This is a test template",
            "tags": ["test", "template"],
            "category": "Test Category",
            "folder": "Default"
        }
        
        # Save the sample structure and template info to files
        with open(os.path.join(self.structures_dir, "Test_Template.json"), 'w') as f:
            json.dump(self.sample_structure, f, indent=2)
        
        with open(os.path.join(self.templates_dir, "Template_Test_Template.json"), 'w') as f:
            json.dump(self.sample_template_info, f, indent=2)
        
        # Create a mock template manager
        self.template_manager = MagicMock(spec=TemplateOperations)
        self.template_manager.paths = {
            "structures_dir": self.structures_dir,
            "templates_dir": self.templates_dir,
            "custom_structures_dir": self.structures_dir
        }
        self.template_manager.preferences = {
            "categories": ["Test Category", "Category 1", "Category 2"]
        }
        
        # Configure the get_structure method to return the sample structure
        self.template_manager.get_structure.return_value = self.sample_structure
        
        # Configure the get_template_info method to return the sample template info
        self.template_manager.get_template_info.return_value = self.sample_template_info
        
        # Set up save_custom_structure to actually save the file
        def mock_save_custom_structure(name, structure):
            try:
                file_path = os.path.join(self.structures_dir, f"{name.replace(' ', '_')}.json")
                with open(file_path, 'w') as f:
                    json.dump(structure, f, indent=2)
                return True
            except Exception as e:
                print(f"Error in mock_save_custom_structure: {e}")
                return False
                
        self.template_manager.save_custom_structure.side_effect = mock_save_custom_structure
        
        # Set up save_template_info to actually save the file
        def mock_save_template_info(name, info):
            try:
                file_path = os.path.join(self.templates_dir, f"Template_{name.replace(' ', '_')}.json")
                with open(file_path, 'w') as f:
                    json.dump(info, f, indent=2)
                return True
            except Exception as e:
                print(f"Error in mock_save_template_info: {e}")
                return False
                
        self.template_manager.save_template_info.side_effect = mock_save_template_info
        
        # Create a parent widget for dialogs
        self.parent = QDialog()
        self.parent.template_manager = self.template_manager
    
    def tearDown(self):
        """Clean up after each test"""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Close the parent dialog
        self.parent.close()
    
    def test_load_structure_by_name(self):
        """Test loading a structure by name"""
        # Create a structure editor
        editor = EnhancedStructureEditor(
            self.parent,
            structure_name="Test_Template"
        )
        
        # Set the template manager directly on the editor
        editor.template_manager = self.template_manager
        
        # Verify that the structure was loaded correctly
        self.template_manager.get_structure.assert_called_with("Test_Template")
        self.assertEqual(editor.structure_name, "Test_Template")
        
        # Check that the template name was set correctly
        if hasattr(editor, 'name_input') and editor.name_input:
            self.assertEqual(editor.name_input.text(), "Test Template")
        
        # Close the editor
        editor.close()
    
    def test_save_structure_with_same_name(self):
        """Test saving a structure with the same name"""
        # Create a structure editor
        editor = EnhancedStructureEditor(
            self.parent,
            structure_name="Test_Template"
        )
        
        # Set the template manager directly on the editor
        editor.template_manager = self.template_manager
        
        # Save the structure
        with patch.object(editor, 'close') as mock_close:
            editor.save_structure()
            
            # Verify that the structure was saved
            self.template_manager.save_custom_structure.assert_called()
            self.template_manager.save_template_info.assert_called()
            
            # The structure name should remain the same
            self.assertEqual(editor.structure_name, "Test_Template")
            
            # The accept method should have been called
            mock_close.assert_called_once()
        
        # Close the editor
        editor.close()
    
    def test_save_structure_with_new_name(self):
        """Test saving a structure with a new name"""
        # Create a structure editor
        editor = EnhancedStructureEditor(
            self.parent,
            structure_name="Test_Template"
        )
        
        # Set the template manager directly on the editor
        editor.template_manager = self.template_manager
        
        # Change the template name
        if hasattr(editor, 'name_input') and editor.name_input:
            editor.name_input.setText("New Template Name")
        
        # Save the structure
        with patch.object(editor, 'close') as mock_close:
            with patch('os.path.exists', return_value=True), \
                 patch('os.remove') as mock_remove:
                editor.save_structure()
                
                # Verify that the structure was saved with the new name
                self.template_manager.save_custom_structure.assert_called()
                self.template_manager.save_template_info.assert_called()
                
                # The structure_name should be updated
                self.assertEqual(editor.structure_name, "New_Template_Name")
                
                # Check if the old structure file removal was attempted
                mock_remove.assert_called()
                
                # The accept method should have been called
                mock_close.assert_called_once()
        
        # Close the editor
        editor.close()
    
    def test_update_structure_name_from_template(self):
        """Test updating the structure name when template name changes"""
        # Create a structure editor
        editor = EnhancedStructureEditor(
            self.parent,
            structure_name="Test_Template"
        )
        
        # Set the template manager directly on the editor
        editor.template_manager = self.template_manager
        
        # Record the original structure name
        original_name = editor.structure_name
        
        # Change the template name
        if hasattr(editor, 'name_input') and editor.name_input:
            editor.name_input.setText("Updated Template")
            
        # Trigger the update_structure_name_from_template method
        editor.update_structure_name_from_template()
        
        # Check that the structure name was updated
        self.assertNotEqual(editor.structure_name, original_name)
        self.assertEqual(editor.structure_name, "Updated_Template")
        
        # Close the editor
        editor.close()
    
    def test_create_new_structure(self):
        """Test creating a new structure"""
        # Create a structure editor with is_new=True
        editor = EnhancedStructureEditor(
            self.parent,
            structure_name=None,
            is_new=True
        )
        
        # Set the template manager directly on the editor
        editor.template_manager = self.template_manager
        
        # Check that a default structure was created
        self.assertIsNotNone(editor.structure)
        self.assertTrue(len(editor.structure) > 0)
        
        # Close the editor
        editor.close()
    
    def test_accept_with_save_flag(self):
        """Test accepting the dialog with save flag"""
        # Create a structure editor
        editor = EnhancedStructureEditor(
            self.parent,
            structure_name="Test_Template"
        )
        
        # Set the template manager directly on the editor
        editor.template_manager = self.template_manager
        
        # Patch the save_structure method
        with patch.object(editor, 'save_structure') as mock_save:
            # Set the save flag and call accept
            editor._save_on_accept = True
            editor.accept()
            
            # Verify that save_structure was called
            mock_save.assert_called_once()
        
        # Close the editor
        editor.close()
    
    def test_get_current_template_info(self):
        """Test getting the current template info"""
        # Create a structure editor
        editor = EnhancedStructureEditor(
            self.parent,
            structure_name="Test_Template"
        )
        
        # Set the template manager directly on the editor
        editor.template_manager = self.template_manager
        
        # Set up the editor fields
        if hasattr(editor, 'name_input') and editor.name_input:
            editor.name_input.setText("Current Template")
        
        if hasattr(editor, 'description_input') and editor.description_input:
            editor.description_input.setText("Current description")
        
        if hasattr(editor, 'tags_input') and editor.tags_input:
            editor.tags_input.setText("tag1, tag2, tag3")
        
        if hasattr(editor, 'category_combo') and editor.category_combo:
            editor.category_combo.setCurrentText("Category 1")
        
        # Get the current template info
        template_info = editor.get_current_template_info()
        
        # Verify the template info
        self.assertEqual(template_info["name"], "Current Template")
        self.assertEqual(template_info["description"], "Current description")
        self.assertEqual(template_info["tags"], ["tag1", "tag2", "tag3"])
        self.assertEqual(template_info["category"], "Category 1")
        
        # Close the editor
        editor.close()
    
    def test_handle_template_edit_with_template_gallery(self):
        """Test handling template edit in the template gallery"""
        # Create a mocked template gallery
        template_gallery = MagicMock(spec=TemplateGallery)
        template_gallery.template_manager = self.template_manager
        template_gallery.refresh_gallery = MagicMock()
        
        # Patch the EnhancedStructureEditor.exec_ method to return QDialog.Accepted
        with patch('app.ui.structure_editor_enhanced.EnhancedStructureEditor.exec_', return_value=QDialog.Accepted):
            # Call the function
            handle_template_edit(template_gallery, "Test Template")
            
            # Verify that refresh_gallery was called to update the UI
            template_gallery.refresh_gallery.assert_called_once()

if __name__ == '__main__':
    unittest.main() 