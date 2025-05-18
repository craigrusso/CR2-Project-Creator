#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script for the new logging system.
This script ensures that our logging system works correctly.
"""

import os
import sys
from PyQt5.QtCore import QCoreApplication

# Set up QCoreApplication for QSettings to work properly
QCoreApplication.setOrganizationName("CR2 Creative")
QCoreApplication.setOrganizationDomain("cr2creative.com")
QCoreApplication.setApplicationName("Echelon")

# Import our logging utilities
from app.utils.logging_utils import (
    initialize_logging, debug, info, warning, error, critical, 
    exception, get_log_file_path, detect_and_set_environment, 
    set_development_mode, set_production_mode
)

def test_logging():
    """Test all logging levels and functions"""
    print("Initializing logging system...")
    initialize_logging()
    
    print("Log file location:", get_log_file_path())
    
    print("Testing log levels...")
    debug("This is a DEBUG message")
    info("This is an INFO message")
    warning("This is a WARNING message")
    error("This is an ERROR message")
    critical("This is a CRITICAL message")
    
    try:
        # Generate an exception for testing
        1/0
    except Exception as e:
        exception("Exception occurred: Division by zero")
    
    print("Testing environment detection...")
    detect_and_set_environment()
    
    print("Testing development mode...")
    set_development_mode()
    debug("This DEBUG message should appear in development mode")
    
    print("Testing production mode...")
    set_production_mode()
    debug("This DEBUG message should NOT appear in production mode")
    info("This INFO message should appear in production mode")
    
    print("Logging test completed successfully!")

if __name__ == "__main__":
    test_logging() 