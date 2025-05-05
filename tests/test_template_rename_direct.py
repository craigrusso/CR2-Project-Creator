#!/usr/bin/env python3
"""
Direct template rename test - tests the rename_template function without using the UI
"""
import os
import sys
import json
import time
import shutil
from pathlib import Path

# Add the app directory to path so we can import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import template manager
from app.templates.template_manager import TemplateManager

def list_existing_templates(template_manager):
    """List existing templates in the template manager"""
    print("\n=== EXISTING TEMPLATES ===")
    if hasattr(template_manager, 'templates') and template_manager.templates:
        for template in template_manager.templates:
            print(f"Template: {template.get('name', 'Unknown')}")
    else:
        print("No templates found")
    print("=========================\n")

def list_structure_files(template_manager):
    """List existing structure files on disk"""
    print("\n=== STRUCTURE FILES ON DISK ===")
    if os.path.exists(template_manager.paths["custom_structures_dir"]):
        files = os.listdir(template_manager.paths["custom_structures_dir"])
        for file in files:
            if file.endswith('.json'):
                print(f"File: {file}")
                # Print the content of the file
                file_path = os.path.join(template_manager.paths["custom_structures_dir"], file)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        print(f"  - name: {data.get('name', 'Unknown')}")
                        print(f"  - display_name: {data.get('display_name', 'Unknown')}")
                        print(f"  - directories: {len(data.get('directories', []))} items")
                except Exception as e:
                    print(f"  - Error reading file: {e}")
    else:
        print("Structures directory not found")
    print("=========================\n")

def test_rename_direct():
    """Test renaming a template directly without the UI"""
    print("\n🧪 DIRECT TEMPLATE RENAME TEST 🧪")
    print("=" * 60)
    
    # Create template manager
    template_manager = TemplateManager()
    print(f"📂 Using templates directory: {template_manager.paths['custom_structures_dir']}")
    
    # List existing templates
    list_existing_templates(template_manager)
    
    # List existing structure files
    list_structure_files(template_manager)
    
    # Get the first template to test with
    if hasattr(template_manager, 'templates') and template_manager.templates:
        template = template_manager.templates[0]
        original_name = template.get('name', 'Unknown')
        
        # Generate a test name with timestamp
        test_name = f"TEST_RENAME_{int(time.time())}"
        
        print(f"🔄 Renaming template '{original_name}' to '{test_name}'")
        
        # Perform the rename
        success = template_manager.rename_template(original_name, test_name)
        
        print(f"✅ Rename operation returned: {success}")
        
        # Check the results
        print("\n=== AFTER RENAME ===")
        list_existing_templates(template_manager)
        list_structure_files(template_manager)
        
        # Now rename back to original
        print(f"🔄 Renaming template back from '{test_name}' to '{original_name}'")
        success = template_manager.rename_template(test_name, original_name)
        
        print(f"✅ Rename back operation returned: {success}")
        
        # Check the final results
        print("\n=== AFTER RENAME BACK ===")
        list_existing_templates(template_manager)
        list_structure_files(template_manager)
        
        print("\n=" * 30)
        if success:
            print("✅ TEST COMPLETED SUCCESSFULLY")
        else:
            print("❌ TEST FAILED")
        print("=" * 60)
        
        return success
    else:
        print("❌ No templates found to test with")
        return False

if __name__ == "__main__":
    test_rename_direct() 