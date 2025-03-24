#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script to verify file caching and copying fixes
This script tests:
1. Creating and caching files
2. Verifying the cache paths are correct
3. Creating a project with the cached files
4. Verifying the files are correctly copied to the project
"""

import os
import shutil
import tempfile
import sys
import json
import datetime

# Add parent directory to path to allow importing app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder
from app.utils.cache_preferences import CachePreferences

def create_test_files(directory):
    """Create test files in the specified directory"""
    # Create a test text file
    text_file = os.path.join(directory, "test_text.txt")
    with open(text_file, 'w') as f:
        f.write("This is a test text file with ${PROJECT_NAME} placeholder.")
    
    # Create a test JSON file
    json_file = os.path.join(directory, "test_config.json")
    with open(json_file, 'w') as f:
        json.dump({
            "name": "${PROJECT_NAME}",
            "description": "Test configuration for ${PROJECT_NAME}",
            "created": datetime.datetime.now().isoformat()
        }, f, indent=2)
    
    # Create a binary-like file
    binary_file = os.path.join(directory, "test_binary.bin")
    with open(binary_file, 'wb') as f:
        f.write(os.urandom(1024))  # 1 KB of random data
    
    return [text_file, json_file, binary_file]

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 40)
    print(f" {title} ")
    print("=" * 40)

def main():
    """Test file caching and project creation with cached files"""
    print_section("File Caching Test")
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    print(f"Created temporary directory at: {temp_dir}")
    
    test_files_dir = os.path.join(temp_dir, "test_files")
    os.makedirs(test_files_dir, exist_ok=True)
    
    cache_dir = os.path.join(temp_dir, "cache", "TEST_CACHE")
    os.makedirs(cache_dir, exist_ok=True)
    
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Create test files
    print_section("Creating Test Files")
    test_files = create_test_files(test_files_dir)
    for file_path in test_files:
        print(f"Created test file: {file_path}")
    
    # Initialize template manager with test paths
    print_section("Initializing Template Manager")
    template_manager = TemplateManager()
    
    # Override cache paths for testing
    template_manager.paths["templates_cache_dir"] = os.path.join(temp_dir, "cache")
    print(f"Set templates_cache_dir to: {template_manager.paths['templates_cache_dir']}")
    
    # Test file caching
    print_section("Testing File Caching")
    print("Testing individual file caching:")
    
    # Test caching each file
    for file_path in test_files:
        cached_path = template_manager._cache_file(file_path, cache_dir)
        if cached_path:
            print(f"Successfully cached file: {file_path} -> {cached_path}")
            # Verify the file exists
            if os.path.exists(cached_path):
                print(f"  Verified cache file exists: {cached_path}")
            else:
                print(f"  ERROR: Cached file does not exist: {cached_path}")
        else:
            print(f"ERROR: Failed to cache file: {file_path}")
    
    # Create a structure with the test files
    print_section("Creating Test Structure")
    structure = []
    
    # Add files to the structure
    for file_path in test_files:
        file_name = os.path.basename(file_path)
        file_item = {
            "name": file_name,
            "type": "file",
            "path": file_path
        }
        structure.append(file_item)
    
    # Add a subdirectory with files
    subdir_structure = {
        "name": "subdir",
        "type": "directory",
        "children": []
    }
    
    # Create a subdirectory in the test files directory
    subdir_path = os.path.join(test_files_dir, "subdir")
    os.makedirs(subdir_path, exist_ok=True)
    
    # Create a file in the subdirectory
    subdir_file = os.path.join(subdir_path, "subdir_file.txt")
    with open(subdir_file, 'w') as f:
        f.write("This is a file in a subdirectory for ${PROJECT_NAME}")
    
    # Add the subdirectory file to the structure
    subdir_structure["children"].append({
        "name": "subdir_file.txt",
        "type": "file",
        "path": subdir_file
    })
    
    # Add the subdirectory to the structure
    structure.append(subdir_structure)
    
    print(f"Created structure with {len(structure)} top-level items")
    
    # Cache the structure files
    print_section("Caching Structure Files")
    
    # Use direct file caching
    print("Caching files directly:")
    # Use a simple file caching function to avoid dependencies
    def cache_files(structure, cache_dir):
        """Simple function to cache files in a structure"""
        os.makedirs(cache_dir, exist_ok=True)
        
        def process_item(item):
            """Process a structure item and cache files"""
            if isinstance(item, dict):
                if item.get('type') == 'file' and 'path' in item:
                    path = item['path']
                    if os.path.exists(path):
                        # Cache the file
                        filename = os.path.basename(path)
                        cache_path = os.path.join(cache_dir, filename)
                        shutil.copy2(path, cache_path)
                        print(f"Cached file: {path} -> {cache_path}")
                        
                        # Add cache path to the item
                        item['cache_path'] = cache_path
                
                # Process children if present
                if 'children' in item and isinstance(item['children'], list):
                    for child in item['children']:
                        process_item(child)
                        
            elif isinstance(item, list):
                for child in item:
                    process_item(child)
                    
        # Process the structure
        process_item(structure)
        return structure
        
    # Create cache directory
    cache_dir = os.path.join(template_manager.paths['templates_cache_dir'], "TEST_CACHE")
    print(f"Caching files to: {cache_dir}")
    
    # Cache the files
    updated_structure = cache_files(structure, cache_dir)
    
    # Verify cache paths
    print_section("Verifying Cache Paths")
    
    def check_cache_paths(structure, depth=0):
        """Check if all files in the structure have valid cache paths"""
        indent = "  " * depth
        if isinstance(structure, list):
            for item in structure:
                check_cache_paths(item, depth)
        elif isinstance(structure, dict):
            if structure.get('type') == 'file':
                name = structure.get('name', 'unnamed')
                path = structure.get('path', 'no path')
                cache_path = structure.get('cache_path', 'no cache path')
                
                print(f"{indent}File: {name}")
                print(f"{indent}  Original: {path}")
                print(f"{indent}  Cache: {cache_path}")
                
                if isinstance(cache_path, str) and os.path.exists(cache_path):
                    print(f"{indent}  ✅ Cache file exists")
                else:
                    print(f"{indent}  ❌ Cache file does not exist or is not a valid path")
            
            if 'children' in structure and isinstance(structure['children'], list):
                name = structure.get('name', 'unnamed')
                print(f"{indent}Directory: {name}")
                check_cache_paths(structure['children'], depth + 1)
    
    check_cache_paths(updated_structure)
    
    # Create project with the structure
    print_section("Creating Project with Cached Files")
    
    project_builder = ProjectBuilder(template_manager)
    project_name = "CACHE_TEST_PROJECT"
    
    print(f"Creating project '{project_name}' in {output_dir}")
    success, result = project_builder.create_project(
        project_name=project_name,
        output_path=output_dir,
        structure_data=updated_structure
    )
    
    if success:
        print(f"Project created successfully at: {result}")
        project_path = result
        
        # List the created files
        print_section("Listing Created Files")
        for root, dirs, files in os.walk(project_path):
            rel_path = os.path.relpath(root, project_path)
            level = rel_path.count(os.sep)
            indent = "  " * level
            
            if rel_path != '.':
                print(f"{indent}{os.path.basename(root)}/")
            else:
                print(f"{project_name}/")
                
            for file in files:
                print(f"{indent}  {file}")
                
                # Check if placeholders were replaced in text files
                file_path = os.path.join(root, file)
                if file.endswith('.txt') or file.endswith('.json'):
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            if '${PROJECT_NAME}' in content:
                                print(f"{indent}    ❌ Placeholder not replaced in {file}")
                            else:
                                print(f"{indent}    ✅ Placeholders replaced")
                    except Exception as e:
                        print(f"{indent}    ❌ Error reading file: {e}")
    else:
        print(f"ERROR: Failed to create project: {result}")
    
    # Clean up
    print_section("Cleaning Up")
    print(f"Removing temporary directory: {temp_dir}")
    shutil.rmtree(temp_dir)
    print("Cleanup complete")

if __name__ == "__main__":
    main() 