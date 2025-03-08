#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import tkinter as tk
from tkinter import ttk, messagebox, BOTH, LEFT, RIGHT, END, X, Y
from tkinter.constants import DISABLED, WORD, NONE

from app.ui.color_scheme import colors

def preview_structure(app):
    """Show preview of project structure based on current settings"""
    if not app.project_name.get().strip():
        messagebox.showerror("Error", "Please enter a project name")
        return
    
    # Create preview window
    preview_window = tk.Toplevel(app.root)
    preview_window.title("Project Structure Preview")
    preview_window.geometry("500x500")
    preview_window.transient(app.root)
    
    # Preview frame with scrollbar
    preview_frame = tk.Frame(preview_window)
    preview_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
    
    # Project name header
    project_name = app.project_name.get().strip()
    tk.Label(preview_frame, text=f"Project: {project_name}", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))
    
    # Project type
    project_type = "Standard"
    tk.Label(preview_frame, text=f"Type: {project_type}", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 10))
    
    # Structure frame with scrollbar
    structure_frame = tk.Frame(preview_frame)
    structure_frame.pack(fill=BOTH, expand=True)
    
    scrollbar = ttk.Scrollbar(structure_frame)
    scrollbar.pack(side=RIGHT, fill=Y)
    
    structure_text = tk.Text(structure_frame, wrap=NONE, yscrollcommand=scrollbar.set)
    structure_text.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.config(command=structure_text.yview)
    
    # Get directory structure
    structure_name = app.structure_var.get()
    if structure_name == "Default":
        directory_structure = app.template_manager.get_default_structure(project_type)
    else:
        directory_structure = app.template_manager.get_structure(structure_name)
    
    # Display structure
    structure_text.insert(END, f"{project_name}/\n")
    
    for directory in directory_structure:
        level = directory.count('/')
        indent = '    ' * level
        folder = directory.split('/')[-1]
        structure_text.insert(END, f"{indent}├── {folder}/\n")
        
    # Add template file if selected
    if app.template_file_path:
        filename = os.path.basename(app.template_file_path)
        _, ext = os.path.splitext(filename)
        new_filename = f"{project_name}{ext}"
        
        # Determine location in structure
        if ext.lower() in ['.prproj']:
            parent = "01_PREMIER_PROJECT"
        elif ext.lower() in ['.aep', '.aepx']:
            if project_type == "Motion Graphics":
                parent = "01_AE_PROJECTS"
            else:
                parent = "02_AE_PROJECTS"
        elif ext.lower() in ['.psd']:
            parent = "01_PHOTOSHOP_PROJECTS" 
        elif ext.lower() in ['.ai']:
            parent = "02_ILLUSTRATOR_PROJECTS"
        else:
            parent = ""
            
        if parent:
            level = 1
            indent = '    ' * level
            structure_text.insert(END, f"{indent}    └── {new_filename}\n")
    
    # Add README file
    structure_text.insert(END, "    └── README.txt\n")
    
    # Disable editing
    structure_text.configure(state=DISABLED)
