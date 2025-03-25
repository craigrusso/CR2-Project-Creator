#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import sys
import tempfile
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

def main():
    """Test the show_batch_results function with different result formats"""
    # Import required modules
    from app.ui.color_scheme_pyqt import colors, BUTTON_STYLE, ACCENT_BUTTON_STYLE
    from app.dialogs.dialog_windows_pyqt import show_batch_results
    
    # Get command line arguments
    show_ui = "--show-ui" in sys.argv
    
    # Create a QApplication instance for testing
    app = QApplication(sys.argv)
    
    # Test case 1: Dictionary results format with summary key
    print("\n=== Test Case 1: Dictionary results with summary ===")
    dict_results = {
        "Project1": {
            "success": True,
            "directory": "/fake/path/Project1",
            "message": "Project created successfully"
        },
        "Project2": {
            "success": True,
            "directory": "/fake/path/Project2",
            "message": "Project created successfully"
        },
        "Project3": {
            "success": False,
            "error": "Failed to create project",
            "message": "Failed to create project"
        },
        "summary": {
            "successful_count": 2,
            "total_count": 3,
            "success_rate": "2/3"
        }
    }
    
    # This should display "2 of 3 projects created successfully"
    print("Expected result: 2 of 3 projects created successfully")
    if show_ui:
        print("Running UI test: show_batch_results(None, dict_results)")
        show_batch_results(None, dict_results)
    
    # Test case 2: Tuple list format
    print("\n=== Test Case 2: Tuple list format ===")
    tuple_results = [
        ("Project1", True, "/fake/path/Project1"),
        ("Project2", True, "/fake/path/Project2"),
        ("Project3", False, "Error message")
    ]
    
    # This should display "2 of 3 projects created successfully"
    print("Expected result: 2 of 3 projects created successfully")
    if show_ui:
        print("Running UI test: show_batch_results(None, tuple_results)")
        show_batch_results(None, tuple_results)
    
    # Test case 3: Empty results
    print("\n=== Test Case 3: Empty results ===")
    empty_results = {}
    
    # This should not display anything
    print("Expected result: No dialog shown")
    if show_ui:
        print("Running UI test: show_batch_results(None, empty_results)")
        show_batch_results(None, empty_results)
    
    # Test case 4: Large batch results
    print("\n=== Test Case 4: Large batch (17 projects) ===")
    large_batch = {}
    for i in range(1, 18):
        large_batch[f"Project{i}"] = {
            "success": True,
            "directory": f"/fake/path/Project{i}",
            "message": "Project created successfully"
        }
    large_batch["summary"] = {
        "successful_count": 17,
        "total_count": 17,
        "success_rate": "17/17"
    }
    
    # This should display "17 of 17 projects created successfully"
    print("Expected result: 17 of 17 projects created successfully")
    if show_ui:
        print("Running UI test: show_batch_results(None, large_batch)")
        show_batch_results(None, large_batch)
    
    if show_ui:
        print("\nAll UI tests completed. Check that the dialogs displayed correct information.")
    else:
        print("\nTests completed in headless mode. Pass --show-ui to see the actual dialogs.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 