#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import platform
import tkinter as tk
from tkinter import BooleanVar

from app.core.app_config import setup_dpi_awareness
from app.ui.color_scheme import colors
from app.utils.utils import load_config, save_config, load_recent_projects, load_recent_templates
from app.templates.template_manager import TemplateManager
from app.core.project_builder import ProjectBuilder
from app.ui.app_theme import configure_styles, apply_theme_to_widgets

def initialize_app(app):
    """Initialize the application state and configuration"""
    # Set up high DPI awareness for Windows
    setup_dpi_awareness()
    
    # Configure tkinter styles
    configure_styles(app)
    
    # Set up managers
    app.template_manager = TemplateManager()
    app.project_builder = ProjectBuilder(app.template_manager)
    
    # Initialize application state
    app.selected_template_file = None
    app.selected_structure_template = None
    app.current_template = None
    app.template_file_path = ""  # Add this for preview_dialog.py
    app.template_cards = []
    app.recent_template_cards = []
    app.current_filter = None
    app.recent_projects = []
    app.recent_templates = []
    app.root_path = ""  # Add this for batch_dialog.py
    
    # Initialize UI variables
    app.project_name = tk.StringVar()
    app.project_name_var = tk.StringVar()  # Alternative name sometimes used
    app.category_var = tk.StringVar(value="All Categories")
    app.search_var = tk.StringVar()
    app.structure_var = tk.StringVar(value="Default")
    
    # Create a dummy search_box that has a get method to return empty string
    class DummySearchBox:
        def get(self):
            return ""
    app.search_box = DummySearchBox()
    
    # Set up configuration variables
    app.paths = app.template_manager.paths
    
    # Add output_dir to paths if not present, but don't set a default value
    if "output_dir" not in app.paths:
        app.paths["output_dir"] = ""  # Empty string instead of default location
    
    app.config = load_config()
    app.advanced_var = BooleanVar(value=False)
    
    # Ensure required directories exist
    _ensure_required_directories(app)
    
    # Apply theme to widgets after UI is created
    app.root.after(100, lambda: apply_theme_to_widgets(app))
    
    # Set up resize handler for responsive UI
    app.root.bind("<Configure>", app.on_resize)
    
    # Load saved template and structure selections after UI is created
    app.root.after(300, lambda: _load_saved_selections(app))
    
    return app

def _ensure_required_directories(app):
    """Ensure all required directories exist"""
    # Ensure templates directory exists
    os.makedirs(app.paths["templates_dir"], exist_ok=True)
    
    # Ensure custom structures directory exists
    os.makedirs(app.paths["custom_structures_dir"], exist_ok=True)
    
    # Ensure output directory exists if it's set
    if app.paths["output_dir"] and app.paths["output_dir"].strip():
        os.makedirs(app.paths["output_dir"], exist_ok=True)
    
    # Ensure config directory exists
    os.makedirs(os.path.dirname(app.paths["config_file"]), exist_ok=True)

def _load_saved_selections(app):
    """Load and apply saved template file and structure selections from config"""
    try:
        # Load template file selection if available
        if "template_file_path" in app.config and app.config["template_file_path"]:
            file_path = app.config["template_file_path"]
            if os.path.exists(file_path):
                # Set the file path
                app.template_file_path = file_path
                app.selected_template_file = file_path  # Also set selected_template_file for highlighting
                filename = os.path.basename(file_path)
                
                # Update UI if elements exist
                if hasattr(app, 'template_file_info'):
                    app.template_file_info.config(text=filename)
                
                # Enable rename button if it exists
                if hasattr(app, 'rename_template_file_btn'):
                    app.rename_template_file_btn.config(state="normal")
                
                # Add to recent templates
                from app.core.project_operations import add_to_recent_templates
                add_to_recent_templates(app, file_path, preserve_order=True)
                
                # Highlight the selected template file in the gallery
                if hasattr(app, '_highlight_in_gallery'):
                    app.root.after(500, lambda: app._highlight_in_gallery(file_path))
        
        # Load structure template selection if available
        if "structure_template" in app.config and app.config["structure_template"]:
            template_name = app.config["structure_template"]
            
            # Find the template in available templates
            template_found = False
            for template in app.template_manager.templates:
                if template.get("name") == template_name:
                    # Set as current template
                    app.current_template = template
                    app.selected_structure_template = template_name
                    template_found = True
                    
                    # Update UI if elements exist
                    if hasattr(app, 'structure_template_info'):
                        app.structure_template_info.config(text=template_name)
                    
                    break
            
            # If not found, reset the saved selection
            if not template_found and template_name != "Default":
                app.config["structure_template"] = "Default"
                save_config(app.config)
            
            # Highlight the current structure in the dropdown
            from app.core.structures import highlight_current_structure
            # Set structure variable
            app.structure_var.set(template_name)
            app.root.after(500, lambda: highlight_current_structure(app))
            
            # We'll refresh the template gallery to show highlighting, but ensure we don't cause recursion
            # by directly updating the UI elements instead of triggering a full refresh
            def update_template_gallery_highlighting():
                # Check if the UI elements exist
                if hasattr(app, 'template_list_frame') and hasattr(app.template_list_frame, 'scrollable_frame'):
                    # Define colors
                    blue_highlight = "#4682B4"  # Steel Blue
                    dark_text = "#FFFFFF"  # White text for better visibility on blue
                    
                    # Look for the template card matching our selected template
                    for card in app.template_list_frame.scrollable_frame.winfo_children():
                        if hasattr(card, 'template') and card.template.get("name") == template_name:
                            # Apply blue highlight to the entire card and all its parts
                            card.configure(bg=blue_highlight)
                            if hasattr(card, 'info_frame'):
                                card.info_frame.configure(bg=blue_highlight)
                            
                            # Also highlight the icon
                            if hasattr(card, 'icon_label'):
                                card.icon_label.configure(bg=blue_highlight, fg=dark_text)
                            
                            # Also highlight info frame contents with dark text for contrast
                            if hasattr(card, 'info_frame'):
                                for widget in card.info_frame.winfo_children():
                                    widget.configure(bg=blue_highlight, fg=dark_text)
                            break
            
            app.root.after(700, update_template_gallery_highlighting)
    except Exception as e:
        print(f"Error loading saved selections: {e}")

def load_app_config(app):
    """Load application configuration"""
    app.config = load_config()
    app._update_ui_from_config()

def load_app_recent_projects(app):
    """Load recent projects"""
    app.recent_projects = load_recent_projects()
    app.update_recent_menu()

def load_app_recent_templates(app):
    """Load recent templates"""
    app.recent_templates = load_recent_templates()
    app.update_recent_templates_gallery() 