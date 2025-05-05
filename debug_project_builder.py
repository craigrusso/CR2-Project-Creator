#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Debug script to test the fixed project_builder._process_files_array method.
"""

import os
import sys
import tempfile
import json
import shutil
import platform
from pathlib import Path

# Add parent directory to path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.core.project_builder import ProjectBuilder
except ImportError:
    print("Failed to import ProjectBuilder. Make sure you're running this from the project root.")
    sys.exit(1)

def create_test_template():
    """Create a simple test template with files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple structure
        template_dir = os.path.join(temp_dir, "template")
        os.makedirs(template_dir, exist_ok=True)
        
        # Create test files
        files = [
            ("src/main.txt", "This is a test main file with {{PROJECT_NAME}} placeholder"),
            ("docs/readme.txt", "This is a test readme for {{PROJECT_NAME}}"),
            ("assets/images/logo.txt", "This is a logo file for {{PROJECT_NAME}}"),
            ("assets/fonts/font.txt", "This is a font file for {{PROJECT_NAME}}")
        ]
        
        for file_path, content in files:
            full_path = os.path.join(template_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Created template file: {full_path}")
        
        # Create template JSON
        template_json = {
            "name": "Test Template",
            "description": "A test template for debugging",
            "structure": [
                {
                    "type": "folder",
                    "name": "src",
                    "children": []
                },
                {
                    "type": "folder",
                    "name": "docs",
                    "children": []
                },
                {
                    "type": "folder",
                    "name": "assets",
                    "children": [
                        {
                            "type": "folder",
                            "name": "images",
                            "children": []
                        },
                        {
                            "type": "folder",
                            "name": "fonts",
                            "children": []
                        }
                    ]
                }
            ],
            "files": []
        }
        
        # Add files to template
        for file_path, _ in files:
            original_path = os.path.join(template_dir, file_path)
            folder = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            
            file_info = {
                "file_name": file_name,
                "original_path": original_path,
                "folder": folder,
                "is_binary": False,
                "rename_flag": False
            }
            
            template_json["files"].append(file_info)
        
        # Add one file with PROJECT_NAME placeholder
        template_json["files"].append({
            "file_name": "${PROJECT_NAME}_config.txt",
            "original_path": os.path.join(template_dir, "src/main.txt"),
            "folder": "config",
            "is_binary": False,
            "rename_flag": True
        })
        
        # Write template JSON
        template_json_path = os.path.join(temp_dir, "template.json")
        with open(template_json_path, 'w', encoding='utf-8') as f:
            json.dump(template_json, f, indent=2)
        
        print(f"Created template JSON: {template_json_path}")
        
        # Create a ProjectBuilder instance
        project_builder = ProjectBuilder(None)
        
        # Create output directory
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create project directory
        project_name = "DebugProject"
        project_dir = os.path.join(output_dir, project_name)
        os.makedirs(project_dir, exist_ok=True)
        
        # Create placeholders
        placeholders = {
            "PROJECT_NAME": project_name,
            "project_name": project_name.lower(),
            "Project_Name": project_name.title(),
            "ProjectName": project_name.replace(" ", ""),
            "PROJECT_DIR": project_dir
        }
        
        # Create folder structure
        print("\nCreating folder structure...")
        created_folders = project_builder._create_folders_from_structure(project_dir, template_json["structure"])
        print(f"Created {len(created_folders)} folders")
        
        # Process files
        print("\nProcessing files...")
        success, result = project_builder._process_files_array(
            project_dir, 
            template_json["files"], 
            placeholders
        )
        
        # Check results
        print(f"\nSuccess: {success}")
        if success:
            print(f"Copied {len(result)} files:")
            for file_path in result:
                print(f"  - {file_path}")
                # Verify file exists
                if os.path.exists(file_path):
                    print(f"    ✅ File exists")
                    # Check file content
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if project_name in content:
                            print(f"    ✅ Content has placeholder replaced")
                        else:
                            print(f"    ❌ Content does not have placeholder replaced")
                    except Exception as e:
                        print(f"    ❌ Error reading file: {e}")
                else:
                    print(f"    ❌ File does not exist")
        else:
            print(f"Error: {result}")
        
        # Open output directory
        print(f"\nOutput directory: {output_dir}")
        print(f"Template directory: {template_dir}")
        
        # Copy output to a more permanent location for inspection
        debug_output = os.path.join(os.getcwd(), "debug_output")
        if os.path.exists(debug_output):
            shutil.rmtree(debug_output)
        shutil.copytree(output_dir, debug_output)
        print(f"\nCopied output to: {debug_output}")
        
        # Keep terminal open for inspection
        input("\nPress Enter to exit and clean up temporary directories...")

def main():
    """Main debug function"""
    print(f"Running debug test on {platform.system()} {platform.version()}")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    # Test the ProjectBuilder._process_files_array method
    create_test_template()

if __name__ == "__main__":
    main() 