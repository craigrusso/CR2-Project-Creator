#!/usr/bin/env python3
"""
Test script for analyzing and fixing structure format processing.
This tests the structure format handling to identify why folders are created as unnamed_item_X
"""

import os
import json
import shutil
import tempfile
import sys

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder

def dump_structure(structure, indent=0):
    """Pretty print the structure for debugging"""
    if isinstance(structure, dict):
        for key, value in structure.items():
            print("  " * indent + f"{key}: {type(value)}")
            if isinstance(value, (dict, list)):
                dump_structure(value, indent + 1)
    elif isinstance(structure, list):
        for i, item in enumerate(structure):
            if isinstance(item, dict):
                for key, value in item.items():
                    print("  " * indent + f"[{i}] {key}: {type(value)}")
                    if isinstance(value, (dict, list)):
                        dump_structure(value, indent + 1)
            else:
                print("  " * indent + f"[{i}] {item} ({type(item)})")

def test_process_template_original():
    """Test the original _process_template method behavior with our structure format"""
    print("\n=== Testing Original Process Template Behavior ===")
    
    # Create a temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Initialize managers
        template_manager = TemplateManager()
        project_builder = ProjectBuilder(template_manager)
        
        # Load a real custom structure
        test_structure_path = "/Users/craigrusso/.echelon/structures/Template_oh_my_goe.json"
        
        with open(test_structure_path, 'r') as f:
            structure_data = json.load(f)
        
        print(f"Loaded structure: {structure_data['name']}")
        print(f"Structure format:")
        dump_structure(structure_data)
        
        # Extract the directories array
        directories = structure_data.get('directories', [])
        
        print("\nProcessing structure with original method...\n")
        created_paths = project_builder._create_folder_structure(output_dir, directories)
        
        print(f"\nCreated {len(created_paths)} paths with original method")
        print("Created directory structure:")
        for path in created_paths:
            rel_path = os.path.relpath(path, output_dir)
            print(f"  {rel_path}")
        
    finally:
        # Clean up
        print(f"\nCleaning up temp directory: {temp_dir}")
        shutil.rmtree(temp_dir)

def enhanced_process_template(project_builder, output_path, structure, placeholders, created_paths, dry_run=False):
    """Enhanced version of _process_template that handles our custom structure format correctly"""
    if not structure:
        return created_paths
    
    # Handle a list of items (this is the format from our structure JSON)
    if isinstance(structure, list):
        for item in structure:
            # If item is a dictionary with a single key (folder name) and list value (children)
            if isinstance(item, dict) and len(item.keys()) == 1:
                folder_name = list(item.keys())[0]  # Get the folder name (dictionary key)
                children = item.get(folder_name, [])  # Get the children (list value)
                
                # Create the directory
                dir_path = os.path.join(output_path, folder_name)
                print(f"DEBUG: Creating custom directory: {dir_path}")
                
                if not dry_run:
                    os.makedirs(dir_path, exist_ok=True)
                
                created_paths.append(dir_path)
                
                # Process children recursively
                if children:
                    enhanced_process_template(project_builder, dir_path, children, placeholders, created_paths, dry_run)
            else:
                # Fall back to original processing
                project_builder._process_template(output_path, item, placeholders, created_paths, dry_run)
        return created_paths
    
    # For other formats, use the original method
    return project_builder._process_template(output_path, structure, placeholders, created_paths, dry_run)

def test_enhanced_process_template():
    """Test the enhanced _process_template method with our structure format"""
    print("\n=== Testing Enhanced Process Template Behavior ===")
    
    # Create a temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    output_dir = os.path.join(temp_dir, "output_enhanced")
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Initialize managers
        template_manager = TemplateManager()
        project_builder = ProjectBuilder(template_manager)
        
        # Load a real custom structure
        test_structure_path = "/Users/craigrusso/.echelon/structures/Template_oh_my_goe.json"
        
        with open(test_structure_path, 'r') as f:
            structure_data = json.load(f)
        
        print(f"Loaded structure: {structure_data['name']}")
        
        # Extract the directories array
        directories = structure_data.get('directories', [])
        
        print("\nProcessing structure with enhanced method...\n")
        created_paths = []
        enhanced_process_template(project_builder, output_dir, directories, {}, created_paths)
        
        print(f"\nCreated {len(created_paths)} paths with enhanced method")
        print("Created directory structure:")
        for path in created_paths:
            rel_path = os.path.relpath(path, output_dir)
            print(f"  {rel_path}")
        
    finally:
        # Clean up
        print(f"\nCleaning up temp directory: {temp_dir}")
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_process_template_original()
    test_enhanced_process_template() 