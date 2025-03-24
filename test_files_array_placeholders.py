#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script to verify proper handling of project name placeholders in the files array
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime

# Add project directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import project modules
from app.core.project_builder import ProjectBuilder

def main():
    """Main test function"""
    print("\n=== Testing Project Name Placeholders in Files Array ===\n")
    
    # Create temp directory and test files
    test_dir = tempfile.mkdtemp()
    project_dir = tempfile.mkdtemp()
    
    try:
        # Create a test file
        test_file_path = os.path.join(test_dir, "test_file.txt")
        with open(test_file_path, 'w') as f:
            f.write("This is a test file with ${PROJECT_NAME} placeholder")
        
        # Create files array with different placeholder and rename_flag combinations
        files_array = [
            # Case 1: Regular file (no placeholders or renaming)
            {
                "file_name": "regular_file.txt",
                "original_path": test_file_path,
                "folder": "regular",
                "rename_flag": False
            },
            # Case 2: File with rename_flag=True
            {
                "file_name": "renamed_file.txt",
                "original_path": test_file_path,
                "folder": "renamed",
                "rename_flag": True
            },
            # Case 3: File with ${PROJECT_NAME} in the filename
            {
                "file_name": "${PROJECT_NAME}_placeholder.txt",
                "original_path": test_file_path,
                "folder": "placeholders",
                "rename_flag": False
            },
            # Case 4: File with ${PROJECT_NAME} in filename AND rename_flag=True
            {
                "file_name": "${PROJECT_NAME}_with_flag.txt",
                "original_path": test_file_path,
                "folder": "mixed",
                "rename_flag": True
            }
        ]
        
        # Initialize project builder
        project_builder = ProjectBuilder(None)
        
        # Define project name and placeholders
        project_name = "TestFilesArray"
        placeholders = {"PROJECT_NAME": project_name}
        
        # Process files array
        print(f"Processing files array with project name: {project_name}")
        copied_files = project_builder._process_files_array(
            project_dir, 
            files_array, 
            placeholders
        )
        
        print(f"\nFiles processed: {len(copied_files)}")
        
        # Define expected files
        expected_files = [
            # Case 1: Regular file (unchanged)
            os.path.join(project_dir, "regular", "regular_file.txt"),
            # Case 2: File with rename_flag=True (should use project name)
            os.path.join(project_dir, "renamed", f"{project_name}.txt"),
            # Case 3: File with placeholder (should replace placeholder)
            os.path.join(project_dir, "placeholders", f"{project_name}_placeholder.txt"),
            # Case 4: File with placeholder and rename_flag (should prioritize placeholder)
            os.path.join(project_dir, "mixed", f"{project_name}_with_flag.txt")
        ]
        
        # Verify files were created correctly
        all_passed = True
        for file_path in expected_files:
            if os.path.exists(file_path):
                print(f"✅ File exists as expected: {file_path}")
                
                # Check file content (should have placeholders replaced)
                with open(file_path, 'r') as f:
                    content = f.read()
                if project_name in content:
                    print(f"  ✅ Content contains project name")
                else:
                    print(f"  ❌ Content missing project name")
                    all_passed = False
            else:
                print(f"❌ Expected file not found: {file_path}")
                all_passed = False
                
        # List all created files for debugging
        print("\nActual files created:")
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                print(f"  {os.path.join(root, file)}")
        
        if all_passed:
            print("\n✅ All tests passed! File array placeholders are working correctly.")
        else:
            print("\n❌ Tests failed! There are issues with file array placeholders.")
            
    finally:
        # Clean up
        print("\nCleaning up test directories...")
        shutil.rmtree(test_dir)
        shutil.rmtree(project_dir)

if __name__ == "__main__":
    main() 