#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Template JSON Fix Script

This script diagnoses and fixes issues with template and structure JSON files
to ensure consistent naming.
"""

import os
import sys
import json
import time
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

def check_json_file(file_path):
    """Read and display a JSON file's contents"""
    if not os.path.exists(file_path):
        print(f"❌ File does not exist: {file_path}")
        return None
        
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        print(f"✅ File content for {file_path}:")
        for key, value in data.items():
            print(f"  {key}: {value}")
        return data
    except Exception as e:
        print(f"❌ Error reading file {file_path}: {e}")
        return None

def analyze_template_structure_consistency():
    """Analyze the consistency between template and structure files"""
    print_separator("Analyzing Template-Structure Consistency")
    
    # Initialize the template manager
    template_manager = TemplateManager()
    
    # Get paths
    templates_dir = template_manager.paths["templates_dir"]
    structures_dir = template_manager.paths["custom_structures_dir"]
    
    print(f"Templates directory: {templates_dir}")
    print(f"Structures directory: {structures_dir}")
    
    # Get all template files (excluding special files)
    template_files = []
    structure_files = []
    
    special_files = ["folders.json", "preferences.json"]
    
    for filename in os.listdir(templates_dir):
        if filename.endswith(".json") and filename not in special_files:
            template_files.append(filename)
    
    for filename in os.listdir(structures_dir):
        if filename.endswith(".json"):
            structure_files.append(filename)
    
    print(f"\nFound {len(template_files)} template files:")
    for filename in template_files:
        print(f"  - {filename}")
    
    print(f"\nFound {len(structure_files)} structure files:")
    for filename in structure_files:
        print(f"  - {filename}")
    
    # Analyze each template file
    issues_found = []
    
    print_separator("Detailed Analysis")
    
    for template_filename in template_files:
        template_path = os.path.join(templates_dir, template_filename)
        template_data = check_json_file(template_path)
        
        if not template_data:
            continue
        
        template_name = template_data.get("name", "")
        structure_name = template_data.get("structure_name", "")
        
        print(f"\nTemplate: {template_name}")
        print(f"References structure: {structure_name}")
        
        # Check if the structure file exists
        if structure_name:
            normalized_name = structure_name.replace(" ", "_")
            structure_filename = f"{normalized_name}.json"
            structure_path = os.path.join(structures_dir, structure_filename)
            
            if os.path.exists(structure_path):
                print(f"✅ Referenced structure file exists: {structure_filename}")
                
                # Check if the structure name matches what's in the file
                structure_data = check_json_file(structure_path)
                if structure_data:
                    stored_name = structure_data.get("name", "")
                    display_name = structure_data.get("display_name", "")
                    
                    if stored_name != structure_name:
                        print(f"❌ Structure name mismatch: '{stored_name}' vs '{structure_name}'")
                        issues_found.append({
                            "type": "structure_name_mismatch",
                            "template_file": template_path,
                            "structure_file": structure_path,
                            "template_data": template_data,
                            "structure_data": structure_data
                        })
            else:
                print(f"❌ Referenced structure file does not exist: {structure_filename}")
                
                # Try to find by alternate naming
                alt_name = structure_name.replace("Template_", "")
                alt_normalized = alt_name.replace(" ", "_")
                alt_filename = f"Template_{alt_normalized}.json"
                alt_path = os.path.join(structures_dir, alt_filename)
                
                if os.path.exists(alt_path):
                    print(f"✅ Found structure with alternate name: {alt_filename}")
                    issues_found.append({
                        "type": "structure_name_alternate",
                        "template_file": template_path,
                        "structure_file": alt_path,
                        "template_data": template_data,
                        "alt_structure_name": f"Template_{alt_normalized}"
                    })
                else:
                    print(f"❌ Could not find structure with any naming convention")
                    issues_found.append({
                        "type": "structure_missing",
                        "template_file": template_path,
                        "template_data": template_data
                    })
    
    return issues_found

def fix_template_structure_issues(issues):
    """Fix issues between templates and structures"""
    print_separator("Fixing Template-Structure Issues")
    
    if not issues:
        print("No issues to fix.")
        return
    
    print(f"Found {len(issues)} issues to fix.")
    
    for i, issue in enumerate(issues):
        print(f"\nIssue #{i+1}: {issue['type']}")
        
        if issue['type'] == 'structure_name_mismatch':
            print(f"Fixing structure name mismatch...")
            
            template_file = issue['template_file']
            structure_file = issue['structure_file']
            template_data = issue['template_data']
            structure_data = issue['structure_data']
            
            # Update the structure data to match what the template expects
            structure_name = template_data.get('structure_name', '')
            if structure_name:
                # Update the structure file
                structure_data['name'] = structure_name
                
                # If the structure name includes Template_ prefix, get display name
                display_name = structure_name
                if structure_name.startswith('Template_'):
                    display_name = structure_name[9:]  # Remove "Template_" prefix
                structure_data['display_name'] = display_name
                
                # Save updated structure
                try:
                    with open(structure_file, 'w') as f:
                        json.dump(structure_data, f, indent=2)
                    print(f"✅ Updated structure file: {structure_file}")
                except Exception as e:
                    print(f"❌ Error updating structure file: {e}")
            
        elif issue['type'] == 'structure_name_alternate':
            print(f"Fixing structure reference with alternate name...")
            
            template_file = issue['template_file']
            template_data = issue['template_data']
            alt_structure_name = issue['alt_structure_name']
            
            # Update the template to reference the correct structure name
            template_data['structure_name'] = alt_structure_name
            
            # Save updated template
            try:
                with open(template_file, 'w') as f:
                    json.dump(template_data, f, indent=2)
                print(f"✅ Updated template file: {template_file}")
            except Exception as e:
                print(f"❌ Error updating template file: {e}")
                
        elif issue['type'] == 'structure_missing':
            print(f"Cannot fix missing structure - would need to create structure.")
            # This would require creating a new structure file
            # We don't have the structure data to create it
    
    print("\n✅ Finished fixing issues.")

def main():
    """Main function to analyze and fix template JSON files"""
    print_separator("TEMPLATE JSON FIX SCRIPT")
    
    # Analyze templates
    issues = analyze_template_structure_consistency()
    
    # Fix issues if any found
    if issues:
        print_separator("ISSUES SUMMARY")
        print(f"Found {len(issues)} issues that need fixing.")
        
        confirm = input("\nDo you want to fix these issues? (y/n): ")
        if confirm.lower() == 'y':
            fix_template_structure_issues(issues)
        else:
            print("No changes made.")
    else:
        print("\n✅ No issues found! Templates and structures are consistent.")

if __name__ == "__main__":
    main() 