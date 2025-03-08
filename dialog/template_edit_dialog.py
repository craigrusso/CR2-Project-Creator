#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, StringVar, BooleanVar
from tkinter.constants import *

def edit_template_dialog(app, template):
    """Show dialog for editing a template"""
    # Guard against invalid templates
    if not isinstance(template, dict):
        messagebox.showerror("Error", "Invalid template format")
        return
    
    # Get template name with fallback
    template_name = template.get("name", "Unnamed Template")
    
    # Create dialog
    dialog = tk.Toplevel(app.root)
    dialog.title(f"Edit Template: {template_name}")
    dialog.geometry("500x400")
    dialog.transient(app.root)
    dialog.grab_set()
    
    # Main frame
    main_frame = tk.Frame(dialog, padx=20, pady=20)
    main_frame.pack(fill=BOTH, expand=True)
    
    # Template name
    name_frame = tk.Frame(main_frame)
    name_frame.pack(fill=X, pady=(0, 15))
    
    tk.Label(name_frame, text="Template Name:").pack(side=LEFT)
    
    name_var = StringVar(value=template_name)
    name_entry = tk.Entry(name_frame, textvariable=name_var, width=30)
    name_entry.pack(side=LEFT, padx=(10, 0), fill=X, expand=True)
    
    # Category
    category_frame = tk.Frame(main_frame)
    category_frame.pack(fill=X, pady=(0, 15))
    
    tk.Label(category_frame, text="Category:").pack(side=LEFT)
    
    category_var = StringVar(value=template.get("category", "Custom"))
    categories = app.category_manager.get_all_categories()
    
    category_combo = ttk.Combobox(category_frame, textvariable=category_var, values=categories, width=28)
    category_combo.pack(side=LEFT, padx=(10, 0), fill=X, expand=True)
    
    # Template file selection
    file_frame = tk.Frame(main_frame)
    file_frame.pack(fill=X, pady=(0, 15))
    
    tk.Label(file_frame, text="Template File:").pack(side=LEFT)
    
    file_path = template.get("file_path", "")
    file_label = tk.Label(file_frame, text=file_path, anchor="w", width=25, relief="sunken", padx=5)
    file_label.pack(side=LEFT, padx=(10, 5), fill=X, expand=True)
    
    browse_btn = ttk.Button(file_frame, text="Browse...", 
                          command=lambda: change_template_file(dialog, template, file_label))
    browse_btn.pack(side=LEFT)
    
    # Description frame
    desc_frame = tk.Frame(main_frame)
    desc_frame.pack(fill=X, pady=(0, 15))
    
    tk.Label(desc_frame, text="Description:").pack(anchor="w")
    
    description_var = StringVar(value=template.get("description", ""))
    description_entry = tk.Entry(desc_frame, textvariable=description_var, width=30)
    description_entry.pack(fill=X, pady=(5, 0))
    
    # Tags frame - for future use
    # Folders - checkboxes for associated folders
    folders_frame = tk.Frame(main_frame)
    folders_frame.pack(fill=X, pady=(0, 15))
    
    tk.Label(folders_frame, text="Folders:").pack(anchor="w")
    
    # Get folders from template manager
    folders = app.template_manager.get_folders()
    
    folder_vars = {}
    template_folders = template.get("folders", [])
    
    # Create a canvas and scrollbar if there are many folders
    canvas_frame = tk.Frame(folders_frame)
    canvas_frame.pack(fill=X, expand=True, pady=(5, 0))
    
    for folder in folders:
        var = BooleanVar(value=folder in template_folders)
        folder_vars[folder] = var
        
        checkbox = ttk.Checkbutton(canvas_frame, text=folder, variable=var)
        checkbox.pack(anchor="w")
    
    # Bottom buttons
    button_frame = tk.Frame(main_frame)
    button_frame.pack(fill=X, side=BOTTOM, pady=(15, 0))
    
    save_btn = ttk.Button(button_frame, text="Save Changes", 
                        command=lambda: save_template_changes(app, dialog, template, 
                                                          name_var.get(), 
                                                          category_var.get(),
                                                          description_var.get(),
                                                          folder_vars))
    save_btn.pack(side=RIGHT, padx=(5, 0))
    
    cancel_btn = ttk.Button(button_frame, text="Cancel", command=dialog.destroy)
    cancel_btn.pack(side=RIGHT)
    
    # Initialize UI
    dialog.wait_window()

def change_template_file(dialog, template, file_label):
    """Change the template file via file browser"""
    initial_dir = os.path.dirname(template.get("file_path", "")) or os.path.expanduser("~")
    
    new_file = filedialog.askopenfilename(
        parent=dialog,
        title="Select Template File",
        initialdir=initial_dir,
        filetypes=[
            ("All Files", "*.*"),
            ("JSON Files", "*.json"),
            ("YAML Files", "*.yml *.yaml"),
            ("Python Files", "*.py"),
            ("Text Files", "*.txt")
        ]
    )
    
    if new_file:
        # Update file label
        file_label.config(text=new_file)
        
        # Update template data
        template["file_path"] = new_file

def save_template_changes(app, dialog, template, new_name, new_category, 
                       new_description, folder_vars):
    """Save changes to a template"""
    
    # Validate name
    if not new_name or new_name.isspace():
        messagebox.showerror("Error", "Template name cannot be empty")
        return
    
    # Check for duplicate name if name has changed
    if new_name != template.get("name"):
        # Check if name already exists
        existing_names = [t.get("name") for t in app.template_manager.templates]
        if new_name in existing_names:
            messagebox.showerror("Error", f"A template named '{new_name}' already exists")
            return
    
    # Update template data
    template["name"] = new_name
    template["category"] = new_category
    template["description"] = new_description
    template["last_modified"] = app.template_manager.get_timestamp()
    
    # Update folder associations
    template["folders"] = [folder for folder, var in folder_vars.items() if var.get()]
    
    # Update the template file on disk
    template_file = os.path.join(app.paths["templates_dir"], f"{template['id']}.json")
    
    try:
        with open(template_file, 'w') as f:
            import json
            json.dump(template, f, indent=2)
            
        messagebox.showinfo("Success", f"Template '{new_name}' has been updated")
        
        # Refresh the template list
        app.template_manager.load_templates()
        app.trigger_template_updated()
        
        # Close dialog
        dialog.destroy()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save template: {str(e)}") 