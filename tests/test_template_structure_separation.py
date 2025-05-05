#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Template-Structure Separation Test Script

This script tests that template renaming doesn't affect structure files
and that structure files are properly preserved even when templates are renamed.
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

def check_file_exists(file_path, expected=True):
    """Check if a file exists and print the result"""
    exists = os.path.exists(file_path)
    status = "✅" if exists == expected else "❌"
    print(f"{status} File exists at {file_path}: {exists}")
    return exists

def create_test_template():
    """Create a test template with a structure for testing"""
    print_separator("Creating Test Template")
    
    # Generate a unique test name
    timestamp = int(time.time())
    template_name = f"TEST_TEMPLATE_{timestamp}"
    structure_name = f"Template_{template_name}"
    
    # Initialize the template manager
    template_manager = TemplateManager()
    
    # Define template and structure
    print(f"Creating template '{template_name}' with structure '{structure_name}'")
    
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
    
    # Define a simple template
    template_data = {
        "name": template_name,
        "description": "Test template for verifying separation",
        "tags": ["test", "separation"],
        "created": time.time(),
        "modified": time.time(),
        "structure_name": structure_name,
        "structure": structure
    }
    
    # Save the structure
    print(f"Saving structure '{structure_name}'...")
    success = template_manager.save_custom_structure(structure_name, structure)
    print(f"Structure save result: {success}")
    
    # Define file paths
    template_file = os.path.join(template_manager.paths["templates_dir"], 
                                f"{template_name.replace(' ', '_')}.json")
    structure_file = os.path.join(template_manager.paths["custom_structures_dir"], 
                                f"{structure_name.replace(' ', '_')}.json")
    
    # Save the template
    print(f"Saving template to {template_file}...")
    try:
        os.makedirs(os.path.dirname(template_file), exist_ok=True)
        with open(template_file, 'w') as f:
            json.dump(template_data, f, indent=2)
        print("Template saved successfully.")
        
        # Verify files exist
        template_exists = check_file_exists(template_file)
        structure_exists = check_file_exists(structure_file)
        
        if template_exists and structure_exists:
            print("✅ Template and structure created successfully!")
            return {
                "template_name": template_name,
                "structure_name": structure_name,
                "template_file": template_file,
                "structure_file": structure_file
            }
        else:
            print("❌ Failed to create template or structure!")
            return None
    except Exception as e:
        print(f"❌ Error saving template: {e}")
        return None

def test_template_rename():
    """Test renaming a template without affecting structure file"""
    print_separator("Testing Template Rename With Structure Preservation")
    
    # Create test template
    test_data = create_test_template()
    if not test_data:
        print("❌ Failed to create test template, cannot proceed with test.")
        return False
    
    template_name = test_data["template_name"]
    structure_name = test_data["structure_name"]
    template_file = test_data["template_file"]
    structure_file = test_data["structure_file"]
    
    # Initialize template manager
    template_manager = TemplateManager()
    
    # Define new template name but keep structure name
    new_template_name = f"{template_name}_RENAMED"
    new_template_file = os.path.join(template_manager.paths["templates_dir"], 
                                    f"{new_template_name.replace(' ', '_')}.json")
    
    print(f"\nRenaming template '{template_name}' to '{new_template_name}'...")
    print(f"Structure name should remain as '{structure_name}'")
    
    # Call rename_template
    result = template_manager.rename_template(template_name, new_template_name)
    print(f"Rename result: {result}")
    
    # Check files after rename
    print("\nChecking files after rename:")
    print("\nOld template file should be gone:")
    check_file_exists(template_file, expected=False)
    
    print("\nNew template file should exist:")
    new_template_exists = check_file_exists(new_template_file)
    
    print("\nStructure file should still exist with original name:")
    structure_exists = check_file_exists(structure_file)
    
    # Verify structure reference in new template
    structure_ref_correct = False
    if new_template_exists:
        try:
            with open(new_template_file, 'r') as f:
                new_template_data = json.load(f)
            
            stored_structure_name = new_template_data.get("structure_name", "")
            print(f"\nTemplate structure reference: '{stored_structure_name}'")
            structure_ref_correct = stored_structure_name == structure_name
            print(f"{'✅' if structure_ref_correct else '❌'} Structure reference is {'correct' if structure_ref_correct else 'incorrect'}")
        except Exception as e:
            print(f"❌ Error reading new template file: {e}")
    
    # Cleanup test files
    print("\nCleaning up test files...")
    for file_path in [template_file, new_template_file, structure_file]:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Removed {file_path}")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")
    
    # Determine test success
    success = (not os.path.exists(template_file) and 
              new_template_exists and 
              structure_exists and 
              structure_ref_correct)
    
    print(f"\n{'✅' if success else '❌'} Test {'PASSED' if success else 'FAILED'}")
    return success

def test_multiple_templates_same_structure():
    """Test creating multiple templates that reference the same structure"""
    print_separator("Testing Multiple Templates Using Same Structure")
    
    # Create initial test template with structure
    test_data = create_test_template()
    if not test_data:
        print("❌ Failed to create first test template, cannot proceed with test.")
        return False
    
    template_name = test_data["template_name"]
    structure_name = test_data["structure_name"]
    template_file = test_data["template_file"]
    structure_file = test_data["structure_file"]
    
    # Initialize template manager
    template_manager = TemplateManager()
    
    # Create a second template that uses the same structure
    second_template_name = f"{template_name}_SECOND"
    second_template_file = os.path.join(template_manager.paths["templates_dir"], 
                                       f"{second_template_name.replace(' ', '_')}.json")
    
    print(f"\nCreating second template '{second_template_name}' using same structure '{structure_name}'...")
    
    # Load the structure
    structure = None
    try:
        with open(structure_file, 'r') as f:
            structure_data = json.load(f)
            if isinstance(structure_data, dict) and 'directories' in structure_data:
                structure = structure_data['directories']
            else:
                structure = structure_data
    except Exception as e:
        print(f"❌ Error loading structure: {e}")
        return False
    
    # Create second template data
    second_template_data = {
        "name": second_template_name,
        "description": "Second test template using same structure",
        "tags": ["test", "shared"],
        "created": time.time(),
        "modified": time.time(),
        "structure_name": structure_name,  # Reference same structure
        "structure": structure
    }
    
    # Save second template
    try:
        with open(second_template_file, 'w') as f:
            json.dump(second_template_data, f, indent=2)
        print("✅ Second template saved successfully.")
    except Exception as e:
        print(f"❌ Error saving second template: {e}")
        return False
    
    # Verify files exist
    print("\nVerifying template files:")
    first_template_exists = check_file_exists(template_file)
    second_template_exists = check_file_exists(second_template_file)
    structure_exists = check_file_exists(structure_file)
    
    # Now delete the first template and verify the structure is preserved
    print(f"\nDeleting first template '{template_name}'...")
    try:
        os.remove(template_file)
        print("✅ First template deleted successfully.")
    except Exception as e:
        print(f"❌ Error deleting first template: {e}")
    
    # Check if structure still exists
    print("\nVerifying structure is preserved after deleting first template:")
    structure_preserved = check_file_exists(structure_file)
    
    # Cleanup test files
    print("\nCleaning up remaining test files...")
    for file_path in [second_template_file, structure_file]:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Removed {file_path}")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")
    
    # Determine test success
    success = second_template_exists and structure_exists and structure_preserved
    
    print(f"\n{'✅' if success else '❌'} Test {'PASSED' if success else 'FAILED'}")
    return success

def main():
    """Main function to run all tests"""
    print_separator("TEMPLATE-STRUCTURE SEPARATION TEST SCRIPT")
    
    # Run tests
    test1 = test_template_rename()
    test2 = test_multiple_templates_same_structure()
    
    # Summarize results
    print_separator("TEST RESULTS")
    print(f"Template Rename Test: {'✅ PASSED' if test1 else '❌ FAILED'}")
    print(f"Multiple Templates Same Structure Test: {'✅ PASSED' if test2 else '❌ FAILED'}")
    
    # Overall status
    overall = test1 and test2
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall else '❌ SOME TESTS FAILED'}")

if __name__ == "__main__":
    main() 