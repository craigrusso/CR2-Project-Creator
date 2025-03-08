#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import tkinter as tk
from tkinter import ttk, BOTH, LEFT, RIGHT, END, X, Y, BOTTOM, TOP
from tkinter.constants import WORD

from app.ui.color_scheme import colors


def show_batch_create(app):
    """Show dialog for batch project creation"""
    batch_dialog = tk.Toplevel(app.root)
    batch_dialog.title("Batch Create Projects")
    
    # Main container with fixed layout
    main_frame = tk.Frame(batch_dialog)
    main_frame.pack(fill=BOTH, expand=True)
    
    # Top section for content
    content_frame = tk.Frame(main_frame, padx=20, pady=20)
    content_frame.pack(fill=BOTH, expand=True)
    
    # Header
    tk.Label(content_frame, text="Create Multiple Projects", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 15))
    
    # Instructions
    tk.Label(content_frame, text="Enter one project name per line:", anchor="w").pack(fill=X, pady=(0, 5))
    tk.Label(content_frame, text="You can paste a list from email or other sources.", anchor="w").pack(fill=X, pady=(0, 15))
    
    # Project names text area with scrollbar
    editor_frame = tk.Frame(content_frame)
    editor_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
    
    scrollbar = ttk.Scrollbar(editor_frame)
    scrollbar.pack(side=RIGHT, fill=Y)
    
    editor = tk.Text(editor_frame, wrap=WORD, yscrollcommand=scrollbar.set, height=10)
    editor.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.config(command=editor.yview)
    
    # Editor gets focus
    editor.focus_set()
    
    # Settings info
    if app.root_path:
        location_display = app.root_path if len(app.root_path) < 40 else "..." + app.root_path[-37:]
        tk.Label(content_frame, text=f"Output location: {location_display}").pack(anchor="w")
    else:
        tk.Label(content_frame, text="Warning: No output location selected").pack(anchor="w")
    
    # Button frame - separate from content with fixed height, increased to 70px
    button_frame = tk.Frame(main_frame, height=70, padx=20, pady=15, bg=colors["bg"])
    button_frame.pack(fill=X, side=BOTTOM)
    button_frame.pack_propagate(False)  # Prevent frame from shrinking
    
    from app.core.project_operations import handle_batch_create
    
    # Function to handle batch creation
    def create_projects():
        projects_text = editor.get("1.0", "end-1c")
        result = handle_batch_create(app, projects_text)
        if result:
            batch_dialog.destroy()
    
    cancel_btn = ttk.Button(button_frame, text="Cancel", command=batch_dialog.destroy)
    cancel_btn.pack(side=RIGHT, pady=(10, 0))  # Added vertical padding
    
    create_btn = ttk.Button(button_frame, text="Create Projects", 
                          command=create_projects,
                          style="Accent.TButton")
    create_btn.pack(side=RIGHT, padx=(0, 10), pady=(10, 0))  # Added vertical padding
    
    # Calculate position relative to main window to avoid hiding bottom buttons
    # Get the main window's position and size
    root_x = app.root.winfo_x()
    root_y = app.root.winfo_y()
    root_width = app.root.winfo_width()
    
    # Set a fixed size that ensures buttons are visible
    dialog_width = 500
    dialog_height = 420
    
    # Calculate position to be in the upper portion of the main window
    dialog_x = root_x + (root_width - dialog_width) // 2
    dialog_y = root_y + 50  # Position near the top with padding
    
    batch_dialog.geometry(f"{dialog_width}x{dialog_height}+{dialog_x}+{dialog_y}")
    batch_dialog.minsize(500, 420)
    batch_dialog.transient(app.root)
    batch_dialog.grab_set()
    
    # Update the window to properly calculate sizes
    batch_dialog.update_idletasks()


def show_batch_results(app, results):
    """Show detailed results of batch project creation"""
    results_window = tk.Toplevel(app.root)
    results_window.title("Batch Creation Results")
    results_window.geometry("600x400")
    results_window.transient(app.root)
    
    # Results frame with scrollbar
    results_frame = tk.Frame(results_window, padx=20, pady=20)
    results_frame.pack(fill=BOTH, expand=True)
    
    tk.Label(results_frame, text="Batch Creation Results", 
          font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 15))
    
    # Results list with scrollbar
    list_frame = tk.Frame(results_frame)
    list_frame.pack(fill=BOTH, expand=True)
    
    scrollbar = ttk.Scrollbar(list_frame)
    scrollbar.pack(side=RIGHT, fill=Y)
    
    results_text = tk.Text(list_frame, wrap=WORD, yscrollcommand=scrollbar.set)
    results_text.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.config(command=results_text.yview)
    
    # Add results
    for name, success, result in results:
        if success:
            results_text.insert(END, f"✅ {name}: Created at {result}\n")
        else:
            results_text.insert(END, f"❌ {name}: {result}\n")
    
    # Disable editing
    results_text.configure(state="disabled")
    
    # Close button
    close_btn = ttk.Button(results_frame, text="Close", command=results_window.destroy)
    close_btn.pack(pady=(15, 0))
