#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Debug script to test file copying issues on Windows
"""

import os
import sys
import platform
import shutil
import tempfile
import traceback

def create_test_folder_structure(base_dir):
    """Create a test folder structure"""
    print(f"Creating test folder structure in: {base_dir}")
    
    # Create a simple structure
    folders = [
        "src",
        "docs",
        "assets/images",
        "assets/fonts"
    ]
    
    for folder in folders:
        folder_path = os.path.join(base_dir, folder)
        os.makedirs(folder_path, exist_ok=True)
        print(f"Created folder: {folder_path}")
    
    # Create some test files
    files = [
        ("src/main.txt", "This is a test main file with {{PROJECT_NAME}} placeholder"),
        ("docs/readme.txt", "This is a test readme for {{PROJECT_NAME}}"),
        ("assets/images/logo.txt", "Pretend this is a binary file for {{PROJECT_NAME}}"),
        ("assets/fonts/font.txt", "Pretend font file for {{PROJECT_NAME}}")
    ]
    
    for file_path, content in files:
        full_path = os.path.join(base_dir, file_path)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created file: {full_path}")
    
    return folders, files

def test_file_copy_basic(src_dir, dest_dir):
    """Basic file copy test using shutil.copy2"""
    print("\n=== BASIC FILE COPY TEST ===")
    print(f"Source directory: {src_dir}")
    print(f"Destination directory: {dest_dir}")
    
    # Create destination folder structure
    for folder in ["src", "docs", "assets/images", "assets/fonts"]:
        folder_path = os.path.join(dest_dir, folder)
        os.makedirs(folder_path, exist_ok=True)
    
    # Test files to copy (similar to the app's method)
    test_files = [
        ("src/main.txt", "src/main.txt"),
        ("docs/readme.txt", "docs/readme.txt"),
        ("assets/images/logo.txt", "assets/images/logo.txt"),
        ("assets/fonts/font.txt", "assets/fonts/font.txt")
    ]
    
    success_count = 0
    failure_count = 0
    
    for src_rel_path, dest_rel_path in test_files:
        src_path = os.path.join(src_dir, src_rel_path)
        dest_path = os.path.join(dest_dir, dest_rel_path)
        
        print(f"\nCopying: {src_path} -> {dest_path}")
        try:
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            # Perform the copy
            shutil.copy2(src_path, dest_path)
            
            # Verify the file exists
            if os.path.exists(dest_path):
                print(f"✅ SUCCESS: File copied successfully")
                success_count += 1
            else:
                print(f"❌ ERROR: File not found after copy")
                failure_count += 1
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            traceback.print_exc()
            failure_count += 1
    
    print(f"\nCopy Results: {success_count} succeeded, {failure_count} failed")
    return success_count, failure_count

def test_path_handling():
    """Test path handling issues between Windows and Mac"""
    print("\n=== PATH HANDLING TEST ===")
    
    # Test paths with mixed separators
    test_paths = [
        r"folder\subfolder\file.txt",  # Windows style
        "folder/subfolder/file.txt",   # Unix style
        r"folder/subfolder\file.txt",  # Mixed style
    ]
    
    for path in test_paths:
        norm_path = os.path.normpath(path)
        print(f"Original: {path}")
        print(f"Normalized: {norm_path}")
        print(f"Join parts: {os.path.join(*norm_path.split(os.sep))}")
        # Convert Windows paths to Unix style for storage/comparison
        print(f"Unix style: {norm_path.replace(os.sep, '/')}")
        print()

def main():
    """Main test function"""
    print(f"Running file copy tests on {platform.system()} {platform.release()}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    # Create temp directories for testing
    with tempfile.TemporaryDirectory() as template_dir:
        with tempfile.TemporaryDirectory() as project_dir:
            print(f"\nTemplate directory: {template_dir}")
            print(f"Project directory: {project_dir}")
            
            # Create test structure
            folders, files = create_test_folder_structure(template_dir)
            
            # Run basic file copy test
            test_file_copy_basic(template_dir, project_dir)
            
            # Test path handling
            test_path_handling()
            
            # Test permissions (only relevant on Windows)
            if platform.system() == "Windows":
                print("\n=== WINDOWS PERMISSIONS TEST ===")
                test_file = os.path.join(template_dir, "test_perm.txt")
                with open(test_file, 'w') as f:
                    f.write("Test permissions")
                
                try:
                    # Try to set read-only attribute
                    import stat
                    os.chmod(test_file, stat.S_IREAD)
                    print(f"Set read-only permission on {test_file}")
                    
                    # Try to copy read-only file
                    dest_file = os.path.join(project_dir, "test_perm.txt")
                    shutil.copy2(test_file, dest_file)
                    print(f"✅ Copied read-only file successfully")
                except Exception as e:
                    print(f"❌ Error with permissions test: {e}")
                    traceback.print_exc()

if __name__ == "__main__":
    main()
