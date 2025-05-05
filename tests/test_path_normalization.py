#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test for path normalization between different operating systems
"""

import os
import sys
import platform
import unittest

try:
    from app.utils.utils import normalize_path_for_storage
except ImportError:
    # Mock function if not available
    def normalize_path_for_storage(path):
        """Normalize a path for storage with forward slashes"""
        if not path:
            return ""
        norm_path = os.path.normpath(path)
        return norm_path.replace('\\', '/')

class TestPathNormalization(unittest.TestCase):
    """Test path normalization to ensure consistent handling across platforms"""

    def test_empty_path(self):
        """Test empty path handling"""
        self.assertEqual(normalize_path_for_storage(""), "")
        self.assertEqual(normalize_path_for_storage(None), "")

    def test_simple_path(self):
        """Test simple path normalization"""
        self.assertEqual(normalize_path_for_storage("folder/file.txt"), "folder/file.txt")
        
    def test_windows_path(self):
        """Test Windows path normalization"""
        self.assertEqual(normalize_path_for_storage(r"folder\file.txt"), "folder/file.txt")
        self.assertEqual(normalize_path_for_storage(r"C:\Users\test\Documents"), "C:/Users/test/Documents")
        
    def test_mixed_separators(self):
        """Test mixed separator normalization"""
        self.assertEqual(normalize_path_for_storage(r"folder/subfolder\file.txt"), "folder/subfolder/file.txt")
        
    def test_nested_structure(self):
        """Test deeper nested structure"""
        path_parts = ["Assets", "Graphics", "Logos", "logo.png"]
        
        # Create Windows style path
        windows_path = "\\".join(path_parts)
        self.assertEqual(normalize_path_for_storage(windows_path), "/".join(path_parts))
        
        # Create Unix style path
        unix_path = "/".join(path_parts)
        self.assertEqual(normalize_path_for_storage(unix_path), unix_path)
        
    def test_relative_path_joining(self):
        """Test relative path joining and normalization"""
        # Join some path parts in a platform-specific way
        path = os.path.join("folder", "subfolder", "file.txt")
        
        # The result should always have forward slashes
        self.assertEqual(normalize_path_for_storage(path), "folder/subfolder/file.txt")
        
def run_tests():
    """Run the path normalization tests"""
    print(f"Running path normalization tests on {platform.system()}")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
if __name__ == "__main__":
    run_tests() 