#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import platform
import tkinter as tk
from app.core.app_module import ProjectCreatorApp
from app.core.app_config import APP_NAME, APP_VERSION, setup_dpi_awareness
from app.ui.app_theme import apply_dark_theme_to_template_section
from app.templates.template_manager_migration import TemplateManagerMigration

def main():
    """Main entry point for the CR2 Creative Pro application"""
    # Setup DPI awareness for Windows
    setup_dpi_awareness()
    
    # Set app ID for Windows taskbar
    if platform.system() == "Windows":
        try:
            import ctypes
            myappid = 'cr2creative.projectcreator.pro.2.1'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass
    
    # Create root window
    root = tk.Tk()
    root.title(f"{APP_NAME} {APP_VERSION}")
    
    # Set minimum size to ensure all buttons are visible
    root.minsize(width=950, height=650)
    
    # Create and start application
    app = ProjectCreatorApp(root)
    
    # If we're upgrading from an older version with dual template management systems,
    # apply the migration to ensure all data is properly transferred
    TemplateManagerMigration.apply_migration(app)
    
    # Apply dark theme to template section
    root.after(100, lambda: apply_dark_theme_to_template_section(app))
    
    # Start main loop
    root.mainloop()

if __name__ == "__main__":
    main()
