#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Runtime test for the Project Type Manager functionality
This script should be run with the main application loaded
"""

import sys
import os
import time

# Add the project directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox, QDialog
from PyQt6.QtCore import QTimer

# Updated import for the category management dialog
from app.dialogs.category_management_dialog import CategoryManagementDialog, manage_categories_dialog 

def test_project_type_manager(app):
    """Test the project type manager functionality with the running application"""
    from app.templates.project_type_manager import ProjectTypeManager
    
    # Check if we have the app instance
    if not app:
        print("ERROR: App instance not found")
        return False
    
    # Check if template manager is available
    if not hasattr(app, 'template_manager'):
        print("ERROR: Template manager not found in app")
        return False
    
    # Create a test category
    test_category = f"Test Category {int(time.time())}"
    print(f"Creating test category: {test_category}")
    
    # Get current categories
    template_manager = app.template_manager
    current_categories = template_manager.get_categories()
    print(f"Current categories before dialog: {current_categories}")
    
    # Test the category manager dialog
    print("Opening category manager dialog...")
    dialog_result = manage_categories_dialog(app)
    
    # Initialize updated_categories with current_categories to handle dialog cancellation
    updated_categories = current_categories 

    if dialog_result == QDialog.DialogCode.Accepted:
        print("Category management dialog was accepted. Changes should have been saved and propagated.")
        # To verify, we re-fetch categories from the source
        # A brief delay might be needed if category saving/notification is asynchronous
        # For this test, assume synchronous or fast enough for immediate re-fetch.
        QApplication.processEvents() # Allow signals to process
        updated_categories = template_manager.get_categories()
        print(f"Categories after dialog accepted: {updated_categories}")
    else:
        print("Category management dialog was canceled or failed.")
        # updated_categories remains as current_categories (no changes)
        print(f"Categories after dialog canceled: {updated_categories}")
    
    # Verify project_type_manager was initialized
    if hasattr(template_manager, 'project_type_manager') and template_manager.project_type_manager:
        print("Project type manager initialized correctly")
        
        # Add the test category directly
        result = template_manager.project_type_manager.create_project_type(test_category, "Video Editing - Standard")
        print(f"Creating category directly: {result}")
        
        # Get updated categories
        updated_categories = template_manager.get_categories()
        print(f"Updated categories from template manager: {updated_categories}")
        
        # Verify the test category was added
        if test_category in updated_categories:
            print(f"SUCCESS: Test category '{test_category}' was added correctly")
        else:
            print(f"ERROR: Test category '{test_category}' not found in updated categories")
            
        # Test saving to disk
        project_types_path = os.path.join(
            template_manager.paths["templates_dir"], 
            "project_types.json"
        )
        if os.path.exists(project_types_path):
            print(f"Project types file exists at: {project_types_path}")
            
            # Read the file
            import json
            try:
                with open(project_types_path, 'r') as f:
                    saved_types = json.load(f)
                print(f"Saved project types from file: {saved_types}")
                
                # Verify test category is in the file
                if test_category in saved_types:
                    print(f"SUCCESS: Test category saved to disk correctly")
                else:
                    print(f"ERROR: Test category not found in saved file")
            except Exception as e:
                print(f"ERROR reading project types file: {e}")
        else:
            print(f"ERROR: Project types file does not exist")
    else:
        print("ERROR: Project type manager not initialized in template manager")
    
    # Update the UI
    print("Refreshing UI...")
    if hasattr(app, 'template_gallery') and app.template_gallery:
        app.template_gallery.populate_gallery(force_refresh=True)
        print("Template gallery refreshed")
    
    print("Test completed")
    return True

if __name__ == "__main__":
    # Check if we're running in the context of the main application
    app = None
    
    # Try to get the app instance
    try:
        from PyQt6.QtWidgets import QApplication
        app_instance = QApplication.instance()
        if app_instance:
            # Try to find the main window
            for widget in app_instance.topLevelWidgets():
                if hasattr(widget, 'template_manager'):
                    app = widget
                    break
    except Exception as e:
        print(f"Error finding app instance: {e}")
    
    if app:
        print(f"Found app instance: {app}")
        test_project_type_manager(app)
    else:
        print("ERROR: Could not find app instance. Make sure the main application is running.")
        sys.exit(1) 