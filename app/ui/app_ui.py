#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, BOTH, X, W, LEFT, RIGHT, BOTTOM, TOP, Y
from tkinter.constants import SOLID

# Define constants directly to avoid circular imports
APP_VERSION = "2.1"

from app.ui.color_scheme import colors
from app.ui.ui_components import ToolTip, CardFrame, SearchBox, TemplateFileCard, ScrollableFrame
from app.templates.templates import (populate_template_gallery, select_template_from_gallery, 
                     get_template_file, clear_template_file, clear_structure_template,
                     rename_current_template, rename_template_file, create_template_directory,
                     edit_directory_template, edit_template_structure, apply_structure_to_template)
from app.core.structures import update_structure_dropdown, create_custom_structure, edit_structure, manage_structures
from app.ui.app_theme import configure_styles
from dialog.dialog_windows import show_batch_create, preview_structure
from app.core.project_operations import create_project, use_recent_template
from app.utils.integration import extend_create_ui  # ADDED: Import the integration module

# Define a simple tooltip function that works with any widget
def simple_tooltip(widget, text):
    def on_enter(event):
        x = widget.winfo_rootx() + widget.winfo_width() // 2
        y = widget.winfo_rooty() + widget.winfo_height() + 5
        
        # Create tooltip
        tip = tk.Toplevel(widget)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tip, text=text, background=colors["card_bg"],
                       foreground=colors["text"], relief="solid", borderwidth=1,
                       padx=5, pady=2, font=("Segoe UI", 9))
        label.pack()
        
        # Store tooltip
        widget._tooltip = tip
    
    def on_leave(event):
        if hasattr(widget, "_tooltip"):
            widget._tooltip.destroy()
            del widget._tooltip
    
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)

def run_import_dialog(app):
    """
    Direct import function that doesn't use subprocess
    This avoids subprocess issues that can crash the application
    macOS-compatible version
    """
    try:
        # Update status before running to give user feedback
        app.status_var.set("Opening import dialog...")
        app.root.update_idletasks()
        
        # Import the function directly, with special error handling for macOS
        try:
            from app.templates.import_template import import_template_direct
            success = import_template_direct()
        except Exception as e:
            # If the normal import fails, fallback to a more basic dialog
            print(f"Error with standard import, falling back to basic dialog: {e}")
            success = _fallback_import_dialog(app)
        
        # Update UI based on result
        if success:
            app.template_manager.load_templates()
            populate_template_gallery(app)
            app.status_var.set("Template imported successfully")
        else:
            app.status_var.set("Template import cancelled")
            
    except Exception as e:
        print(f"Error importing template: {e}")
        app.status_var.set(f"Error importing template")

def _fallback_import_dialog(app):
    """A super simple fallback import dialog for macOS in case the normal one fails"""
    try:
        from tkinter import filedialog, simpledialog, messagebox
        import os
        import json
        import datetime
        
        # Get the templates directory
        templates_dir = app.template_manager.paths["templates_dir"]
        
        # Simple file dialog with no filetypes
        file_path = filedialog.askopenfilename(title="Select Template File")
        
        if not file_path:
            return False  # User cancelled
        
        # Get filename
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        
        # Get template name from user
        template_name = simpledialog.askstring("Import Template", 
                                         "Enter template name:", initialvalue=name)
        
        if not template_name:
            return False  # User cancelled
        
        # Determine category from file extension
        category = "Custom"
        if ext.lower() in ['.prproj']:
            category = "Video Editing"
            structure_type = "Video Editing"
        elif ext.lower() in ['.aep', '.aepx']:
            category = "Motion Graphics"
            structure_type = "Motion Graphics"
        elif ext.lower() in ['.psd', '.ai']:
            category = "Design"
            structure_type = "Design"
        else:
            category = "Custom"
            structure_type = "Standard"
        
        # Set icon
        icons = {
            "Video Editing": "🎬",
            "Motion Graphics": "✨",
            "Design": "📷",
            "Audio": "🎧",
            "Custom": "📂"
        }
        icon = icons.get(category, "📂")
        
        # Create template
        template = {
            "name": template_name,
            "category": category,
            "file": file_path,
            "type": structure_type,
            "description": f"{category} template",
            "structure_type": structure_type,
            "icon": icon,
            "created": datetime.datetime.now().isoformat()
        }
        
        # Save template
        save_filename = template_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        save_path = os.path.join(templates_dir, f"{save_filename}.json")
        
        with open(save_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        # Show success message
        messagebox.showinfo("Template Imported", f"Template '{template_name}' imported successfully")
        
        return True
    
    except Exception as e:
        print(f"Error in fallback import dialog: {e}")
        return False

def create_template_section(app, parent):
    """Create the template selection section"""
    template_frame = CardFrame(parent, title="Template Selection")
    
    # Template file section
    file_frame = tk.Frame(template_frame.content_frame, bg=colors["bg"])
    file_frame.pack(fill=X, expand=True, pady=(0, 10))
    
    # Create single-line title and buttons layout
    title_row = tk.Frame(file_frame, bg=colors["bg"])
    title_row.pack(fill=X, expand=True)
    
    # Template file label
    tk.Label(title_row, text="Template File:", bg=colors["bg"], fg=colors["text"],
           anchor="w", font=("Segoe UI", 11)).pack(side=LEFT, pady=5)
    
    # Add space between label and buttons
    title_row.pack_propagate(False)
    title_row.config(height=30)
    
    # Buttons for template file
    buttons_frame = tk.Frame(title_row, bg=colors["bg"])
    buttons_frame.pack(side=RIGHT)
    
    # Template directory button
    create_dir_btn = ttk.Button(buttons_frame, text="Create Directory Template", 
                             command=lambda: create_template_directory(app),
                             style="Slim.TButton")
    create_dir_btn.pack(side=RIGHT, padx=5)
    
    # Edit directory template button (initially disabled)
    app.edit_template_dir_btn = ttk.Button(buttons_frame, text="Edit Directory Template", 
                                     command=lambda: edit_directory_template(app, app.current_template),
                                     style="Slim.TButton", state=DISABLED)
    app.edit_template_dir_btn.pack(side=RIGHT, padx=5)
    
    # Browse button
    browse_btn = ttk.Button(buttons_frame, text="Browse...", 
                          command=lambda: get_template_file(app),
                          style="Slim.TButton")
    browse_btn.pack(side=RIGHT, padx=5)
    
    # Clear button
    clear_btn = ttk.Button(buttons_frame, text="Clear", 
                         command=lambda: clear_template_file(app),
                         style="Slim.TButton")
    clear_btn.pack(side=RIGHT, padx=5)
    
    # Rename button (initially disabled)
    app.rename_template_file_btn = ttk.Button(buttons_frame, text="Rename", 
                                          command=lambda: rename_template_file(app),
                                          style="Slim.TButton", state=DISABLED)
    app.rename_template_file_btn.pack(side=RIGHT, padx=5)
    
    # Template file info
    info_frame = tk.Frame(file_frame, bg=colors["bg"])
    info_frame.pack(fill=X, expand=True, pady=(5, 0))
    
    app.template_file_info = tk.Label(info_frame, text="No template file selected", 
                                    bg=colors["card_bg"], fg=colors["text"],
                                    padx=10, pady=5, anchor="w")
    app.template_file_info.pack(fill=X, expand=True)

    return template_frame

def create_ui(app):
    """Create the main application UI"""
    # Configure styles
    configure_styles(app)
    
    # Create an outer frame to hold everything except the bottom bar
    outer_frame = tk.Frame(app.root, bg=colors["bg"])
    outer_frame.pack(fill=BOTH, expand=True)
    
    # Create a scrollable main container for the entire UI
    main_scroll_container = ScrollableFrame(outer_frame, bg=colors["bg"])
    main_scroll_container.pack(fill=BOTH, expand=True)
    
    # Store a reference to the scrollable container for later access
    app.main_scroll_container = main_scroll_container
    
    # Main container - now inside the scrollable frame
    main_frame = tk.Frame(main_scroll_container.scrollable_frame, bg=colors["bg"])
    main_frame.pack(fill=BOTH, expand=True, padx=20, pady=(20, 0))
    
    # Header
    header_frame = tk.Frame(main_frame, bg=colors["bg"])
    header_frame.pack(fill=X, pady=(0, 20))
    
    title_label = tk.Label(header_frame, text="Create New Project", font=("Segoe UI", 24, "bold"),
                        bg=colors["bg"], fg=colors["text"])
    title_label.pack(side=LEFT)
    
    # Batch create button
    batch_btn = ttk.Button(header_frame, text="Batch Create", 
                         command=lambda: show_batch_create(app))
    batch_btn.pack(side=RIGHT, padx=10)
    ToolTip(batch_btn, "Create multiple projects at once")
    
    # Main content - split into left and right panels
    content_frame = tk.Frame(main_frame, bg=colors["bg"])
    content_frame.pack(fill=BOTH, expand=True)
    
    # Left panel - Project Settings
    left_panel = tk.Frame(content_frame, bg=colors["bg"], width=500)
    left_panel.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
    
    # Create a card-like frame for project settings
    settings_card = CardFrame(left_panel, title="Project Settings")
    settings_card.pack(fill=BOTH, expand=True)
    
    # Settings content frame - using pack layout manager
    settings_content = tk.Frame(settings_card, bg=colors["card_bg"])
    settings_content.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    # Project name
    project_name_frame = tk.Frame(settings_content, bg=colors["card_bg"])
    project_name_frame.pack(fill=X, pady=(0, 15))
    
    project_name_label = tk.Label(project_name_frame, text="Project Name", font=("Segoe UI", 10),
                                bg=colors["card_bg"], fg=colors["text"])
    project_name_label.pack(anchor=W, pady=(0, 5))
    
    app.project_name_entry = tk.Entry(project_name_frame, textvariable=app.project_name, font=("Segoe UI", 10),
                                    bg=colors["card_bg"], fg=colors["text"], insertbackground=colors["text"],
                                    relief=SOLID, bd=1, width=30)
    app.project_name_entry.pack(fill=X)
    
    # Template file selection
    template_file_container = tk.Frame(settings_content, bg="#282828")
    template_file_container.pack(fill=X, pady=(0, 15))
    
    template_file_label = tk.Label(template_file_container, text="Template File", font=("Segoe UI", 10, "bold"),
                                  bg="#282828", fg=colors["text"])
    template_file_label.pack(anchor=W, pady=(0, 5))
    
    # Description of what template file is
    template_file_desc = tk.Label(template_file_container,
                               text="Select a project file (.prproj, .aep, etc.) to include in your project",
                               font=("Segoe UI", 9), wraplength=400,
                               bg="#282828", fg=colors["secondary_text"])
    template_file_desc.pack(anchor=W, pady=(0, 5))
    
    # Template file info section with fixed width and height to prevent panel resizing
    app.template_file_frame = tk.Frame(template_file_container, bg="#282828", width=450, height=40)
    app.template_file_frame.pack(fill=X)
    app.template_file_frame.pack_propagate(False)  # Prevent frame from shrinking/expanding
    
    # Create a dedicated frame for buttons with the dark grey background - pack this FIRST
    template_buttons_frame = tk.Frame(app.template_file_frame, bg="#282828")
    template_buttons_frame.pack(side=RIGHT, fill=Y)
    
    select_template_file_btn = ttk.Button(template_buttons_frame, text="Browse", 
                                        command=lambda: get_template_file(app))
    select_template_file_btn.pack(side=RIGHT, padx=(10, 0), pady=5)
    
    clear_template_file_btn = ttk.Button(template_buttons_frame, text="Clear", 
                                       command=lambda: clear_template_file(app))
    clear_template_file_btn.pack(side=RIGHT, pady=5)
    
    # Rename template file button
    app.rename_template_file_btn = ttk.Button(template_buttons_frame, text="Rename", 
                                           command=lambda: rename_template_file(app))
    app.rename_template_file_btn.pack(side=RIGHT, padx=(10, 0), pady=5)
    app.rename_template_file_btn.config(state="disabled")  # Disabled until template selected
    
    # Fixed width label with ellipsis for long text - pack this AFTER buttons to ensure buttons get space first
    app.template_file_info = tk.Label(app.template_file_frame, text="No template file selected", 
                                    font=("Segoe UI", 9), width=30,  # Reduced width to give more space to buttons
                                    bg="#282828", fg=colors["secondary_text"], 
                                    anchor="w", pady=5, padx=12)
    app.template_file_info.pack(side=LEFT, fill=X, expand=True)
    
    # Recent template files gallery
    recent_templates_label = tk.Label(template_file_container, text="Recent Template Files", font=("Segoe UI", 10),
                                    bg="#282828", fg=colors["text"])
    recent_templates_label.pack(anchor=W, pady=(10, 5))
    
    # Create frame for recent template files
    app.recent_templates_frame = tk.Frame(template_file_container, bg="#282828")
    app.recent_templates_frame.pack(fill=X)
    
    # Update recent templates gallery (function defined in app.py)
    app.update_recent_templates_gallery()
    
    # Structure Template selection
    structure_template_container = tk.Frame(settings_content, bg=colors["bg"])
    structure_template_container.pack(fill=X, pady=(0, 15))
    
    structure_template_label = tk.Label(structure_template_container, text="Structure Template", font=("Segoe UI", 10, "bold"),
                                       bg=colors["bg"], fg=colors["text"])
    structure_template_label.pack(anchor=W, pady=(0, 5))
    
    structure_template_desc = tk.Label(structure_template_container,
                                     text="Select a structure template to organize your project folders",
                                     font=("Segoe UI", 9), bg=colors["bg"], fg=colors["secondary_text"], wraplength=450)
    structure_template_desc.pack(anchor=W, pady=(0, 5))
    
    # Container for structure template frame (used for border styling)
    app.structure_container_frame = tk.Frame(structure_template_container, bg=colors["bg"], bd=0)
    app.structure_container_frame.pack(fill=X, padx=0, pady=5)
    
    # Create the structure frame with border styling
    app.structure_template_frame = tk.Frame(
        app.structure_container_frame, 
        bg=colors["bg"], 
        highlightbackground=colors["bg"],
        highlightthickness=1,
        bd=0,
        height=50
    )
    app.structure_template_frame.pack(fill=X, padx=2, pady=2)
    
    # Create a dedicated frame for structure buttons - pack this FIRST
    structure_buttons_frame = tk.Frame(app.structure_template_frame, bg=colors["bg"])
    structure_buttons_frame.pack(side=RIGHT, fill=Y)
    
    # Switch back to ttk.Button but use a specific style to match Browse button
    clear_structure_btn = ttk.Button(
        structure_buttons_frame, 
        text="Clear", 
        command=lambda: clear_structure_template(app),
        style="TButton"
    )
    clear_structure_btn.pack(side=RIGHT, padx=5, pady=5)
    
    # Rename structure template with the same styling
    rename_structure_btn = ttk.Button(
        structure_buttons_frame, 
        text="Rename", 
        command=lambda: rename_current_template(app),
        style="TButton"
    )
    rename_structure_btn.pack(side=RIGHT, padx=(10, 0), pady=5)
    
    # Fixed width label with ellipsis for long text - pack this AFTER buttons to ensure buttons get space first
    app.structure_template_info = tk.Label(app.structure_template_frame, text="No structure template selected", 
                                         font=("Segoe UI", 9), width=30,  # Reduced width to give more space to buttons
                                         bg=colors["bg"], fg=colors["secondary_text"], 
                                         anchor="w", pady=5, padx=12)
    app.structure_template_info.pack(side=LEFT, fill=X, expand=True)
    
    # Update hover effects for the frame and text only
    def on_structure_hover_enter(event):
        if not hasattr(app, 'structure_is_highlighted') or not app.structure_is_highlighted:
            hover_bg = colors["hover_bg"]  # Use the hover bg from the color scheme
            app.structure_template_frame.configure(bg=hover_bg, highlightbackground=hover_bg)
            app.structure_template_info.configure(bg=hover_bg)
            structure_buttons_frame.configure(bg=hover_bg)
    
    def on_structure_hover_leave(event):
        if not hasattr(app, 'structure_is_highlighted') or not app.structure_is_highlighted:
            app.structure_template_frame.configure(bg=colors["bg"], highlightbackground=colors["bg"])
            app.structure_template_info.configure(bg=colors["bg"])
            structure_buttons_frame.configure(bg=colors["bg"])
    
    # Add hover bindings to structure elements
    for widget in [app.structure_template_frame, app.structure_template_info, structure_buttons_frame]:
        widget.bind("<Enter>", on_structure_hover_enter)
        widget.bind("<Leave>", on_structure_hover_leave)
    
    # Output location
    output_frame_container = tk.Frame(settings_content, bg=colors["card_bg"])
    output_frame_container.pack(fill=X, pady=(0, 15))
    
    output_label = tk.Label(output_frame_container, text="Output Location", font=("Segoe UI", 10),
                          bg=colors["card_bg"], fg=colors["text"])
    output_label.pack(anchor=W, pady=(0, 5))
    
    app.output_frame = tk.Frame(output_frame_container, bg=colors["card_bg"], width=450, height=40)
    app.output_frame.pack(fill=X)
    app.output_frame.pack_propagate(False)  # Prevent frame from shrinking
    
    app.output_path = tk.Label(app.output_frame, text="Select Output Location", font=("Segoe UI", 9),
                              width=40, bg=colors["card_bg"], fg=colors["secondary_text"], 
                              anchor="w", pady=5)
    app.output_path.pack(side=LEFT, fill=X, expand=True)
    
    select_output_btn = ttk.Button(app.output_frame, text="Browse", command=app.get_output_dir)
    select_output_btn.pack(side=RIGHT)
    
    # Move the folder structure functionality directly into the template section
    structure_section = tk.Frame(structure_template_container, bg=colors["bg"])
    structure_section.pack(fill=X, pady=(10, 0))
    
    structure_label = tk.Label(structure_section, text="Folder Structure Management", 
                             font=("Segoe UI", 10, "bold"), bg=colors["bg"], fg=colors["text"])
    structure_label.pack(anchor=W, pady=(0, 5))
    
    # Create a description for the folder structure
    structure_desc = tk.Label(structure_section, 
                           text="Define the folders that will be created when using this template", 
                           font=("Segoe UI", 9), bg=colors["bg"], fg=colors["secondary_text"])
    structure_desc.pack(anchor=W, pady=(0, 10))
    
    # Structure buttons
    structure_btn_frame = tk.Frame(structure_section, bg=colors["bg"])
    structure_btn_frame.pack(fill=X)
    
    create_structure_btn = ttk.Button(structure_btn_frame, text="Create Custom Structure", 
                                   command=lambda: create_custom_structure(app))
    create_structure_btn.pack(side=LEFT, padx=(0, 5))
    
    # Edit Template Structure button removed - moved to template editor dialog
    
    # Add a button to manage all structures
    manage_structures_btn = ttk.Button(structure_btn_frame, text="Manage All Structures", 
                                   command=lambda: manage_structures(app))
    manage_structures_btn.pack(side=LEFT, padx=(0, 5))
    
    # Add a visual hint that this is connected to the template
    structure_hint = tk.Label(structure_section, 
                           text="The structure is associated with the selected template", 
                           font=("Segoe UI", 9, "italic"), bg=colors["bg"], fg="#999999")
    structure_hint.pack(fill=X, pady=(5, 0))
    
    # Structure dropdown (keep this from advanced section)
    structure_dropdown_frame = tk.Frame(structure_section, bg=colors["bg"])
    structure_dropdown_frame.pack(fill=X, pady=(10, 0))
    
    # Populate structure dropdown
    app.structure_var = tk.StringVar(value="Default")
    update_structure_dropdown(app)
    
    dropdown_label = tk.Label(structure_dropdown_frame, text="Selected Structure:", 
                           font=("Segoe UI", 9), bg=colors["bg"], fg=colors["secondary_text"])
    dropdown_label.pack(side=LEFT, padx=(0, 5))
    
    app.structure_dropdown = ttk.OptionMenu(structure_dropdown_frame, app.structure_var, "Default",
                                          "Default", *app.template_manager.custom_structures.keys())
    app.structure_dropdown.pack(side=LEFT, fill=X, expand=True)
    
    # Right panel - Template Gallery
    right_panel = tk.Frame(content_frame, bg=colors["bg"], width=500)
    right_panel.pack(side=RIGHT, fill=BOTH, expand=True, padx=(10, 0))
    
    # Create a card-like frame for template gallery
    templates_card = CardFrame(right_panel, title="File Structure Templates")
    templates_card.pack(fill=BOTH, expand=True)
    
    # Store the template gallery card (needed for enhanced gallery integration)
    app.templates_card = templates_card
    
    # Template list frame - create a placeholder that will be replaced by the enhanced gallery
    app.template_list_frame = ScrollableFrame(templates_card, bg=colors["card_bg"])
    app.template_list_frame.pack(fill=BOTH, expand=True)
    
    # Note: The filter controls, search box, category dropdown, and add button 
    # are now created in template_gallery_ui.py with the enhanced gallery
    
    # Bottom buttons - place them in the fixed bottom container that was created in app.py
    button_frame = tk.Frame(app.bottom_container, bg=colors["bg"], height=40)
    button_frame.pack(fill=X, side=TOP, pady=(10, 10))  # Increased bottom padding from 5 to 10
    button_frame.pack_propagate(False)  # Prevent frame from shrinking
    
    reset_btn = ttk.Button(button_frame, text="Reset", command=app.reset_form)
    reset_btn.pack(side=LEFT, padx=20, pady=(0, 5))  # Added bottom padding to the button
    
    # Create spacer
    spacer = tk.Frame(button_frame, bg=colors["bg"])
    spacer.pack(side=LEFT, fill=X, expand=True)
    
    create_btn = ttk.Button(button_frame, text="Create Project", 
                          command=lambda: create_project(app), style="Accent.TButton")
    create_btn.pack(side=RIGHT, padx=(10, 20), pady=(0, 5))  # Added bottom padding to the button
    
    preview_btn = ttk.Button(button_frame, text="Preview Structure", 
                           command=lambda: preview_structure(app))
    preview_btn.pack(side=RIGHT, pady=(0, 5))  # Added bottom padding to the button
    
    # ADDED: Initialize enhanced template management
    extend_create_ui()(app)
