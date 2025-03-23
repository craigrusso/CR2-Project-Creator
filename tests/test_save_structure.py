#!/usr/bin/env python3

import sys
import os
import unittest
from PyQt5.QtWidgets import QApplication, QTreeWidgetItem
from PyQt5.QtCore import Qt

# Add the parent directory to the path to import the app modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import the enhanced structure editor
from app.ui.structure_editor_enhanced import EnhancedStructureEditor

class TestSaveStructureMethod(unittest.TestCase):
    """Test the save_structure method of EnhancedStructureEditor."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the QApplication once for all tests."""
        cls.app = QApplication.instance() or QApplication(sys.argv)
    
    def setUp(self):
        """Set up a fresh instance of EnhancedStructureEditor for each test."""
        self.editor = EnhancedStructureEditor(None, "Test_Structure")
        
        # Create a simple tree structure
        root = self.editor.tree.invisibleRootItem()
        
        # Add Project Root item
        project_root = QTreeWidgetItem(root)
        project_root.setText(0, "Project Root")
        project_root.setData(0, Qt.UserRole, "folder")
        
        # Add a folder item
        folder_item = QTreeWidgetItem(project_root)
        folder_item.setText(0, "Test Folder")
        folder_item.setData(0, Qt.UserRole, "folder")
        
        # Add a file item
        file_item = QTreeWidgetItem(project_root)
        file_item.setText(0, "Test File")
        file_item.setData(0, Qt.UserRole, "file")
        
        # Create temporary directory for test output
        self.test_dir = os.path.join(parent_dir, "tests/temp")
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Mock some methods and attributes to isolate testing
        def get_config_paths_mock():
            return {"custom_structures_dir": self.test_dir}
        
        # Inject our mock to bypass dependency on actual config paths
        self.original_utils = sys.modules.get('app.utils.utils', None)
        import types
        mock_utils = types.ModuleType('utils')
        mock_utils.get_config_paths = get_config_paths_mock
        sys.modules['app.utils.utils'] = mock_utils
        
        # Template info for testing
        self.editor.template_name_edit = type('obj', (object,), {'text': lambda: "Test Template"})
    
    def tearDown(self):
        """Clean up after each test."""
        # Remove test files
        for f in os.listdir(self.test_dir):
            file_path = os.path.join(self.test_dir, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
        
        # Restore original modules if they were replaced
        if self.original_utils:
            sys.modules['app.utils.utils'] = self.original_utils
    
    def test_save_structure_basic(self):
        """Test that save_structure correctly saves structure data."""
        # Mock template_ops methods
        from app.templates.template_operations import TemplateOperations
        original_save_structure = TemplateOperations.save_structure
        original_save_template_info = TemplateOperations.save_template_info
        
        # Replace with test versions that track calls
        calls = []
        def mock_save_structure(self, name, structure):
            calls.append(('save_structure', name, structure))
            return True
            
        def mock_save_template_info(self, name, info):
            calls.append(('save_template_info', name, info))
            return True
        
        TemplateOperations.save_structure = mock_save_structure
        TemplateOperations.save_template_info = mock_save_template_info
        
        try:
            # Run the save structure method
            result = self.editor.save_structure()
            
            # Verify results
            self.assertTrue(result, "save_structure should return True on success")
            self.assertTrue(hasattr(self.editor, 'structure_saved'), "structure_saved flag should be set")
            self.assertTrue(self.editor.structure_saved, "structure_saved flag should be True")
            
            # Check file was created
            json_file = os.path.join(self.test_dir, "Test_Template.json")
            self.assertTrue(os.path.exists(json_file), f"File {json_file} should be created")
            
            # Verify structure matches our tree
            import json
            with open(json_file, 'r') as f:
                data = json.load(f)
                self.assertEqual(data['name'], "Test Template", "Template name should match")
                self.assertEqual(len(data['structure']), 2, "Structure should have 2 items")
                
                # Check item types
                folder_item = None
                file_item = None
                for item in data['structure']:
                    if item['type'] == 'folder':
                        folder_item = item
                    elif item['type'] == 'file':
                        file_item = item
                
                self.assertIsNotNone(folder_item, "Folder item should exist in structure")
                self.assertIsNotNone(file_item, "File item should exist in structure")
                self.assertEqual(folder_item['name'], "Test Folder", "Folder name should match")
                self.assertEqual(file_item['name'], "Test File", "File name should match")
                
        finally:
            # Restore original methods
            TemplateOperations.save_structure = original_save_structure
            TemplateOperations.save_template_info = original_save_template_info
    
    def test_accept_without_endless_loop(self):
        """Test that calling accept doesn't create an endless loop."""
        # Track calls to save_structure to ensure it's only called once
        original_save_structure = self.editor.save_structure
        
        call_count = 0
        def mock_save_structure():
            nonlocal call_count
            call_count += 1
            # Don't actually execute the method to avoid side effects
            return True
        
        self.editor.save_structure = mock_save_structure
        
        try:
            # Call accept, which should call save_structure once
            self.editor.accept()
            
            # Verify it called save_structure just once
            self.assertEqual(call_count, 1, "accept() should call save_structure exactly once")
            
            # Now set structure_saved to True
            self.editor.structure_saved = True
            
            # Reset counter
            call_count = 0
            
            # Call accept again, it should skip save_structure
            self.editor.accept()
            
            # Verify save_structure wasn't called again
            self.assertEqual(call_count, 0, "accept() should not call save_structure when structure_saved is True")
            
        finally:
            # Restore original method
            self.editor.save_structure = original_save_structure
    
    def test_circular_reference_prevention(self):
        """Test that we don't create a circular reference between save_structure and accept."""
        # Mock super().accept() to track calls and prevent actual dialog closing
        super_called = False
        
        # Store original QDialog.accept method
        original_qdialog_accept = self.editor.__class__.__bases__[0].accept
        
        # Replace it with our mock
        def mock_super_accept(self):
            nonlocal super_called
            super_called = True
        
        # Apply the mock
        self.editor.__class__.__bases__[0].accept = mock_super_accept
        
        try:
            # Call save_structure
            self.editor.save_structure()
            
            # Verify it didn't call accept, which would trigger loop
            self.assertEqual(self.editor.result(), 1, "Dialog result should be set to 1 (Accepted)")
            self.assertFalse(super_called, "save_structure should not call super().accept()")
            
            # Now call accept
            self.editor.accept()
            
            # Verify it did call super.accept now
            self.assertTrue(super_called, "accept() should call super().accept()")
            
        finally:
            # Restore original method
            self.editor.__class__.__bases__[0].accept = original_qdialog_accept

if __name__ == '__main__':
    unittest.main() 