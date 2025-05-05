#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test placeholder replacement directly to diagnose the issue.
"""

import sys
import os
import unittest
import re

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestReplacementFix(unittest.TestCase):
    """Direct test for placeholder replacement logic"""
    
    def test_direct_placeholder_replacement(self):
        """Test different methods of replacing placeholders"""
        # Original placeholder and test strings
        project_name = "TestProject123"
        placeholder = "${PROJECT_NAME}"
        test_str = f"{placeholder}.txt"
        test_folder = f"{placeholder}_folder"
        
        print(f"Original placeholder: '{placeholder}'")
        print(f"Original test string: '{test_str}'")
        print(f"Project name to use: '{project_name}'")
        
        # Method 1: Simple string replacement
        method1_result = test_str.replace(placeholder, project_name)
        print(f"Method 1 (simple replace): '{method1_result}'")
        self.assertEqual(f"{project_name}.txt", method1_result)
        
        # Method 2: Split and join
        parts = test_str.split(placeholder)
        method2_result = project_name.join(parts)
        print(f"Method 2 (split/join): '{method2_result}'")
        self.assertEqual(f"{project_name}.txt", method2_result)
        
        # Method 3: Using re.sub for more control
        method3_result = re.sub(r'\${PROJECT_NAME}', project_name, test_str)
        print(f"Method 3 (regex): '{method3_result}'")
        self.assertEqual(f"{project_name}.txt", method3_result)
        
        # Method 4: Isolate just the $
        method4_result = test_str.replace("$", "").replace("{PROJECT_NAME}", project_name)
        print(f"Method 4 (two-step): '{method4_result}'")
        
        # Test folder name replacement
        folder_method1 = test_folder.replace(placeholder, project_name)
        print(f"Folder Method 1: '{folder_method1}'")
        self.assertEqual(f"{project_name}_folder", folder_method1)
        
        print("All tests completed successfully")

if __name__ == "__main__":
    unittest.main() 