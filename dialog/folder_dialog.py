#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, StringVar
from tkinter.constants import *

def create_new_folder(app):
    """Create a new template folder"""
    # Ask for folder name
    folder_name = simpledialog.askstring(
        "New Folder", 
        "Enter a name for the new folder:",
        parent=app.root
    )
    
    if not folder_name:
        return  # User canceled
    
    # Check if folder already exists
    existing_folders = app.template_manager.get_folders()
    
    if folder_name in existing_folders:
        messagebox.showerror("Error", f"Folder '{folder_name}' already exists")
        return
    
    # Add the new folder
    app.template_manager.add_folder(folder_name)
    
    # Refresh UI components that display folders
    app.refresh_folders()
    
    return folder_name

def add_folder_from_dialog(app, dialog, listbox):
    """Add a new folder from the manage folders dialog"""
    # Ask for folder name
    folder_name = simpledialog.askstring(
        "New Folder", 
        "Enter a name for the new folder:",
        parent=dialog
    )
    
    if not folder_name:
        return  # User canceled
    
    # Check if folder already exists
    existing_folders = app.template_manager.get_folders()
    
    if folder_name in existing_folders:
        messagebox.showerror("Error", f"Folder '{folder_name}' already exists")
        return
    
    # Add the new folder
    app.template_manager.add_folder(folder_name)
    
    # Refresh the folder list
    folders = app.template_manager.get_folders()
    listbox.delete(0, tk.END)
    for folder in folders:
        listbox.insert(tk.END, folder)
    
    # Select the new folder
    try:
        index = folders.index(folder_name)
        listbox.selection_set(index)
        listbox.see(index)
    except ValueError:
        pass

def rename_selected_folder(app, dialog, listbox):
    """Rename a selected folder"""
    # Get selected folder
    selection = listbox.curselection()
    if not selection:
        messagebox.showinfo("Info", "Please select a folder to rename")
        return
    
    selected_index = selection[0]
    selected_folder = listbox.get(selected_index)
    
    # Ask for new folder name
    new_folder_name = simpledialog.askstring(
        "Rename Folder", 
        "Enter new folder name:",
        initialvalue=selected_folder,
        parent=dialog
    )
    
    if not new_folder_name:
        return  # User canceled
    
    # Check if already exists
    existing_folders = app.template_manager.get_folders()
    if new_folder_name in existing_folders:
        messagebox.showerror("Error", f"Folder '{new_folder_name}' already exists")
        return
    
    # Rename the folder
    try:
        # Update all templates that reference this folder
        templates = app.template_manager.templates
        for template in templates:
            if "folders" in template and selected_folder in template["folders"]:
                template["folders"].remove(selected_folder)
                template["folders"].append(new_folder_name)
                
                # Save the template
                app.template_manager.save_template_to_disk(template)
        
        # Update folder cache
        app.template_manager.rename_folder(selected_folder, new_folder_name)
        
        # Refresh the folder list
        folders = app.template_manager.get_folders()
        listbox.delete(0, tk.END)
        for folder in folders:
            listbox.insert(tk.END, folder)
        
        # Select the renamed folder
        try:
            index = folders.index(new_folder_name)
            listbox.selection_set(index)
            listbox.see(index)
        except ValueError:
            pass
        
        messagebox.showinfo("Success", f"Folder renamed to '{new_folder_name}'")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to rename folder: {str(e)}")

def delete_selected_folder(app, dialog, listbox):
    """Delete a selected folder"""
    # Get selected folder
    selection = listbox.curselection()
    if not selection:
        messagebox.showinfo("Info", "Please select a folder to delete")
        return
    
    selected_index = selection[0]
    selected_folder = listbox.get(selected_index)
    
    # Confirm deletion
    confirm = messagebox.askyesno(
        "Confirm Deletion", 
        f"Are you sure you want to delete the folder '{selected_folder}'?\n\n"
        "This will remove it from all templates that use it.",
        parent=dialog
    )
    
    if not confirm:
        return  # User canceled
    
    # Delete the folder
    try:
        # Update all templates that reference this folder
        templates = app.template_manager.templates
        for template in templates:
            if "folders" in template and selected_folder in template["folders"]:
                template["folders"].remove(selected_folder)
                
                # Save the template
                app.template_manager.save_template_to_disk(template)
        
        # Update folder cache
        app.template_manager.remove_folder(selected_folder)
        
        # Refresh the folder list
        folders = app.template_manager.get_folders()
        listbox.delete(0, tk.END)
        for folder in folders:
            listbox.insert(tk.END, folder)
        
        messagebox.showinfo("Success", f"Folder '{selected_folder}' deleted")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete folder: {str(e)}") 