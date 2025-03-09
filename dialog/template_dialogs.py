#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, StringVar, BooleanVar
from tkinter.constants import *

from app.ui.color_scheme import colors
from dialog.template_edit_dialog import edit_template_dialog
from dialog.category_dialog import create_new_category
from dialog.folder_dialog import create_new_folder
from dialog.template_management_dialog import manage_templates_dialog
from app.templates.templates import edit_template_structure

# Keeping this file as a facade to maintain backward compatibility
# All dialog functions are now imported from specific modules

# Export all functions to maintain the same API
__all__ = [
    'edit_template_dialog',
    'create_new_category',
    'create_new_folder',
    'manage_templates_dialog'
]

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
    
    # Get the main window's position and size
    root_x = app.root.winfo_x()
    root_y = app.root.winfo_y()
    root_width = app.root.winfo_width()
    root_height = app.root.winfo_height()
    
    # Calculate a position that won't cover the bottom buttons
    # Position the dialog in the upper portion of the main window
    dialog_width = 550
    dialog_height = 450
    dialog_x = root_x + (root_width - dialog_width) // 2
    dialog_y = root_y + 50  # Position it near the top with some padding
    
    dialog.geometry(f"{dialog_width}x{dialog_height}+{dialog_x}+{dialog_y}")
    dialog.transient(app.root)
    dialog.grab_set()
    
    # Make dialog resizable but with minimum size to ensure all controls are visible
    dialog.minsize(500, 400)
    
    # Use a two-part layout: content area and fixed button area at bottom
    # Create a canvas with scrollbar for the content
    canvas_container = tk.Frame(dialog)
    canvas_container.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    # Add canvas and scrollbar
    canvas = tk.Canvas(canvas_container, highlightthickness=0)
    scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
    
    # Configure the canvas
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Pack the scrollbar and canvas
    scrollbar.pack(side=RIGHT, fill=Y)
    canvas.pack(side=LEFT, fill=BOTH, expand=True)
    
    # Create a frame inside the canvas for the content
    content_frame = tk.Frame(canvas, padx=15, pady=15)
    
    # Add the content frame to the canvas
    canvas_window = canvas.create_window((0, 0), window=content_frame, anchor=NW)
    
    # Configure canvas to resize with window
    def on_canvas_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(canvas_window, width=event.width)
    
    # Bind events for scrolling
    canvas.bind("<Configure>", on_canvas_configure)
    content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    
    # Add mousewheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows/MacOS
    canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
    canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))  # Linux
    
    # Button frame - fixed at bottom
    button_frame = tk.Frame(dialog, padx=20, pady=10, bg=colors["bg"])
    button_frame.pack(fill=X, side=BOTTOM)
    
    # Add separator above button frame
    separator = ttk.Separator(dialog, orient='horizontal')
    separator.pack(fill=X, side=BOTTOM, before=button_frame)
    
    # Template name
    name_frame = tk.Frame(content_frame)
    name_frame.pack(fill=X, pady=(0, 15))
    
    tk.Label(name_frame, text="Template Name:").pack(side=LEFT)
    
    name_var = StringVar(value=template_name)
    name_entry = tk.Entry(name_frame, textvariable=name_var, width=30)
    name_entry.pack(side=LEFT, padx=(10, 0), fill=X, expand=True)
    
    # Category
    category_frame = tk.Frame(content_frame)
    category_frame.pack(fill=X, pady=(0, 15))
    
    tk.Label(category_frame, text="Category:").pack(side=LEFT)
    
    category_var = StringVar(value=template.get("category", "Custom"))
    categories = app.category_manager.get_all_categories()
    
    category_menu = ttk.OptionMenu(category_frame, category_var, category_var.get(), *categories)
    category_menu.pack(side=LEFT, padx=(10, 0))
    
    # New category button
    new_category_btn = ttk.Button(category_frame, text="New Category", 
                                command=lambda: create_new_category(app, category_var))
    new_category_btn.pack(side=RIGHT)
    
    # Folders section
    folders_frame = tk.Frame(content_frame)
    folders_frame.pack(fill=X, pady=(0, 15))
    
    tk.Label(folders_frame, text="Folders:").pack(anchor="w")
    
    # Create checkboxes for each folder
    folders_list_frame = tk.Frame(folders_frame)
    folders_list_frame.pack(fill=X, pady=(5, 0))
    
    folder_vars = {}
    for folder_name in app.template_manager.folders:
        var = BooleanVar(value=template_name in app.template_manager.folders[folder_name])
        folder_vars[folder_name] = var
        
        folder_check = ttk.Checkbutton(folders_list_frame, text=folder_name, variable=var)
        folder_check.pack(anchor="w")
    
    # Description
    desc_frame = tk.Frame(content_frame)
    desc_frame.pack(fill=X, pady=(0, 15))
    
    tk.Label(desc_frame, text="Description:").pack(anchor="w")
    
    desc_var = StringVar(value=template.get("description", ""))
    desc_entry = tk.Entry(desc_frame, textvariable=desc_var)
    desc_entry.pack(fill=X, pady=(5, 0))
    
    # Template file path (display only)
    file_frame = tk.Frame(content_frame)
    file_frame.pack(fill=X, pady=(0, 15))
    
    tk.Label(file_frame, text="Template File:").pack(anchor="w")
    
    file_path = template.get("file", "")
    if file_path and os.path.exists(file_path):
        # Truncate long paths
        if len(file_path) > 50:
            display_path = file_path[:20] + "..." + file_path[-27:]
        else:
            display_path = file_path
    else:
        display_path = "No file assigned"
    
    file_label = tk.Label(file_frame, text=display_path)
    file_label.pack(anchor="w", pady=(5, 0))
    
    # Change file button
    if file_path:
        change_file_btn = ttk.Button(file_frame, text="Change File", 
                                   command=lambda: change_template_file(dialog, template, file_label))
        change_file_btn.pack(anchor="w", pady=(5, 0))
    
    # Template Structure section
    structure_frame = tk.Frame(content_frame)
    structure_frame.pack(fill=X, pady=(0, 15))
    
    tk.Label(structure_frame, text="Template Structure:").pack(anchor="w")
    
    structure_btn = ttk.Button(structure_frame, text="Edit Template Structure",
                           command=lambda: edit_template_structure(app, template))
    structure_btn.pack(anchor="w", pady=(5, 0))
    
    # Buttons
    cancel_btn = ttk.Button(button_frame, text="Cancel", 
                         command=lambda: close_dialog(dialog, canvas))
    cancel_btn.pack(side=RIGHT, padx=(10, 0))
    
    save_btn = ttk.Button(button_frame, text="Save", 
                        command=lambda: save_and_close(
                            app, dialog, template, name_var.get(), category_var.get(), 
                            desc_var.get(), folder_vars, canvas
                        ))
    save_btn.pack(side=RIGHT)

    # Initialize UI
    dialog.wait_window()

def close_dialog(dialog, canvas):
    """Close dialog and clean up bindings"""
    # Unbind mousewheel events
    canvas.unbind_all("<MouseWheel>")
    canvas.unbind_all("<Button-4>")
    canvas.unbind_all("<Button-5>")
    
    # Destroy dialog
    dialog.destroy()

def save_and_close(app, dialog, template, new_name, new_category, 
                new_description, folder_vars, canvas):
    """Save changes and close dialog"""
    # First save changes
    result = save_template_changes(app, dialog, template, new_name, new_category, 
                          new_description, folder_vars)
    
    # If save was successful, clean up and close
    if result:
        # Unbind mousewheel events
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")
        
        # Close dialog
        dialog.destroy()

def change_template_file(dialog, template, file_label):
    """Change the file associated with a template"""
    import platform
    
    # Open file dialog
    if platform.system() == "Darwin":  # macOS
        file_path = filedialog.askopenfilename(
            title="Select Template File",
            filetypes=[("All Files", "*.*")]
        )
    else:
        file_path = filedialog.askopenfilename(
            title="Select Template File",
            filetypes=[
                ("Adobe Premiere", "*.prproj"),
                ("After Effects", "*.aep;*.aepx"),
                ("Photoshop", "*.psd"),
                ("Illustrator", "*.ai"),
                ("All Files", "*.*")
            ]
        )
    
    if not file_path:
        return
    
    # Update template
    template["file"] = file_path
    
    # Update display
    if len(file_path) > 50:
        display_path = file_path[:20] + "..." + file_path[-27:]
    else:
        display_path = file_path
    
    file_label.config(text=display_path)


def save_template_changes(app, dialog, template, new_name, new_category, 
                        new_description, folder_vars):
    """Save changes to a template"""
    old_name = template.get("name", "Unnamed Template")
    
    # Validate inputs
    if not new_name:
        messagebox.showerror("Error", "Template name cannot be empty")
        return False
    
    # Check for name conflicts if name changed
    if new_name != old_name:
        for t in app.template_manager.templates:
            if t != template and t.get("name") == new_name:
                messagebox.showerror("Error", f"Template '{new_name}' already exists")
                return False
    
    # Save changes
    try:
        # Handle rename if needed
        if new_name != old_name:
            # Rename template
            success = app.template_manager.rename_template(old_name, new_name)
            if not success:
                messagebox.showerror("Error", f"Failed to rename template to '{new_name}'")
                return False
            
            # Update folder references
            for folder_name in app.template_manager.folders:
                if old_name in app.template_manager.folders[folder_name]:
                    app.template_manager.folders[folder_name].remove(old_name)
                    app.template_manager.folders[folder_name].append(new_name)
        
        # Update template properties
        template["name"] = new_name
        template["category"] = new_category
        template["description"] = new_description
        
        # Save template file
        filename = new_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        file_path = os.path.join(app.template_manager.paths["templates_dir"], f"{filename}.json")
        
        with open(file_path, 'w') as f:
            import json
            json.dump(template, f, indent=2)
        
        # Update folder assignments
        for folder_name, var in folder_vars.items():
            # Check if folder assignment changed
            is_in_folder = new_name in app.template_manager.folders[folder_name]
            should_be_in_folder = var.get()
            
            if is_in_folder and not should_be_in_folder:
                # Remove from folder
                app.template_manager.folders[folder_name].remove(new_name)
            elif not is_in_folder and should_be_in_folder:
                # Add to folder
                app.template_manager.folders[folder_name].append(new_name)
        
        # Save folder changes
        app.template_manager.save_folders()
        
        # Update UI
        from app.templates.template_gallery_ui import populate_enhanced_gallery
        populate_enhanced_gallery(app)
        
        # Update status
        app.status_var.set(f"Template '{new_name}' updated")
        
        # Return success
        return True
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save template changes: {str(e)}")
        return False


def create_new_category(app, category_var=None):
    """Create a new template category"""
    new_category = simpledialog.askstring("New Category", "Enter new category name:")
    
    if not new_category:
        return
    
    # Validate category name
    if not new_category.strip():
        messagebox.showerror("Error", "Category name cannot be empty")
        return
    
    # Create the category
    success = app.category_manager.create_category(new_category)
    
    if success:
        # Update category dropdown in main UI
        try:
            categories = app.category_manager.get_all_categories()
            menu = app.category_var["menu"]
            menu.delete(0, "end")
            menu.add_command(label="All", command=lambda v="All": app.category_var.set(v))
            
            for category in categories:
                menu.add_command(label=category, command=lambda v=category: app.category_var.set(v))
            
            # Set the new category if a variable was provided
            if category_var:
                category_var.set(new_category)
        except Exception as e:
            print(f"Error updating category menu: {e}")
    else:
        messagebox.showerror("Error", f"Failed to create category '{new_category}'")


def create_new_folder(app):
    """Create a new template folder"""
    new_folder = simpledialog.askstring("New Folder", "Enter new folder name:")
    
    if not new_folder:
        return
    
    # Validate folder name
    if not new_folder.strip():
        messagebox.showerror("Error", "Folder name cannot be empty")
        return
    
    if new_folder in app.template_manager.folders:
        messagebox.showerror("Error", f"Folder '{new_folder}' already exists")
        return
    
    # Create the folder
    success = app.template_manager.create_folder(new_folder)
    
    if success:
        # Update folder dropdown using the central method
        app.template_manager.update_ui_folder_dropdown(app)
        
        # Show success message
        app.status_var.set(f"Created folder: {new_folder}")
        
        # Refreshes the enhanced gallery
        from app.templates.template_gallery_ui import populate_enhanced_gallery
        populate_enhanced_gallery(app)
    else:
        messagebox.showerror("Error", f"Failed to create folder '{new_folder}'")


def manage_templates_dialog(app):
    """Show dialog for managing templates and folders"""
    dialog = tk.Toplevel(app.root)
    dialog.title("Manage Templates")
    
    # Get the main window's position and size
    root_x = app.root.winfo_x()
    root_y = app.root.winfo_y()
    root_width = app.root.winfo_width()
    root_height = app.root.winfo_height()
    
    # Calculate a position that won't cover the bottom buttons
    dialog_width = 700
    dialog_height = 500
    dialog_x = root_x + (root_width - dialog_width) // 2
    dialog_y = root_y + 50  # Position it near the top with some padding
    
    dialog.geometry(f"{dialog_width}x{dialog_height}+{dialog_x}+{dialog_y}")
    dialog.transient(app.root)
    
    # Make dialog resizable but with minimum size to ensure all controls are visible
    dialog.minsize(650, 450)
    
    # Create notebook (tabs)
    notebook = ttk.Notebook(dialog)
    notebook.pack(fill=BOTH, expand=True, padx=20, pady=20)
    
    # Templates tab
    templates_tab = tk.Frame(notebook)
    notebook.add(templates_tab, text="Templates")
    
    # Folders tab
    folders_tab = tk.Frame(notebook)
    notebook.add(folders_tab, text="Folders")
    
    # Categories tab
    categories_tab = tk.Frame(notebook)
    notebook.add(categories_tab, text="Categories")
    
    # ===== Templates Tab =====
    
    templates_frame = tk.Frame(templates_tab, padx=10, pady=10)
    templates_frame.pack(fill=BOTH, expand=True)
    
    # Template list with scrollbar
    list_frame = tk.Frame(templates_frame)
    list_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
    
    templates_scrollbar = tk.Scrollbar(list_frame)
    templates_scrollbar.pack(side=RIGHT, fill=Y)
    
    templates_listbox = tk.Listbox(list_frame, yscrollcommand=templates_scrollbar.set,
                                font=("Segoe UI", 10))
    templates_listbox.pack(side=LEFT, fill=BOTH, expand=True)
    templates_scrollbar.config(command=templates_listbox.yview)
    
    # Populate templates list
    for template in app.template_manager.templates:
        template_name = template.get("name", "Unnamed Template")
        category = template.get("category", "Unknown")
        templates_listbox.insert(END, f"{template_name} ({category})")
    
    # Template action buttons
    template_buttons = tk.Frame(templates_frame)
    template_buttons.pack(fill=X)
    
    edit_template_btn = ttk.Button(template_buttons, text="Edit", 
                                 command=lambda: edit_selected_template(app, dialog, templates_listbox))
    edit_template_btn.pack(side=LEFT, padx=(0, 5))
    
    delete_template_btn = ttk.Button(template_buttons, text="Delete", 
                                   command=lambda: delete_selected_template(app, dialog, templates_listbox))
    delete_template_btn.pack(side=LEFT, padx=(0, 5))
    
    import_template_btn = ttk.Button(template_buttons, text="Import", 
                                   command=lambda: import_template(app, dialog))
    import_template_btn.pack(side=LEFT)
    
    # ===== Folders Tab =====
    
    folders_frame = tk.Frame(folders_tab, padx=10, pady=10)
    folders_frame.pack(fill=BOTH, expand=True)
    
    # Folders list with scrollbar
    folders_list_frame = tk.Frame(folders_frame)
    folders_list_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
    
    folders_scrollbar = tk.Scrollbar(folders_list_frame)
    folders_scrollbar.pack(side=RIGHT, fill=Y)
    
    folders_listbox = tk.Listbox(folders_list_frame, yscrollcommand=folders_scrollbar.set,
                               font=("Segoe UI", 10))
    folders_listbox.pack(side=LEFT, fill=BOTH, expand=True)
    folders_scrollbar.config(command=folders_listbox.yview)
    
    # Populate folders list
    for folder_name in app.template_manager.folders:
        count = len(app.template_manager.folders[folder_name])
        folders_listbox.insert(END, f"{folder_name} ({count} templates)")
    
    # Folder action buttons
    folder_buttons = tk.Frame(folders_frame)
    folder_buttons.pack(fill=X)
    
    add_folder_btn = ttk.Button(folder_buttons, text="New Folder",
                              command=lambda: add_folder_from_dialog(app, dialog, folders_listbox))
    add_folder_btn.pack(side=LEFT, padx=(0, 5))
    
    rename_folder_btn = ttk.Button(folder_buttons, text="Rename",
                                 command=lambda: rename_selected_folder(app, dialog, folders_listbox))
    rename_folder_btn.pack(side=LEFT, padx=(0, 5))
    
    delete_folder_btn = ttk.Button(folder_buttons, text="Delete",
                                 command=lambda: delete_selected_folder(app, dialog, folders_listbox))
    delete_folder_btn.pack(side=LEFT)
    
    # ===== Categories Tab =====
    
    categories_frame = tk.Frame(categories_tab, padx=10, pady=10)
    categories_frame.pack(fill=BOTH, expand=True)
    
    # Categories list with scrollbar
    categories_list_frame = tk.Frame(categories_frame)
    categories_list_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
    
    categories_scrollbar = tk.Scrollbar(categories_list_frame)
    categories_scrollbar.pack(side=RIGHT, fill=Y)
    
    categories_listbox = tk.Listbox(categories_list_frame, yscrollcommand=categories_scrollbar.set,
                                  font=("Segoe UI", 10))
    categories_listbox.pack(side=LEFT, fill=BOTH, expand=True)
    categories_scrollbar.config(command=categories_listbox.yview)
    
    # Populate categories list
    categories = app.category_manager.get_all_categories()
    for category in categories:
        # Count templates in this category
        count = 0
        for template in app.template_manager.templates:
            if template.get("category") == category:
                count += 1
        
        categories_listbox.insert(END, f"{category} ({count} templates)")
    
    # Category action buttons
    category_buttons = tk.Frame(categories_frame)
    category_buttons.pack(fill=X)
    
    add_category_btn = ttk.Button(category_buttons, text="New Category",
                                command=lambda: add_category_from_dialog(app, dialog, categories_listbox))
    add_category_btn.pack(side=LEFT)
    
    # Bottom buttons
    button_frame = tk.Frame(dialog)
    button_frame.pack(fill=X, padx=20, pady=20)
    
    close_btn = ttk.Button(button_frame, text="Close", command=dialog.destroy)
    close_btn.pack(side=RIGHT)


def edit_selected_template(app, dialog, listbox):
    """Edit the selected template from the management dialog"""
    selected = listbox.curselection()
    if not selected:
        messagebox.showerror("Error", "Please select a template to edit")
        return
    
    index = selected[0]
    template_text = listbox.get(index)
    template_name = template_text.split(" (")[0]
    
    # Find the template
    template_to_edit = None
    for template in app.template_manager.templates:
        if template.get("name") == template_name:
            template_to_edit = template
            break
    
    if template_to_edit:
        # Close management dialog and open edit dialog
        dialog.destroy()
        edit_template_dialog(app, template_to_edit)
    else:
        messagebox.showerror("Error", f"Template '{template_name}' not found")


def delete_selected_template(app, dialog, listbox):
    """Delete the selected template from the management dialog"""
    selected = listbox.curselection()
    if not selected:
        messagebox.showerror("Error", "Please select a template to delete")
        return
    
    index = selected[0]
    template_text = listbox.get(index)
    template_name = template_text.split(" (")[0]
    
    # Find the template
    template_to_delete = None
    for template in app.template_manager.templates:
        if template.get("name") == template_name:
            template_to_delete = template
            break
    
    if template_to_delete:
        # Delete template
        from app.templates.template_gallery_ui import delete_template_confirm
        success = delete_template_confirm(app, template_to_delete)
        
        if success:
            # Remove from listbox
            listbox.delete(index)
    else:
        messagebox.showerror("Error", f"Template '{template_name}' not found")


def import_template(app, dialog):
    """Import a template from the management dialog"""
    from app.ui.app_ui import run_import_dialog
    
    # Close management dialog and run import
    dialog.destroy()
    run_import_dialog(app)


def add_folder_from_dialog(app, dialog, listbox):
    """Add a new folder from the management dialog"""
    new_folder = simpledialog.askstring("New Folder", "Enter new folder name:")
    
    if not new_folder:
        return
    
    # Validate folder name
    if not new_folder.strip():
        messagebox.showerror("Error", "Folder name cannot be empty")
        return
    
    if new_folder in app.template_manager.folders:
        messagebox.showerror("Error", f"Folder '{new_folder}' already exists")
        return
    
    # Create the folder
    success = app.template_manager.create_folder(new_folder)
    
    if success:
        # Add to listbox
        listbox.insert(END, f"{new_folder} (0 templates)")
        
        # Update folder dropdown using the central method
        app.template_manager.update_ui_folder_dropdown(app)
        
        # Show success message
        app.status_var.set(f"Created folder: {new_folder}")
    else:
        messagebox.showerror("Error", f"Failed to create folder '{new_folder}'")


def rename_selected_folder(app, dialog, listbox):
    """Rename the selected folder"""
    selected = listbox.curselection()
    if not selected:
        messagebox.showerror("Error", "Please select a folder to rename")
        return
    
    index = selected[0]
    item_text = listbox.get(index)
    
    # Extract folder name from list item text
    folder_name = item_text.split(" (")[0]
    
    # Ask for new name
    new_name = simpledialog.askstring("Rename Folder", 
                                    f"Enter new name for folder '{folder_name}':", 
                                    initialvalue=folder_name)
    
    if not new_name:
        return
    
    # Validate new name
    if not new_name.strip():
        messagebox.showerror("Error", "Folder name cannot be empty")
        return
    
    if new_name in app.template_manager.folders:
        messagebox.showerror("Error", f"Folder '{new_name}' already exists")
        return
    
    # Rename the folder
    success = app.template_manager.rename_folder(folder_name, new_name)
    
    if success:
        # Update the listbox
        count = len(app.template_manager.folders[new_name])
        listbox.delete(index)
        listbox.insert(index, f"{new_name} ({count} templates)")
        
        # Update folder dropdown using the central method
        app.template_manager.update_ui_folder_dropdown(app)
        
        # Show success message
        app.status_var.set(f"Renamed folder: {folder_name} → {new_name}")
    else:
        messagebox.showerror("Error", f"Failed to rename folder '{folder_name}'")


def delete_selected_folder(app, dialog, listbox):
    """Delete the selected folder"""
    selected = listbox.curselection()
    if not selected:
        messagebox.showerror("Error", "Please select a folder to delete")
        return
    
    index = selected[0]
    item_text = listbox.get(index)
    
    # Extract folder name from list item text
    folder_name = item_text.split(" (")[0]
    
    # Check if this is a default folder that cannot be deleted
    if folder_name in ["Recent", "Favorites"]:
        messagebox.showerror("Error", f"'{folder_name}' is a default folder and cannot be deleted")
        return
    
    # Count templates in folder
    count = len(app.template_manager.folders[folder_name])
    
    # Confirm deletion
    message = f"Are you sure you want to delete the folder '{folder_name}'?"
    if count > 0:
        message += f"\n\nThis folder contains {count} templates. " + \
                 "The templates will not be deleted, but they will be removed from this folder."
    
    if not messagebox.askyesno("Confirm Deletion", message):
        return
    
    # Delete the folder
    success = app.template_manager.delete_folder(folder_name)
    
    if success:
        # Remove from listbox
        listbox.delete(index)
        
        # Update folder dropdown using the central method
        app.template_manager.update_ui_folder_dropdown(app)
        
        # Show success message
        app.status_var.set(f"Deleted folder: {folder_name}")
    else:
        messagebox.showerror("Error", f"Failed to delete folder '{folder_name}'")


def add_category_from_dialog(app, dialog, listbox):
    """Add a new category from the management dialog"""
    new_category = simpledialog.askstring("New Category", "Enter new category name:")
    
    if not new_category:
        return
    
    # Validate category name
    if not new_category.strip():
        messagebox.showerror("Error", "Category name cannot be empty")
        return
    
    # Create the category
    success = app.category_manager.create_category(new_category)
    
    if success:
        # Add to listbox
        listbox.insert(END, f"{new_category} (0 templates)")
        
        # Update category dropdown in main UI
        try:
            categories = ["All"] + app.category_manager.get_all_categories()
            menu = app.category_var["menu"]
            menu.delete(0, "end")
            
            menu.add_command(label="All", 
                        command=lambda v="All": (app.category_var.set(v), app.filter_templates()))
            
            for category in categories:
                if category != "All":
                    menu.add_command(label=category, 
                                command=lambda v=category: (app.category_var.set(v), app.filter_templates()))
            
            # Show success message
            app.status_var.set(f"Created category: {new_category}")
        except Exception as e:
            print(f"Error updating category menu: {e}")
    else:
        messagebox.showerror("Error", f"Failed to create category '{new_category}'")
