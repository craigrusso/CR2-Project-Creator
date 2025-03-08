#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.constants import *

from dialog.template_edit_dialog import edit_template_dialog
from dialog.folder_dialog import add_folder_from_dialog, rename_selected_folder, delete_selected_folder
from dialog.category_dialog import add_category_from_dialog

def manage_templates_dialog(app):
    """Show dialog for managing templates, folders, and categories"""
    # Create dialog
    dialog = tk.Toplevel(app.root)
    dialog.title("Manage Templates")
    dialog.geometry("850x600")
    dialog.transient(app.root)
    dialog.grab_set()
    
    # Create notebook for tabs
    notebook = ttk.Notebook(dialog)
    notebook.pack(fill=BOTH, expand=True, padx=20, pady=20)
    
    # Templates tab
    templates_frame = ttk.Frame(notebook)
    notebook.add(templates_frame, text="Templates")
    
    # Create template list with scrollbar
    template_list_frame = ttk.Frame(templates_frame)
    template_list_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    template_list = tk.Listbox(template_list_frame, width=50, height=15)
    template_list.pack(side=LEFT, fill=BOTH, expand=True)
    
    scrollbar = ttk.Scrollbar(template_list_frame, orient=VERTICAL, command=template_list.yview)
    scrollbar.pack(side=RIGHT, fill=Y)
    template_list.config(yscrollcommand=scrollbar.set)
    
    # Populate the list
    templates = app.template_manager.templates
    for template in templates:
        template_list.insert(tk.END, template.get("name", "Unnamed"))
    
    # Template action buttons
    template_buttons_frame = ttk.Frame(templates_frame)
    template_buttons_frame.pack(fill=X, padx=10, pady=(0, 10))
    
    edit_template_btn = ttk.Button(template_buttons_frame, text="Edit",
                                 command=lambda: edit_selected_template(app, dialog, template_list))
    edit_template_btn.pack(side=LEFT, padx=(0, 5))
    
    delete_template_btn = ttk.Button(template_buttons_frame, text="Delete",
                                   command=lambda: delete_selected_template(app, dialog, template_list))
    delete_template_btn.pack(side=LEFT, padx=(0, 5))
    
    import_template_btn = ttk.Button(template_buttons_frame, text="Import...",
                                   command=lambda: import_template(app, dialog))
    import_template_btn.pack(side=LEFT)
    
    # Folders tab
    folders_frame = ttk.Frame(notebook)
    notebook.add(folders_frame, text="Folders")
    
    # Create folder list with scrollbar
    folder_list_frame = ttk.Frame(folders_frame)
    folder_list_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    folder_list = tk.Listbox(folder_list_frame, width=50, height=15)
    folder_list.pack(side=LEFT, fill=BOTH, expand=True)
    
    folders_scrollbar = ttk.Scrollbar(folder_list_frame, orient=VERTICAL, command=folder_list.yview)
    folders_scrollbar.pack(side=RIGHT, fill=Y)
    folder_list.config(yscrollcommand=folders_scrollbar.set)
    
    # Populate the folder list
    folders = app.template_manager.get_folders()
    for folder in folders:
        folder_list.insert(tk.END, folder)
    
    # Folder action buttons
    folder_buttons_frame = ttk.Frame(folders_frame)
    folder_buttons_frame.pack(fill=X, padx=10, pady=(0, 10))
    
    add_folder_btn = ttk.Button(folder_buttons_frame, text="Add",
                              command=lambda: add_folder_from_dialog(app, dialog, folder_list))
    add_folder_btn.pack(side=LEFT, padx=(0, 5))
    
    rename_folder_btn = ttk.Button(folder_buttons_frame, text="Rename",
                                 command=lambda: rename_selected_folder(app, dialog, folder_list))
    rename_folder_btn.pack(side=LEFT, padx=(0, 5))
    
    delete_folder_btn = ttk.Button(folder_buttons_frame, text="Delete",
                                 command=lambda: delete_selected_folder(app, dialog, folder_list))
    delete_folder_btn.pack(side=LEFT)
    
    # Categories tab
    categories_frame = ttk.Frame(notebook)
    notebook.add(categories_frame, text="Categories")
    
    # Create category list with scrollbar
    category_list_frame = ttk.Frame(categories_frame)
    category_list_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    category_list = tk.Listbox(category_list_frame, width=50, height=15)
    category_list.pack(side=LEFT, fill=BOTH, expand=True)
    
    categories_scrollbar = ttk.Scrollbar(category_list_frame, orient=VERTICAL, command=category_list.yview)
    categories_scrollbar.pack(side=RIGHT, fill=Y)
    category_list.config(yscrollcommand=categories_scrollbar.set)
    
    # Populate the category list
    categories = app.category_manager.get_all_categories()
    for category in categories:
        category_list.insert(tk.END, category)
    
    # Category action buttons
    category_buttons_frame = ttk.Frame(categories_frame)
    category_buttons_frame.pack(fill=X, padx=10, pady=(0, 10))
    
    add_category_btn = ttk.Button(category_buttons_frame, text="Add",
                                command=lambda: add_category_from_dialog(app, dialog, category_list))
    add_category_btn.pack(side=LEFT, padx=(0, 5))
    
    # Bottom buttons
    button_frame = ttk.Frame(dialog)
    button_frame.pack(fill=X, padx=20, pady=(0, 20))
    
    close_btn = ttk.Button(button_frame, text="Close", command=dialog.destroy)
    close_btn.pack(side=RIGHT)
    
    # Initialize UI
    dialog.wait_window()

def edit_selected_template(app, dialog, listbox):
    """Edit the selected template"""
    # Get selected template
    selection = listbox.curselection()
    if not selection:
        messagebox.showinfo("Info", "Please select a template to edit")
        return
    
    selected_index = selection[0]
    selected_name = listbox.get(selected_index)
    
    # Find the template data
    template = None
    for t in app.template_manager.templates:
        if t.get("name") == selected_name:
            template = t
            break
    
    if not template:
        messagebox.showerror("Error", "Template not found")
        return
    
    # Open the edit dialog
    edit_template_dialog(app, template)
    
    # Refresh the template list
    templates = app.template_manager.templates
    listbox.delete(0, tk.END)
    for template in templates:
        listbox.insert(tk.END, template.get("name", "Unnamed"))

def delete_selected_template(app, dialog, listbox):
    """Delete the selected template"""
    # Get selected template
    selection = listbox.curselection()
    if not selection:
        messagebox.showinfo("Info", "Please select a template to delete")
        return
    
    selected_index = selection[0]
    selected_name = listbox.get(selected_index)
    
    # Confirm deletion
    confirm = messagebox.askyesno(
        "Confirm Deletion", 
        f"Are you sure you want to delete the template '{selected_name}'?",
        parent=dialog
    )
    
    if not confirm:
        return  # User canceled
    
    # Delete the template
    result = app.template_manager.delete_template(selected_name)
    
    if result:
        # Refresh the template list
        templates = app.template_manager.templates
        listbox.delete(0, tk.END)
        for template in templates:
            listbox.insert(tk.END, template.get("name", "Unnamed"))
            
        messagebox.showinfo("Success", f"Template '{selected_name}' deleted")
    else:
        messagebox.showerror("Error", f"Failed to delete template '{selected_name}'")

def import_template(app, dialog):
    """Import a template from file"""
    # Use the template manager's import function
    app.template_manager.import_template_ui(app)
    
    # Refresh the template list
    templates = app.template_manager.templates
    
    # Find the template listbox in the dialog
    for widget in dialog.winfo_children():
        if isinstance(widget, ttk.Notebook):
            for tab in widget.tabs():
                tab_name = widget.tab(tab)["text"]
                if tab_name == "Templates":
                    # We found the templates tab
                    templates_frame = widget.nametowidget(tab)
                    for child in templates_frame.winfo_children():
                        if isinstance(child, ttk.Frame) and child.winfo_children() and isinstance(child.winfo_children()[0], tk.Listbox):
                            # We found the listbox frame
                            listbox = child.winfo_children()[0]
                            
                            # Refresh the listbox
                            listbox.delete(0, tk.END)
                            for template in templates:
                                listbox.insert(tk.END, template.get("name", "Unnamed"))
                            break
                    break 