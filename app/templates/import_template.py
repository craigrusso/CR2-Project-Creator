#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Template import functionality.
This module provides both a standalone script entry point and a direct function.
macOS-specific version to fix filetypes issue.
"""

import os
import sys
import json
import platform
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

def get_config_paths():
    """Get paths for configuration files and directories"""
    config_dir = os.path.join(os.path.expanduser("~"), ".cr2creator")
    
    paths = {
        "config_dir": config_dir,
        "config_file": os.path.join(config_dir, "config.pkl"),
        "recent_projects_file": os.path.join(config_dir, "recent.pkl"),
        "templates_dir": os.path.join(config_dir, "templates"),
        "custom_structures_dir": os.path.join(config_dir, "structures")
    }
    
    # Create directories if they don't exist
    for dir_path in [config_dir, paths["templates_dir"], paths["custom_structures_dir"]]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
    
    return paths

def import_template():
    """
    Standalone import function for when run as a script
    """
    # Create a temporary root window
    root = tk.Tk()
    root.title("Import Template")
    root.withdraw()  # Hide the root window
    
    try:
        result = import_template_core(root)
        root.destroy()
        return result
    except Exception as e:
        print(f"Template import error: {e}", file=sys.stderr)
        try:
            root.destroy()
        except:
            pass
        return False

def import_template_direct():
    """
    Direct import function for when called from the main application
    """
    # Don't create a new root window, use the existing one
    return import_template_core(None)

def import_template_core(root=None):
    """
    Core import functionality that can be used both standalone and directly
    
    Args:
        root: Optional Tk root window. If None, no window will be created/destroyed
              (assume we're being called from an existing app)
    
    Returns:
        bool: True if import was successful, False otherwise
    """
    try:
        # Get config paths 
        config_paths = get_config_paths()
        templates_dir = config_paths["templates_dir"]
        
        # Make sure the directory exists
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
        
        # MacOS-specific handling for file dialog
        if platform.system() == "Darwin":
            # On macOS, use simplified filetypes or no filetypes to avoid the NSInvalidArgumentException
            file_path = filedialog.askopenfilename(
                title="Select Template File"
                # No filetypes parameter on macOS to avoid crash
            )
        else:
            # For other platforms, use the full filetypes specification
            file_path = filedialog.askopenfilename(
                title="Select Template File",
                filetypes=[
                    ("Project Files", "*.prproj *.aep *.aepx *.psd *.ai"),  # Fixed syntax
                    ("Adobe Premiere", "*.prproj"),
                    ("After Effects", "*.aep *.aepx"),  # Fixed syntax
                    ("Photoshop", "*.psd"),
                    ("Illustrator", "*.ai"),
                    ("All Files", "*.*")
                ]
            )
        
        if not file_path:
            return False  # User cancelled
        
        # Get file information
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        
        # Ask user for template name
        template_name = simpledialog.askstring(
            "Import Template", 
            "Template name:", 
            initialvalue=name
        )
        
        if not template_name:
            return False  # User cancelled
        
        # Determine category from file extension
        category = "Custom"
        if ext.lower() in ['.prproj']:
            category = "Video Editing"
            structure_type = "Video Editing"
        elif ext.lower() in ['.aep', '.aepx']:
            category = "Motion Graphics"
            structure_type = "Motion Graphics"
        elif ext.lower() in ['.psd', '.ai']:
            category = "Design"
            structure_type = "Design"
        else:
            category = "Custom"
            structure_type = "Standard"
        
        # Set icon based on category
        icons = {
            "Video Editing": "🎬",
            "Motion Graphics": "✨",
            "Design": "📷",
            "Audio": "🎧",
            "Custom": "📂"
        }
        icon = icons.get(category, "📂")
        
        # Create template info
        template = {
            "name": template_name,
            "category": category,
            "file": file_path,
            "type": structure_type,
            "description": f"{category} template",
            "structure_type": structure_type,
            "icon": icon,
            "created": datetime.datetime.now().isoformat()
        }
        
        # Save to file
        save_filename = template_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        save_path = os.path.join(templates_dir, f"{save_filename}.json")
        
        with open(save_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        # Show success message
        messagebox.showinfo(
            "Template Imported", 
            f"Template '{template_name}' imported successfully"
        )
        
        return True
        
    except Exception as e:
        # Show detailed error message
        messagebox.showerror(
            "Import Error", 
            f"Failed to import template: {str(e)}"
        )
        
        # Print to console for debugging
        print(f"Template import error: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    try:
        # When run directly, execute the standalone import function
        success = import_template()
        # Exit with status code (0 for success, 1 for failure)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Fatal error in import_template.py: {e}", file=sys.stderr)
        sys.exit(1)
