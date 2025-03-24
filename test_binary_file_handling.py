#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script to verify proper handling of binary files
"""

import os
import sys
import tempfile
import shutil
import filecmp
import binascii

# Add project directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import project modules
from app.core.project_builder import ProjectBuilder
from app.utils.binary_file_handler import BinaryFileHandler

def verify_binary_file_integrity(original_path, new_path):
    """Verify that two binary files are identical"""
    # First check file sizes
    original_size = os.path.getsize(original_path)
    new_size = os.path.getsize(new_path)
    
    print(f"Original file size: {original_size} bytes")
    print(f"New file size: {new_size} bytes")
    
    if original_size != new_size:
        print(f"❌ File sizes don't match! Original: {original_size}, New: {new_size}")
        return False
    
    # Compare files byte by byte
    if filecmp.cmp(original_path, new_path, shallow=False):
        print("✅ Files are identical (byte-by-byte comparison)")
        return True
    else:
        print("❌ Files are different (byte-by-byte comparison)")
        
        # Read the start of both files to see differences
        with open(original_path, 'rb') as f1, open(new_path, 'rb') as f2:
            orig_data = f1.read(100)
            new_data = f2.read(100)
            
        print(f"Original file start (hex): {binascii.hexlify(orig_data)}")
        print(f"New file start (hex): {binascii.hexlify(new_data)}")
        return False

def main():
    """Main test function"""
    print("\n=== Testing Binary File Handling ===\n")
    
    # Create temp directory and test files
    test_dir = tempfile.mkdtemp()
    project_dir = tempfile.mkdtemp()
    
    try:
        # Create a sample binary file (a small PNG image)
        binary_file_path = os.path.join(test_dir, "test_binary.png")
        
        # Create a simple PNG file (1x1 pixel, transparent)
        with open(binary_file_path, 'wb') as f:
            # PNG header and minimal chunks to create a valid PNG
            png_data = bytes.fromhex(
                '89504e470d0a1a0a' # PNG signature
                '0000000d49484452' # IHDR chunk length and type
                '00000001000000010800000000' # width=1, height=1, bit depth=8, color type=0
                '3a7e9b55' # CRC
                '0000000a49444154789c63000100000500010d0a' # IDAT chunk
                'ae426082' # CRC
                '0000000049454e44ae426082' # IEND chunk
            )
            f.write(png_data)
        
        print(f"Created test binary file at: {binary_file_path}")
        original_size = os.path.getsize(binary_file_path)
        print(f"Original file size: {original_size} bytes")
        
        # ======== Test 1: Basic copy using shutil.copy2 ========
        print("\n--- Test 1: Basic copy using shutil.copy2 ---")
        basic_copy_path = os.path.join(project_dir, "basic_copy.png")
        shutil.copy2(binary_file_path, basic_copy_path)
        
        print(f"Basic copy file size: {os.path.getsize(basic_copy_path)} bytes")
        verify_binary_file_integrity(binary_file_path, basic_copy_path)
        
        # ======== Test 2: Copy using _process_files_array ========
        print("\n--- Test 2: Copy using _process_files_array ---")
        
        # Create a files array for testing
        files_array = [
            {
                "file_name": "test_via_array.png",
                "original_path": binary_file_path,
                "folder": "array_test",
                "rename_flag": False,
                "is_binary": True
            }
        ]
        
        # Initialize project builder
        project_builder = ProjectBuilder(None)
        
        # Define placeholders
        placeholders = {"PROJECT_NAME": "TestBinary"}
        
        # Process files array
        copied_files = project_builder._process_files_array(
            project_dir, 
            files_array, 
            placeholders
        )
        
        # Check the copied file
        if copied_files:
            array_copy_path = copied_files[0]
            print(f"File copied via _process_files_array: {array_copy_path}")
            verify_binary_file_integrity(binary_file_path, array_copy_path)
        else:
            print("❌ No files were copied via _process_files_array")
        
        # ======== Test 3: Test if _might_contain_placeholders is handling binary files correctly ========
        print("\n--- Test 3: Test _might_contain_placeholders ---")
        
        # Check if binary file is detected as possibly containing placeholders
        might_contain = project_builder._might_contain_placeholders(binary_file_path)
        print(f"Binary file detected as possibly containing placeholders: {might_contain}")
        
        # Add placeholder to binary file to see if it's detected
        with open(os.path.join(test_dir, "binary_with_placeholder.png"), 'wb') as f:
            # Add a placeholder string after PNG header
            f.write(png_data)
            f.write(b'${PROJECT_NAME}')
        
        placeholder_path = os.path.join(test_dir, "binary_with_placeholder.png")
        might_contain = project_builder._might_contain_placeholders(placeholder_path)
        print(f"Binary file with injected placeholder detected: {might_contain}")
        
        # ======== Test 4: Test _process_binary_file method ========
        print("\n--- Test 4: Test _process_binary_file method ---")
        
        binary_process_path = os.path.join(project_dir, "processed_binary.png")
        success = project_builder._process_binary_file(binary_file_path, binary_process_path, placeholders)
        
        if success:
            print(f"Binary file processed: {binary_process_path}")
            verify_binary_file_integrity(binary_file_path, binary_process_path)
        else:
            print("❌ Failed to process binary file")
        
        # ======== Test 5: Test binary file with rename flag ========
        print("\n--- Test 5: Test binary file with rename flag ---")
        
        # Create a files array with rename_flag
        files_array_renamed = [
            {
                "file_name": "rename_test.png", 
                "original_path": binary_file_path,
                "folder": "rename_test",
                "rename_flag": True,
                "is_binary": True
            }
        ]
        
        # Process files array with rename flag
        renamed_files = project_builder._process_files_array(
            project_dir, 
            files_array_renamed, 
            placeholders
        )
        
        # Check the renamed file
        if renamed_files:
            renamed_path = renamed_files[0]
            print(f"Renamed file: {renamed_path}")
            verify_binary_file_integrity(binary_file_path, renamed_path)
        else:
            print("❌ No files were copied in rename test")
        
    finally:
        # Clean up
        print("\nCleaning up test directories...")
        shutil.rmtree(test_dir)
        shutil.rmtree(project_dir)

if __name__ == "__main__":
    main() 