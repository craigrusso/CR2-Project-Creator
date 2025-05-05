#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script to verify proper handling of project name flags
"""

import os
import sys
import tempfile
import shutil
import json
from datetime import datetime

# Add project directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import project modules
from app.core.project_builder import ProjectBuilder

def create_test_template():
    """Create a simple test template with both regular and project name files"""
    # Create temp directory for test files
    test_dir = tempfile.mkdtemp()
    
    # Create test files
    test_file_path = os.path.join(test_dir, "test_file.txt")
    with open(test_file_path, 'w') as f:
        f.write("Regular file content")
    
    project_file_path = os.path.join(test_dir, "project_name_file.txt")
    with open(project_file_path, 'w') as f:
        f.write("File that should use project name")
    
    # Create template structure
    template = {
        "name": "Test Template",
        "description": "Test template for project name handling",
        "category": "Test",
        "created": datetime.now().isoformat(),
        "modified": datetime.now().isoformat(),
        "structure": [
            {
                "type": "folder",
                "name": "Project Folder",
                "children": [
                    {
                        "type": "folder",
                        "name": "Regular Files",
                        "children": [
                            {
                                "type": "file",
                                "name": "regular_file.txt",
                                "rename_flag": False,
                                "uses_project_name": False,
                                "path": test_file_path
                            }
                        ]
                    },
                    {
                        "type": "folder",
                        "name": "Project Files",
                        "children": [
                            {
                                "type": "file",
                                "name": "project_name_file.txt",
                                "rename_flag": True,
                                "uses_project_name": True,
                                "path": project_file_path
                            },
                            {
                                "type": "file",
                                "name": "${PROJECT_NAME}_config.json",
                                "rename_flag": False,
                                "uses_project_name": False,
                                "content": "{ \"project\": \"${PROJECT_NAME}\" }"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    return template, test_dir

def main():
    """Main test function"""
    print("Creating test template...")
    template, test_dir = create_test_template()
    
    try:
        # Create output directory
        output_dir = tempfile.mkdtemp()
        print(f"Output directory: {output_dir}")
        
        # Initialize project builder
        project_builder = ProjectBuilder(None)
        
        # Create project with test template
        project_name = "TestProjectName"
        project_path = os.path.join(output_dir, project_name)
        os.makedirs(project_path, exist_ok=True)
        
        print(f"Creating project '{project_name}' with template...")
        placeholders = {"PROJECT_NAME": project_name}
        
        # Process template structure
        created_paths = project_builder._create_folder_structure(
            project_path, 
            template["structure"],
            placeholders
        )
        
        print(f"Project created. Files and folders created: {len(created_paths)}")
        
        # Verify project files
        expected_files = [
            # Regular file shouldn't be renamed
            os.path.join(project_path, "Project Folder", "Regular Files", "regular_file.txt"),
            # File with rename_flag=True should use project name
            os.path.join(project_path, "Project Folder", "Project Files", f"{project_name}.txt"),
            # File with ${PROJECT_NAME} in name should have placeholder replaced
            os.path.join(project_path, "Project Folder", "Project Files", f"{project_name}_config.json")
        ]
        
        all_passed = True
        for file_path in expected_files:
            if os.path.exists(file_path):
                print(f"✅ File exists: {file_path}")
            else:
                print(f"❌ File missing: {file_path}")
                all_passed = False
        
        # List all created files for debugging
        print("\nActual files created in the project folder:")
        for root, dirs, files in os.walk(project_path):
            for file in files:
                print(f"  {os.path.join(root, file)}")
        
        if all_passed:
            print("\n✅ All tests passed! Project name flags are working correctly.")
        else:
            print("\n❌ Tests failed! There are issues with project name flags.")
            
    finally:
        # Clean up
        print("\nCleaning up test directories...")
        shutil.rmtree(test_dir)
        shutil.rmtree(output_dir)

if __name__ == "__main__":
    main() 