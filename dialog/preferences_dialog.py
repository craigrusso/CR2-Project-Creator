#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import tkinter as tk
from tkinter import ttk, messagebox, StringVar, BOTH, LEFT, RIGHT, X

from app.ui.color_scheme import colors
from app.utils.utils import load_config, save_config, open_folder

def show_preferences(app):
    """Show preferences dialog"""
    prefs_window = tk.Toplevel(app.root)
    prefs_window.title("Preferences")
    prefs_window.geometry("500x400")
    prefs_window.transient(app.root)
    prefs_window.grab_set()
    
    # Create notebook (tabs)
    notebook = ttk.Notebook(prefs_window)
    notebook.pack(fill=BOTH, expand=True, padx=20, pady=20)
    
    # General tab
    general_tab = tk.Frame(notebook)
    notebook.add(general_tab, text="General")
    
    # Default output location
    location_frame = tk.Frame(general_tab, pady=10)
    location_frame.pack(fill=X)
    
    tk.Label(location_frame, text="Default Output Location:", width=20, anchor="w").pack(side=LEFT)
    
    location_label = tk.Label(location_frame, text=app.root_path or "Not set")
    location_label.pack(side=LEFT, fill=X, expand=True)
    
    browse_btn = ttk.Button(location_frame, text="Browse", 
                          command=lambda: set_default_location(app, location_label))
    browse_btn.pack(side=RIGHT)
    
    # Templates tab
    templates_tab = tk.Frame(notebook)
    notebook.add(templates_tab, text="Templates")
    
    tk.Label(templates_tab, text="Template Storage Location:", anchor="w").pack(fill=X, pady=(10, 5))
    tk.Label(templates_tab, text=app.template_manager.paths["templates_dir"], anchor="w").pack(fill=X, pady=(0, 10))
    
    # Buttons
    open_folder_btn = ttk.Button(templates_tab, text="Open Templates Folder", 
                               command=lambda: open_folder(app.template_manager.paths["templates_dir"]))
    open_folder_btn.pack(anchor="w", pady=5)
    
    import_btn = ttk.Button(templates_tab, text="Import Templates", 
                          command=lambda: app.template_manager.import_template_ui(app))
    import_btn.pack(anchor="w", pady=5)
    
    manage_btn = ttk.Button(templates_tab, text="Manage Templates", 
                          command=lambda: app.template_manager.manage_templates_ui(app))
    manage_btn.pack(anchor="w", pady=5)
    
    # Recent template files
    tk.Label(templates_tab, text="Recent Template Files:", anchor="w").pack(fill=X, pady=(10, 5))
    
    from app.core.project_operations import clear_recent_templates
    
    clear_templates_btn = ttk.Button(templates_tab, text="Clear Recent Templates", 
                                   command=lambda: clear_recent_templates(app))
    clear_templates_btn.pack(anchor="w", pady=5)
    
    # Custom Structures tab
    structures_tab = tk.Frame(notebook)
    notebook.add(structures_tab, text="Custom Structures")
    
    tk.Label(structures_tab, text="Custom Structures Location:", anchor="w").pack(fill=X, pady=(10, 5))
    tk.Label(structures_tab, text=app.template_manager.paths["custom_structures_dir"], anchor="w").pack(fill=X, pady=(0, 10))
    
    # Buttons
    open_structures_btn = ttk.Button(structures_tab, text="Open Structures Folder", 
                                   command=lambda: open_folder(app.template_manager.paths["custom_structures_dir"]))
    open_structures_btn.pack(anchor="w", pady=5)
    
    from structures import create_custom_structure, manage_structures
    
    create_structure_btn = ttk.Button(structures_tab, text="Create New Structure", 
                                    command=lambda: create_custom_structure(app))
    create_structure_btn.pack(anchor="w", pady=5)
    
    manage_structures_btn = ttk.Button(structures_tab, text="Manage Structures", 
                                     command=lambda: manage_structures(app))
    manage_structures_btn.pack(anchor="w", pady=5)
    
    # Advanced tab
    advanced_tab = tk.Frame(notebook)
    notebook.add(advanced_tab, text="Advanced")
    
    # Reset settings button
    reset_btn = ttk.Button(advanced_tab, text="Reset All Settings", 
                         command=lambda: reset_settings(app))
    reset_btn.pack(anchor="w", pady=10)
    
    # Clear recent projects
    from app.core.project_operations import clear_recent_projects
    clear_recent_btn = ttk.Button(advanced_tab, text="Clear Recent Projects", 
                               command=lambda: clear_recent_projects(app))
    clear_recent_btn.pack(anchor="w", pady=5)
    
    # Bottom buttons
    button_frame = tk.Frame(prefs_window)
    button_frame.pack(fill=X, padx=20, pady=20)
    
    save_btn = ttk.Button(button_frame, text="Save", style="Accent.TButton",
                        command=lambda: save_preferences(app, prefs_window))
    save_btn.pack(side=RIGHT, padx=(10, 0))
    
    cancel_btn = ttk.Button(button_frame, text="Cancel", command=prefs_window.destroy)
    cancel_btn.pack(side=RIGHT)


def set_default_location(app, label):
    """Set the default output location"""
    from tkinter import filedialog
    directory = filedialog.askdirectory(title="Select Default Output Location")
    if directory:
        app.root_path = directory
        label.config(text=directory)


def save_preferences(app, window):
    """Save preferences from the preferences dialog"""
    # Save config
    config = load_config()
    config["last_directory"] = app.root_path
    save_config(config)
    
    # Close window
    window.destroy()
    
    # Show message
    messagebox.showinfo("Preferences Saved", 
                      "Preferences saved successfully.")


def reset_settings(app):
    """Reset all settings to defaults"""
    # Confirm reset
    confirm = messagebox.askyesno("Confirm Reset", 
                                "Are you sure you want to reset all settings? This cannot be undone.")
    if not confirm:
        return
    
    # Reset settings
    app.root_path = ""
    
    # Save config
    config = load_config()
    config["last_directory"] = ""
    save_config(config)
    
    # Show message
    messagebox.showinfo("Settings Reset", 
                      "All settings have been reset to defaults. Please restart the application.")
