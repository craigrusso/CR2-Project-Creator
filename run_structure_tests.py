#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Run Structure Tests

This script runs the test suite for structure conversion to help diagnose loading issues.
"""

import os
import sys
import time

def main():
    """Main entry point for the test runner"""
    print("Running structure converter tests...")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Add the current directory to the path
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    
    # Import and run the test module
    try:
        from app.tests.test_structure_converter import (
            test_sample_structure,
            test_load_save_cycle,
            test_load_from_file
        )
        
        # Run all tests
        print("\n=== Running sample structure test ===")
        test_sample_structure()
        
        print("\n=== Running load-save cycle test ===")
        test_load_save_cycle()
        
        print("\n=== Running load from file test ===")
        test_load_from_file()
        
        print("\nAll tests completed successfully.")
    except Exception as e:
        print(f"Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 