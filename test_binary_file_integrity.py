#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Targeted test script to verify binary file integrity during project creation
Focuses specifically on the _process_files_array method that handles binary files
"""

import os
import sys
import tempfile
import shutil
import filecmp

# Add project directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import project modules
from app.core.project_builder import ProjectBuilder
from app.utils.binary_file_handler import BinaryFileHandler

def main():
    """Main test function"""
    print("\n=== Testing Binary File Integrity in _process_files_array ===\n")
    
    # Create temp directories
    test_dir = tempfile.mkdtemp()
    project_dir = tempfile.mkdtemp()
    
    try:
        # Create a sample binary file
        binary_path = os.path.join(test_dir, "binary_file.png")
        
        # Create a simple PNG test file
        with open(binary_path, 'wb') as f:
            # Simple PNG signature and minimal data
            data = bytes.fromhex(
                '89504e470d0a1a0a'  # PNG signature
                '0000000d49484452'  # IHDR chunk
                '00000001000000010802000000'  # width=1, height=1, bit depth=8, color type=2 (RGB)
                '90043a25'  # CRC
                '00000009704859730000000ec300000ec301c76fa8640000001049444154789c63641860000000ffff034afbff'  # IDAT
                '6221c4b8'  # CRC
                '0000000049454e44ae426082'  # IEND
            )
            f.write(data)
        
        print(f"Created test binary file: {binary_path}")
        print(f"Original file size: {os.path.getsize(binary_path)} bytes")
        
        # Define files array for testing
        files_array = [
            # Test 1: Regular binary file
            {
                "file_name": "regular.png",
                "original_path": binary_path,
                "folder": "regular",
                "is_binary": True
            },
            # Test 2: Binary file with rename_flag
            {
                "file_name": "renamed.png",
                "original_path": binary_path,
                "folder": "renamed",
                "rename_flag": True,
                "is_binary": True
            },
            # Test 3: Binary file with placeholder in name
            {
                "file_name": "${PROJECT_NAME}.png",
                "original_path": binary_path,
                "folder": "placeholder",
                "is_binary": True
            }
        ]
        
        # Create a ProjectBuilder instance
        builder = ProjectBuilder(None)
        
        # Define placeholders
        placeholders = {"PROJECT_NAME": "TestProject"}
        
        # Process files array
        print("\nProcessing files array...")
        copied_files = builder._process_files_array(project_dir, files_array, placeholders)
        
        print(f"\nFiles copied: {len(copied_files)}")
        for file_path in copied_files:
            print(f" - {file_path}")
        
        # Check integrity of copied files
        print("\nVerifying file integrity...")
        all_passed = True
        
        expected_files = [
            os.path.join(project_dir, "regular", "regular.png"),
            os.path.join(project_dir, "renamed", "TestProject.png"),
            os.path.join(project_dir, "placeholder", "TestProject.png")
        ]
        
        for expected_file in expected_files:
            if os.path.exists(expected_file):
                print(f"✅ File exists: {expected_file}")
                
                # Check file size
                expected_size = os.path.getsize(binary_path)
                actual_size = os.path.getsize(expected_file)
                
                print(f"  Original size: {expected_size} bytes")
                print(f"  New file size: {actual_size} bytes")
                
                if expected_size == actual_size:
                    print(f"  ✅ Size matches")
                else:
                    print(f"  ❌ Size mismatch!")
                    all_passed = False
                
                # Check content byte-by-byte
                if filecmp.cmp(binary_path, expected_file, shallow=False):
                    print(f"  ✅ Content identical")
                else:
                    print(f"  ❌ Content differs!")
                    all_passed = False
            else:
                print(f"❌ File not found: {expected_file}")
                all_passed = False
        
        if all_passed:
            print("\n✅ All binary files maintained their integrity!")
        else:
            print("\n❌ Some binary files were corrupted during processing!")
        
    finally:
        # Clean up
        print("\nCleaning up test directories...")
        shutil.rmtree(test_dir)
        shutil.rmtree(project_dir)

if __name__ == "__main__":
    main() 