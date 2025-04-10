#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script for file handling in templates
"""

import os
import sys
import json
import tempfile
import shutil
import time
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
from app.utils.file_cache_manager import FileCacheManager
from app.core.project_builder import ProjectBuilder
from app.templates.template_manager import TemplateManager

def create_test_files(temp_dir):
    """Create some test files for our test"""
    test_files = {}
    
    # Create a text file
    text_file = os.path.join(temp_dir, "test_text.txt")
    with open(text_file, 'w') as f:
        f.write("This is a test text file for the template\nProject: ${PROJECT_NAME}")
    test_files['text'] = text_file
    
    # Create a JSON file
    json_file = os.path.join(temp_dir, "test_config.json")
    with open(json_file, 'w') as f:
        json.dump({
            "name": "Test Config", 
            "version": "1.0.0",
            "projectName": "${PROJECT_NAME}"
        }, f, indent=2)
    test_files['json'] = json_file
    
    # Create a mock project file
    project_file = os.path.join(temp_dir, "TEST_PROJECT.prproj")
    with open(project_file, 'w') as f:
        f.write("Mock Premiere Pro project file for ${PROJECT_NAME}")
    test_files['project'] = project_file
    
    return test_files

def create_test_template(template_name, file_paths):
    """Create a test template with the new file structure format"""
    # Create the basic structure
    template = {
        "name": template_name,
        "description": "Test template with file objects",
        "category": "Test",
        "type": "Standard",
        "created": time.time(),
        "modified": time.time(),
        "tags": ["test"],
        "structure": {
            "root": [
                {
                    "name": "1_Project_Files",
                    "type": "folder",
                    "children": [
                        {
                            "name": "Version_01",
                            "type": "folder"
                        }
                    ]
                },
                {
                    "name": "2_Assets",
                    "type": "folder",
                    "children": [
                        {
                            "name": "Documents",
                            "type": "folder"
                        }
                    ]
                },
                {
                    "name": "3_Exports",
                    "type": "folder"
                }
            ]
        },
        "files": [
            {
                "file_name": "TEST_PROJECT.prproj",
                "original_path": file_paths['project'],
                "cached_path": "",  # Will be populated by cache manager
                "rename_flag": True,
                "folder": "1_Project_Files/Version_01",
                "file_type": "video",
                "size": os.path.getsize(file_paths['project']),
                "last_modified": datetime.fromtimestamp(os.path.getmtime(file_paths['project'])).isoformat()
            },
            {
                "file_name": "test_text.txt",
                "original_path": file_paths['text'],
                "cached_path": "",  # Will be populated by cache manager
                "rename_flag": False,
                "folder": "2_Assets/Documents",
                "file_type": "document",
                "size": os.path.getsize(file_paths['text']),
                "last_modified": datetime.fromtimestamp(os.path.getmtime(file_paths['text'])).isoformat()
            },
            {
                "file_name": "test_config.json",
                "original_path": file_paths['json'],
                "cached_path": "",  # Will be populated by cache manager
                "rename_flag": False,
                "folder": "2_Assets",
                "file_type": "code",
                "size": os.path.getsize(file_paths['json']),
                "last_modified": datetime.fromtimestamp(os.path.getmtime(file_paths['json'])).isoformat()
            }
        ]
    }
    
    return template

def cache_template_files(template, cache_dir):
    """Cache files in the template"""
    cache_manager = FileCacheManager(cache_dir)
    template_name = template["name"]
    
    # Cache each file and update cached_path
    for i, file_data in enumerate(template["files"]):
        file_path = file_data["original_path"]
        folder = file_data["folder"]
        
        # Cache the file
        file_info = cache_manager.cache_file(file_path, template_name, folder)
        
        if file_info:
            # Update cached_path in template
            template["files"][i]["cached_path"] = file_info["cached_path"]
            print(f"Cached file: {file_path} -> {file_info['cached_path']}")
        else:
            print(f"Failed to cache file: {file_path}")
    
    return template

def test_project_creation(template, output_dir):
    """Test creating a project with the template"""
    # Initialize project builder without template manager
    project_builder = ProjectBuilder(None)
    
    # Create project
    project_name = "TestFileProject"
    
    # Process template files array directly with a placeholder
    placeholders = {'PROJECT_NAME': project_name}
    
    # Create project directory
    project_dir = os.path.join(output_dir, project_name)
    os.makedirs(project_dir, exist_ok=True)
    
    # Create the folder structure
    if 'structure' in template:
        structure_data = template['structure']
        # Create folder structure
        folders_created = project_builder._create_folders_from_structure(project_dir, structure_data)
        print(f"Created {len(folders_created)} folders")
    
    # Process files
    if 'files' in template:
        success, files_processed = project_builder._process_files_array(project_dir, template['files'], placeholders, True)
        if success:
            print(f"Processed {len(files_processed)} files")
        else:
            print(f"Error processing files: {files_processed}")
    
    # Return success with project directory
    success = True
    return success, project_dir

def main():
    """Main test function"""
    print("=== Testing File Template System ===")
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    cache_dir = os.path.join(temp_dir, "cache")
    output_dir = os.path.join(temp_dir, "output")
    
    try:
        # Create test directories
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # Create test files
        print("\n1. Creating test files...")
        test_files = create_test_files(temp_dir)
        print(f"Created {len(test_files)} test files in {temp_dir}")
        
        # Create test template
        print("\n2. Creating test template...")
        template = create_test_template("TestFileTemplate", test_files)
        print(f"Created template: {template['name']}")
        
        # Cache template files
        print("\n3. Caching template files...")
        template = cache_template_files(template, cache_dir)
        
        # Save template to file
        template_path = os.path.join(temp_dir, "test_template.json")
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)
        print(f"Saved template to: {template_path}")
        
        # Test project creation
        print("\n4. Testing project creation...")
        test_project_creation(template, output_dir)
        
    finally:
        print(f"\nCleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main() 