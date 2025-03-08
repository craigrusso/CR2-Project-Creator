#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import sys
import os
import tkinter as tk
from tkinter import ttk
from app.core.app_module import ProjectCreatorApp
from app.core.app_config import setup_dpi_awareness, APP_NAME, APP_VERSION
from app.utils.integration import patch_app_file

def enhance_app():
    """Create and run an enhanced version of the app with additional features"""
    # Enable HiDPI awareness
    setup_dpi_awareness()
    
    # Create root window
    root = tk.Tk()
    root.title(f"{APP_NAME} {APP_VERSION} - Enhanced")
    
    # Patch app_ui.create_ui
    from app.ui.app_ui import create_ui
    import app.ui.app_ui as app_ui
    app_ui.create_ui = patch_app_file()
    
    # Add custom styling
    ttk.Style().configure("TButton", padding=6, relief="flat", 
                           background="#cccccc", foreground="#000000")
    
    # Create application
    app = ProjectCreatorApp(root)
    
    # Add our enhancement plugin (this would be more sophisticated in real app)
    add_enhancements(app)
    
    # Run the application
    root.mainloop()
    
def add_enhancements(app):
    """Add enhancements to the base app"""
    # This is where actual enhancements would go
    pass

if __name__ == "__main__":
    enhance_app()
