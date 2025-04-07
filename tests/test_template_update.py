#!/usr/bin/env python3
# Test script to verify template update and file caching

import os
import json
from app.templates.template_operations import TemplateOperations

def test_template_update():
    print("Testing template update with file caching...")
    
    # Create a test directory and file
    test_dir = "test_edit"
    test_file = os.path.join(test_dir, "test_file.txt")
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a test file with content
    with open(test_file, "w") as f:
        f.write("This is a test file for caching")
    
    # Initialize template operations
    ops = TemplateOperations()
    
    # Create a test template
    template_name = "TEST_EDIT"
    structure = {
        "name": "root",
        "type": "folder",
        "children": [
            {
                "name": "folder1",
                "type": "folder",
                "children": []
            }
        ]
    }
    
    print(f"Creating template '{template_name}'...")
    template_data = {
        "name": template_name,
        "structure": structure,
        "cache_files": True
    }
    success = ops.save_template(template_data)
    print(f"Template created successfully: {success}")
    
    # Get the template file path
    from app.utils.utils import get_config_paths
    paths = get_config_paths()
    template_file = os.path.join(paths["templates_dir"], f"{template_name}.json")
    print(f"Template saved to {template_file}")
    
    # Load the template
    with open(template_file, "r") as f:
        template = json.load(f)
    
    # Add a file to the structure
    print("Adding a file to the structure...")
    template_structure = template.get("structure", {})
    children = template_structure.get("children", [])
    children.append({
        "name": "test_file.txt",
        "type": "file",
        "original_path": os.path.abspath(test_file)
    })
    
    # Update the template
    print("Updating the template...")
    success = ops.update_template(template)
    print(f"Update successful: {success}")
    
    # Load the updated template
    with open(template_file, "r") as f:
        updated = json.load(f)
    
    # Check if files were properly cached
    files = updated.get("files", [])
    print(f"Updated template has {len(files)} files")
    print("Cached paths:")
    for f in files:
        print(f"  - {f.get('file_name')}: {f.get('cached_path', 'None')}")
    
    # Check if cache directory exists
    cache_dir = paths.get("templates_cache_dir")
    if cache_dir:
        template_cache_dir = os.path.join(cache_dir, template_name)
        print(f"Template cache directory: {template_cache_dir}")
        if os.path.exists(template_cache_dir):
            print("Cache directory exists!")
            print("Files in cache directory:")
            for root, dirs, files in os.walk(template_cache_dir):
                for file in files:
                    print(f"  - {os.path.join(root, file)}")
        else:
            print("Cache directory does not exist!")
    else:
        print("No cache directory specified in paths!")

if __name__ == "__main__":
    test_template_update() 