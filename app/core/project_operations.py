#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import platform
import datetime
import re
import sys
import json
import time
import threading
import shutil

# Using PyQt for the UI framework
from PyQt6.QtWidgets import QMessageBox
from app.ui.color_scheme_pyqt import colors
UI_FRAMEWORK = 'pyqt'

from app.utils.utils import (
    open_folder, open_in_explorer, parse_project_names, 
    save_recent_projects, load_recent_projects,
    save_recent_templates, load_recent_templates
)


def template_has_structure(template):
    """
    Check if a template has a valid structure
    
    Args:
        template: Template dictionary or object
        
    Returns:
        bool: True if template has a valid structure, False otherwise
    """
    if not template:
        return False
        
    # Check for structure field
    if isinstance(template, dict) and 'structure' in template:
        structure = template['structure']
        
        # Check if structure is valid and not empty
        if isinstance(structure, dict) and 'folders' in structure and structure['folders']:
            return True
        elif isinstance(structure, list) and structure:
            return True
            
    return False


def create_project(app, project_name, output_directory=None):
    """Create a new project with the given name"""
    # Validate project name
    if not project_name:
        error_msg = "Please enter a project name"
        app.show_status_message(error_msg)
        return False
        
    # Validate template selection
    if not app.selected_template:
        error_msg = "Please select a template"
        app.show_status_message(error_msg)
        return False
    
    # Check if the template has a structure and prevent project creation if not
    if not template_has_structure(app.selected_template):
        error_msg = "This template has no folder structure defined. Projects require a folder structure to be created."
        app.show_status_message(error_msg, message_type="error")
        return False
            
    # Get output directory from UI if not provided
    if not output_directory:
        output_directory = app.output_directory_input.text()
    
    # Save output directory in config
    app.config.set('output_directory', output_directory)
    app.config.save()
    
    # Create project directory
    project_path = os.path.join(output_directory, project_name)
    try:
        os.makedirs(project_path, exist_ok=True)
    except Exception as e:
        error_msg = f"Failed to create project directory: {str(e)}"
        app.show_status_message(error_msg)
        print(f"ERROR: {error_msg}")
        return False
    
    # Get structure name
    if UI_FRAMEWORK == 'pyqt':
        structure_name = app.structure_combo.currentText() if hasattr(app, 'structure_combo') else "Default"
    else:
        structure_name = app.structure_var.get() if hasattr(app, 'structure_var') else "Default"
    
    # If the selected template has a structure_name, use that instead
    if isinstance(app.selected_template, dict) and 'structure_name' in app.selected_template:
        structure_name = app.selected_template['structure_name']
    
    if structure_name == "Default":
        structure_name = None
    
    # Use the selected template
    template_path = app.selected_template.get('path') if isinstance(app.selected_template, dict) and 'path' in app.selected_template else None
    
    # For compatibility, set template_file_path to the selected template's path
    app.template_file_path = template_path
    
    if template_path:
        add_to_recent_templates(app, template_path)
    
    # Create the project using the selected output directory
    result, project_path_or_info = app.project_builder.create_project(
        project_name=project_name,
        output_dir=output_directory,
        template_file=template_path,
        project_type="Standard", 
        structure_name=structure_name,
        create_backup=True
    )
    
    # We should no longer have no_structure flag since we're preventing those projects
    if result:
        # Use project_path directly if not a dict
        if isinstance(project_path_or_info, dict):
            project_path = project_path_or_info.get('project_dir')
        else:
            project_path = project_path_or_info
            
        # Show success message
        success_message = f"Project '{project_name}' created successfully at\n{project_path}"
        QMessageBox.information(app, "Success", success_message)
        
        # Add to recent projects
        add_to_recent_projects(app, project_name, project_path)
        
        # Update recent projects menu
        app.update_recent_menu()
        
        # Reset or clear project name for next project
        if hasattr(app, 'project_name_input'):
            app.project_name_input.clear()
        
        # Show path in status bar
        app.show_status_message(f"Project created at: {project_path}")
    else:
        # Error case
        error_message = f"Failed to create project '{project_name}': {project_path_or_info}"
        QMessageBox.critical(app, "Error", error_message)
        print(f"ERROR: {error_message}")
        app.show_status_message(f"Error creating project: {project_path_or_info}", message_type="error")
    
    return result


def handle_batch_create(app, project_names_text):
    """
    Handle the batch creation of projects.
    
    Args:
        app: The main application instance
        project_names_text: Text containing project names (one per line)
        
    Returns:
        dict: Results of batch creation
    """
    # Parse project names (one per line)
    project_names = [name.strip() for name in project_names_text.split('\n') if name.strip()]
    
    has_selected_template = hasattr(app, 'selected_template') and bool(app.selected_template)
    
    if has_selected_template:
        pass
    
    has_template_gallery = hasattr(app, 'template_gallery') and bool(app.template_gallery)
    
    # Get the selected template
    template_name = None
    template_data = None

    # PRIORITY 1: Use the TemplateGallery's unified selection access via get_primary_selected_template
    if hasattr(app, 'template_gallery') and hasattr(app.template_gallery, 'get_primary_selected_template'):
        try:
            selected_template_from_gallery = app.template_gallery.get_primary_selected_template()
            if selected_template_from_gallery:
                template_name = selected_template_from_gallery.get('name')
                
                # Load the complete template data with files array from template manager
                if hasattr(app, 'template_manager') and hasattr(app.template_manager, 'template_io'):
                    complete_template_data = app.template_manager.template_io.get_template(template_name)
                    if complete_template_data:
                        template_data = complete_template_data
                        template_path = None  # For templates loaded from manager
                    else:
                        template_data = selected_template_from_gallery
                        template_path = None
                else:
                    template_data = selected_template_from_gallery
                    template_path = None
            else:
                template_data = None
                template_path = None
        except Exception as e:
            print(f"Error (handle_batch_create) accessing gallery.get_primary_selected_template: {e}")
            template_data = None
            template_path = None

    # Fallback 1: Legacy direct file path
    if not template_data and hasattr(app, 'template_file_path') and app.template_file_path:
        template_path = app.template_file_path
        try:
            with open(template_path, 'r') as f:
                template_data = json.load(f)
            template_name = template_data.get('name', os.path.basename(template_path))
        except Exception as e:
            print(f"ERROR (handle_batch_create) loading template file: {e}")
            return {"error": f"Error loading template file: {e}"}
    
    # Fallback 2: Legacy direct attribute on app (app.selected_template)
    if not template_data and hasattr(app, 'selected_template') and app.selected_template:
        template_data = app.selected_template
        template_name = template_data.get('name')
    
    # Fallback 3: Gallery's older get_selected_template (less specific than get_primary_selected_template)
    if not template_data and hasattr(app, 'template_gallery') and app.template_gallery and hasattr(app.template_gallery, 'get_selected_template'):
        try:
            template_info = app.template_gallery.get_selected_template()
            if template_info:
                template_data = template_info
                template_name = template_info.get('name')
        except Exception as e:
            print(f"Error (handle_batch_create) checking gallery.get_selected_template: {e}")

    if not template_name or not template_data:
        print("ERROR: No template selected!")
        return {"error": "No template selected. Please select a template first."}

    # Check if the template has a structure
    if not template_has_structure(template_data):
        error_msg = "This template has no folder structure defined. Projects require a folder structure to be created."
        app.show_status_message(error_msg, message_type="error")
        return {"error": "Template has no structure defined", "successful_count": 0, "total_count": len(project_names)}
    
    print(f"Using gallery template without file path: {template_name}")
    
    # Get the output directory
    output_dir = None
    if hasattr(app, 'get_current_output_dir') and callable(app.get_current_output_dir):
        output_dir = app.get_current_output_dir(use_fallbacks=False)
    elif hasattr(app, 'output_directory') and app.output_directory:
        output_dir = app.output_directory
    elif hasattr(app, 'default_output_path'):
        output_dir = app.default_output_path
        
    # If no output directory is available, always prompt the user to select one
    if not output_dir:
        # User needs to select an output directory
        if hasattr(app, 'get_output_dir') and callable(app.get_output_dir):
            output_dir = app.get_output_dir()
            
            # If user cancelled the selection, abort the operation
            if not output_dir:
                app.show_status_message("Project creation cancelled - no output location selected", message_type="warning")
                return {"error": "Project creation cancelled - no output location selected", "successful_count": 0, "total_count": 0}
        else:
            # Critical error - no way to get an output directory
            error_msg = "Cannot create projects - no method available to select output directory"
            app.show_status_message(error_msg, message_type="error")
            return {"error": error_msg, "successful_count": 0, "total_count": 0}
    
    # Create debug output
    structure_name = f"Template_{template_name}" if template_name else None
    
    # Execute the batch creation 
    try:
        return app.project_builder.batch_create_projects(
            project_names=project_names,
            template_name=template_name,  # Use actual template name, not 'gallery_template'
            structure_name=structure_name,
            output_dir=output_dir,
            template_data=template_data
        )
    except Exception as e:
        print(f"Error in batch creation: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Error in batch creation: {str(e)}"}


def batch_creation_complete(app, results, selected_template=None):
    """Handle batch creation completion"""
    # Store results for display
    app.batch_results = results
    
    # Count successes and failures
    successes = sum(1 for _, success, _ in results if success)
    failures = len(results) - successes
    
    # Add successful projects to recent projects
    recent_projects = []
    for name, success, path in results:
        if success:
            # Add path to recent projects
            recent_projects.append({"name": name, "path": path})
    
    # Update recent projects (no more than 10)
    if recent_projects:
        app.recent_projects = recent_projects + app.recent_projects
        app.recent_projects = app.recent_projects[:10]
        save_recent_projects(app.recent_projects)
    
    # Update recent templates
    template_file = None
    
    # Check if there's a direct path available
    if hasattr(app, 'template_file_path') and app.template_file_path:
        template_file = app.template_file_path
    
    # If we have a gallery template, add it to recent templates
    if selected_template and isinstance(selected_template, dict) and 'name' in selected_template:
        # Add the gallery template to recent templates - use the local function
        add_to_recent_templates(app, selected_template)
    elif template_file:
        # Add the direct template file to recent templates
        add_to_recent_templates(app, template_file)
    
    # Show status message
    app.show_status_message(f"Batch creation complete: {successes} projects created", message_type="success")


def add_to_recent_projects(app, project_name, project_path, max_recent=10):
    """Add a project to the recent projects list"""
    # Load recent projects
    recent_projects = load_recent_projects()
    
    # Create new project entry
    project = {
        'name': project_name,
        'path': project_path,
        'timestamp': f"{datetime.datetime.now().isoformat()}"
    }
    
    # Make sure recent_projects exists
    if not hasattr(app, 'recent_projects') or app.recent_projects is None:
        app.recent_projects = []
    
    # Add to recent projects, avoid duplicates
    app.recent_projects = [p for p in app.recent_projects if p['path'] != project_path]
    app.recent_projects.insert(0, project)  # Add to start of list
    
    # Limit to max_recent items
    app.recent_projects = app.recent_projects[:max_recent]
    
    # Save to file
    save_recent_projects(app.recent_projects)
    
    # Update menu
    app.update_recent_menu()


def add_to_recent_templates(app, template_file_path, max_recent=5, preserve_order=False):
    """Add a template file to recent templates list
    
    Args:
        app: The application instance
        template_file_path: Path to template file or dict with path key
        max_recent: Maximum number of templates to keep in the list
        preserve_order: If True, will add the template without reordering the list
    """
    # Handle both string paths and dictionary templates
    if isinstance(template_file_path, dict):
        path = template_file_path.get('path', '')
    else:
        path = template_file_path
    
    if not path or not os.path.exists(path):
        return
    
    # Create template entry
    template = {
        'path': path,
        'name': os.path.basename(path),
        'timestamp': f"{datetime.datetime.now().isoformat()}"
    }
    
    # Make sure recent_templates exists
    if not hasattr(app, 'recent_templates') or app.recent_templates is None:
        app.recent_templates = []
    
    # Check for duplicates and whether the template is already in the list
    template_exists = False
    filtered_templates = []
    
    for t in app.recent_templates:
        if (isinstance(t, dict) and t.get('path') == path) or t == path:
            template_exists = True
            # Skip this template as we'll add it based on preserve_order
            continue
        filtered_templates.append(t)
    
    # Create new template list based on whether to preserve order
    if preserve_order and template_exists:
        # Just update the template in its current position
        # This is a bit complex - find where it was and insert there
        position = next((i for i, t in enumerate(app.recent_templates) 
                        if (isinstance(t, dict) and t.get('path') == path) or t == path), 0)
        
        if position == 0:
            app.recent_templates = [template] + filtered_templates
        elif position >= len(filtered_templates):
            app.recent_templates = filtered_templates + [template]
        else:
            app.recent_templates = filtered_templates[:position] + [template] + filtered_templates[position:]
    else:
        # Add to the beginning (default behavior)
        app.recent_templates = [template] + filtered_templates
    
    # Limit to max items
    app.recent_templates = app.recent_templates[:max_recent]
    
    # Save to file
    save_recent_templates(app.recent_templates)
    
    # Update UI if requested
    if hasattr(app, 'update_recent_templates_menu'):
        app.update_recent_templates_menu()


def open_recent_project(app, project):
    """Open a recent project folder"""
    path = project.get("path", "")
    if path and os.path.isdir(path):
        open_folder(path)
        app.show_status_message(f"Opened project folder: {os.path.basename(path)}")
    else:
        app.show_status_message(f"Project folder not found: {path}", message_type="error")


def use_recent_template(app, template):
    """Use a recently used template file"""
    path = template.get("path", "")
    
    if not path or not os.path.isfile(path):
        app.show_status_message(f"Template file not found: {path}", message_type="error")
        
        # Remove invalid template from recents
        remove_from_recent_templates(app, template)
        return False
    
    try:
        # Get display filename
        name = os.path.basename(path)
        
        # Set as current template
        app.template_file_path = path
        app.selected_template_file = path  # Set selected_template_file for highlighting
        
        # Update UI
        if hasattr(app, 'template_file_info'):
            app.template_file_info.config(text=name)
            
        # Enable rename button
        if hasattr(app, 'rename_template_file_btn'):
            app.rename_template_file_btn.config(state="normal")
            
        # Update status
        if hasattr(app, 'status_var'):
            app.show_status_message(f"Selected template file: {name}")
            
        # Apply highlighting BEFORE updating the gallery
        if hasattr(app, '_highlight_in_gallery'):
            app._highlight_in_gallery(path)
            
        # Update card highlighting - re-add to recents so this one goes to top
        add_to_recent_templates(app, path, preserve_order=False)
        
        return True
    except Exception as e:
        app.show_status_message("Invalid template format", message_type="error")
        return False


def remove_from_recent_templates(app, template):
    """Remove a template from the recent templates list"""
    # Handle both string paths and dictionary templates
    if isinstance(template, str):
        path = template
    elif isinstance(template, dict):
        path = template.get('path', '')
    else:
        return  # Invalid format
    
    # Remove from list
    filtered_templates = []
    for t in app.recent_templates:
        if isinstance(t, dict) and t.get('path') == path:
            continue  # Skip this template
        elif t == path:
            continue  # Skip this template
        filtered_templates.append(t)
    
    app.recent_templates = filtered_templates
    
    # Save to file
    save_recent_templates(app.recent_templates)
    
    # Update UI
    app.update_recent_templates_gallery()
    app.update_recent_templates_menu()


def clear_recent_projects(app):
    """Clear the list of recent projects"""
    app.recent_projects = []
    save_recent_projects(app.recent_projects)
    app.update_recent_menu()
    
    # Update status
    app.status_var.set("Recent projects cleared")


def clear_recent_templates(app):
    """Clear the list of recent templates"""
    app.recent_templates = []
    save_recent_templates(app.recent_templates)
    try:
        app.update_recent_templates_gallery()
    except Exception as e:
        print(f"Error updating templates gallery: {e}")
    
    # Update status
    app.status_var.set("Recent templates cleared")


def update_card_highlighting(card, template_path):
    """Update the highlighting of a template card based on selection state"""
    # Define a custom blue highlight color
    blue_highlight = "#4682B4"  # Steel Blue
    # Define dark text for better contrast on blue
    dark_text = "#FFFFFF"  # White text for better visibility on blue
    
    if hasattr(card, 'template_path') and card.template_path == template_path:
        # Highlight the entire card with blue background
        card.configure(bg=blue_highlight)
        
        # Highlight all parts of the card with blue background
        if hasattr(card, 'icon_label'):
            card.icon_label.configure(bg=blue_highlight, fg=dark_text)
            
        # Highlight all parts of the card with blue
        if hasattr(card, 'info_frame'):
            card.info_frame.configure(bg=blue_highlight)
            # Also highlight all widgets inside info_frame
            for widget in card.info_frame.winfo_children():
                widget.configure(bg=blue_highlight, fg=dark_text)
                
        # Special handling for name and path labels if they exist
        if hasattr(card, 'name_label'):
            card.name_label.configure(fg=dark_text)
        if hasattr(card, 'path_label'):
            card.path_label.configure(fg=dark_text)
            
        # Make sure remove button stays visible on highlighted cards
        if hasattr(card, 'remove_btn'):
            card.remove_btn.configure(bg=blue_highlight, fg=dark_text)
    else:
        # Reset to default colors
        card.configure(bg=colors["bg"])
        
        # Reset icon label
        if hasattr(card, 'icon_label'):
            card.icon_label.configure(bg=colors["bg"], fg=colors["text"])
            
        # Reset info frame and all its children
        if hasattr(card, 'info_frame'):
            card.info_frame.configure(bg=colors["bg"])
            for widget in card.info_frame.winfo_children():
                widget.configure(bg=colors["bg"], fg=colors["text"])
            # Reset secondary labels
            if hasattr(card, 'path_label'):
                card.path_label.configure(fg=colors["secondary_text"])
            if hasattr(card, 'category_label'):
                card.category_label.configure(fg=colors["secondary_text"])
                
        # Reset remove button if it exists
        if hasattr(card, 'remove_btn'):
            card.remove_btn.configure(bg=colors["bg"], fg="white")


def get_structure_template(app):
    """Get the selected structure template"""
    # Get the structure template
    structure_name = app.structure_combo.currentText() if hasattr(app, 'structure_combo') else "Default"
    return structure_name
