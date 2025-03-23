#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script for structure editor file operations.
Tests the addition of files and folders, context menu, and basic functionality.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QTreeWidgetItem
from PyQt5.QtCore import Qt

# Create application instance first
app = QApplication(sys.argv)

# Import structure editor after QApplication created
from app.ui.structure_editor_enhanced import EnhancedStructureEditor

def test_file_operations():
    """Test file operations in the structure editor"""
    # Create structure editor
    editor = EnhancedStructureEditor(
        structure_name="Test_Structure",
        is_new=True
    )
    
    # Test if file_operations was initialized correctly
    assert hasattr(editor, 'file_operations'), "file_operations not initialized"
    assert editor.file_operations is not None, "file_operations is None"
    
    print("\n=== Testing Add Folder ===")
    # Test adding a folder
    root_folder = editor.add_folder()
    assert root_folder is not None, "Failed to add root folder"
    assert isinstance(root_folder, QTreeWidgetItem), "Root folder not a QTreeWidgetItem"
    
    # Get the folder data
    folder_data = root_folder.data(0, Qt.UserRole)
    assert folder_data is not None, "Folder data is None"
    assert folder_data.get('type') == 'folder', "Folder type not set correctly"
    
    print("\n=== Testing Add File ===")
    # Test adding a file with a specific filename to bypass the dialog
    editor.tree_widget.setCurrentItem(root_folder)
    
    # Use a direct call to the file operations with a filename
    file_item = editor.file_operations.add_file(parent_item=root_folder, file_name="test_file.txt")
    
    assert file_item is not None, "Failed to add file item"
    
    # Get child count
    child_count = root_folder.childCount()
    assert child_count > 0, "No file was added to the folder"
    
    # Get the file data
    file_data = file_item.data(0, Qt.UserRole)
    assert file_data is not None, "File data is None"
    assert file_data.get('type') == 'file', "File type not set correctly"
    
    print("\n=== Testing Delete ===")
    # Test deleting an item
    editor.tree_widget.setCurrentItem(file_item)
    editor.delete_selected()
    
    # Check if the file was deleted
    new_child_count = root_folder.childCount()
    assert new_child_count < child_count, "File was not deleted"
    
    print("\n=== Tests Passed ===")
    return True

if __name__ == "__main__":
    try:
        # Run the test
        test_result = test_file_operations()
        sys.exit(0 if test_result else 1)
    except Exception as e:
        print(f"ERROR: Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 