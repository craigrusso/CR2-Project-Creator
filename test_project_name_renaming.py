#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script to verify proper renaming of files with rename_flag or uses_project_name flags
"""

import os
import sys
import tempfile
import shutil
import glob
from pathlib import Path

# Add project directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import project modules
from app.core.project_builder import ProjectBuilder

def create_test_structure():
    """Create a test structure with files that should be renamed"""
    # Create temporary files
    test_dir = tempfile.mkdtemp()
    
    # Create test files
    file1_path = os.path.join(test_dir, "regular_file.txt")
    with open(file1_path, 'w') as f:
        f.write("Regular file content")
    
    file2_path = os.path.join(test_dir, "rename_flag_file.txt")
    with open(file2_path, 'w') as f:
        f.write("File with rename_flag=True")
    
    file3_path = os.path.join(test_dir, "uses_project_name_file.txt")
    with open(file3_path, 'w') as f:
        f.write("File with uses_project_name=True")
    
    file4_path = os.path.join(test_dir, "both_flags_file.txt")
    with open(file4_path, 'w') as f:
        f.write("File with both flags")
    
    file5_path = os.path.join(test_dir, "binary_file.bin")
    with open(file5_path, 'wb') as f:
        f.write(b'\x00\x01\x02\x03')
        
    # Test structure with different combinations of flags
    structure = [
        {
            "name": "root",
            "type": "folder",
            "children": [
                {
                    "name": "regular_files",
                    "type": "folder",
                    "children": [
                        {
                            "name": "regular_file.txt",
                            "type": "file",
                            "rename_flag": False,
                            "uses_project_name": False,
                            "path": file1_path
                        }
                    ]
                },
                {
                    "name": "renamed_files",
                    "type": "folder",
                    "children": [
                        {
                            "name": "rename_flag_file.txt",
                            "type": "file",
                            "rename_flag": True,
                            "uses_project_name": False,
                            "path": file2_path
                        },
                        {
                            "name": "uses_project_name_file.txt",
                            "type": "file",
                            "rename_flag": False,
                            "uses_project_name": True,
                            "path": file3_path
                        },
                        {
                            "name": "both_flags_file.txt",
                            "type": "file",
                            "rename_flag": True, 
                            "uses_project_name": True,
                            "path": file4_path
                        },
                        {
                            "name": "binary_file.bin",
                            "type": "file",
                            "rename_flag": True,
                            "uses_project_name": True,
                            "path": file5_path,
                            "is_binary": True
                        }
                    ]
                }
            ]
        }
    ]
    
    return structure, test_dir

def run_test():
    """Run the test and verify that files are renamed correctly"""
    print("=== Testing Project Name Renaming ===")
    
    # Create test structure
    structure, test_dir = create_test_structure()
    print(f"Created test structure in {test_dir}")
    
    try:
        # Create output directory
        output_dir = tempfile.mkdtemp()
        print(f"Output directory: {output_dir}")
        
        # Initialize project builder
        project_builder = ProjectBuilder(None)
        
        # Test project name
        project_name = "TestProject"
        project_path = os.path.join(output_dir, project_name)
        os.makedirs(project_path, exist_ok=True)
        
        # Create placeholders
        placeholders = {"PROJECT_NAME": project_name}
        
        # Process structure
        created_paths = project_builder._create_folder_structure(
            project_path,
            structure,
            placeholders
        )
        
        print(f"Created {len(created_paths)} paths")
        
        # Check for renamed files
        regular_file_path = os.path.join(project_path, "regular_files", "regular_file.txt")
        rename_flag_path = os.path.join(project_path, "renamed_files", f"{project_name}.txt")
        uses_project_name_path = os.path.join(project_path, "renamed_files", f"{project_name}.txt")
        both_flags_path = os.path.join(project_path, "renamed_files", f"{project_name}.txt")
        binary_file_path = os.path.join(project_path, "renamed_files", f"{project_name}.bin")
        
        # Verify regular file
        print("\nChecking regular file (should not be renamed)...")
        if os.path.exists(regular_file_path):
            print(f"✅ Regular file exists at expected path: {regular_file_path}")
        else:
            print(f"❌ Regular file missing at expected path: {regular_file_path}")
            # Search for where it might actually be
            search_pattern = os.path.join(project_path, "**", "regular_file.txt")
            found_files = glob.glob(search_pattern, recursive=True)
            if found_files:
                print(f"   Found at: {found_files[0]}")
            else:
                print("   File not found anywhere in project directory")
        
        # Verify file with rename_flag
        print("\nChecking file with rename_flag=True...")
        if os.path.exists(rename_flag_path):
            print(f"✅ File with rename_flag=True renamed correctly: {rename_flag_path}")
        else:
            print(f"❌ File with rename_flag=True not found at expected path: {rename_flag_path}")
            # Search for where it might actually be
            search_pattern = os.path.join(project_path, "**", "rename_flag_file.txt")
            found_files = glob.glob(search_pattern, recursive=True)
            if found_files:
                print(f"   Found at original name: {found_files[0]}")
            else:
                search_pattern = os.path.join(project_path, "**", f"{project_name}*.txt")
                found_files = glob.glob(search_pattern, recursive=True)
                if found_files:
                    print(f"   Found renamed at: {found_files[0]}")
                else:
                    print("   File not found anywhere in project directory")
        
        # Verify file with uses_project_name
        print("\nChecking file with uses_project_name=True...")
        if os.path.exists(uses_project_name_path):
            print(f"✅ File with uses_project_name=True renamed correctly: {uses_project_name_path}")
        else:
            print(f"❌ File with uses_project_name=True not found at expected path: {uses_project_name_path}")
            # Search for where it might actually be
            search_pattern = os.path.join(project_path, "**", "uses_project_name_file.txt")
            found_files = glob.glob(search_pattern, recursive=True)
            if found_files:
                print(f"   Found at original name: {found_files[0]}")
            else:
                search_pattern = os.path.join(project_path, "**", f"{project_name}*.txt")
                found_files = glob.glob(search_pattern, recursive=True)
                if found_files:
                    print(f"   Found renamed at: {found_files[0]}")
                else:
                    print("   File not found anywhere in project directory")
        
        # Verify binary file
        print("\nChecking binary file with rename_flag=True...")
        if os.path.exists(binary_file_path):
            print(f"✅ Binary file renamed correctly: {binary_file_path}")
        else:
            print(f"❌ Binary file not found at expected path: {binary_file_path}")
            # Search for where it might actually be
            search_pattern = os.path.join(project_path, "**", "binary_file.bin")
            found_files = glob.glob(search_pattern, recursive=True)
            if found_files:
                print(f"   Found at original name: {found_files[0]}")
            else:
                search_pattern = os.path.join(project_path, "**", f"{project_name}*.bin")
                found_files = glob.glob(search_pattern, recursive=True)
                if found_files:
                    print(f"   Found renamed at: {found_files[0]}")
                else:
                    print("   File not found anywhere in project directory")
        
        # List all created files for verification
        print("\nAll files created in project directory:")
        for root, dirs, files in os.walk(project_path):
            rel_root = os.path.relpath(root, project_path)
            if rel_root == ".":
                rel_root = ""
            for file in files:
                print(f"  {os.path.join(rel_root, file)}")
        
    finally:
        # Clean up
        print("\nCleaning up test directories...")
        shutil.rmtree(test_dir)
        shutil.rmtree(output_dir)

if __name__ == "__main__":
    run_test() 