#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, StringVar
from tkinter.constants import *

def create_new_category(app, category_var=None):
    """Create a new template category"""
    # Ask for category name
    category_name = simpledialog.askstring(
        "New Category", 
        "Enter a name for the new category:",
        parent=app.root
    )
    
    if not category_name:
        return  # User canceled
    
    # Check if category already exists
    existing_categories = app.category_manager.get_all_categories()
    
    if category_name in existing_categories:
        messagebox.showerror("Error", f"Category '{category_name}' already exists")
        return
    
    # Add the new category
    app.category_manager.add_category(category_name)
    
    # Update any category variable if provided
    if category_var and isinstance(category_var, StringVar):
        category_var.set(category_name)
        
    # Refresh UI components that display categories
    app.refresh_categories()
    
    return category_name

def add_category_from_dialog(app, dialog, listbox):
    """Add a new category from the manage categories dialog"""
    # Ask for category name
    category_name = simpledialog.askstring(
        "New Category", 
        "Enter a name for the new category:",
        parent=dialog
    )
    
    if not category_name:
        return  # User canceled
    
    # Check if category already exists
    existing_categories = app.category_manager.get_all_categories()
    
    if category_name in existing_categories:
        messagebox.showerror("Error", f"Category '{category_name}' already exists")
        return
    
    # Add the new category
    app.category_manager.add_category(category_name)
    
    # Refresh the category list
    categories = app.category_manager.get_all_categories()
    listbox.delete(0, tk.END)
    for category in categories:
        listbox.insert(tk.END, category)
    
    # Select the new category
    try:
        index = categories.index(category_name)
        listbox.selection_set(index)
        listbox.see(index)
    except ValueError:
        pass 