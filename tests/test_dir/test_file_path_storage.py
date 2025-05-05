#!/usr/bin/env python3
"""
Test script to verify file path storage during caching and project creation.
This tests the fix for correctly storing original file paths in structure JSON.
"""

import os
import sys
import json
import shutil
import tempfile
import datetime

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the required modules
from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder
from app.utils.utils import get_config_paths


def create_test_files(temp_dir):
    """Create test files in a temporary directory."""
    # Create test files
    test_files = {
        "test1.txt": "This is test file 1.",
        "test2.txt": "This is test file 2.",
        "test3.json": '{"name": "Test JSON", "value": 42}'
    }
    
    # Create subdirectories
    os.makedirs(os.path.join(temp_dir, "subdir1"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "subdir2"), exist_ok=True)
    
    # Create files in subdirectories
    test_files_in_subdirs = {
        os.path.join("subdir1", "subtest1.txt"): "This is a test file in subdir1.",
        os.path.join("subdir2", "subtest2.json"): '{"name": "Subdir Test JSON", "value": 99}'
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


def create_test_structure(file_paths):
    """Create a test structure using the file paths."""
    # Create a custom structure in the format {"folder_name": [children]}
    structure = [
        {"TestRoot": [
            file_paths["test1.txt"],  # Direct file path
            {"SubFolder1": [
                file_paths["test2.txt"],
                file_paths["subdir1/subtest1.txt"]
            ]},
            {"SubFolder2": [
                file_paths["test3.json"],
                file_paths["subdir2/subtest2.json"]
            ]}
        ]}
    ]
    
    return structure


def create_enhanced_structure(file_paths):
    """Create a test structure using the enhanced dictionary format for files."""
    # Create a custom structure in the enhanced format with file dictionaries
    structure = [
        {"TestRoot": [
            # File with dictionary format including path
            {
                'type': 'file',
                'name': os.path.basename(file_paths["test1.txt"]),
                'path': file_paths["test1.txt"],
                'is_binary': False
            },
            {"SubFolder1": [
                # File with dictionary format including path
                {
                    'type': 'file',
                    'name': os.path.basename(file_paths["test2.txt"]),
                    'path': file_paths["test2.txt"],
                    'is_binary': False
                },
                # File with dictionary format including path
                {
                    'type': 'file',
                    'name': os.path.basename(file_paths["subdir1/subtest1.txt"]),
                    'path': file_paths["subdir1/subtest1.txt"],
                    'is_binary': False
                }
            ]},
            {"SubFolder2": [
                # File with dictionary format including path
                {
                    'type': 'file',
                    'name': os.path.basename(file_paths["test3.json"]),
                    'path': file_paths["test3.json"],
                    'is_binary': False
                },
                # File with dictionary format including path
                {
                    'type': 'file',
                    'name': os.path.basename(file_paths["subdir2/subtest2.json"]),
                    'path': file_paths["subdir2/subtest2.json"],
                    'is_binary': False
                }
            ]}
        ]}
    ]
    
    return structure


def main():
    """Main test function."""
    print("Starting file path storage test...")
    
    # Create a temporary directory for the test
    temp_dir = tempfile.mkdtemp()
    cache_dir = os.path.join(temp_dir, "cache")
    output_dir = os.path.join(temp_dir, "output")
    
    print(f"Test directory: {temp_dir}")
    print(f"Cache directory: {cache_dir}")
    print(f"Output directory: {output_dir}")
    
    try:
        # Create the directories
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # Create test files
        print("Creating test files...")
        file_paths = create_test_files(temp_dir)
        
        for name, path in file_paths.items():
            print(f"  {name}: {path}")
        
        # Create a test structure
        print("Creating test structure...")
        structure = create_test_structure(file_paths)
        
        # Configure paths for the template manager
        config_paths = get_config_paths()
        
        # Create required directories for our test
        test_paths = {
            "templates_dir": os.path.join(temp_dir, "templates"),
            "structures_dir": os.path.join(temp_dir, "structures"),
            "custom_structures_dir": os.path.join(temp_dir, "custom_structures"),
            "template_directories_dir": os.path.join(temp_dir, "template_directories"),
            "templates_cache_dir": cache_dir
        }
        
        # Create the test directories
        for path in test_paths.values():
            os.makedirs(path, exist_ok=True)
        
        # Initialize template manager and project builder
        print("Initializing TemplateManager...")
        # Create a monkey patch for get_config_paths to return our test paths
        def mock_get_config_paths():
            paths = test_paths.copy()
            return paths
            
        # Backup original function
        original_get_config_paths = get_config_paths
        
        # Apply monkey patch
        import app.utils.utils
        app.utils.utils.get_config_paths = mock_get_config_paths
        
        # Initialize with monkey patched paths
        template_manager = TemplateManager()
        
        # Restore original function
        app.utils.utils.get_config_paths = original_get_config_paths
        
        # Save the test structure
        structure_name = f"test_structure_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        print(f"Saving test structure as '{structure_name}'...")
        success = template_manager.save_custom_structure(structure_name, structure)
        
        if not success:
            print("Failed to save custom structure")
            return False
            
        # Create a project using the structure
        print("Creating ProjectBuilder...")
        project_builder = ProjectBuilder(template_manager)
        
        project_name = f"test_project_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        print(f"Creating project '{project_name}' with structure '{structure_name}'...")
        
        success, message = project_builder.create_project(
            project_name=project_name,
            output_path=output_dir,
            structure_name=structure_name
        )
        
        if not success:
            print(f"Failed to create project: {message}")
            return False
            
        print(f"Project created successfully at {message}")
        
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
                
                # Read the first 100 bytes of the file to verify it has content
                try:
                    with open(file_path, 'r') as f:
                        content = f.read(100)
                    print(f"    Content (first 100 chars): {content[:100]}")
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


def test_enhanced_structure():
    """Test the enhanced structure format with file dictionaries."""
    print("\n=== Testing Enhanced Structure Format ===")
    
    # Create a temporary directory for the test
    temp_dir = tempfile.mkdtemp()
    cache_dir = os.path.join(temp_dir, "cache")
    output_dir = os.path.join(temp_dir, "output")
    
    print(f"Test directory: {temp_dir}")
    
    try:
        # Create the directories
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # Create test files
        print("Creating test files...")
        file_paths = create_test_files(temp_dir)
        
        # Create a test structure with enhanced format
        print("Creating enhanced test structure...")
        structure = create_enhanced_structure(file_paths)
        
        # Validate the structure can be serialized correctly
        print("Validating structure serialization...")
        structure_str = json.dumps(structure, indent=2)
        test_json_path = os.path.join(temp_dir, "test_structure.json")
        with open(test_json_path, 'w') as f:
            f.write(structure_str)
        
        # Deserialize to make sure it's valid
        with open(test_json_path, 'r') as f:
            loaded_structure = json.load(f)
        
        # Print the structure for debugging
        print(f"Structure sample: {json.dumps(structure[0], indent=2)[:500]}")
        
        # Configure paths for the template manager
        # Create required directories for our test
        test_paths = {
            "templates_dir": os.path.join(temp_dir, "templates"),
            "structures_dir": os.path.join(temp_dir, "structures"),
            "custom_structures_dir": os.path.join(temp_dir, "custom_structures"),
            "template_directories_dir": os.path.join(temp_dir, "template_directories"),
            "templates_cache_dir": cache_dir
        }
        
        # Create the test directories
        for path in test_paths.values():
            os.makedirs(path, exist_ok=True)
        
        # Initialize template manager and project builder
        print("Initializing TemplateManager...")
        # Create a monkey patch for get_config_paths to return our test paths
        def mock_get_config_paths():
            paths = test_paths.copy()
            return paths
            
        # Backup original function
        import app.utils.utils
        original_get_config_paths = app.utils.utils.get_config_paths
        
        # Apply monkey patch
        app.utils.utils.get_config_paths = mock_get_config_paths
        
        # Initialize with monkey patched paths
        template_manager = TemplateManager()
        
        # Restore original function
        app.utils.utils.get_config_paths = original_get_config_paths
        
        # Save the test structure
        structure_name = f"enhanced_test_structure_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        print(f"Saving enhanced test structure as '{structure_name}'...")
        success = template_manager.save_custom_structure(structure_name, structure)
        
        if not success:
            print("Failed to save custom structure")
            return False
            
        # Create a project using the structure
        print("Creating ProjectBuilder...")
        project_builder = ProjectBuilder(template_manager)
        
        project_name = f"enhanced_test_project_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        print(f"Creating project '{project_name}' with structure '{structure_name}'...")
        
        success, message = project_builder.create_project(
            project_name=project_name,
            output_path=output_dir,
            structure_name=structure_name
        )
        
        if not success:
            print(f"Failed to create project: {message}")
            return False
            
        print(f"Project created successfully at {message}")
        
        # Verify the project was created correctly
        project_dir = os.path.join(output_dir, project_name)
        if not os.path.exists(project_dir):
            print(f"Project directory does not exist: {project_dir}")
            return False
            
        # List all files and directories created
        print("Files and directories created in enhanced structure:")
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_dir)
                print(f"  {rel_path}")
                
                # Read the first 100 bytes of the file to verify it has content
                try:
                    with open(file_path, 'r') as f:
                        content = f.read(100)
                    print(f"    Content (first 100 chars): {content[:100]}")
                except Exception as e:
                    print(f"    Error reading file: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error in enhanced structure test: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up temporary directory
        print(f"Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("\n=== Running Standard Structure Test ===")
    standard_success = main()
    
    print("\n=== Running Enhanced Structure Test ===")
    enhanced_success = test_enhanced_structure()
    
    # Exit with success if both tests pass
    sys.exit(0 if standard_success and enhanced_success else 1) 