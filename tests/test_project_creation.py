#!/usr/bin/env python3
# Test script for project creation with cached files

import os
import tempfile
import shutil
import sys

# Set up paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our classes
from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder

def main():
    """Test project creation with the template manager and project builder"""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Temporary directory: {temp_dir}")
    print(f"Output directory: {output_dir}")
    
    try:
        # Create instances of our classes
        template_manager = TemplateManager()
        project_builder = ProjectBuilder(template_manager)
        
        # Create a test file to be cached
        test_file_path = os.path.join(temp_dir, "test_file.txt")
        with open(test_file_path, 'w') as f:
            f.write("This is a test file with {{PROJECT_NAME}} placeholder")
        
        # Force-update the structure to include our test file
        print("\n=== Modifying structure to include test file ===")
        # Get an existing structure
        test_structure_name = "Template_THIS IS TEST"
        structure_data = template_manager.get_structure(test_structure_name)
        
        if not structure_data:
            print(f"Error: Could not find structure: {test_structure_name}")
            return
            
        # If structure data is a list, modify the first element
        if isinstance(structure_data, list) and len(structure_data) > 0:
            # If it's a directory, add a file to its children
            if isinstance(structure_data[0], dict):
                if 'children' not in structure_data[0]:
                    structure_data[0]['children'] = []
                    
                # Add our test file to the children
                structure_data[0]['children'].append({
                    'type': 'file',
                    'name': 'test_file.txt',
                    'path': test_file_path,
                    'is_binary': False
                })
                
                print(f"Added test file to structure: {test_file_path}")
            
        # Try to cache the updated structure
        print("\n=== Caching test file ===")
        if hasattr(template_manager, '_cache_template_files'):
            print(f"Caching template files for: {test_structure_name}")
            template_name = "THIS IS TEST"  # Without the Template_ prefix
            template_manager._cache_template_files(template_name, temp_dir, structure_data, True)
        
        # Create project with the modified structure
        project_name = "TEST_PROJECT"
        project_path = os.path.join(output_dir, project_name)
        
        print(f"\n=== Creating project: {project_name} ===")
        print(f"Using structure: {test_structure_name}")
        
        success, message = project_builder.create_project(
            project_name=project_name,
            output_path=output_dir,
            structure_name=test_structure_name,
            template_name=None
        )
        
        # Check result
        if success:
            print(f"Project creation successful: {message}")
            # List created files
            print("\n=== Files created ===")
            for root, dirs, files in os.walk(project_path):
                rel_path = os.path.relpath(root, project_path)
                if rel_path == ".":
                    print(f"Files in project root:")
                else:
                    print(f"Files in {rel_path}:")
                    
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    print(f"  - {file} ({file_size} bytes)")
                    
                    # If it's our test file, check if placeholders were replaced
                    if file == "test_file.txt":
                        with open(file_path, 'r') as f:
                            content = f.read()
                            print(f"    Content: {content}")
        else:
            print(f"Project creation failed: {message}")
        
        # Now try creating a project with a template directly
        print("\n=== Creating project from template ===")
        template_name = "THIS IS TEST"
        project_name = "TEMPLATE_PROJECT"
        
        success, message = project_builder.create_project(
            project_name=project_name,
            output_path=output_dir,
            structure_name=None,
            template_name=template_name
        )
        
        if success:
            print(f"Template project creation successful: {message}")
            template_project_path = os.path.join(output_dir, project_name)
            print("\n=== Files created from template ===")
            for root, dirs, files in os.walk(template_project_path):
                rel_path = os.path.relpath(root, template_project_path)
                if rel_path == ".":
                    print(f"Files in project root:")
                else:
                    print(f"Files in {rel_path}:")
                    
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    print(f"  - {file} ({file_size} bytes)")
        else:
            print(f"Template project creation failed: {message}")
    
    finally:
        # Clean up
        print(f"\nCleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir)
        
if __name__ == "__main__":
    main() 