#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script to verify enhanced structure handling for drag and drop files
This verifies that files added via drag and drop maintain their file paths 
in the structure JSON and can be correctly used when creating a project.
"""

import os
import sys
import json
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create QApplication first
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from app.ui.structure_editor.structure_converter import StructureConverter
from app.core.project_builder import ProjectBuilder

def create_test_files(temp_dir):
    """Create test files in a temporary directory."""
    # Create test files
    test_files = {
        "test1.txt": "This is test file 1 with ${PROJECT_NAME}.",
        "test2.txt": "This is test file 2 for ${PROJECT_NAME}.",
        "test3.json": '{"name": "${PROJECT_NAME}", "value": 42}'
    }
    
    # Create subdirectories
    os.makedirs(os.path.join(temp_dir, "subdir"), exist_ok=True)
    
    # Create files in subdirectories
    test_files_in_subdirs = {
        os.path.join("subdir", "subtest.txt"): "This is a test file in subdir for ${PROJECT_NAME}."
    }
    
    # Write files to disk
    file_paths = {}
    for filename, content in test_files.items():
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        file_paths[filename] = file_path
    
    for rel_path, content in test_files_in_subdirs.items():
        file_path = os.path.join(temp_dir, rel_path)
        with open(file_path, 'w') as f:
            f.write(content)
        file_paths[rel_path] = file_path
    
    return file_paths

def test_structure_converter():
    """Test the StructureConverter class to ensure it preserves file paths."""
    print("=== Testing StructureConverter file path preservation ===")
    
    # Create temp directory for test files
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create test files
        print("Creating test files...")
        file_paths = create_test_files(temp_dir)
        
        # Create a mock QTreeWidgetItem with file data
        from PyQt5.QtWidgets import QTreeWidgetItem, QTreeWidget
        from PyQt5.QtCore import Qt
        
        # Create a tree widget to hold our items
        tree = QTreeWidget()
        root = tree.invisibleRootItem()
        
        # Create a folder item
        folder_item = QTreeWidgetItem(root)
        folder_item.setText(0, "TestFolder")
        folder_data = {'type': 'folder', 'name': 'TestFolder'}
        folder_item.setData(0, Qt.UserRole, folder_data)
        
        # Create file items in the folder with file paths
        for filename, filepath in file_paths.items():
            file_item = QTreeWidgetItem(folder_item)
            file_item.setText(0, os.path.basename(filename))
            
            # Create the file data with path info
            file_data = {
                'type': 'file',
                'name': os.path.basename(filename),
                'path': filepath,
                'is_binary': False
            }
            file_item.setData(0, Qt.UserRole, file_data)
        
        # Create structure converter
        converter = StructureConverter(tree)
        
        # Convert tree to structure
        print("Converting tree to structure...")
        structure = converter.create_structure_from_tree()
        
        # Serialize the structure to JSON
        print("Serializing structure to JSON...")
        structure_json = json.dumps(structure, indent=2)
        
        # Print a sample of the structure
        print(f"Structure sample: {structure_json[:500]}...")
        
        # Write to a temp file
        json_path = os.path.join(temp_dir, "structure.json")
        with open(json_path, 'w') as f:
            f.write(structure_json)
            
        # Read back as if coming from a file
        with open(json_path, 'r') as f:
            deserialized_structure = json.load(f)
            
        print("Testing ProjectBuilder with the structure...")
        # Create output directory
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create project builder directly (no template manager)
        builder = ProjectBuilder(None)
        
        # Test creating a project
        success, result = builder.create_project(
            project_name="TestProject",
            output_path=output_dir,
            structure_data=deserialized_structure
        )
        
        if success:
            print(f"Project created successfully at: {result}")
            
            # Check for files
            print("Files in the project:")
            for root, dirs, files in os.walk(result):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, result)
                    print(f"  {rel_path}")
                    
                    # Read content to verify placeholder replacements
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read(100)
                        print(f"    Content: {content[:100]}")
                    except Exception as e:
                        print(f"    Error reading file: {e}")
                        
            return True
        else:
            print(f"Failed to create project: {result}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)
        
if __name__ == "__main__":
    result = test_structure_converter()
    sys.exit(0 if result else 1) 