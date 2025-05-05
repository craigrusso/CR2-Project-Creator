#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script to verify proper handling of project name flags with different combinations
of rename_flag, uses_project_name and ${PROJECT_NAME} placeholders
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
    """Create a test template with various combinations of flags and placeholders"""
    # Create temp directory for test files
    test_dir = tempfile.mkdtemp()
    
    # Create test files
    test_file_path = os.path.join(test_dir, "test_file.txt")
    with open(test_file_path, 'w') as f:
        f.write("Regular file content")
    
    # Create template structure
    template = {
        "name": "Flag Combinations Test Template",
        "description": "Test template for project name flag combinations",
        "category": "Test",
        "created": datetime.now().isoformat(),
        "modified": datetime.now().isoformat(),
        "structure": [
            {
                "type": "folder",
                "name": "Test Files",
                "children": [
                    # Case 1: Regular file (no renaming)
                    {
                        "type": "file",
                        "name": "regular_file.txt",
                        "rename_flag": False,
                        "uses_project_name": False,
                        "path": test_file_path
                    },
                    # Case 2: rename_flag=True only
                    {
                        "type": "file",
                        "name": "rename_flag_true.txt",
                        "rename_flag": True,
                        "uses_project_name": False,
                        "path": test_file_path
                    },
                    # Case 3: uses_project_name=True only (legacy)
                    {
                        "type": "file",
                        "name": "uses_project_name_true.txt",
                        "rename_flag": False,
                        "uses_project_name": True,
                        "path": test_file_path
                    },
                    # Case 4: Both flags True
                    {
                        "type": "file",
                        "name": "both_flags_true.txt",
                        "rename_flag": True,
                        "uses_project_name": True,
                        "path": test_file_path
                    },
                    # Case 5: ${PROJECT_NAME} in filename
                    {
                        "type": "file",
                        "name": "${PROJECT_NAME}_placeholder.txt",
                        "rename_flag": False,
                        "uses_project_name": False,
                        "path": test_file_path
                    },
                    # Case 6: ${PROJECT_NAME} + rename_flag=True (should prioritize placeholder)
                    {
                        "type": "file",
                        "name": "${PROJECT_NAME}_with_rename_flag.txt",
                        "rename_flag": True,
                        "uses_project_name": False,
                        "path": test_file_path
                    },
                    # Case 7: ${PROJECT_NAME} with content placeholders
                    {
                        "type": "file",
                        "name": "${PROJECT_NAME}_config.json",
                        "rename_flag": False,
                        "uses_project_name": False,
                        "content": "{ \"project\": \"${PROJECT_NAME}\", \"description\": \"Config for ${PROJECT_NAME}\" }"
                    }
                ]
            }
        ]
    }
    
    return template, test_dir

def main():
    """Main test function"""
    print("\n=== Testing Project Name Flag Combinations ===\n")
    print("Creating test template...")
    template, test_dir = create_test_template()
    
    try:
        # Create output directory
        output_dir = tempfile.mkdtemp()
        print(f"Output directory: {output_dir}")
        
        # Initialize project builder
        project_builder = ProjectBuilder(None)
        
        # Create project with test template
        project_name = "TestFlagProject"
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
        
        print(f"\nProject created. Files and folders created: {len(created_paths)}")
        
        # Define expected files with details for checking
        expected_files = {
            # Case 1: Regular file (no renaming)
            os.path.join(project_path, "Test Files", "regular_file.txt"): {
                "description": "Regular file with no renaming",
                "requires_exact_match": True
            },
            # Case 2: rename_flag=True only
            os.path.join(project_path, "Test Files", f"{project_name}.txt"): {
                "description": "File with rename_flag=True",
                "requires_exact_match": False
            },
            # Case 3: uses_project_name=True only (legacy)
            os.path.join(project_path, "Test Files", f"{project_name}.txt"): {
                "description": "File with uses_project_name=True (legacy)",
                "requires_exact_match": False
            },
            # Case 4: Both flags True
            os.path.join(project_path, "Test Files", f"{project_name}.txt"): {
                "description": "File with both flags True",
                "requires_exact_match": False
            },
            # Case 5: ${PROJECT_NAME} in filename
            os.path.join(project_path, "Test Files", f"{project_name}_placeholder.txt"): {
                "description": "File with ${PROJECT_NAME} placeholder in name",
                "requires_exact_match": True
            },
            # Case 6: ${PROJECT_NAME} + rename_flag=True (should prioritize placeholder)
            os.path.join(project_path, "Test Files", f"{project_name}_with_rename_flag.txt"): {
                "description": "File with ${PROJECT_NAME} placeholder and rename_flag=True",
                "requires_exact_match": False  # It might get renamed due to conflict
            },
            # Case 7: ${PROJECT_NAME} with content placeholders
            os.path.join(project_path, "Test Files", f"{project_name}_config.json"): {
                "description": "File with ${PROJECT_NAME} in name and content",
                "requires_exact_match": True,
                "check_content": True
            }
        }
        
        # Verify project files
        all_passed = True
        
        # Set to track which test cases have been verified
        verified_test_cases = set()
        
        # First check for the specific expected files
        for file_path, details in expected_files.items():
            description = details["description"]
            if os.path.exists(file_path):
                print(f"✅ File exists: {file_path} ({description})")
                verified_test_cases.add(file_path)
                
                # For JSON file, verify content placeholders were replaced
                if details.get("check_content", False):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    if project_name in content:
                        print(f"  ✅ Content placeholders replaced correctly: {content}")
                    else:
                        print(f"  ❌ Content placeholders not replaced: {content}")
                        all_passed = False
        
        # List all created files for debugging and check for timestamp variants
        print("\nActual files created in the project folder:")
        created_file_paths = []
        for root, dirs, files in os.walk(project_path):
            for file in files:
                file_path = os.path.join(root, file)
                created_file_paths.append(file_path)
                print(f"  {file_path}")
        
        # Check each expected file against the list of actually created files
        for expected_path, details in expected_files.items():
            if expected_path in verified_test_cases:
                # Already verified
                continue
                
            description = details['description']
            requires_exact_match = details.get('requires_exact_match', False)
            
            # Skip this check if we need an exact match but it wasn't found
            if requires_exact_match:
                print(f"❌ Required exact match not found: {expected_path} ({description})")
                all_passed = False
                continue
            
            # Look for variations of the expected file
            expected_dir = os.path.dirname(expected_path)
            expected_name = os.path.basename(expected_path)
            expected_base, expected_ext = os.path.splitext(expected_name)
            
            match_found = False
            for created_path in created_file_paths:
                created_dir = os.path.dirname(created_path)
                created_name = os.path.basename(created_path)
                created_base, created_ext = os.path.splitext(created_name)
                
                # Check if this is a match or variant
                if (created_dir == expected_dir and 
                    created_ext == expected_ext and 
                    (created_base == expected_base or  # Exact base name match
                     created_base == project_name or   # Renamed to just project name
                     created_base.startswith(f"{project_name}_"))):  # Timestamped variant
                    
                    print(f"✅ File variant match: {created_path} ({description})")
                    match_found = True
                    verified_test_cases.add(expected_path)
                    break
                    
            if not match_found:
                print(f"❌ No matching variant found for: {expected_path} ({description})")
                all_passed = False
        
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