#!/usr/bin/env python3
"""
Test script to diagnose template editing path issues
"""
import os
import sys
import json
import shutil
from pathlib import Path

# Add the app directory to path so we can import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import necessary modules
from app.utils.utils import get_config_paths
from app.templates.template_manager import TemplateManager
from app.templates.template_operations import TemplateOperations
from app.templates.structure_operations import StructureOperations

def print_separator(label):
    """Print a separator line with a label"""
    print("\n" + "=" * 80)
    print(f"  {label}  ".center(80, "="))
    print("=" * 80 + "\n")

def check_file_content(file_path):
    """Check and print the content of a JSON file"""
    if not os.path.exists(file_path):
        print(f"🚫 File does not exist: {file_path}")
        return None
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            print(f"✅ File found: {file_path}")
            print(f"   Content:\n")
            print(json.dumps(data, indent=2))
            return data
    except Exception as e:
        print(f"❌ Error reading file {file_path}: {e}")
        return None

def list_templates_in_memory(template_manager):
    """List templates currently loaded in memory"""
    print_separator("TEMPLATES IN MEMORY")
    
    if hasattr(template_manager, 'templates') and template_manager.templates:
        for i, template in enumerate(template_manager.templates):
            print(f"{i+1}. Template: {template.get('name', 'Unknown')}")
            if 'structure_name' in template:
                print(f"   Structure name: {template.get('structure_name')}")
            print(f"   Type: {template.get('type', 'Unknown')}")
            print()
    else:
        print("No templates found in memory.")

def list_structures_in_memory(template_manager):
    """List structures currently loaded in memory"""
    print_separator("STRUCTURES IN MEMORY")
    
    if hasattr(template_manager, 'custom_structures') and template_manager.custom_structures:
        structures = list(template_manager.custom_structures.keys())
        print(f"Found {len(structures)} structures in memory:")
        for i, name in enumerate(structures):
            print(f"{i+1}. {name}")
            
            structure = template_manager.custom_structures[name]
            if isinstance(structure, dict):
                if 'name' in structure:
                    print(f"   Internal name: {structure.get('name')}")
                if 'display_name' in structure:
                    print(f"   Display name: {structure.get('display_name')}")
            print()
    else:
        print("No structures found in memory.")

def list_files_on_disk():
    """List template and structure files on disk"""
    print_separator("FILES ON DISK")
    
    paths = get_config_paths()
    templates_dir = paths["templates_dir"]
    structures_dir = paths["custom_structures_dir"]
    
    # Check templates directory
    print(f"Templates directory: {templates_dir}")
    if os.path.exists(templates_dir):
        template_files = [f for f in os.listdir(templates_dir) if f.endswith('.json')]
        print(f"Found {len(template_files)} template files:")
        for file in template_files:
            print(f"- {file}")
    else:
        print("Templates directory does not exist.")
    
    print()
    
    # Check structures directory
    print(f"Structures directory: {structures_dir}")
    if os.path.exists(structures_dir):
        structure_files = [f for f in os.listdir(structures_dir) if f.endswith('.json')]
        print(f"Found {len(structure_files)} structure files:")
        for file in structure_files:
            print(f"- {file}")
    else:
        print("Structures directory does not exist.")

def test_template_rename(template_manager, old_name, new_name):
    """Test the rename_template function"""
    print_separator(f"RENAMING TEMPLATE: {old_name} -> {new_name}")
    
    # Get paths to relevant files before rename
    paths = get_config_paths()
    structures_dir = paths["custom_structures_dir"]
    templates_dir = paths["templates_dir"]
    
    # Check for existing files
    old_template_path = os.path.join(templates_dir, f"{old_name.replace(' ', '_')}.json")
    old_structure_path = os.path.join(structures_dir, f"Template_{old_name.replace(' ', '_')}.json")
    
    print(f"Checking for template file: {old_template_path}")
    check_file_content(old_template_path)
    
    print(f"Checking for structure file: {old_structure_path}")
    check_file_content(old_structure_path)
    
    # Perform the rename
    print(f"\nExecuting template_manager.rename_template('{old_name}', '{new_name}')")
    success = template_manager.rename_template(old_name, new_name)
    print(f"Rename operation returned: {success}")
    
    # Check files after rename
    new_template_path = os.path.join(templates_dir, f"{new_name.replace(' ', '_')}.json")
    new_structure_path = os.path.join(structures_dir, f"Template_{new_name.replace(' ', '_')}.json")
    
    print(f"\nChecking for new template file: {new_template_path}")
    check_file_content(new_template_path)
    
    print(f"Checking for new structure file: {new_structure_path}")
    check_file_content(new_structure_path)
    
    # Verify old files are gone
    if os.path.exists(old_template_path):
        print(f"⚠️ Warning: Old template file still exists: {old_template_path}")
    else:
        print(f"✅ Old template file successfully removed.")
        
    if os.path.exists(old_structure_path):
        print(f"⚠️ Warning: Old structure file still exists: {old_structure_path}")
    else:
        print(f"✅ Old structure file successfully removed.")
    
    return success

def test_template_save(template_manager, name, with_structure=True):
    """Test saving a template directly"""
    print_separator(f"SAVING TEMPLATE: {name}")
    
    # Create a test template
    template = {
        "name": name,
        "description": f"Test template for {name}",
        "type": "Standard",
        "path": os.getcwd()  # Just use current directory
    }
    
    # Add structure name if needed
    if with_structure:
        structure_name = f"Template_{name}"
        template["structure_name"] = structure_name
        
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
        print(f"Saving structure '{structure_name}'")
        structure_success = template_manager.save_custom_structure(structure_name, structure)
        print(f"Structure save result: {structure_success}")
    
    # Save the template using TemplateOperations
    print(f"Saving template '{name}'")
    
    # Use template operations to save it
    to = TemplateOperations()
    template_data = {
        "name": name,
        "structure": os.getcwd(),
        "type": "Standard",
        "description": template["description"]
    }
    template_success = to.save_template(template_data)
    print(f"Template save result: {template_success}")
    
    # Verify files were created
    paths = get_config_paths()
    templates_dir = paths["templates_dir"]
    structures_dir = paths["custom_structures_dir"]
    
    template_path = os.path.join(templates_dir, f"{name.replace(' ', '_')}.json")
    structure_path = os.path.join(structures_dir, f"Template_{name.replace(' ', '_')}.json")
    
    print(f"\nChecking template file: {template_path}")
    template_data = check_file_content(template_path)
    
    if with_structure:
        print(f"\nChecking structure file: {structure_path}")
        structure_data = check_file_content(structure_path)
    
    return template_success

def test_save_and_rename():
    """Test saving and then renaming a template"""
    print_separator("SAVE AND RENAME TEST")
    
    # Create a template manager
    tm = TemplateManager()
    
    # First create a test template
    test_name = "EDIT_TEST_1"
    save_success = test_template_save(tm, test_name)
    
    if save_success:
        # Now try to rename it
        new_name = "EDIT_TEST_RENAMED"
        rename_success = test_template_rename(tm, test_name, new_name)
        
        if rename_success:
            print("\n✅ Save and rename test completed successfully!")
        else:
            print("\n❌ Rename operation failed.")
    else:
        print("\n❌ Initial save operation failed, skipping rename test.")

def main():
    """Main test function"""
    print_separator("TEMPLATE EDITING DIAGNOSTIC TEST")
    
    # Get configuration paths
    paths = get_config_paths()
    print(f"Templates directory: {paths['templates_dir']}")
    print(f"Structures directory: {paths['custom_structures_dir']}")
    
    # Initialize template manager
    tm = TemplateManager()
    
    # List templates and structures currently in the system
    list_templates_in_memory(tm)
    list_structures_in_memory(tm)
    list_files_on_disk()
    
    # Run tests
    test_save_and_rename()
    
    print_separator("TEST COMPLETED")

if __name__ == "__main__":
    main() 