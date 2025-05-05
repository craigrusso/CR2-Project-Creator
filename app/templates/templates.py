#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import platform
import subprocess
import sys

# Using PyQt for the UI framework
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QInputDialog
from app.ui.color_scheme_pyqt import colors
UI_FRAMEWORK = 'pyqt'

import json

from app.utils.utils import load_config, save_config

# Import PyQt UI components
from app.ui.ui_components_pyqt import TemplateDirectoryEditor, StructureEditor


def populate_template_gallery(app):
    """
    Legacy function to populate the template gallery with available templates.
    Now delegates to the refactored gallery implementation.
    """
    # Check if we have the new gallery implementation
    if hasattr(app, 'template_gallery'):
        # Use the new implementation
        app.template_gallery.populate_gallery(force_refresh=True)
        return
        
    # Legacy implementation for backward compatibility
    try:
        # Clear existing templates
        if hasattr(app, 'template_list_frame') and hasattr(app.template_list_frame, 'scrollable_frame'):
            for widget in app.template_list_frame.scrollable_frame.winfo_children():
                widget.destroy()
        else:
            # Skip if template list frame not ready
            return
        
        # Get templates - use both file and directory templates
        templates = app.template_manager.get_all_templates()
        
        # Apply filters if any
        search = app.search_box.get() if hasattr(app, 'search_box') else ""
        
        # Safe category handling
        category = None
        if hasattr(app, 'category_var'):
            try:
                category = app.category_var.get()
            except (AttributeError, TypeError):
                category = "All"
        else:
            category = "All"
        
        if search or (category and category != "All"):
            try:
                templates = app.template_manager.filter_templates(search, category)
            except Exception as e:
                print(f"Error filtering templates: {e}")
        
        # Display message if no templates
        if not templates:
            no_templates_label = tk.Label(app.template_list_frame.scrollable_frame, 
                                        text="No templates found", font=("Segoe UI", 11),
                                        bg=colors["card_bg"], fg=colors["text"])
            no_templates_label.pack(pady=20)
            return
        
        # Display templates
        for template in templates:
            # Create the card with additional icons/badges for directory templates
            is_directory = template.get('type') == 'directory'
            
            # Use folder icon for directory templates
            if is_directory and 'icon' not in template:
                template['icon'] = '📁'  # Folder icon
            
            card = app.template_manager.create_template_card(
                app.template_list_frame.scrollable_frame, 
                template,
                select_callback=lambda t=template: select_template_from_gallery(app, t)
            )
            card.pack(fill=X, pady=5, padx=5)
            
            # Add badge for directory templates
            if is_directory:
                badge_frame = tk.Frame(card, bg="#3d85c6", padx=3, pady=1)
                badge_frame.place(relx=0.97, rely=0.1, anchor="ne")
                badge_label = tk.Label(badge_frame, text="DIR", font=("Segoe UI", 7, "bold"),
                                     bg="#3d85c6", fg="white")
                badge_label.pack()
            
            # Force fixed height for consistency
            card.config(height=80)
            card.pack_propagate(False)
            
            # Store template reference on the card for easier access
            card.template = template
            
            # Add hover effects directly to ensure they work
            card.bind("<Enter>", lambda e, c=card: _on_card_hover_enter(c))
            card.bind("<Leave>", lambda e, c=card: _on_card_hover_leave(c))
            
            # Apply highlight if this is the current template
            should_highlight = False
            
            # Check if this is the current template
            if hasattr(app, 'current_template') and app.current_template:
                if template == app.current_template:
                    should_highlight = True
                elif app.current_template.get("name") and template.get("name") == app.current_template.get("name"):
                    should_highlight = True
            
            if hasattr(app, 'selected_structure_template') and app.selected_structure_template:
                if template.get("name") == app.selected_structure_template:
                    should_highlight = True
                
            if should_highlight:
                # Apply blue highlight
                highlight_bg = "#2C4F76"
                highlight_border = "#4682B4"
                highlight_text = "white"
                
                # Set the card as highlighted to prevent hover effects
                card.is_highlighted = True
                
                # Apply highlight styling
                card.configure(bg=highlight_bg, highlightbackground=highlight_border, highlightthickness=2)
                card.info_frame.configure(bg=highlight_bg)
                
                # Highlight the icon and text
                if hasattr(card, 'icon_label'):
                    card.icon_label.configure(bg=highlight_bg, fg=highlight_text)
                
                for widget in card.info_frame.winfo_children():
                    widget.configure(bg=highlight_bg, fg=highlight_text)
                    
                # Force UI update
                card.update()

            if hasattr(card, 'edit_btn'):
                card.edit_btn.configure(bg=colors["card_bg"], fg="white")
            if hasattr(card, 'delete_btn'):
                card.delete_btn.configure(bg=colors["card_bg"], fg="white")
    except Exception as e:
        print(f"Error populating template gallery: {e}")
        import traceback
        traceback.print_exc()


def filter_templates(app, *args):
    """Filter templates based on search and category"""
    try:
        # Just re-populate the gallery which handles filtering
        populate_template_gallery(app)
        
        # Update status
        search_term = app.search_box.get()
        category = app.category_var.get()
        app.status_var.set(f"Filtering templates: Search='{search_term}' Category='{category}'")
    except Exception as e:
        print(f"Error filtering templates: {e}")


def select_template_from_gallery(app, template):
    """
    Legacy function to handle selection of a template from the gallery.
    Now delegates to the refactored gallery implementation.
    """
    # Check if we have the new gallery implementation
    if hasattr(app, 'template_gallery'):
        # Import the refactored function
        from app.templates.refactored_template_gallery import select_template_from_gallery as new_select_template
        # Use the new implementation
        return new_select_template(app, template)
        
    # Legacy implementation for backward compatibility
    try:
        # Set current template
        app.current_template = template
        
        # Get the template name
        name = template.get("name", "Unknown")
        is_directory = template.get('type') == 'directory'
        
        # Update UI to show selected template
        if is_directory:
            app.structure_template_info.config(text=f"{name} (Directory)")
        else:
            app.structure_template_info.config(text=name)
            
        app.selected_structure_template = name
        app.template_file_path = template.get('path', '')
        app.template_is_directory = is_directory
        
        # Set the associated structure if available
        if hasattr(app, 'structure_var'):
            structure_name = None
            
            # Check if the template has an associated structure
            if 'structure_name' in template:
                structure_name = template.get('structure_name')
            elif is_directory:
                # For directory templates, check the template.json file
                template_json_path = os.path.join(template.get('path', ''), "template.json")
                if os.path.exists(template_json_path):
                    try:
                        with open(template_json_path, 'r') as f:
                            template_info = json.load(f)
                            if 'structure_name' in template_info:
                                structure_name = template_info['structure_name']
                    except Exception as e:
                        print(f"Error reading template.json: {e}")
            
            # Try the template name as a structure name
            if not structure_name:
                template_structure_name = f"Template_{name}"
                if template_structure_name in app.template_manager.custom_structures:
                    structure_name = template_structure_name
            
            # Set the structure if found
            if structure_name and structure_name in app.template_manager.custom_structures:
                app.structure_var.set(structure_name)
            else:
                # Default to "Default" structure
                app.structure_var.set("Default")
        
        # Enable edit button if this is a directory template
        if hasattr(app, 'edit_template_dir_btn'):
            if is_directory:
                app.edit_template_dir_btn.config(state=NORMAL)
            else:
                app.edit_template_dir_btn.config(state=DISABLED)
        
        # Save selection to config
        config = load_config()
        config["structure_template"] = name
        save_config(config)
        
        # Highlight the selected template in gallery
        highlight_selected_template_in_gallery(app, template)
    except Exception as e:
        print(f"Error selecting template from gallery: {e}")
        import traceback
        traceback.print_exc()


def highlight_selected_template_in_gallery(app, selected_template):
    """Highlight the selected template in the gallery"""
    if not hasattr(app, 'template_list_frame') or not hasattr(app.template_list_frame, 'scrollable_frame'):
        return
        
    # Define highlight colors
    highlight_border = colors["highlight_border"]
    highlight_bg = colors["highlight_bg"]
    highlight_text = colors["highlight_text"]
    
    # Reset all cards first
    for card in app.template_list_frame.scrollable_frame.winfo_children():
        if hasattr(card, 'template') and hasattr(card, 'info_frame'):
            # Reset highlight flag
            if hasattr(card, 'is_highlighted'):
                card.is_highlighted = False
                
            # Reset styling to default
            card.configure(
                bg=colors["card_bg"], 
                highlightbackground=colors["card_bg"],  # Match background in default state
                highlightthickness=1
            )
            card.info_frame.configure(bg=colors["card_bg"])
            
            # Reset icon
            if hasattr(card, 'icon_label'):
                card.icon_label.configure(bg=colors["card_bg"], fg=colors["text"])
            
            # Reset info frame contents with appropriate colors
            if hasattr(card, 'name_label'):
                card.name_label.configure(bg=colors["card_bg"], fg=colors["text"])
            if hasattr(card, 'category_label'):
                card.category_label.configure(bg=colors["card_bg"], fg=colors["secondary_text"])
            if hasattr(card, 'desc_label'):
                card.desc_label.configure(bg=colors["card_bg"], fg=colors["text"])
    
    # Find and highlight the selected card
    for card in app.template_list_frame.scrollable_frame.winfo_children():
        if (hasattr(card, 'template') and card.template == selected_template) or \
           (hasattr(card, 'template') and card.template.get('name') == selected_template.get('name')):
            # Set highlight flag
            card.is_highlighted = True
            
            # Apply highlight styling
            card.configure(bg=highlight_bg, highlightbackground=highlight_border, highlightthickness=2)
            card.info_frame.configure(bg=highlight_bg)
            
            # Highlight the icon
            if hasattr(card, 'icon_label'):
                card.icon_label.configure(bg=highlight_bg, fg=highlight_text)
            
            # Highlight info frame contents
            if hasattr(card, 'name_label'):
                card.name_label.configure(bg=highlight_bg, fg=highlight_text)
            if hasattr(card, 'category_label'):
                card.category_label.configure(bg=highlight_bg, fg=highlight_text)
            if hasattr(card, 'desc_label'):
                card.desc_label.configure(bg=highlight_bg, fg=highlight_text)
            
            break


def create_template_directory(app):
    """Create a new template directory"""
    # Prompt the user to select a source directory
    source_dir = filedialog.askdirectory(
        title="Select Source Directory for Template"
    )
    
    if not source_dir:
        return  # User cancelled
    
    # Get template name
    name = simpledialog.askstring(
        "Template Name", 
        "Enter a name for this template:",
        initialvalue=os.path.basename(source_dir)
    )
    
    if not name:
        return  # User cancelled
    
    # Get category
    categories = app.template_manager.get_categories()
    
    # Create category selector dialog
    dialog = tk.Toplevel(app.root)
    dialog.title("Select Category")
    dialog.geometry("400x250")
    dialog.transient(app.root)
    dialog.grab_set()
    
    frame = tk.Frame(dialog, padx=20, pady=20)
    frame.pack(fill=BOTH, expand=True)
    
    tk.Label(frame, text="Select a category for this template:", anchor="w").pack(fill=X, pady=(0, 10))
    
    category_var = StringVar()
    if categories:
        category_var.set(categories[0])
    
    category_listbox = tk.Listbox(frame, selectmode=SINGLE, height=8)
    category_listbox.pack(fill=BOTH, expand=True, pady=(0, 10))
    
    for category in categories:
        category_listbox.insert(END, category)
    
    # Select the first item
    if categories:
        category_listbox.selection_set(0)
    
    # New category entry
    tk.Label(frame, text="Or create a new category:", anchor="w").pack(fill=X, pady=(10, 5))
    
    new_category_var = StringVar()
    new_category_entry = tk.Entry(frame, textvariable=new_category_var)
    new_category_entry.pack(fill=X, pady=(0, 10))
    
    # Description entry
    tk.Label(frame, text="Description (optional):", anchor="w").pack(fill=X, pady=(10, 5))
    
    description_var = StringVar()
    description_entry = tk.Entry(frame, textvariable=description_var)
    description_entry.pack(fill=X, pady=(0, 10))
    
    # Buttons
    button_frame = tk.Frame(frame)
    button_frame.pack(fill=X)
    
    result = [None]  # Use a list to store the result
    
    def on_ok():
        if new_category_var.get():
            result[0] = (name, new_category_var.get(), description_var.get())
        elif category_listbox.curselection():
            index = category_listbox.curselection()[0]
            result[0] = (name, categories[index], description_var.get())
        dialog.destroy()
    
    def on_cancel():
        dialog.destroy()
    
    ok_button = ttk.Button(button_frame, text="OK", command=on_ok)
    ok_button.pack(side=RIGHT, padx=(5, 0))
    
    cancel_button = ttk.Button(button_frame, text="Cancel", command=on_cancel)
    cancel_button.pack(side=RIGHT)
    
    # Wait for dialog to close
    app.root.wait_window(dialog)
    
    # Process result
    if result[0]:
        name, category, description = result[0]
        
        # Create the template directory
        success, result_path = app.template_manager.create_template_directory(
            name, category, source_dir, description
        )
        
        if success:
            messagebox.showinfo("Success", f"Template directory '{name}' created successfully")
            
            # Refresh the template gallery
            populate_template_gallery(app)
        else:
            messagebox.showerror("Error", f"Failed to create template directory: {result_path}")


def get_template_file(app):
    """Open file dialog to select a template file or directory"""
    try:
        # Show options dialog: File or Directory
        dialog = tk.Toplevel(app.root)
        dialog.title("Select Template Type")
        dialog.geometry("300x150")
        dialog.transient(app.root)
        dialog.grab_set()
        
        frame = tk.Frame(dialog, padx=20, pady=20)
        frame.pack(fill=BOTH, expand=True)
        
        tk.Label(frame, text="What type of template do you want to use?", 
              anchor="w").pack(fill=X, pady=(0, 10))
        
        result = [None]  # Use a list to store the result
        
        def select_file():
            result[0] = "file"
            dialog.destroy()
        
        def select_directory():
            result[0] = "directory"
            dialog.destroy()
        
        def cancel():
            dialog.destroy()
        
        button_frame = tk.Frame(frame)
        button_frame.pack(fill=X, pady=(10, 0))
        
        file_button = ttk.Button(button_frame, text="Template File", command=select_file)
        file_button.pack(side=LEFT, padx=(0, 5))
        
        dir_button = ttk.Button(button_frame, text="Template Directory", command=select_directory)
        dir_button.pack(side=LEFT)
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=cancel)
        cancel_button.pack(side=RIGHT)
        
        # Wait for dialog to close
        app.root.wait_window(dialog)
        
        # Process result
        if not result[0]:
            return  # User cancelled
        
        if result[0] == "file":
            # Select template file
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
        else:
            # Select template directory
            file_path = filedialog.askdirectory(
                title="Select Template Directory"
            )
        
        if not file_path:
            return  # User cancelled
        
        # Update UI elements
        app.template_file_path = file_path
        app.template_is_directory = os.path.isdir(file_path)
        
        # Set text based on file type
        if app.template_is_directory:
            app.template_file_info.config(text=f"Directory: {os.path.basename(file_path)}")
        else:
            app.template_file_info.config(text=f"File: {os.path.basename(file_path)}")
        
        # Create a template in the recent templates
        add_template_from_path(app, file_path)
        
        return file_path
    except Exception as e:
        print(f"Error selecting template file: {e}")
        return None


def add_template_from_path(app, file_path):
    """Add a template to recent templates from a file or directory path"""
    try:
        # Determine if this is a file or directory
        is_directory = os.path.isdir(file_path)
        
        # Create a minimal template object
        template = {
            'name': os.path.basename(file_path),
            'path': file_path,
            'type': 'directory' if is_directory else 'file',
            'category': 'Custom',
            'description': f"{'Directory' if is_directory else 'File'} template"
        }
        
        # Add to recent templates
        app.current_template = template
        
        # Tell the user we created a template from their selection
        app.show_status_message(f"Created template from {'directory' if is_directory else 'file'}: {os.path.basename(file_path)}")
    except Exception as e:
        print(f"Error adding template from path: {e}")


def clear_template_file(app):
    """Clear the current template file selection"""
    try:
        app.template_file_path = ""
        app.template_file_info.config(text="No template file selected")
        app.rename_template_file_btn.config(state=DISABLED)
        
        # Remove from config
        config = load_config()
        if "template_file_path" in config:
            config["template_file_path"] = ""
            save_config(config)
        
        # Update status
        app.status_var.set("Template file cleared")
    except Exception as e:
        print(f"Error clearing template file: {e}")


def reset_card_highlighting(card):
    """Helper function to reset card highlighting"""
    try:
        card.configure(
            bg=colors["bg"],
            highlightbackground=colors["bg"],  # Match background in default state
            highlightthickness=1
        )
        
        if hasattr(card, 'icon_label'):
            card.icon_label.configure(bg=colors["bg"], fg=colors["text"])
        if hasattr(card, 'info_frame'):
            card.info_frame.configure(bg=colors["bg"])
            for widget in card.info_frame.winfo_children():
                widget.configure(bg=colors["bg"], fg=colors["text"])
            # Reset name label to standard color
            if hasattr(card, 'name_label'):
                card.name_label.configure(fg=colors["text"])
            # Reset path label to secondary color
            if hasattr(card, 'path_label'):
                card.path_label.configure(fg=colors["secondary_text"])
                
        # Force UI update
        card.update()
    except Exception as e:
        print(f"Error resetting card highlighting: {e}")


def clear_structure_template(app):
    """Clear the current structure template selection"""
    try:
        app.current_template = None
        app.selected_structure_template = None
        app.structure_template_info.config(text="No structure template selected")
        
        # Remove from config
        config = load_config()
        if "structure_template" in config:
            config["structure_template"] = "Default"
            save_config(config)
        
        # Update status
        app.status_var.set("Structure template cleared")
    except Exception as e:
        print(f"Error clearing structure template: {e}")


def rename_template_file(app):
    """Rename the template file displayed in the UI"""
    try:
        # Verify we have a template file
        if not app.template_file_path:
            app.show_status_message("No template file selected to rename", message_type="error")
            return
            
        file_path = app.template_file_path
        old_name = os.path.basename(file_path)
        name, ext = os.path.splitext(old_name)
        
        # Ask for new name
        new_name = simpledialog.askstring("Rename Template File", 
                                        "Enter new name:",
                                        initialvalue=name)
        
        if new_name:
            # Just update the displayed name, not the actual file
            app.template_file_info.config(text=f"{new_name}{ext}")
            
            # Update status
            app.show_status_message(f"Template file renamed to '{new_name}{ext}'")
    except Exception as e:
        app.show_status_message(f"Failed to rename template file: {str(e)}", message_type="error")


def rename_current_template(app):
    """Rename the current template structure in the UI"""
    try:
        # Verify we have a template
        if not app.current_template:
            app.show_status_message("No structure template selected to rename", message_type="error")
            return
            
        old_name = app.current_template.get("name", "")
        
        # Ask for new name
        new_name = simpledialog.askstring("Rename Structure Template", 
                                        "Enter new name:",
                                        initialvalue=old_name)
        
        if new_name:
            # Update the display
            app.structure_template_info.config(text=new_name)
            
            # Update the template in place
            app.current_template["name"] = new_name
            
            # Update status
            app.show_status_message(f"Structure template renamed to '{new_name}'")
    except Exception as e:
        app.show_status_message(f"Failed to rename template to '{new_name}'", message_type="error")


def _on_card_hover_enter(card):
    """Handle hover enter for template card"""
    # Skip if card is already highlighted
    if hasattr(card, 'is_highlighted') and card.is_highlighted:
        return
        
    # Light grey hover effect
    hover_bg = "#303030"  # Slightly lighter than card_bg
    
    # Update the card and all its children - border should match background (no blue outline)
    card.configure(
        bg=hover_bg, 
        highlightbackground=hover_bg  # Match border to background (no visible border)
    )
    
    if hasattr(card, 'icon_label'):
        card.icon_label.configure(bg=hover_bg)
    
    if hasattr(card, 'info_frame'):
        card.info_frame.configure(bg=hover_bg)
        
        # Update all info frame widgets
        for widget in card.info_frame.winfo_children():
            widget.configure(bg=hover_bg)
    
    # Set cursor
    card.configure(cursor="hand2")
    

def _on_card_hover_leave(card):
    """Handle hover leave for template card"""
    # Skip if card is highlighted
    if hasattr(card, 'is_highlighted') and card.is_highlighted:
        return
        
    # Reset to card background
    card.configure(
        bg=colors["card_bg"], 
        highlightbackground=colors["card_bg"],  # Match background in default state
        highlightthickness=1
    )
    
    if hasattr(card, 'icon_label'):
        card.icon_label.configure(bg=colors["card_bg"], fg=colors["text"])
    
    if hasattr(card, 'info_frame'):
        card.info_frame.configure(bg=colors["card_bg"])
        
        # Reset all info frame widgets with appropriate colors
        if hasattr(card, 'name_label'):
            card.name_label.configure(bg=colors["card_bg"], fg=colors["text"])
        if hasattr(card, 'category_label'):
            card.category_label.configure(bg=colors["card_bg"], fg=colors["secondary_text"])
        if hasattr(card, 'desc_label'):
            card.desc_label.configure(bg=colors["card_bg"], fg=colors["text"])
    
    # Reset cursor
    card.configure(cursor="")


def edit_directory_template(app, template):
    """
    Open the template directory editor for editing a directory-based template
    
    Args:
        app: The application instance
        template: The template object to edit
    """
    # Check if this is a directory template
    if not template or template.get('type') != 'directory':
        messagebox.showerror("Error", "This is not a directory template")
        return
    
    # Get the template path
    template_path = template.get('path')
    if not template_path or not os.path.isdir(template_path):
        messagebox.showerror("Error", "Template directory not found")
        return
    
    # Create the editor
    editor = TemplateDirectoryEditor(
        app.root, 
        template_path=template_path,
        save_callback=lambda: refresh_after_edit(app, template)
    )
    
    # Wait for editor to close
    app.root.wait_window(editor)


def refresh_after_edit(app, template):
    """Refresh UI after editing a template"""
    # Refresh the template in the gallery
    populate_template_gallery(app)
    
    # Re-highlight the template
    highlight_selected_template_in_gallery(app, template)
    
    # Show a success message
    app.show_status_message(f"Template '{template.get('name', 'Unknown')}' updated successfully")


def _show_template_details(app, template):
    """Show details about a template"""
    details_window = tk.Toplevel(app.root)
    details_window.title("Template Details")
    details_window.geometry("500x350")
    details_window.transient(app.root)
    details_window.grab_set()
    
    frame = tk.Frame(details_window, padx=20, pady=20)
    frame.pack(fill=BOTH, expand=True)
    
    # Template name
    name_frame = tk.Frame(frame)
    name_frame.pack(fill=X, pady=(0, 10))
    tk.Label(name_frame, text="Name:", width=10, anchor="w").pack(side=LEFT)
    tk.Label(name_frame, text=template.get("name", "Unknown")).pack(side=LEFT, fill=X, expand=True)
    
    # Template type
    type_frame = tk.Frame(frame)
    type_frame.pack(fill=X, pady=(0, 10))
    tk.Label(type_frame, text="Type:", width=10, anchor="w").pack(side=LEFT)
    tk.Label(type_frame, text=template.get("type", "Unknown")).pack(side=LEFT, fill=X, expand=True)
    
    # Template category
    category_frame = tk.Frame(frame)
    category_frame.pack(fill=X, pady=(0, 10))
    tk.Label(category_frame, text="Category:", width=10, anchor="w").pack(side=LEFT)
    tk.Label(category_frame, text=template.get("category", "Unknown")).pack(side=LEFT, fill=X, expand=True)
    
    # Template description
    desc_frame = tk.Frame(frame)
    desc_frame.pack(fill=X, pady=(0, 10))
    tk.Label(desc_frame, text="Description:", width=10, anchor="w").pack(side=LEFT)
    tk.Label(desc_frame, text=template.get("description", ""), 
           wraplength=350).pack(side=LEFT, fill=X, expand=True)
    
    # Template path
    path_frame = tk.Frame(frame)
    path_frame.pack(fill=X, pady=(0, 10))
    tk.Label(path_frame, text="Path:", width=10, anchor="w").pack(side=LEFT)
    path_value = tk.Label(path_frame, text=template.get("path", ""), 
                       wraplength=350)
    path_value.pack(side=LEFT, fill=X, expand=True)
    
    # Add Open folder button if path exists
    if template.get("path") and os.path.exists(template.get("path")):
        open_btn = ttk.Button(frame, text="Open in File Explorer", 
                           command=lambda: _open_template_location(template.get("path")))
        open_btn.pack(pady=10)
    
    # Close button
    close_btn = ttk.Button(frame, text="Close", command=details_window.destroy)
    close_btn.pack(pady=10)


def _open_template_location(path):
    """Open the template location in file explorer"""
    if not path or not os.path.exists(path):
        return
    
    # If it's a file, open its containing directory
    if os.path.isfile(path):
        path = os.path.dirname(path)
    
    # Open in file explorer based on platform
    try:
        path = os.path.normpath(path)
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", path], check=True)
        else:  # Linux
            subprocess.run(["xdg-open", path], check=True)
    except Exception as e:
        print(f"Error opening location: {e}")


def edit_template_structure(app, template=None):
    """Edit the folder structure of the currently selected template"""
    # If no template is provided, use the current template
    if template is None:
        if not hasattr(app, 'current_template') or not app.current_template:
            app.show_status_message("Please select a template first.", message_type="error")
            return
        template = app.current_template
    
    is_directory = template.get('type') == 'directory'
    
    # If it's a directory template, open the directory editor
    if is_directory:
        edit_directory_template(app, template)
    else:
        # For file templates, we need to look up or create an associated structure
        template_name = template.get('name', '')
        template_structure_name = f"Template_{template_name}"
        
        # See if we have a structure with this name already
        structure_exists = False
        if template_structure_name in app.template_manager.custom_structures:
            structure_exists = True
            structure = app.template_manager.get_structure(template_structure_name)
        else:
            # Use default structure based on template type or project type
            template_type = template.get('type', 'Standard')
            
            # Make sure the template_type is properly capitalized to match the keys in DEFAULT_STRUCTURES
            if template_type.lower() == 'standard':
                template_type = 'Standard'  # Ensure proper capitalization
            
            try:
                structure = app.template_manager.get_default_structure(template_type)
            except KeyError:
                # If the template type doesn't have a defined structure, use Basic
                structure = app.template_manager.get_default_structure('Standard')
        
        # Open enhanced structure editor instead of the basic one
        from app.dialogs.dialog_windows_pyqt import show_enhanced_structure_editor
        from app.ui.structure_editor_enhanced import EnhancedStructureEditor
        
        # Create a custom save callback that uses the template structure name convention
        def template_save_callback(name, structure):
            _save_template_structure(app, template_structure_name, name, structure, template)
            return True
        
        # Create the enhanced editor
        editor = EnhancedStructureEditor(
            app.root,
            structure_name=template_structure_name,
            structure=structure,
            save_callback=template_save_callback
        )
        
        # Set the window title
        editor.setWindowTitle(f"Edit Structure for '{template_name}'")
        
        # If the structure already exists, lock the name field
        if structure_exists:
            editor.name_input.setText(template_structure_name)
            editor.name_input.setReadOnly(True)
        
        # Show the dialog
        editor.exec_()


def _save_template_structure(app, old_name, new_name, structure, template):
    """Save a structure associated with a template"""
    from app.core.structures import update_structure_dropdown
    
    # Save the structure
    success = app.template_manager.save_custom_structure(new_name, structure)
    
    if success:
        # Associate the structure with the template
        template_info_path = ""
        
        if template.get('type') == 'directory':
            # For directory templates, save in the template.json within the directory
            template_dir = template.get('path', '')
            if template_dir and os.path.isdir(template_dir):
                template_info_path = os.path.join(template_dir, "template.json")
        else:
            # For file templates, update our in-memory template
            template['structure_name'] = new_name
        
        # If we have a template.json, update it
        if template_info_path and os.path.exists(template_info_path):
            try:
                with open(template_info_path, 'r') as f:
                    template_info = json.load(f)
                
                template_info['structure_name'] = new_name
                
                with open(template_info_path, 'w') as f:
                    json.dump(template_info, f, indent=2)
            except Exception as e:
                print(f"Error updating template info: {e}")
        
        # Update UI
        messagebox.showinfo("Success", f"Structure saved and associated with template '{template.get('name', '')}'")
        
        # Update the structures dropdown
        update_structure_dropdown(app)
        
        # Set the structure as selected
        app.structure_var.set(new_name)
    else:
        messagebox.showerror("Error", f"Failed to save structure")


def apply_structure_to_template(app, template=None):
    """Apply a custom structure to the selected template"""
    # If no template is provided, use the current template
    if template is None:
        if not hasattr(app, 'current_template') or not app.current_template:
            app.show_status_message("Please select a template first.", message_type="error")
            return
        template = app.current_template
    
    # Get template name
    template_name = template.get('name', 'Unknown')
    
    # Create a dialog to select which structure to apply
    dialog = tk.Toplevel(app.root)
    dialog.title(f"Apply Structure to '{template_name}'")
    dialog.geometry("600x400")
    dialog.transient(app.root)
    dialog.grab_set()
    
    frame = tk.Frame(dialog, padx=20, pady=20, bg=colors["bg"])
    frame.pack(fill=BOTH, expand=True)
    
    # Header
    header = tk.Label(frame, text=f"Apply Structure to '{template_name}'", 
                    font=("Segoe UI", 14, "bold"), bg=colors["bg"], fg=colors["text"])
    header.pack(fill=X, pady=(0, 15))
    
    # Explanation
    explanation = tk.Label(frame, 
                         text="Select a custom structure to associate with this template. "
                              "This structure will be used whenever this template is selected.",
                         wraplength=560, justify=LEFT, bg=colors["bg"], fg=colors["text"])
    explanation.pack(fill=X, pady=(0, 15))
    
    # Get list of available structures
    available_structures = list(app.template_manager.custom_structures.keys())
    
    if not available_structures:
        # No custom structures available
        no_structures = tk.Label(frame, 
                              text="No custom structures available. Please create a custom structure first.",
                              wraplength=560, bg=colors["bg"], fg=colors["text"])
        no_structures.pack(pady=20)
        
        ttk.Button(frame, text="Create New Structure", 
                 command=lambda: (dialog.destroy(), 
                                 create_custom_structure(app))).pack(pady=10)
        
        ttk.Button(frame, text="Close", 
                 command=dialog.destroy).pack(pady=5)
        return
    
    # Add "Default" to the list of available structures
    available_structures = ["Default"] + available_structures
    
    # Currently selected structure
    current_structure = None
    # Check if the template has an associated structure
    if 'structure_name' in template:
        current_structure = template.get('structure_name')
    elif template.get('type') == 'directory':
        # For directory templates, check the template.json file
        template_path = template.get('path', '')
        if template_path and os.path.isdir(template_path):
            template_json_path = os.path.join(template_path, "template.json")
            if os.path.exists(template_json_path):
                try:
                    with open(template_json_path, 'r') as f:
                        template_info = json.load(f)
                        if 'structure_name' in template_info:
                            current_structure = template_info['structure_name']
                except Exception as e:
                    print(f"Error reading template.json: {e}")
    
    # Create a listbox with the available structures
    structures_frame = tk.Frame(frame, bg=colors["bg"])
    structures_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
    
    # Listbox with scrollbar
    scrollbar = ttk.Scrollbar(structures_frame)
    scrollbar.pack(side=RIGHT, fill=Y)
    
    listbox = tk.Listbox(structures_frame, yscrollcommand=scrollbar.set, 
                       font=("Segoe UI", 10), bg=colors["card_bg"], fg=colors["text"],
                       selectbackground="#4682B4", selectforeground="white",
                       height=10)
    listbox.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.config(command=listbox.yview)
    
    # Fill the listbox with available structures
    for i, structure_name in enumerate(available_structures):
        # Add a star to the currently selected structure
        display_name = structure_name
        if structure_name == current_structure:
            display_name = f"★ {structure_name}"
        
        listbox.insert(tk.END, display_name)
        
        # Select the current structure in the listbox
        if structure_name == current_structure:
            listbox.selection_set(i)
    
    # Preview section
    preview_frame = tk.Frame(frame, bg=colors["card_bg"], padx=15, pady=15)
    preview_frame.pack(fill=X, pady=(0, 15))
    
    preview_label = tk.Label(preview_frame, text="Structure Preview:", 
                          font=("Segoe UI", 10, "bold"), bg=colors["card_bg"], fg=colors["text"])
    preview_label.pack(anchor=tk.W, pady=(0, 5))
    
    preview_text = tk.Text(preview_frame, height=6, bg=colors["card_bg"], fg=colors["text"],
                        font=("Consolas", 9), relief=tk.FLAT)
    preview_text.pack(fill=X)
    preview_text.config(state=tk.DISABLED)  # Make it read-only
    
    # Function to update the preview when a structure is selected
    def update_preview(event=None):
        selected = listbox.curselection()
        if not selected:
            return
        
        index = selected[0]
        structure_name = available_structures[index]
        
        # Get the structure
        if structure_name == "Default":
            # Use default structure based on template type
            template_type = template.get('type', 'Standard')
            if template_type.lower() == 'standard':
                template_type = 'Standard'
            
            try:
                structure = app.template_manager.get_default_structure(template_type)
            except KeyError:
                structure = app.template_manager.get_default_structure('Standard')
        else:
            structure = app.template_manager.get_structure(structure_name)
        
        # Update preview
        preview_text.config(state=tk.NORMAL)
        preview_text.delete(1.0, tk.END)
        
        if structure:
            preview_content = "\n".join([f"• {folder}" for folder in structure[:15]])
            if len(structure) > 15:
                preview_content += f"\n... and {len(structure) - 15} more folders"
            preview_text.insert(tk.END, preview_content)
        else:
            preview_text.insert(tk.END, "No folders in this structure")
        
        preview_text.config(state=tk.DISABLED)
    
    # Bind the selection event
    listbox.bind('<<ListboxSelect>>', update_preview)
    
    # Update the preview for the initially selected item
    if listbox.curselection():
        update_preview()
    
    # Buttons
    button_frame = tk.Frame(frame, bg=colors["bg"])
    button_frame.pack(fill=X)
    
    # Apply button
    apply_button = ttk.Button(button_frame, text="Apply Structure", 
                           command=lambda: apply_selected_structure())
    apply_button.pack(side=tk.RIGHT, padx=(5, 0))
    
    # Cancel button
    cancel_button = ttk.Button(button_frame, text="Cancel", 
                            command=dialog.destroy)
    cancel_button.pack(side=tk.RIGHT)
    
    # Function to apply the selected structure
    def apply_selected_structure():
        selected = listbox.curselection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a structure to apply.")
            return
        
        index = selected[0]
        structure_name = available_structures[index]
        
        # If "Default" is selected, use None to remove any custom structure
        if structure_name == "Default":
            structure_name = None
        
        # Apply the structure to the template
        success = _associate_structure_with_template(app, template, structure_name)
        
        if success:
            messagebox.showinfo("Success", 
                              f"Structure '{structure_name or 'Default'}' applied to template '{template_name}'")
            dialog.destroy()
            
            # Update the UI to show the new structure
            if hasattr(app, 'structure_var') and structure_name:
                app.structure_var.set(structure_name)
            else:
                app.structure_var.set("Default")
        else:
            messagebox.showerror("Error", "Failed to apply structure to template")


def _associate_structure_with_template(app, template, structure_name):
    """Associate a structure with a template"""
    try:
        # For in-memory templates
        template['structure_name'] = structure_name
        
        # For directory templates, update the template.json file
        if template.get('type') == 'directory':
            template_path = template.get('path', '')
            if template_path and os.path.isdir(template_path):
                template_json_path = os.path.join(template_path, "template.json")
                
                # Read existing data or create new
                template_info = {}
                if os.path.exists(template_json_path):
                    try:
                        with open(template_json_path, 'r') as f:
                            template_info = json.load(f)
                    except:
                        pass
                
                # Update with new structure
                if structure_name:
                    template_info['structure_name'] = structure_name
                elif 'structure_name' in template_info:
                    del template_info['structure_name']  # Remove structure association
                
                # Save back to file
                with open(template_json_path, 'w') as f:
                    json.dump(template_info, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error associating structure with template: {e}")
        return False
