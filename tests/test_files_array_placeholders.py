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
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test file with a placeholder
        test_file_path = os.path.join(temp_dir, "test_file.txt")
        with open(test_file_path, "w") as f:
            f.write("This is a test file with {{PROJECT_NAME}} placeholder\n")
        
        # Create output directory
        project_dir = os.path.join(temp_dir, "output")
        os.makedirs(project_dir, exist_ok=True)
        
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
        success, copied_files = project_builder._process_files_array(
            project_dir, 
            files_array, 
            placeholders
        )
        
        if success:
            print(f"\nFiles processed successfully: {len(copied_files)}")
            
            # Verify the results
            expected_files = [
                os.path.join(project_dir, "regular", "regular_file.txt"),
                os.path.join(project_dir, "renamed", "TestFilesArray.txt"),
                os.path.join(project_dir, "placeholders", "TestFilesArray_placeholder.txt"),
                os.path.join(project_dir, "mixed", "TestFilesArray.txt")
            ]
            
            for expected_file in expected_files:
                if os.path.exists(expected_file):
                    print(f"✅ File exists: {expected_file}")
                else:
                    print(f"❌ File missing: {expected_file}")
        else:
            print(f"\nError processing files: {copied_files}")

if __name__ == "__main__":
    main() 