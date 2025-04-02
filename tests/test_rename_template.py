#!/usr/bin/env python3
"""
Test script to verify template renaming functionality
"""
import os
import sys
import json
import time
import random
import shutil
from pathlib import Path

# Add the app directory to path so we can import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import necessary modules
from app.utils.utils import get_config_paths
from app.templates.template_manager import TemplateManager

def create_test_template(name):
    """Create a test template for renaming"""
    tm = TemplateManager()
    
    # Create a simple structure
    structure = [
        "Assets",
        "Documents",
        {"Source Files": [
            "Graphics",
            "Audio"
        ]}
    ]
    
    # Save the structure first
    structure_name = f"Template_{name}"
    print(f"Creating structure '{structure_name}'")
    structure_success = tm.save_custom_structure(structure_name, structure)
    print(f"Structure save result: {structure_success}")
    
    # Create template data
    template_data = {
        "name": name,
        "description": f"Test template for rename testing",
        "type": "Standard",
        "path": os.getcwd(),
        "structure_name": structure_name
    }
    
    # Save template
    tm.templates.append(template_data)
    
    # Save to disk
    paths = get_config_paths()
    templates_dir = paths["templates_dir"]
    template_path = os.path.join(templates_dir, f"{name.replace(' ', '_')}.json")
    
    try:
        with open(template_path, 'w') as f:
            json.dump(template_data, f, indent=2)
        
        print(f"Template saved to {template_path}")
        return True
    except Exception as e:
        print(f"Error saving template: {e}")
        return False

def check_template_exists(name):
    """Check if a template with the given name exists"""
    paths = get_config_paths()
    templates_dir = paths["templates_dir"]
    structures_dir = paths["custom_structures_dir"]
    
    template_path = os.path.join(templates_dir, f"{name.replace(' ', '_')}.json")
    structure_path = os.path.join(structures_dir, f"Template_{name.replace(' ', '_')}.json")
    
    template_exists = os.path.exists(template_path)
    structure_exists = os.path.exists(structure_path)
    
    print(f"Template file exists: {template_exists} ({template_path})")
    print(f"Structure file exists: {structure_exists} ({structure_path})")
    
    return template_exists and structure_exists

def check_template_content(name):
    """Check template content for correct name values"""
    paths = get_config_paths()
    templates_dir = paths["templates_dir"]
    structures_dir = paths["custom_structures_dir"]
    
    template_path = os.path.join(templates_dir, f"{name.replace(' ', '_')}.json")
    structure_path = os.path.join(structures_dir, f"Template_{name.replace(' ', '_')}.json")
    
    template_data = None
    structure_data = None
    
    try:
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                template_data = json.load(f)
            print(f"Template data loaded from {template_path}")
        
        if os.path.exists(structure_path):
            with open(structure_path, 'r') as f:
                structure_data = json.load(f)
            print(f"Structure data loaded from {structure_path}")
            
        # Check template content
        if template_data:
            template_name_matches = template_data.get('name') == name
            structure_name_matches = template_data.get('structure_name') == f"Template_{name}"
            
            print(f"Template name matches: {template_name_matches}")
            print(f"Structure name reference matches: {structure_name_matches}")
            
            if not template_name_matches or not structure_name_matches:
                print(f"Template data content: {json.dumps(template_data, indent=2)}")
                
        # Check structure content
        if structure_data:
            structure_name_matches = structure_data.get('name') == f"Template_{name}"
            display_name_matches = structure_data.get('display_name') == name
            
            print(f"Structure name matches: {structure_name_matches}")
            print(f"Display name matches: {display_name_matches}")
            
            if not structure_name_matches or not display_name_matches:
                print(f"Structure data content: {json.dumps(structure_data, indent=2)}")
            
            return (template_data and template_name_matches and structure_name_matches and 
                    structure_data and structure_name_matches and display_name_matches)
    except Exception as e:
        print(f"Error checking template content: {e}")
    
    return False

def test_rename_template():
    """Test renaming a template"""
    # Create a unique name for testing
    original_name = "TEST 01"
    # Use a more descriptive format for the new name to avoid confusion with real templates
    new_name = f"TEST_{original_name}_RENAMED_{int(time.time())}"
    
    print(f"\n=== Starting template rename test ===")
    print(f"Original name: {original_name}")
    print(f"New name: {new_name}")
    
    # Create a test template if it doesn't exist
    if not check_template_exists(original_name):
        print(f"Creating test template '{original_name}'")
        create_test_template(original_name)
        
        # Verify test template was created
        if not check_template_exists(original_name):
            print(f"Failed to create test template")
            return False
    
    # Make sure original template has correct content
    print(f"\nChecking original template content:")
    check_template_content(original_name)
    
    # Create a new template manager
    tm = TemplateManager()
    
    # Rename the template
    print(f"\nRenaming template '{original_name}' to '{new_name}'")
    rename_success = tm.rename_template(original_name, new_name)
    print(f"Rename operation result: {rename_success}")
    
    # Check if new template exists
    print(f"\nChecking if new template exists:")
    new_template_exists = check_template_exists(new_name)
    
    # Check if old template is gone
    print(f"\nChecking if old template is gone:")
    paths = get_config_paths()
    templates_dir = paths["templates_dir"]
    structures_dir = paths["custom_structures_dir"]
    
    old_template_path = os.path.join(templates_dir, f"{original_name.replace(' ', '_')}.json")
    old_structure_path = os.path.join(structures_dir, f"Template_{original_name.replace(' ', '_')}.json")
    
    old_template_gone = not os.path.exists(old_template_path)
    old_structure_gone = not os.path.exists(old_structure_path)
    
    print(f"Old template file is gone: {old_template_gone} ({old_template_path})")
    print(f"Old structure file is gone: {old_structure_gone} ({old_structure_path})")
    
    # Check new template content
    print(f"\nChecking new template content:")
    content_correct = check_template_content(new_name)
    
    # Overall test result
    test_passed = rename_success and new_template_exists and old_template_gone and old_structure_gone and content_correct
    
    print(f"\n=== Template rename test {'PASSED' if test_passed else 'FAILED'} ===")
    return test_passed

if __name__ == "__main__":
    test_rename_template() 