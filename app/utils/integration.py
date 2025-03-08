#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import tkinter as tk
from tkinter import ttk, BOTH, X, LEFT, RIGHT
from app.ui.color_scheme import colors

def integrate_enhanced_templates(app):
    """
    Main function to integrate enhanced template management functionality
    into the existing application.
    """
    # Import the enhanced template components
    from app.templates.enhanced_template_card import TemplateCardEnhanced
    from app.templates.template_folder_card import TemplateFolderCard
    from app.templates.add_template_canvas import AddTemplateCanvas
    from app.templates.enhanced_template_manager import TemplateManagerEnhanced
    from app.templates.template_category_manager import TemplateCategoryManager
    from app.templates.template_gallery_ui import create_template_gallery_enhanced, populate_enhanced_gallery
    
    # Clean up any existing filter or gallery elements from the old implementation
    if hasattr(app, 'filter_frame'):
        try:
            for widget in app.filter_frame.winfo_children():
                widget.destroy()
            app.filter_frame.destroy()
        except:
            pass  # Ignore errors if widgets are already destroyed
    
    # Clean up any old control frames
    if hasattr(app, 'bottom_controls_frame'):
        try:
            app.bottom_controls_frame.destroy()
        except:
            pass
    
    if hasattr(app, 'top_controls_frame'):
        try:
            app.top_controls_frame.destroy()
        except:
            pass
        
    # Initialize enhanced template manager components
    app.template_manager_enhanced = TemplateManagerEnhanced(app.template_manager)
    app.category_manager = TemplateCategoryManager(app.template_manager)
    
    # Replace the original filter_templates function
    original_filter_templates = app.filter_templates
    
    def enhanced_filter_templates(*args):
        """Enhanced version of filter_templates that uses our new components"""
        from app.templates.template_gallery_ui import filter_templates_enhanced, populate_enhanced_gallery
        
        # Get filtered templates
        filter_templates_enhanced(app)
        
        # Populate gallery with filtered templates
        populate_enhanced_gallery(app)
        
        # Update status
        search_term = app.search_box.get() if hasattr(app, 'search_box') else ""
        category = app.category_var.get() if hasattr(app, 'category_var') else "All"
        folder = app.folder_var.get() if hasattr(app, 'folder_var') else "All"
        
        status = f"Filtering templates: "
        if search_term:
            status += f"Search='{search_term}' "
        if category != "All":
            status += f"Category='{category}' "
        if folder != "All":
            status += f"Folder='{folder}' "
        
        if status == "Filtering templates: ":
            status = "Ready"
        
        if hasattr(app, 'status_var'):
            app.status_var.set(status)
    
    # Replace the filter_templates function
    app.filter_templates = enhanced_filter_templates
    
    # Create enhanced template gallery (will replace existing one)
    create_template_gallery_enhanced(app)
    
    # Schedule a gallery refresh after a short delay to ensure proper rendering
    app.root.after(100, lambda: populate_enhanced_gallery(app))
    app.root.after(500, lambda: populate_enhanced_gallery(app))  # Second refresh as backup


def patch_app_ui_run_import_dialog():
    """
    Patch the run_import_dialog function in app_ui.py to refresh the enhanced gallery
    after importing a template.
    """
    # Import original run_import_dialog
    from app.ui.app_ui import run_import_dialog as original_run_import_dialog
    
    def patched_run_import_dialog(app):
        """Patched version that refreshes the enhanced gallery"""
        # Call original function
        result = original_run_import_dialog(app)
        
        # Refresh enhanced gallery if template was imported successfully
        if result and hasattr(app, 'template_manager_enhanced'):
            from app.templates.template_gallery_ui import populate_enhanced_gallery
            populate_enhanced_gallery(app)
        
        return result
    
    # Replace the original function in the module
    import app.ui.app_ui as app_ui
    app_ui.run_import_dialog = patched_run_import_dialog
    
    return patched_run_import_dialog


def modify_templates_py():
    """
    Patch the functions in templates.py to use enhanced template management
    """
    from app.templates.templates import populate_template_gallery as original_populate_template_gallery
    
    def patched_populate_template_gallery(app):
        """Patched version that uses enhanced gallery"""
        if hasattr(app, 'template_manager_enhanced'):
            from app.templates.template_gallery_ui import populate_enhanced_gallery
            populate_enhanced_gallery(app)
        else:
            original_populate_template_gallery(app)
    
    # Replace the original function in the module
    import app.templates.templates as templates
    templates.populate_template_gallery = patched_populate_template_gallery
    
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
        
        # If we have enhanced templates, update "Recent" folder
        if hasattr(app, 'template_manager_enhanced') and template:
            template_name = template.get("name", "")
            if template_name:
                # Add to Recent folder if not already there
                if "Recent" in app.template_manager_enhanced.folders:
                    recent_folder = app.template_manager_enhanced.folders["Recent"]
                    
                    # Remove if already in the list (to move it to the top)
                    if template_name in recent_folder:
                        recent_folder.remove(template_name)
                    
                    # Add to the top of the list
                    recent_folder.insert(0, template_name)
                    
                    # Limit to 10 recent templates
                    app.template_manager_enhanced.folders["Recent"] = recent_folder[:10]
                    
                    # Save changes
                    app.template_manager_enhanced.save_folders()
    
    # Replace the original function in the module
    import app.templates.templates as templates
    templates.select_template_from_gallery = patched_select_template
    
    return patched_select_template


def extend_create_ui():
    """
    Function to extend the create_ui function in app_ui.py to integrate
    enhanced template management at the end of UI creation
    """
    def create_ui_extension(app):
        """This will be called at the end of create_ui"""
        # Apply all the patches
        patch_app_ui_run_import_dialog()
        modify_templates_py()
        patch_select_template_function()
        
        # Integrate enhanced templates
        integrate_enhanced_templates(app)
    
    return create_ui_extension


def patch_app_file():
    """
    Create a modified version of app_ui.py that includes the enhanced template management
    """
    # Get the original create_ui function
    from app.ui.app_ui import create_ui as original_create_ui
    
    def enhanced_create_ui(app):
        """Enhanced version of create_ui that adds template management"""
        # Call the original function
        original_create_ui(app)
        
        # Add our enhancements
        create_ui_extension = extend_create_ui()
        create_ui_extension(app)
    
    # We would typically replace the function in the module here
    # But for now, we'll just return the enhanced function
    return enhanced_create_ui
