#!/usr/bin/env python3
"""
Script to run all tests for the CLAUSE PROJECT CREATOR application.
This will run the unit tests and optionally the manual interactive tests.
"""

import os
import sys
import unittest
import importlib.util
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Define colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def discover_and_run_tests():
    """Discover and run all test cases in the tests directory"""
    print(f"{BLUE}=== Discovering Tests ==={RESET}")
    
    # Get the directory containing this script
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Find all test files
    test_files = []
    for filename in os.listdir(test_dir):
        if filename.startswith('test_') and filename.endswith('.py') and filename != os.path.basename(__file__):
            test_files.append(filename[:-3])  # Remove .py extension
    
    # Load test modules and add to suite
    loader = unittest.TestLoader()
    for test_file in test_files:
        try:
            # Import the module
            module_path = os.path.join(test_dir, f"{test_file}.py")
            spec = importlib.util.spec_from_file_location(test_file, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Add tests from the module
            test_suite = loader.loadTestsFromModule(module)
            suite.addTests(test_suite)
            print(f"{GREEN}Found tests in {test_file}{RESET}")
        except Exception as e:
            print(f"{RED}Error loading tests from {test_file}: {str(e)}{RESET}")
    
    # Run the tests
    print(f"\n{BLUE}=== Running Tests ==={RESET}")
    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    end_time = time.time()
    
    # Print summary
    print(f"\n{BLUE}=== Test Summary ==={RESET}")
    print(f"Ran {result.testsRun} tests in {end_time - start_time:.2f} seconds")
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

def run_manual_tests():
    """Run the manual interactive tests"""
    print(f"\n{BLUE}=== Manual Interactive Tests ==={RESET}")
    print(f"{YELLOW}Do you want to run the manual interactive tests? (y/n){RESET}")
    choice = input().lower()
    
    if choice != 'y':
        print("Skipping manual tests")
        return True
    
    try:
        # Run structure editor test harness
        test_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manual_test_structure_editor.py")
        if os.path.exists(test_script):
            print(f"{BLUE}Running Structure Editor Test Harness...{RESET}")
            print(f"{YELLOW}This will open a GUI window. Close it when you're done testing.{RESET}")
            
            # Import and run the manual test module
            spec = importlib.util.spec_from_file_location("manual_test_structure_editor", test_script)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.main()
            
            print(f"{GREEN}Manual test completed{RESET}")
            return True
        else:
            print(f"{RED}Manual test script not found at {test_script}{RESET}")
            return False
    except Exception as e:
        print(f"{RED}Error running manual tests: {str(e)}{RESET}")
        import traceback
        traceback.print_exc()
        return False

def run_main_app_test():
    """Run a test of the main application"""
    print(f"\n{BLUE}=== Main Application Test ==={RESET}")
    print(f"{YELLOW}Do you want to run a test of the main application? (y/n){RESET}")
    choice = input().lower()
    
    if choice != 'y':
        print("Skipping main application test")
        return True
    
    try:
        print(f"{BLUE}Starting the main application...{RESET}")
        print(f"{YELLOW}This will open the main application window. Close it when you're done testing.{RESET}")
        
        # Add parent directory to path and import main
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from main import main as run_main_app
        
        # Run the main application
        run_main_app()
        
        print(f"{GREEN}Main application test completed{RESET}")
        return True
    except Exception as e:
        print(f"{RED}Error running main application: {str(e)}{RESET}")
        import traceback
        traceback.print_exc()
        return False

def generate_report(unit_tests_passed, manual_tests_run, main_app_run):
    """Generate a test report"""
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    os.makedirs(report_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(report_dir, f"test_report_{timestamp}.txt")
    
    with open(report_file, 'w') as f:
        f.write("CLAUSE PROJECT CREATOR Test Report\n")
        f.write("=================================\n\n")
        f.write(f"Date and Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("Test Summary:\n")
        f.write(f"- Unit Tests: {'PASSED' if unit_tests_passed else 'FAILED'}\n")
        f.write(f"- Manual Tests: {'RUN' if manual_tests_run else 'SKIPPED'}\n")
        f.write(f"- Main Application: {'RUN' if main_app_run else 'SKIPPED'}\n\n")
        
        f.write("Notes:\n")
        f.write("- See unittest output above for detailed results\n")
        f.write("- Manual tests are interactive and require visual inspection\n\n")
        
        f.write("Overall Status: ")
        if unit_tests_passed:
            f.write("PASSED (all automated tests passed)\n")
        else:
            f.write("FAILED (some automated tests failed)\n")
    
    print(f"\n{GREEN}Test report generated: {report_file}{RESET}")
    return report_file

def main():
    """Main function to run all tests"""
    print(f"{BLUE}========================================{RESET}")
    print(f"{BLUE}=== CLAUSE PROJECT CREATOR Test Suite ==={RESET}")
    print(f"{BLUE}========================================{RESET}")
    print(f"Starting tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run automated tests
    unit_tests_passed = discover_and_run_tests()
    
    # Run manual tests if unit tests passed
    manual_tests_run = False
    main_app_run = False
    
    if unit_tests_passed:
        print(f"\n{GREEN}All unit tests passed. You can now run the manual tests.{RESET}")
        manual_tests_run = run_manual_tests()
        main_app_run = run_main_app_test()
    else:
        print(f"\n{RED}Some unit tests failed. Fix them before running manual tests.{RESET}")
    
    # Generate report
    report_file = generate_report(unit_tests_passed, manual_tests_run, main_app_run)
    
    # Final summary
    print(f"\n{BLUE}=== Final Status ==={RESET}")
    if unit_tests_passed:
        print(f"{GREEN}All unit tests PASSED{RESET}")
    else:
        print(f"{RED}Some unit tests FAILED{RESET}")
    
    print(f"\nTest report available at: {report_file}")
    print(f"\n{BLUE}Tests completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    
    return 0 if unit_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 