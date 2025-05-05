#!/usr/bin/env python3
"""
Script to run a specific test module for the CLAUSE PROJECT CREATOR application.
Usage: python3 run_specific_test.py [test_module_name]
Example: python3 run_specific_test.py test_structure_editor_integration
"""

import os
import sys
import unittest
import importlib.util

# Define colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def list_available_tests():
    """List all available test modules"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_files = []
    
    print(f"{BLUE}Available test modules:{RESET}")
    for filename in os.listdir(test_dir):
        if filename.startswith('test_') and filename.endswith('.py'):
            test_name = filename[:-3]
            test_files.append(test_name)
            print(f"  - {test_name}")
    
    return test_files

def run_test_module(module_name):
    """Run a specific test module"""
    # Add parent directory to path for imports
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, parent_dir)
    
    # Get the full path to the test module
    test_dir = os.path.dirname(os.path.abspath(__file__))
    module_path = os.path.join(test_dir, f"{module_name}.py")
    
    if not os.path.exists(module_path):
        print(f"{RED}Error: Test module '{module_name}' not found{RESET}")
        return False
    
    try:
        print(f"{BLUE}Running test module: {module_name}{RESET}")
        
        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Create test suite and run tests
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Print summary
        print(f"\n{BLUE}=== Test Summary ==={RESET}")
        print(f"Ran {result.testsRun} tests")
        print(f"{GREEN}Passed: {result.testsRun - len(result.failures) - len(result.errors)}{RESET}")
        
        if result.failures:
            print(f"{RED}Failures: {len(result.failures)}{RESET}")
            for failure in result.failures:
                print(f"  - {failure[0]}")
        
        if result.errors:
            print(f"{RED}Errors: {len(result.errors)}{RESET}")
            for error in result.errors:
                print(f"  - {error[0]}")
        
        return result.wasSuccessful()
    
    except Exception as e:
        print(f"{RED}Error running test module: {str(e)}{RESET}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print(f"{BLUE}========================================{RESET}")
    print(f"{BLUE}=== CLAUSE PROJECT CREATOR Test Runner ==={RESET}")
    print(f"{BLUE}========================================{RESET}")
    
    # Check if a module name was provided
    if len(sys.argv) < 2:
        print(f"{YELLOW}No test module specified.{RESET}")
        available_tests = list_available_tests()
        
        if available_tests:
            print(f"\n{YELLOW}Please specify a test module to run:{RESET}")
            print(f"Usage: python3 {os.path.basename(__file__)} [test_module_name]")
            print(f"Example: python3 {os.path.basename(__file__)} {available_tests[0]}")
        return 1
    
    # Get the module name from command line
    module_name = sys.argv[1]
    
    # If the module name includes .py, remove it
    if module_name.endswith('.py'):
        module_name = module_name[:-3]
    
    # Run the specified test module
    success = run_test_module(module_name)
    
    # Return appropriate exit code
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 