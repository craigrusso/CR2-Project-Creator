#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import tkinter as tk
from tkinter import ttk, BOTH, LEFT, RIGHT, X

def show_tutorial(app):
    """Show tutorial dialog"""
    tutorial_window = tk.Toplevel(app.root)
    tutorial_window.title("Tutorial")
    tutorial_window.geometry("700x500")
    tutorial_window.transient(app.root)
    
    # Create notebook (tabs)
    notebook = ttk.Notebook(tutorial_window)
    notebook.pack(fill=BOTH, expand=True, padx=20, pady=20)
    
    # Getting Started tab
    getting_started_tab = tk.Frame(notebook)
    notebook.add(getting_started_tab, text="Getting Started")
    
    tk.Label(getting_started_tab, text="Getting Started with CR2 Creative Pro", 
           font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 15))
    
    tk.Label(getting_started_tab, text="Welcome to CR2 Creative Pro! This tool helps you create organized project structures for your creative workflows.", 
           wraplength=650, justify=LEFT).pack(anchor="w", pady=(0, 10))
         
    steps_text = """
1. Enter your project name in the "Project Name" field
2. Select a template file (optional) using the "Browse" button
3. Choose your output location where the project will be created
4. Expand "Advanced Options" for more settings if needed
5. Click "Create Project" to generate your project structure
    """
    
    tk.Label(getting_started_tab, text=steps_text, wraplength=650, justify=LEFT).pack(anchor="w", pady=(0, 10))
    
    tk.Label(getting_started_tab, text="Batch Project Creation", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(10, 5))
    
    batch_text = """
You can create multiple projects at once by clicking the "Batch Create" button. This allows you to:

• Paste a list of project names from an email
• Create all projects with the same template and settings
• Review the creation results in a single operation
    """
    
    tk.Label(getting_started_tab, text=batch_text, wraplength=650, justify=LEFT).pack(anchor="w", pady=(0, 10))
    
    tk.Label(getting_started_tab, text="Templates", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(10, 5))
    
    templates_text = """
You can select template files from the gallery on the right side of the main window. Templates help you start with predefined structures based on your project type.

You can also create your own templates by setting up your project structure and then using "File > Save as Template".
    """
    
    tk.Label(getting_started_tab, text=templates_text, wraplength=650, justify=LEFT).pack(anchor="w")
    
    # Templates tab
    templates_tab = tk.Frame(notebook)
    notebook.add(templates_tab, text="Templates")
    
    tk.Label(templates_tab, text="Working with Templates", 
           font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 15))
    
    templates_info_text = """
Templates are a powerful way to streamline your workflow. You can:

• Use built-in templates from the gallery
• Create templates from existing projects
• Import templates from colleagues
• Manage your template library
• Rename templates to better describe their purpose

Different project types (Video, Motion Graphics, Design, Audio) have specialized folder structures optimized for those workflows.
    """
    
    tk.Label(templates_tab, text=templates_info_text, wraplength=650, justify=LEFT).pack(anchor="w")
    
    # Advanced Features tab
    advanced_tab = tk.Frame(notebook)
    notebook.add(advanced_tab, text="Custom Structures")
    
    tk.Label(advanced_tab, text="Custom Folder Structures", 
           font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 15))
    
    structures_text = """
CR2 Creative Pro allows you to create and manage custom folder structures:

• Create new folder structures with your preferred organization
• Edit existing structures to adapt to your workflow
• Rename structures for better identification
• Select a custom structure when creating a project
• Share structures with your team

Access these features through the "Advanced Options" section or the "Templates > Manage Structures" menu.
    """
    
    tk.Label(advanced_tab, text=structures_text, wraplength=650, justify=LEFT).pack(anchor="w")
    
    # Close button
    button_frame = tk.Frame(tutorial_window)
    button_frame.pack(fill=X, padx=20, pady=20)
    
    close_btn = ttk.Button(button_frame, text="Close", command=tutorial_window.destroy)
    close_btn.pack(side=RIGHT)
