#!/usr/bin/env python3
"""
Test script to verify the fixes to structure processing.
This creates a test project with all the fixed code.
"""

import os
import json
import shutil
import tempfile
import sys

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder

def test_fixed_project_creation():
    """Test that project creation now works with proper folder names"""
    print("\n=== Testing Fixed Project Creation ===")
    
    # Create a temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    output_dir = os.path.join(temp_dir, "test_project")
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Initialize managers
        template_manager = TemplateManager()
        project_builder = ProjectBuilder(template_manager)
        
        # Get a structure name to test with
        structure_name = "Template_oh my goe"
        
        print(f"Creating project with structure: {structure_name}")
        
        # Create a test project using the structure
        success, result = project_builder.create_project(
            project_name="TEST_PROJECT",
            output_path=output_dir,
            structure_name=structure_name
        )
        
        print(f"Project creation result: {success}, {result}")
        
        # List the created directories
        print("\nCreated directory structure:")
        for root, dirs, files in os.walk(output_dir):
            level = root.replace(output_dir, '').count(os.sep)
            indent = ' ' * 4 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 4 * (level + 1)
            for d in dirs:
                print(f"{subindent}{d}/")
            for f in files:
                print(f"{subindent}{f}")
        
    finally:
        # Clean up
        print(f"\nCleaning up temp directory: {temp_dir}")
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_fixed_project_creation() 