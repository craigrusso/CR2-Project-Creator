#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script for batch creation with the new template format
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
from app.utils.file_cache_manager import FileCacheManager
from app.core.project_builder import ProjectBuilder
from app.templates.template_manager import TemplateManager

def main():
    """Main test function"""
    print("=== Testing Batch Creation with New Template Format ===")
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    cache_dir = os.path.join(temp_dir, "cache")
    templates_dir = os.path.join(temp_dir, "templates")
    output_dir = os.path.join(temp_dir, "output")
    
    try:
        # Create test directories
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(templates_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a test template
        template = create_test_template("BatchTestTemplate")
        template_path = os.path.join(templates_dir, "BatchTestTemplate.json")
        
        # Save template to file
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        print(f"Created template at: {template_path}")
        
        # Initialize the managers with our directories
        template_manager = TemplateManager()
        # Override the template manager's paths
        template_manager.paths = {
            "templates_dir": templates_dir,
            "templates_cache_dir": cache_dir,
            "custom_structures_dir": os.path.join(temp_dir, "structures")
        }
        
        # Force load the template directly
        if not hasattr(template_manager, 'templates'):
            template_manager.templates = []
        template_manager.templates.append(template)
        
        # Print the template
        print(f"Template added to manager's templates list: {template['name']}")
        print(f"Templates in manager: {[t.get('name') for t in template_manager.templates if isinstance(t, dict)]}")
        
        # Initialize project builder with our template manager
        project_builder = ProjectBuilder(template_manager)
        
        # Verify template can be retrieved
        test_template = template_manager.get_template(template["name"])
        if test_template:
            print(f"Successfully retrieved template: {template['name']}")
            template_data = test_template
        else:
            print(f"WARNING: Failed to retrieve template: {template['name']}")
            # Try one more approach for testing - pass the template directly
            template_data = template
        
        # Create test project names
        project_names = ["Project1", "Project2", "Project3"]
        
        # Batch create projects
        print("\nStarting batch project creation...")
        result = project_builder.batch_create_projects(
            project_names=project_names,
            template_name=template["name"],
            output_dir=output_dir,
            use_cached_files=True,
            template_data=template_data
        )
        
        print(f"Batch creation result: {result}")
        
        # List created projects
        print("\nCreated projects:")
        for project_name in project_names:
            project_dir = os.path.join(output_dir, project_name)
            if os.path.exists(project_dir):
                print(f"- {project_name} (Success)")
                # List files in project
                for root, _, files in os.walk(project_dir):
                    rel_path = os.path.relpath(root, project_dir)
                    if rel_path == ".":
                        rel_path = ""
                    else:
                        print(f"  - {rel_path}/")
                    for file in files:
                        file_path = os.path.join(root, file)
                        print(f"    - {file} ({os.path.getsize(file_path)} bytes)")
            else:
                print(f"- {project_name} (Failed - directory not found)")
        
    finally:
        print(f"\nCleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir)

def create_test_template(template_name):
    """Create a test template with the new file structure format"""
    # Create a basic structure
    structure = {
        "folders": {
            "src": {
                "code": {},
                "assets": {}
            },
            "docs": {},
            "resources": {}
        }
    }
    
    # Create the template data
    template = {
        "name": template_name,
        "description": "Test template for batch creation",
        "category": "Test",
        "type": "Standard",
        "created": datetime.now().isoformat(),
        "modified": datetime.now().isoformat(),
        "tags": ["test", "batch"],
        "structure": structure,
        "files": [
            {
                "file_name": "README.md",
                "original_path": create_test_file("README.md", "# ${PROJECT_NAME}\n\nThis is a test project."),
                "cached_path": "",
                "rename_flag": False,
                "folder": "",
                "file_type": "document",
                "size": 0,
                "last_modified": datetime.now().isoformat()
            },
            {
                "file_name": "${PROJECT_NAME}.py",
                "original_path": create_test_file("main.py", "# Main file for ${PROJECT_NAME}\n\nprint('Hello from ${PROJECT_NAME}')"),
                "cached_path": "",
                "rename_flag": True,
                "folder": "src/code",
                "file_type": "code",
                "size": 0,
                "last_modified": datetime.now().isoformat()
            }
        ]
    }
    
    return template

def create_test_file(filename, content):
    """Create a test file with the given content and return its path"""
    temp_file = os.path.join(tempfile.gettempdir(), filename)
    with open(temp_file, 'w') as f:
        f.write(content)
    return temp_file

if __name__ == "__main__":
    main() 