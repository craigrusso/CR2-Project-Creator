#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script to verify proper handling of real-world binary files
This test creates a simple project with binary files (images)
"""

import os
import sys
import tempfile
import shutil
import json
import base64
import filecmp
from datetime import datetime

# Add project directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import project modules
from app.core.project_builder import ProjectBuilder
from app.utils.binary_file_handler import BinaryFileHandler

def print_file_info(file_path):
    """Print information about a file"""
    if not os.path.exists(file_path):
        print(f"❌ File doesn't exist: {file_path}")
        return
        
    # Get file size
    size = os.path.getsize(file_path)
    print(f"File: {os.path.basename(file_path)}")
    print(f"Size: {size} bytes")
    
    # Check if binary
    is_binary = BinaryFileHandler.is_binary_file(file_path)
    print(f"Binary: {is_binary}")
    
    # Show first few bytes as hex
    with open(file_path, 'rb') as f:
        data = f.read(16)
        hex_data = ' '.join([f'{b:02x}' for b in data])
        print(f"First 16 bytes: {hex_data}")
    print()

def create_test_images(output_dir):
    """Create some test image files"""
    # Create a simple PNG image (1x1 pixel, red)
    png_path = os.path.join(output_dir, "red_pixel.png")
    with open(png_path, 'wb') as f:
        # PNG header and minimal chunks for a valid red pixel PNG
        png_data = bytes.fromhex(
            '89504e470d0a1a0a'  # PNG signature
            '0000000d49484452'  # IHDR chunk length and type
            '00000001000000010802000000'  # width=1, height=1, bit depth=8, color type=2 (RGB)
            '90043a25'  # CRC
            '00000009704859730000000ec300000ec301c76fa8640000001049444154789c63641860000000ffff034afbff'  # IDAT chunk (red pixel)
            '6221c4b8'  # CRC
            '0000000049454e44ae426082'  # IEND chunk
        )
        f.write(png_data)
    
    # Create a JPEG file with red pixel
    jpg_path = os.path.join(output_dir, "red_pixel.jpg")
    with open(jpg_path, 'wb') as f:
        # Minimal valid JPEG for a red pixel
        jpg_data = bytes.fromhex(
            'ffd8ffe000104a46494600010101004800480000ffdb00430001010101010101010101010101010101010101'
            '01010101010101010101010101010101010101010101010101010101010101010101010101010101010101ff'
            'c00011080001000103011100021101031101ffc4001500010100000000000000000000000000000000ffc400'
            '14100100000000000000000000000000000000ffda0008010100013f10ff00ff00da000c03010002110311003f'
            '00ff00ffd9'
        )
        f.write(jpg_data)
    
    return [png_path, jpg_path]

def main():
    """Main test function"""
    print("\n=== Testing Real-World Binary File Handling ===\n")
    
    # Create temp directories
    test_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()
    
    try:
        # Create test images
        print("Creating test images...")
        test_images = create_test_images(test_dir)
        
        # Print information about the test files
        for image_path in test_images:
            print_file_info(image_path)
        
        # Create a template structure with binary files
        print("Creating template structure with binary files...")
        template = {
            "name": "BinaryFileTest",
            "description": "A test template with binary files",
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
            "structure": [
                {
                    "type": "folder",
                    "name": "Root Folder",
                    "children": [
                        {
                            "type": "folder",
                            "name": "images",
                            "children": [
                                {
                                    "type": "file",
                                    "name": "regular_image.png",
                                    "original_path": test_images[0],
                                    "is_binary": True
                                },
                                {
                                    "type": "file", 
                                    "name": "${PROJECT_NAME}_image.png",
                                    "original_path": test_images[0],
                                    "is_binary": True
                                }
                            ]
                        },
                        {
                            "type": "file",
                            "name": "regular_image.jpg",
                            "original_path": test_images[1],
                            "is_binary": True
                        },
                        {
                            "type": "file",
                            "name": "renamed_image.jpg",
                            "original_path": test_images[1],
                            "is_binary": True,
                            "rename_flag": True
                        }
                    ]
                }
            ]
        }
        
        # Save template to file for debugging
        with open(os.path.join(test_dir, "template.json"), 'w') as f:
            json.dump(template, f, indent=2)
        
        # Create project builder
        project_builder = ProjectBuilder(None)
        
        # Create project using the template
        project_name = "TestBinaryProject"
        print(f"\nCreating project '{project_name}' with binary files...")
        
        # Create a template file dict
        template_file = {
            "name": template["name"],
            "description": template["description"],
            "version": template["version"],
            "structure": template["structure"]
        }
        
        success, project_path = project_builder.create_project(
            project_name=project_name,
            output_dir=output_dir,
            template_file=template_file
        )
        
        if not success:
            print(f"❌ Failed to create project: {project_path}")
            return
        
        print(f"✅ Project created successfully at: {project_path}")
        
        # Check the created files
        print("\nChecking created files...")
        
        # Expected file paths
        expected_files = [
            os.path.join(project_path, "Root Folder", "images", "regular_image.png"),
            os.path.join(project_path, "Root Folder", "images", f"{project_name}_image.png"),
            os.path.join(project_path, "Root Folder", "regular_image.jpg"),
            os.path.join(project_path, "Root Folder", f"{project_name}.jpg")  # Renamed
        ]
        
        all_passed = True
        for i, expected_file in enumerate(expected_files):
            if os.path.exists(expected_file):
                print(f"✅ File exists: {expected_file}")
                
                # Check if file is intact by comparing with original
                original_file = test_images[0 if i < 2 else 1]  # First two are PNG, second two are JPG
                
                if filecmp.cmp(original_file, expected_file, shallow=False):
                    print(f"  ✅ File content is preserved")
                else:
                    print(f"  ❌ File content is corrupted!")
                    print_file_info(original_file)
                    print_file_info(expected_file)
                    all_passed = False
            else:
                print(f"❌ Expected file not found: {expected_file}")
                all_passed = False
        
        # Print test result
        if all_passed:
            print("\n✅ All binary files were handled correctly!")
        else:
            print("\n❌ There are issues with binary file handling")
        
    finally:
        # Clean up
        print("\nCleaning up test directories...")
        shutil.rmtree(test_dir)
        shutil.rmtree(output_dir)

if __name__ == "__main__":
    main() 