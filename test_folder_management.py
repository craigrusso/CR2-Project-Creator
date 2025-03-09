#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Test script for folder management system
This script tests the unified folder management system to ensure it works correctly.
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox

# Ensure the app directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.app_module import ProjectCreatorApp
from app.templates.template_manager_migration import TemplateManagerMigration
from app.core.app_config import setup_dpi_awareness

def run_folder_tests(app):
    """Run tests on the folder management system"""
    results = []
    
    # Test 1: Create a new folder
    test_folder_name = "Test_Folder_123"
    print(f"Test 1: Creating folder '{test_folder_name}'")
    
    # Delete the folder if it already exists
    if test_folder_name in app.template_manager.folders:
        app.template_manager.delete_folder(test_folder_name)
    
    # Create the folder
    success = app.template_manager.create_folder(test_folder_name)
    results.append(("Create folder", success))
    
    # Verify the folder exists
    folder_exists = test_folder_name in app.template_manager.folders
    results.append(("Folder exists after creation", folder_exists))
    
    # Test 2: Rename the folder
    new_folder_name = "Renamed_Test_Folder"
    print(f"Test 2: Renaming folder '{test_folder_name}' to '{new_folder_name}'")
    
    # Delete the target folder if it already exists
    if new_folder_name in app.template_manager.folders:
        app.template_manager.delete_folder(new_folder_name)
    
    # Rename the folder
    success = app.template_manager.rename_folder(test_folder_name, new_folder_name)
    results.append(("Rename folder", success))
    
    # Verify the folder was renamed
    old_folder_gone = test_folder_name not in app.template_manager.folders
    new_folder_exists = new_folder_name in app.template_manager.folders
    results.append(("Old folder gone after rename", old_folder_gone))
    results.append(("New folder exists after rename", new_folder_exists))
    
    # Test 3: Delete the folder
    print(f"Test 3: Deleting folder '{new_folder_name}'")
    
    # Delete the folder
    success = app.template_manager.delete_folder(new_folder_name)
    results.append(("Delete folder", success))
    
    # Verify the folder was deleted
    folder_gone = new_folder_name not in app.template_manager.folders
    results.append(("Folder gone after deletion", folder_gone))
    
    # Test 4: UI dropdown update
    print("Test 4: Testing UI dropdown update")
    
    # Create a folder
    ui_test_folder = "UI_Test_Folder"
    if ui_test_folder in app.template_manager.folders:
        app.template_manager.delete_folder(ui_test_folder)
    
    app.template_manager.create_folder(ui_test_folder)
    
    # Update the UI dropdown
    ui_updated = app.template_manager.update_ui_folder_dropdown(app)
    results.append(("UI dropdown updated", ui_updated))
    
    # Clean up
    app.template_manager.delete_folder(ui_test_folder)
    
    # Print results
    print("\nTest Results:")
    all_passed = True
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        if not result:
            all_passed = False
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    return all_passed

def main():
    """Main function"""
    # Setup
    setup_dpi_awareness()
    
    # Create root window
    root = tk.Tk()
    root.title("Folder Management Test")
    root.geometry("400x300")
    
    # Create app instance
    app = ProjectCreatorApp(root)
    
    # Run migration
    TemplateManagerMigration.apply_migration(app)
    
    # Add a label to show we're running tests
    label = tk.Label(root, text="Running folder management tests...", pady=20)
    label.pack()
    
    # Run tests after a short delay
    root.after(500, lambda: run_tests_and_show_results(root, app))
    
    # Start the main loop
    root.mainloop()

def run_tests_and_show_results(root, app):
    """Run the tests and show results in the UI"""
    try:
        success = run_folder_tests(app)
        message = "All folder management tests passed!" if success else "Some tests failed. See console for details."
        messagebox.showinfo("Test Results", message)
    except Exception as e:
        messagebox.showerror("Test Error", f"An error occurred during testing: {str(e)}")
    finally:
        root.quit()

if __name__ == "__main__":
    main() 