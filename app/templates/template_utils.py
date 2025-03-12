#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import platform
from PyQt5.QtWidgets import QFileDialog, QMessageBox

def get_template_file(app):
    """Open file dialog to select a template file or directory"""
    try:
        # Use PyQt file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            app,
            "Select Template File",
            "",
            "All Files (*);;Project Files (*.prproj *.aep *.aepx *.psd *.ai)"
        )
        
        if file_path:
            app.template_file_path = file_path
            # Create a template in the recent templates
            if hasattr(app, 'add_to_recent_templates'):
                app.add_to_recent_templates(file_path)
            
            return file_path
        return None
    except Exception as e:
        print(f"Error selecting template file: {e}")
        return None

def clear_template_file(app):
    """Clear the current template file selection"""
    try:
        app.template_file_path = ""
        
        # Update status if available
        if hasattr(app, 'show_status_message'):
            app.show_status_message("Template file cleared")
    except Exception as e:
        print(f"Error clearing template file: {e}")

def clear_structure_template(app):
    """Clear the current structure template selection"""
    try:
        if hasattr(app, 'current_template'):
            app.current_template = None
        if hasattr(app, 'selected_structure_template'):
            app.selected_structure_template = None
            
        # Update status if available
        if hasattr(app, 'show_status_message'):
            app.show_status_message("Structure template cleared")
    except Exception as e:
        print(f"Error clearing structure template: {e}")

def rename_current_template(app):
    """Rename the current template"""
    # This is a stub function to maintain compatibility
    pass

def rename_template_file(app):
    """Rename the template file displayed in the UI"""
    # This is a stub function to maintain compatibility
    pass 