#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Windows-specific file copying test script
This script tests for issues with file copying on Windows platforms
"""

import os
import sys
import platform
import shutil
import tempfile
import traceback
from pathlib import Path

def test_path_normalization():
    """Test path normalization between different formats"""
    print("\n=== PATH NORMALIZATION TESTS ===")
    
    # Test paths
    test_paths = [
        r"folder\subfolder\file.txt",  # Windows style
        "folder/subfolder/file.txt",    # Unix style
        r"folder/subfolder\file.txt",   # Mixed style
        r"C:\Users\test\Documents",     # Windows absolute path
        "/Users/test/Documents",        # Unix absolute path
    ]
    
    for path in test_paths:
        # Test different normalization methods
        path_obj = Path(path)
        norm_path = os.path.normpath(path)
        
        print(f"Original:       {path}")
        print(f"Path object:    {path_obj}")
        print(f"os.path.normpath: {norm_path}")
        print(f"Path parts:     {path_obj.parts}")
        print(f"Path as string: {str(path_obj)}")
        print(f"Path.as_posix:  {path_obj.as_posix()}")
        print("")
    
    # Test joining paths
    parent_dirs = [
        r"C:\Projects",
        "/home/user/projects",
        "projects"
    ]
    
    child_paths = [
        r"template\file.txt",
        "template/file.txt"
    ]
    
    print("\n=== PATH JOINING TESTS ===")
    for parent in parent_dirs:
        for child in child_paths:
            # Test with os.path.join
            joined_path = os.path.join(parent, child)
            print(f"os.path.join({parent}, {child}):")
            print(f"  Result: {joined_path}")
            
            # Test with pathlib
            parent_obj = Path(parent)
            child_obj = Path(child)
            pathlib_joined = parent_obj / child
            print(f"Path({parent}) / {child}:")
            print(f"  Result: {pathlib_joined}")
            print("")

def test_file_copy(source_dir, dest_dir):
    """Test basic file copying with detailed error reporting"""
    print("\n=== FILE COPY TESTS ===")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Source directory: {source_dir}")
    print(f"Destination directory: {dest_dir}")
    
    # Create test files
    test_files = {
        "regular.txt": "Regular text file content",
        "with spaces.txt": "File with spaces in name",
        "binary.bin": b"\x00\x01\x02\x03\x04\xFF"
    }
    
    # Create source files
    for filename, content in test_files.items():
        file_path = os.path.join(source_dir, filename)
        
        if isinstance(content, bytes):
            with open(file_path, "wb") as f:
                f.write(content)
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        print(f"Created source file: {file_path}")
    
    # Create nested folders
    nested_folders = [
        "folder1",
        "folder1/subfolder",
        "folder2/subfolder" # This requires parent folder creation
    ]
    
    for folder in nested_folders:
        folder_path = os.path.join(source_dir, folder)
        os.makedirs(folder_path, exist_ok=True)
        print(f"Created folder: {folder_path}")
        
        # Create a test file in each folder
        test_file = os.path.join(folder_path, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(f"Test file in {folder}")
        print(f"Created test file: {test_file}")
    
    # Test different copy methods
    print("\n=== COPYING FILES ===")
    
    for method in ["copy2", "copy", "copyfile", "pathlib"]:
        print(f"\nUsing method: {method}")
        
        # Create a fresh destination directory for this method
        method_dest = os.path.join(dest_dir, method)
        os.makedirs(method_dest, exist_ok=True)
        
        # Copy all test files
        for filename in test_files.keys():
            source_path = os.path.join(source_dir, filename)
            dest_path = os.path.join(method_dest, filename)
            
            print(f"Copying {source_path} -> {dest_path}")
            try:
                # Make sure destination directory exists
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                
                if method == "copy2":
                    shutil.copy2(source_path, dest_path)
                elif method == "copy":
                    shutil.copy(source_path, dest_path)
                elif method == "copyfile":
                    shutil.copyfile(source_path, dest_path)
                elif method == "pathlib":
                    source = Path(source_path)
                    dest = Path(dest_path)
                    with open(source, "rb") as src_file:
                        with open(dest, "wb") as dst_file:
                            dst_file.write(src_file.read())
                
                # Verify file exists
                if os.path.exists(dest_path):
                    src_size = os.path.getsize(source_path)
                    dst_size = os.path.getsize(dest_path)
                    print(f"  ✅ Success! Source size: {src_size}, Dest size: {dst_size}")
                else:
                    print(f"  ❌ File not found after copy")
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                traceback.print_exc()
    
    # Copy folders
    print("\n=== COPYING FOLDERS ===")
    
    for folder in nested_folders:
        source_path = os.path.join(source_dir, folder)
        dest_path = os.path.join(dest_dir, "folders", folder)
        
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        print(f"Copying folder {source_path} -> {dest_path}")
        try:
            shutil.copytree(source_path, dest_path)
            print(f"  ✅ Success!")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            traceback.print_exc()

def main():
    """Main test function"""
    print(f"Running Windows file copy tests on {platform.system()} {platform.release()}")
    print(f"Python version: {sys.version}")
    
    # Test path normalization
    test_path_normalization()
    
    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as source_dir:
        with tempfile.TemporaryDirectory() as dest_dir:
            print(f"\nTemporary source directory: {source_dir}")
            print(f"Temporary destination directory: {dest_dir}")
            
            # Run file copy tests
            test_file_copy(source_dir, dest_dir)
    
    print("\nTests completed.")

if __name__ == "__main__":
    main() 