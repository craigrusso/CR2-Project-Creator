#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import sys

# Using PyQt for the UI framework
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from app.ui.color_scheme_pyqt import colors
from app.ui.ui_components_pyqt import SearchBox
from app.templates.components import TemplateCard
UI_FRAMEWORK = 'pyqt'

def integrate_enhanced_templates(app):
    """
    Integrate enhanced template system.
    
    This function is kept for backward compatibility but now uses the
    unified template management system.
    """
    # Replace the original filter_templates function
    original_filter_templates = app.filter_templates
    
    def enhanced_filter_templates(*args):
        """Enhanced filter function that handles folder filtering"""
        # Call the original filter function for project types, etc.
        original_filter_templates(*args)
        
        # Apply folder filter if selected
        folder = app.folder_var.get() if hasattr(app, 'folder_var') else "All"
        if folder != "All" and folder in app.template_manager.folders:
            # Handle folder filtering
            from app.templates.template_gallery_ui import populate_enhanced_gallery
            populate_enhanced_gallery(app)
    
    # Replace the filter function
    app.filter_templates = enhanced_filter_templates
    
    # Load the enhanced template gallery UI
    from app.templates.template_gallery_ui import create_template_gallery_enhanced
    app.root.after(100, lambda: create_template_gallery_enhanced(app))
    
    # Return the enhanced filter function
    return enhanced_filter_templates


def patch_app_ui_run_import_dialog():
    """
    Patch the app_ui.py run_import_dialog function to refresh enhanced gallery
    """
    def patched_run_import_dialog(app):
        """Patched version of run_import_dialog that updates the enhanced gallery"""
        from app.ui.app_ui import run_import_dialog as original_run_import_dialog
        
        # Call the original function
        result = original_run_import_dialog(app)
        
        # If a template was imported, refresh the enhanced gallery
        if result:
            # If template was imported successfully, refresh the enhanced gallery
            from app.templates.template_gallery_ui import populate_enhanced_gallery
            populate_enhanced_gallery(app)
        
        return result
    
    return patched_run_import_dialog


def modify_templates_py():
    """
    Modify the templates.py module to use enhanced templates
    """
    def patched_populate_template_gallery(app):
        """Patched version that uses enhanced template gallery"""
        from app.templates.template_gallery_ui import populate_enhanced_gallery
        return populate_enhanced_gallery(app)
    
    return patched_populate_template_gallery


def patch_select_template_function():
    """
    Patch the select_template_from_gallery function to update folders when a template is selected
    """
    from app.templates.templates import select_template_from_gallery as original_select_template
    
    def patched_select_template(app, template):
        """Patched version that updates folder information"""
        # Call original function
        original_select_template(app, template)
        
        # Update "Recent" folder if template is valid
        if hasattr(app, 'template_manager') and template:
            try:
                template_name = template.get("name", "")
                if template_name:
                    # Add to "Recent" folder if it exists
                    if "Recent" in app.template_manager.folders:
                        recent_folder = app.template_manager.folders["Recent"]
                        
                        # First remove template if it's already in the list
                        if template_name in recent_folder:
                            recent_folder.remove(template_name)
                        
                        # Add to the front of the list
                        recent_folder.insert(0, template_name)
                        
                        # Keep only the most recent N templates
                        app.template_manager.folders["Recent"] = recent_folder[:10]
                        
                        # Save updated folders
                        app.template_manager.save_folders()
            except Exception as e:
                print(f"Error adding template to recent: {e}")
    
    # Replace the original function in the module
    import app.templates.templates as templates
    templates.select_template_from_gallery = patched_select_template
    
    return patched_select_template


def extend_create_ui():
    """
    Extend the create_ui function to add enhanced template gallery
    """
    def create_ui_extension(app):
        """Function to extend the UI with enhanced template features"""
        # Load enhanced template gallery
        from app.templates.template_gallery_ui import create_template_gallery_enhanced
        create_template_gallery_enhanced(app)
    
    return create_ui_extension


def patch_app_file():
    """
    Patch the app.py file to use enhanced templates
    """
    def enhanced_create_ui(app):
        """Enhanced version of create_ui that uses template gallery"""
        # Load original UI
        from app.ui.app_ui import create_ui as original_create_ui
        original_create_ui(app)
        
        # Add enhanced template gallery
        from app.templates.template_gallery_ui import create_template_gallery_enhanced
        create_template_gallery_enhanced(app)
    
    return enhanced_create_ui
