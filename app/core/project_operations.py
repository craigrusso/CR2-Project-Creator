#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import platform
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, BOTH, X, LEFT, RIGHT
from tkinter.constants import *
import re

from app.ui.color_scheme import colors
from app.utils.utils import (
    open_folder, open_in_explorer, parse_project_names, 
    save_recent_projects, load_recent_projects,
    save_recent_templates, load_recent_templates
)


def create_project(app):
    """Create a new project from the current settings"""
    # Validate project name
    if not app.project_name.get().strip():
        app.show_status_message("Please enter a project name", message_type="error")
        return
    
    # Validate that a template file is selected
    if not hasattr(app, 'template_file_path') or not app.template_file_path:
        app.show_status_message("Please select a template file", message_type="error")
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
    
    project_name = app.project_name.get().strip()
    structure_name = app.structure_var.get()
    if structure_name == "Default":
        structure_name = None
    
    # Build project
    success, result = app.project_builder.create_project(
        project_name=project_name,
        output_dir=output_dir,
        template_file=app.template_file_path,
        project_type="Standard",
        structure_name=structure_name
    )
    
    # Handle result
    if success:
        # Set success message with green styling in the status bar
        app.show_status_message(f"Project '{project_name}' created at {result}", message_type="success")
        
        # Add project to recent projects
        add_to_recent_projects(app, project_name, result)
        
        # Add template to recent templates if one was used but preserve order
        if app.template_file_path:
            add_to_recent_templates(app, app.template_file_path, preserve_order=True)
    else:
        app.show_status_message(result, message_type="error")


def handle_batch_create(app, project_names_text):
    """Process batch creation of projects"""
    # Validate inputs
    if not project_names_text.strip():
        app.show_status_message("Please enter at least one project name", message_type="error")
        return
    
    # Validate that a template file is selected
    if not hasattr(app, 'template_file_path') or not app.template_file_path:
        app.show_status_message("Please select a template file", message_type="error")
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
    
    # Split project names by newline, comma, or semicolon
    project_names = re.split(r'[\n,;]+', project_names_text)
    project_names = [name.strip() for name in project_names if name.strip()]
    
    if not project_names:
        app.show_status_message("No valid project names found", message_type="error")
        return
    
    # Get the structure template
    structure_name = app.structure_var.get()
    if structure_name == "Default":
        structure_name = None
    
    # Start batch creation in background - send all projects to be processed
    app.project_builder.batch_create_projects(
        project_names=project_names,
        output_dir=output_dir,
        template_file=app.template_file_path,
        project_type="Standard",
        structure_name=structure_name,
        create_backup=True,
        callback=lambda results: batch_creation_complete(app, results)
    )
    
    return True


def batch_creation_complete(app, results):
    """Handle the completion of batch project creation"""
    # Count successes and failures
    successes = sum(1 for _, success, _ in results if success)
    failures = len(results) - successes
    
    # Add successful projects to recent projects
    for name, success, result in results:
        if success:
            add_to_recent_projects(app, name, result)
    
    # Add template to recent templates if one was used but preserve order
    if app.template_file_path:
        add_to_recent_templates(app, app.template_file_path, preserve_order=True)
    
    # Set appropriate message based on results
    if failures == 0:
        app.show_status_message(f"{successes} projects created successfully", message_type="success")
    else:
        app.show_status_message(f"{successes} projects created, {failures} failed", message_type="warning")


def add_to_recent_projects(app, project_name, project_path, max_recent=10):
    """Add a project to the recent projects list"""
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
            card.remove_btn.configure(bg=colors["bg"], fg=colors["text"])
