#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script to verify handling of file dictionaries in ProjectBuilder
This tests the enhancement to properly handle file dictionaries in structure data.
"""

import os
import sys
import json
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.project_builder import ProjectBuilder

def create_test_files(temp_dir):
    """Create test files in a temporary directory."""
    # Create test files
    test_files = {
        "test1.txt": "This is test file 1 with ${PROJECT_NAME}.",
        "test2.txt": "This is test file 2 for ${PROJECT_NAME}.",
        "test3.json": '{"name": "${PROJECT_NAME}", "value": 42}'
    }
    
    # Create files on disk
    file_paths = {}
    for filename, content in test_files.items():
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        file_paths[filename] = file_path
        
    return file_paths

def create_structure_with_file_dicts(file_paths):
    """Create a structure with file dictionaries."""
    # Create the structure
    structure = [
        {"TestRoot": [
            # Add files with dictionary format
            {
                "type": "file",
                "name": "test1.txt",
                "path": file_paths["test1.txt"],
                "is_binary": False
            },
            {
                "type": "file",
                "name": "test2.txt",
                "path": file_paths["test2.txt"],
                "is_binary": False
            },
            {
                "type": "file",
                "name": "test3.json",
                "path": file_paths["test3.json"],
                "is_binary": False
            }
        ]}
    ]
    
    return structure

def test_file_dict_handling():
    """Test the file dictionary handling in ProjectBuilder."""
    print("=== Testing file dictionary handling in ProjectBuilder ===")
    
    # Create temp directory for test files
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create test files
        print("Creating test files...")
        file_paths = create_test_files(temp_dir)
        
        # Create structure with file dictionaries
        print("Creating structure with file dictionaries...")
        structure = create_structure_with_file_dicts(file_paths)
        
        # Serialize and deserialize the structure (to simulate JSON storage)
        print("Serializing and deserializing the structure...")
        json_str = json.dumps(structure)
        json_path = os.path.join(temp_dir, "structure.json")
        with open(json_path, 'w') as f:
            f.write(json_str)
            
        # Read back to simulate real-world usage
        with open(json_path, 'r') as f:
            deserialized_structure = json.load(f)
            
        # Print sample of structure to debug
        print(f"Deserialized structure sample: {str(deserialized_structure)[:500]}...")
        
        # Create output directory
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create the project builder
        project_builder = ProjectBuilder(None)
        
        # Create a project using the structure
        print("Creating project with the structure...")
        project_name = "TestProject"
        success, message = project_builder.create_project(
            project_name=project_name,
            output_path=output_dir,
            structure_data=deserialized_structure
        )
        
        if not success:
            print(f"Failed to create project: {message}")
            return False
            
        print(f"Project created successfully at: {message}")
        
        # Verify the project was created correctly
        project_dir = os.path.join(output_dir, project_name)
        if not os.path.exists(project_dir):
            print(f"Project directory does not exist: {project_dir}")
            return False
            
        # List all files and directories created
        print("Files and directories created:")
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_dir)
                print(f"  {rel_path}")
                
                # Read the first 100 bytes of the file to verify it has content and placeholders
                try:
                    with open(file_path, 'r') as f:
                        content = f.read(100)
                    print(f"    Content: {content[:100]}")
                    
                    # Check if PROJECT_NAME placeholder was replaced
                    if "${PROJECT_NAME}" not in content and project_name in content:
                        print("    ✅ Placeholder successfully replaced")
                    else:
                        print("    ❌ Placeholder not replaced correctly")
                        
                except Exception as e:
                    print(f"    Error reading file: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up temporary directory
        print(f"Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir)
        
if __name__ == "__main__":
    result = test_file_dict_handling()
    sys.exit(0 if result else 1) 