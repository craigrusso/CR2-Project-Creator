#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Script to run template drag and drop tests
"""

import unittest
import sys
import os

# Add parent directory to path to allow importing from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the test module
from app.templates.test_drag_drop import TestTemplateDragDrop

if __name__ == '__main__':
    # Create a test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestTemplateDragDrop)
    
    # Run the tests
    test_result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # Exit with appropriate code
    sys.exit(not test_result.wasSuccessful()) 