#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import sys

# Detect which UI framework is being used
if 'PyQt5' in sys.modules:
    # Import PyQt structures module
    from app.core.structures_pyqt import (
        create_custom_structure, save_custom_structure,
        edit_structure, update_custom_structure,
        manage_structures, rename_structure,
        delete_structure, update_structure_dropdown,
        highlight_current_structure, _update_structure_combo,
        _preview_structure, _edit_structure
    )
    UI_FRAMEWORK = 'pyqt'
else:
    # Use Tkinter version
    import tkinter as tk
    from tkinter import ttk, messagebox, simpledialog
    from tkinter.constants import *

    # Import from our centralized color scheme
    from app.ui.color_scheme import colors

    from app.ui.ui_components import StructureEditor

    UI_FRAMEWORK = 'tkinter'


    def create_custom_structure(app):
        """Create a new custom folder structure"""
        editor = StructureEditor(app.root, save_callback=lambda name, structure: save_custom_structure(app, name, structure))
        app.root.wait_window(editor)


    def save_custom_structure(app, name, structure):
        """Save a custom folder structure"""
        success = app.template_manager.save_custom_structure(name, structure)
        if success:
            messagebox.showinfo("Success", f"Structure '{name}' saved successfully")
            app.template_manager.load_custom_structures()
            update_structure_dropdown(app)
            app.structure_var.set(name)
            highlight_current_structure(app)
        else:
            messagebox.showerror("Error", f"Failed to save structure '{name}'")


    def edit_structure(app):
        """Edit the selected custom structure"""
        structure_name = app.structure_var.get()
        if structure_name == "Default":
            messagebox.showinfo("Information", "Cannot edit the default structure. Create a new custom structure instead.")
            return
        
        # Get the structure
        structure = app.template_manager.get_structure(structure_name)
        
        # Open editor
        editor = StructureEditor(app.root, structure=structure, title=f"Edit Structure - {structure_name}",
                              save_callback=lambda name, s: update_custom_structure(app, structure_name, name, s))
        editor.name_var.set(structure_name)
        app.root.wait_window(editor)


    def update_custom_structure(app, old_name, new_name, structure):
        """Update an existing custom structure"""
        # If name changed, rename first
        if old_name != new_name:
            renamed = app.template_manager.rename_custom_structure(old_name, new_name)
            if not renamed:
                messagebox.showerror("Error", f"Failed to rename structure from '{old_name}' to '{new_name}'")
                return
        
        # Save the updated structure
        success = app.template_manager.save_custom_structure(new_name, structure)
        if success:
            messagebox.showinfo("Success", f"Structure '{new_name}' updated successfully")
            app.template_manager.load_custom_structures()
            update_structure_dropdown(app)
            app.structure_var.set(new_name)
            highlight_current_structure(app)
        else:
            messagebox.showerror("Error", f"Failed to update structure '{new_name}'")


    def manage_structures(app):
        """Manage custom folder structures"""
        manage_window = tk.Toplevel(app.root)
        manage_window.title("Manage Custom Structures")
        manage_window.geometry("500x400")
        manage_window.transient(app.root)
        manage_window.grab_set()
        
        # Structure list frame with scrollbar
        list_frame = tk.Frame(manage_window, padx=20, pady=20)
        list_frame.pack(fill=BOTH, expand=True)
        
        tk.Label(list_frame, text="Custom Folder Structures", 
              font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 15))
        
        # Create listbox with scrollbar
        frame = tk.Frame(list_frame)
        frame.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        structure_listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Segoe UI", 10))
        structure_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=structure_listbox.yview)
        
        # Load structures
        structures = list(app.template_manager.custom_structures.keys())
        for structure in structures:
            structure_listbox.insert(END, structure)
        
        # Button frame
        button_frame = tk.Frame(list_frame)
        button_frame.pack(fill=X)
        
        # Buttons
        rename_btn = ttk.Button(button_frame, text="Rename", 
                              command=lambda: rename_structure(app, structure_listbox, structures))
        rename_btn.pack(side=LEFT, padx=(0, 5))
        
        edit_btn = ttk.Button(button_frame, text="Edit", 
                            command=lambda: edit_structure_from_list(app, structure_listbox, structures))
        edit_btn.pack(side=LEFT, padx=5)
        
        delete_btn = ttk.Button(button_frame, text="Delete", 
                              command=lambda: delete_structure(app, structure_listbox, structures))
        delete_btn.pack(side=LEFT, padx=5)
        
        new_btn = ttk.Button(button_frame, text="New Structure", 
                           command=lambda: create_custom_structure(app))
        new_btn.pack(side=LEFT, padx=5)
        
        close_btn = ttk.Button(button_frame, text="Close", command=manage_window.destroy)
        close_btn.pack(side=RIGHT)


    def rename_structure(app, listbox, structures):
        """Rename a custom structure from the management list"""
        selected = listbox.curselection()
        if not selected:
            messagebox.showerror("Error", "Please select a structure to rename")
            return
        
        index = selected[0]
        name = structures[index]
        
        # Get new name
        new_name = simpledialog.askstring("Rename Structure", 
                                        "Enter new name:", initialvalue=name)
        
        if new_name and new_name != name:
            # Rename the structure
            success = app.template_manager.rename_custom_structure(name, new_name)
            
            if success:
                # Update list
                structures[index] = new_name
                listbox.delete(index)
                listbox.insert(index, new_name)
                
                # Update dropdown
                update_structure_dropdown(app)
                
                # Update selected if needed
                if app.structure_var.get() == name:
                    app.structure_var.set(new_name)
                    highlight_current_structure(app)
                
                messagebox.showinfo("Success", f"Structure renamed to '{new_name}'")
            else:
                messagebox.showerror("Error", f"Failed to rename structure")


    def edit_structure_from_list(app, listbox, structures):
        """Edit a custom structure from the management list"""
        selected = listbox.curselection()
        if not selected:
            messagebox.showerror("Error", "Please select a structure to edit")
            return
        
        index = selected[0]
        name = structures[index]
        
        # Get the structure
        structure = app.template_manager.get_structure(name)
        
        # Open editor
        editor = StructureEditor(app.root, structure=structure, title=f"Edit Structure - {name}",
                              save_callback=lambda new_name, s: update_custom_structure_from_list(
                                  app, name, new_name, s, listbox, structures, index))
        editor.name_var.set(name)
        app.root.wait_window(editor)


    def update_custom_structure_from_list(app, old_name, new_name, structure, listbox, structures, index):
        """Update a custom structure from the management list"""
        # If name changed, rename first
        if old_name != new_name:
            renamed = app.template_manager.rename_custom_structure(old_name, new_name)
            if not renamed:
                messagebox.showerror("Error", f"Failed to rename structure from '{old_name}' to '{new_name}'")
                return
            
            # Update list
            structures[index] = new_name
            listbox.delete(index)
            listbox.insert(index, new_name)
            
            # Update dropdown
            update_structure_dropdown(app)
            
            # Update selected if needed
            if app.structure_var.get() == old_name:
                app.structure_var.set(new_name)
                highlight_current_structure(app)
        
        # Save the updated structure
        success = app.template_manager.save_custom_structure(new_name, structure)
        if success:
            messagebox.showinfo("Success", f"Structure '{new_name}' updated successfully")
            app.template_manager.load_custom_structures()
        else:
            messagebox.showerror("Error", f"Failed to update structure '{new_name}'")


    def delete_structure(app, listbox, structures):
        """Delete a custom structure from the management list"""
        selected = listbox.curselection()
        if not selected:
            messagebox.showerror("Error", "Please select a structure to delete")
            return
        
        index = selected[0]
        name = structures[index]
        
        # Confirm deletion
        confirm = messagebox.askyesno("Confirm Deletion", 
                                    f"Are you sure you want to delete the structure '{name}'?")
        if not confirm:
            return
        
        # Delete the structure
        success = app.template_manager.delete_custom_structure(name)
        
        if success:
            # Update list
            del structures[index]
            listbox.delete(index)
            
            # Update dropdown
            update_structure_dropdown(app)
            
            # Reset selected if needed
            if app.structure_var.get() == name:
                app.structure_var.set("Default")
                highlight_current_structure(app)
            
            messagebox.showinfo("Success", f"Structure '{name}' deleted")
        else:
            messagebox.showerror("Error", f"Failed to delete structure '{name}'")


    def update_structure_dropdown(app):
        """Update the structure dropdown with available structures"""
        menu = app.structure_menu
        
        # Clear the menu
        menu.delete(0, 'end')
        
        # Add the default structure
        menu.add_command(label="Default", 
                      command=lambda: app.set_structure("Default"))
        
        # Add the custom structures
        if app.template_manager.custom_structures:
            menu.add_separator()
            for name in sorted(app.template_manager.custom_structures.keys()):
                menu.add_command(label=name, 
                              command=lambda n=name: app.set_structure(n))


    def highlight_current_structure(app):
        """Apply background color to currently selected structure in dropdown"""
        structure_name = app.structure_var.get()
        menu = app.structure_menu
        
        # Clear any existing highlighting
        for i in range(menu.index('end') + 1):
            try:
                label = menu.entrycget(i, 'label')
                if label == structure_name:
                    menu.entryconfig(i, background=colors["highlight_bg"], 
                                  foreground="white", activebackground=colors["highlight_bg"],
                                  activeforeground="white")
                else:
                    menu.entryconfig(i, background="white", 
                                  foreground="black", activebackground=colors["hover_bg"],
                                  activeforeground="black")
            except:
                # Skip separators
                pass


    def _update_structure_combo(app):
        """Populate the structure combo box (replaced by dropdown menu in latest version)"""
        pass


    def _preview_structure(app):
        """Preview the selected structure"""
        from dialog.preview_dialog import PreviewDialog
        
        structure_name = app.structure_var.get()
        structure = app.template_manager.get_structure(structure_name)
        
        preview = PreviewDialog(app.root, structure)
        app.root.wait_window(preview)


    def _edit_structure(app):
        """Edit button handler"""
        structure_name = app.structure_var.get()
        if structure_name == "Default":
            messagebox.showinfo("Information", 
                              "Cannot edit the default structure. Create a new custom structure instead.")
        else:
            edit_structure(app)
