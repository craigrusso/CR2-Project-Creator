#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Template Manager Test Script

This script tests the functionality of the template manager's handling of
templates and structures to diagnose issues with template editing and renaming.
"""

import os
import sys
import json
import time
import shutil
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import app modules
from app.templates.template_manager import TemplateManager

def print_separator(title):
    """Print a separator with a title"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def check_file_exists(file_path):
    """Check if a file exists and print the result"""
    exists = os.path.exists(file_path)
    print(f"File exists at {file_path}: {exists}")
    return exists

def print_file_content(file_path, max_lines=20):
    """Print the content of a file"""
    if not os.path.exists(file_path):
        print(f"File does not exist: {file_path}")
        return
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        if len(lines) > max_lines:
            print(f"File content (first {max_lines} lines):")
            for i, line in enumerate(lines[:max_lines]):
                print(f"{i+1}: {line}")
            print(f"... (and {len(lines) - max_lines} more lines)")
        else:
            print("File content:")
            for i, line in enumerate(lines):
                print(f"{i+1}: {line}")
            
    except Exception as e:
        print(f"Error reading file: {e}")

def create_test_template():
    """Create a test template for testing"""
    print_separator("Creating Test Template")
    
    # Initialize the template manager
    template_manager = TemplateManager()
    
    # Define a simple test template
    template_name = f"TEST_TEMPLATE_{int(time.time())}"
    template_data = {
        "name": template_name,
        "description": "Test template for testing rename operations",
        "tags": ["test", "sample"],
        "created": time.time(),
        "modified": time.time()
    }
    
    # Define a simple structure
    structure = [
        {"src": [
            "main.py",
            "utils.py",
            {"helpers": [
                "formatter.py",
                "validator.py"
            ]}
        ]},
        {"docs": [
            "README.md",
            "USAGE.md"
        ]},
        "requirements.txt",
        "setup.py"
    ]
    
    # Define the structure name
    structure_name = f"Template_{template_name}"
    
    # Save the structure
    print(f"Saving structure '{structure_name}'...")
    result = template_manager.save_custom_structure(structure_name, structure)
    print(f"Structure save result: {result}")
    
    # Update the template with the structure reference
    template_data["structure_name"] = structure_name
    template_data["structure"] = structure
    
    # Get the template file path
    template_file = os.path.join(template_manager.paths["templates_dir"], f"{template_name.replace(' ', '_')}.json")
    
    # Save the template
    print(f"Saving template to {template_file}...")
    try:
        os.makedirs(os.path.dirname(template_file), exist_ok=True)
        with open(template_file, 'w') as f:
            json.dump(template_data, f, indent=2)
        print("Template saved successfully.")
        
        # Verify the files exist
        template_path = template_file
        structure_path = os.path.join(template_manager.paths["custom_structures_dir"], f"{structure_name.replace(' ', '_')}.json")
        
        print("\nVerifying saved files:")
        check_file_exists(template_path)
        check_file_exists(structure_path)
        
        return template_name, structure_name
    except Exception as e:
        print(f"Error saving template: {e}")
        return None, None

def test_rename_template():
    """Test renaming a template"""
    print_separator("Testing Template Rename")
    
    # Create a test template
    template_name, structure_name = create_test_template()
    if not template_name:
        print("Failed to create test template.")
        return False
    
    # Initialize the template manager
    template_manager = TemplateManager()
    
    # Get file paths before rename
    old_template_path = os.path.join(template_manager.paths["templates_dir"], f"{template_name.replace(' ', '_')}.json")
    old_structure_path = os.path.join(template_manager.paths["custom_structures_dir"], f"{structure_name.replace(' ', '_')}.json")
    
    # Define new name
    new_template_name = f"{template_name}_RENAMED"
    new_structure_name = f"Template_{new_template_name}"
    
    print(f"\nBefore rename - checking original files:")
    template_exists = check_file_exists(old_template_path)
    structure_exists = check_file_exists(old_structure_path)
    
    if not template_exists or not structure_exists:
        print("Original files not found, cannot proceed with rename test.")
        return False
    
    # Perform the rename
    print(f"\nRenaming template from '{template_name}' to '{new_template_name}'...")
    result = template_manager.rename_template(template_name, new_template_name)
    print(f"Rename result: {result}")
    
    # Get file paths after rename
    new_template_path = os.path.join(template_manager.paths["templates_dir"], f"{new_template_name.replace(' ', '_')}.json")
    new_structure_path = os.path.join(template_manager.paths["custom_structures_dir"], f"{new_structure_name.replace(' ', '_')}.json")
    
    print(f"\nAfter rename - checking results:")
    
    # Check if old files are gone
    print("\nChecking if old files were removed:")
    old_template_gone = not check_file_exists(old_template_path)
    old_structure_gone = not check_file_exists(old_structure_path)
    
    # Check if new files exist
    print("\nChecking if new files were created:")
    new_template_exists = check_file_exists(new_template_path)
    new_structure_exists = check_file_exists(new_structure_path)
    
    if new_template_exists:
        print("\nNew template file content:")
        print_file_content(new_template_path)
    
    if new_structure_exists:
        print("\nNew structure file content:")
        print_file_content(new_structure_path)
    
    # Summary
    print("\nRename operation summary:")
    print(f"- Old template file removed: {old_template_gone}")
    print(f"- Old structure file removed: {old_structure_gone}")
    print(f"- New template file created: {new_template_exists}")
    print(f"- New structure file created: {new_structure_exists}")
    
    # Clean up test files
    print("\nCleaning up test files...")
    for path in [old_template_path, old_structure_path, new_template_path, new_structure_path]:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"Removed: {path}")
            except Exception as e:
                print(f"Error removing {path}: {e}")
    
    # Success if all conditions met
    success = old_template_gone and old_structure_gone and new_template_exists and new_structure_exists
    print(f"\nTest {'passed' if success else 'failed'}")
    return success

def test_edit_template():
    """Test editing a template without renaming"""
    print_separator("Testing Template Edit (without rename)")
    
    # Create a test template
    template_name, structure_name = create_test_template()
    if not template_name:
        print("Failed to create test template.")
        return False
    
    # Initialize the template manager
    template_manager = TemplateManager()
    
    # Get file paths
    template_path = os.path.join(template_manager.paths["templates_dir"], f"{template_name.replace(' ', '_')}.json")
    structure_path = os.path.join(template_manager.paths["custom_structures_dir"], f"{structure_name.replace(' ', '_')}.json")
    
    print(f"\nBefore edit - checking files:")
    template_exists = check_file_exists(template_path)
    structure_exists = check_file_exists(structure_path)
    
    if not template_exists or not structure_exists:
        print("Files not found, cannot proceed with edit test.")
        return False
    
    # Load the template and structure
    template = None
    try:
        with open(template_path, 'r') as f:
            template = json.load(f)
        print("Template loaded successfully.")
    except Exception as e:
        print(f"Error loading template: {e}")
        return False
    
    # Modify the structure
    modified_structure = template.get('structure', [])
    # Add a new file to the structure
    modified_structure.append("ADDED_FILE.txt")
    
    # Save the modified structure
    print(f"\nSaving modified structure...")
    result = template_manager.save_custom_structure(structure_name, modified_structure)
    print(f"Structure save result: {result}")
    
    # Update template with modified structure
    template['structure'] = modified_structure
    template['modified'] = time.time()
    
    # Save the template
    print(f"\nSaving modified template...")
    try:
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)
        print("Template saved successfully.")
    except Exception as e:
        print(f"Error saving template: {e}")
        return False
    
    # Verify the files exist and have been modified
    print("\nVerifying files after edit:")
    template_exists = check_file_exists(template_path)
    structure_exists = check_file_exists(structure_path)
    
    if template_exists:
        print("\nModified template file content:")
        print_file_content(template_path)
    
    if structure_exists:
        print("\nModified structure file content:")
        print_file_content(structure_path)
    
    # Clean up test files
    print("\nCleaning up test files...")
    for path in [template_path, structure_path]:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"Removed: {path}")
            except Exception as e:
                print(f"Error removing {path}: {e}")
    
    # Success if all conditions met
    success = template_exists and structure_exists
    print(f"\nTest {'passed' if success else 'failed'}")
    return success

def examine_template_structure_relationship():
    """Examine how templates and structures are related"""
    print_separator("Examining Template-Structure Relationship")
    
    # Initialize the template manager
    template_manager = TemplateManager()
    
    # Print template manager paths
    print("Template Manager Paths:")
    for key, path in template_manager.paths.items():
        print(f"- {key}: {path}")
    
    # List templates
    print("\nTemplates:")
    for i, template in enumerate(template_manager.templates):
        if isinstance(template, dict):
            name = template.get('name', f'Unnamed_{i}')
            structure_name = template.get('structure_name', 'None')
            print(f"- {name} (structure: {structure_name})")
    
    # List structures
    print("\nStructures:")
    if hasattr(template_manager, 'custom_structures'):
        for name, structure in template_manager.custom_structures.items():
            if isinstance(structure, dict):
                display_name = structure.get('display_name', name)
                structure_items = len(structure.get('directories', [])) if isinstance(structure.get('directories'), list) else 0
                print(f"- {name} (display: {display_name}, items: {structure_items})")
    
    return True

def main():
    """Main function to run all tests"""
    print_separator("TEMPLATE MANAGER TEST SCRIPT")
    
    # Run relationship analysis
    examine_template_structure_relationship()
    
    # Run tests
    test_edit_template()
    test_rename_template()
    
    print("\nAll tests completed.")

if __name__ == "__main__":
    main() 