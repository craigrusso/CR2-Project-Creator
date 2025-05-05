#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Debug script to trace the issue with files not being renamed with project name flags
"""

import os
import sys
import tempfile
import shutil
import json
import glob
from pathlib import Path

# Add project directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import project modules
from app.core.project_builder import ProjectBuilder

def run_debug():
    """Run the debug test to trace why files are not being renamed"""
    print("=== Debugging Project Name Renaming ===")
    
    # Template path
    template_path = "/Users/craigrusso/.echelon/templates/ONE_MORE_TIME.json"
    print(f"Loading template from: {template_path}")
    
    # Load template
    try:
        with open(template_path, 'r') as f:
            template_data = json.load(f)
    except Exception as e:
        print(f"Error loading template: {e}")
        return
    
    print(f"Template loaded: {template_data['name']}")
    
    # Print structure to inspect
    print("\nInspecting structure...")
    for idx, item in enumerate(template_data.get('structure', [])):
        if item.get('name') == '1_Premiere Project':
            print(f"Found Premiere Project folder at index {idx}")
            for child in item.get('children', []):
                if child.get('name') == 'REV01':
                    print(f"Found REV01 folder")
                    for file in child.get('children', []):
                        print(f"File: {file.get('name')}")
                        print(f"  rename_flag: {file.get('rename_flag')}")
                        print(f"  uses_project_name: {file.get('uses_project_name')}")
                        print(f"  path: {file.get('path')}")
                        print(f"  original_path: {file.get('original_path')}")
                        print(f"  cached_path: {file.get('cached_path')}")
                        print(f"  is_binary: {file.get('is_binary')}")
    
    # Create output directory
    output_dir = tempfile.mkdtemp()
    print(f"\nOutput directory: {output_dir}")
    
    # Initialize project builder
    project_builder = ProjectBuilder(None)
    
    # Test project name
    project_name = "TestProjectName"
    project_path = os.path.join(output_dir, project_name)
    os.makedirs(project_path, exist_ok=True)
    
    # Create placeholders
    placeholders = {"PROJECT_NAME": project_name}
    
    # Process structure
    print("\nProcessing template structure...")
    created_paths = project_builder._create_folder_structure(
        project_path,
        template_data.get('structure', []),
        placeholders
    )
    
    print(f"\nCreated {len(created_paths)} paths")
    
    # List all created files for verification
    print("\nAll files created in project directory:")
    for root, dirs, files in os.walk(project_path):
        rel_root = os.path.relpath(root, project_path)
        if rel_root == ".":
            rel_root = ""
        for file in files:
            print(f"  {os.path.join(rel_root, file)}")
    
    # Look specifically for renamed files
    print("\nSearching for NASCAR file that should be renamed:")
    search_pattern = os.path.join(project_path, "**", "*.prproj")
    found_files = glob.glob(search_pattern, recursive=True)
    for file in found_files:
        rel_path = os.path.relpath(file, project_path)
        print(f"  {rel_path}")
        
    # Clean up
    print("\nCleaning up test directory...")
    shutil.rmtree(output_dir)

if __name__ == "__main__":
    run_debug() 