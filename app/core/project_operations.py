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
from PyQt5.QtWidgets import QMessageBox
from app.ui.color_scheme_pyqt import colors
UI_FRAMEWORK = 'pyqt'

from app.utils.utils import (
    open_folder, open_in_explorer, parse_project_names, 
    save_recent_projects, load_recent_projects,
    save_recent_templates, load_recent_templates
)


def create_project(app):
    """Create a new project from the current settings"""
    # Validate project name
    project_name_val = app.project_name_input.text().strip() if hasattr(app, 'project_name_input') else ""
    
    if not project_name_val:
        app.show_status_message("Please enter a project name", message_type="error")
        return
    
    # Check for selected template - try multiple locations
    selected_template = None
    
    # Method 1: Check app.selected_template
    if hasattr(app, 'selected_template') and app.selected_template:
        selected_template = app.selected_template
        print(f"Using template from app.selected_template: {selected_template}")
    
    # Method 2: Check gallery's selected template
    if not selected_template and hasattr(app, 'template_gallery'):
        if hasattr(app.template_gallery, 'get_selected_template'):
            selected_template = app.template_gallery.get_selected_template()
            if selected_template:
                print(f"Using template from gallery: {selected_template}")
    
    # Method 3: Check template_file_path as fallback
    if not selected_template and hasattr(app, 'template_file_path') and app.template_file_path:
        template_path = app.template_file_path
        print(f"Using template from template_file_path: {template_path}")
        
        # Create a simple template object
        selected_template = {
            'name': os.path.basename(template_path),
            'path': template_path,
            'type': 'file' if os.path.isfile(template_path) else 'directory'
        }
    
    if not selected_template:
        app.show_status_message("Please select a template from the gallery", message_type="error")
        return
    
    # Get output directory
    output_dir = app.get_current_output_dir() if hasattr(app, 'get_current_output_dir') else app.root_path
    
    # If no output directory is set, prompt the user to select one
    if not output_dir:
        app.show_status_message("Please select an output location", message_type="warning")
        
        # Prompt user to select a location
        output_dir = app.get_output_dir()
        
        # If user still hasn't selected a location, abort
        if not output_dir:
            app.show_status_message("Please select an output location", message_type="error")
            return
    
    # Ensure the output directory is saved in the config
    if hasattr(app, 'config'):
        app.config["last_output_dir"] = output_dir
        if hasattr(app, 'save_config'):
            app.save_config()
        elif 'save_config' in globals():
            save_config(app.config)
    
    # Get project name
    project_name = project_name_val
    
    # Get structure name
    if UI_FRAMEWORK == 'pyqt':
        structure_name = app.structure_combo.currentText() if hasattr(app, 'structure_combo') else "Default"
    else:
        structure_name = app.structure_var.get() if hasattr(app, 'structure_var') else "Default"
    
    # If the selected template has a structure_name, use that instead
    if isinstance(selected_template, dict) and 'structure_name' in selected_template:
        structure_name = selected_template['structure_name']
        print(f"Using template's structure_name: {structure_name}")
    
    if structure_name == "Default":
        structure_name = None
    
    # Use the selected template
    template_path = selected_template.get('path') if isinstance(selected_template, dict) and 'path' in selected_template else None
    
    # For compatibility, set template_file_path to the selected template's path
    app.template_file_path = template_path
    
    # Add to recent templates if successful
    if template_path:
        add_to_recent_templates(app, template_path)
    
    # Create the project
    result, project_path = app.project_builder.create_project(
        project_name=project_name,
        output_dir=output_dir,
        template_file=template_path,
        project_type="Standard", 
        structure_name=structure_name,
        create_backup=True
    )
    
    if result:
        # Show success message
        success_message = f"Project '{project_name}' created successfully at\n{output_dir}"
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
        error_message = f"Failed to create project '{project_name}': {project_path}"
        QMessageBox.critical(app, "Error", error_message)
        app.show_status_message(f"Error creating project: {project_path}", message_type="error")


def handle_batch_create(app, project_names_text):
    """Handle batch project creation"""
    # Get project names from text
    project_names = parse_project_names(project_names_text)
    
    # Validate inputs
    if not project_names:
        app.show_status_message("No valid project names found", message_type="error")
        return
    
    # Debug existing application state
    print("====== BATCH CREATE DEBUG INFO ======")
    print(f"Project names: {project_names}")
    print(f"Has app.template_file_path: {hasattr(app, 'template_file_path')}")
    if hasattr(app, 'template_file_path'):
        print(f"  Value: {app.template_file_path}")
    
    print(f"Has app.selected_template: {hasattr(app, 'selected_template')}")
    if hasattr(app, 'selected_template'):
        print(f"  Value: {app.selected_template}")
        if isinstance(app.selected_template, dict) and 'name' in app.selected_template:
            print(f"  Template name: {app.selected_template['name']}")
    
    print(f"Has template_gallery: {hasattr(app, 'template_gallery')}")
    if hasattr(app, 'template_gallery') and hasattr(app.template_gallery, 'get_selected_template'):
        try:
            gallery_template = app.template_gallery.get_selected_template()
            print(f"  Gallery selected template: {gallery_template}")
        except Exception as e:
            print(f"  Error getting gallery template: {e}")
    print("======================================")
    
    # Get template - check multiple locations
    template_file = None
    selected_template = None
    structure_name = None
    
    # Method 1: Check if there's a selected template from gallery or app object first
    if hasattr(app, 'selected_template') and app.selected_template:
        selected_template = app.selected_template
        print(f"Using template from app.selected_template: {selected_template}")
        
        # If the selected template has a structure_name, use that
        if isinstance(selected_template, dict) and 'structure_name' in selected_template:
            structure_name = selected_template['structure_name']
            print(f"Using structure_name from selected template: {structure_name}")
        
        # If the selected template has a path property, use that
        if isinstance(selected_template, dict) and 'path' in selected_template and selected_template['path']:
            template_file = selected_template['path']
            print(f"Using path from selected template: {template_file}")
        else:
            # Otherwise, we'll use the structure_name for template creation
            print(f"Using gallery template without file path: {selected_template.get('name', 'Unknown') if isinstance(selected_template, dict) else selected_template}")
            # Set a dummy template path to pass validation
            template_file = "gallery_template"
    
    # Method 2: Check if there's a direct template file path as fallback
    elif hasattr(app, 'template_file_path') and app.template_file_path:
        template_file = app.template_file_path
        print(f"Using template file path: {template_file}")
    
    # Method 3: Check if there's a template gallery with a selected template
    elif hasattr(app, 'template_gallery') and hasattr(app.template_gallery, 'get_selected_template'):
        try:
            selected_template = app.template_gallery.get_selected_template()
            if selected_template:
                app.selected_template = selected_template  # Make sure it's set on app too
                print(f"Retrieved template from gallery: {selected_template}")
                
                # If the selected template has a structure_name, use that
                if isinstance(selected_template, dict) and 'structure_name' in selected_template:
                    structure_name = selected_template['structure_name']
                    print(f"Using structure_name from retrieved template: {structure_name}")
                
                # Set a dummy template path to pass validation
                template_file = "gallery_template"
        except Exception as e:
            print(f"Error getting selected template from gallery: {e}")
    
    # Validate that we have some form of template
    if not template_file and not selected_template:
        app.show_status_message("Please select a template", message_type="error")
        return
    
    # Get structure name if not set from selected template
    if not structure_name and hasattr(app, 'structure_var'):
        structure_name = app.structure_var.get()
        if structure_name == "Default":
            structure_name = None
    
    # Get the output directory
    output_dir = app.get_current_output_dir()
    if not output_dir:
        app.show_status_message("Please select an output directory", message_type="error")
        return
    
    # Prepare project builder
    project_builder = app.project_builder
    project_type = "Standard"  # Default to Standard project type
    
    # Check if project_type_var is available (backward compatibility)
    if hasattr(app, 'project_type_var'):
        project_type = app.project_type_var.get()
    
    # Starting batch creation
    print(f"Starting batch creation. Template: {template_file}, Structure: {structure_name}, Output: {output_dir}")
    app.show_status_message(f"Creating {len(project_names)} projects in {output_dir}...", message_type="info")
    
    # Start batch creation in background
    app.project_builder.batch_create_projects(
        project_names=project_names,
        output_dir=output_dir,
        template_file=template_file,
        project_type=project_type,
        structure_name=structure_name,
        create_backup=True,
        callback=lambda results: batch_creation_complete(app, results, selected_template)
    )
    
    return True


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
        # Add the gallery template to recent templates
        from app.templates.template_utils import add_to_recent_templates as add_to_recent_templates_util
        add_to_recent_templates_util(app, selected_template)
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
