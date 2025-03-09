#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import platform
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from app.core.app_module_pyqt import ProjectCreatorApp
from app.core.app_config import APP_NAME, APP_VERSION, setup_dpi_awareness
from app.ui.app_theme_pyqt import apply_dark_theme_to_template_section
from app.templates.template_manager_migration import TemplateManagerMigration

# This is the PyQt version of the application
UI_FRAMEWORK = 'pyqt'

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
        except Exception as e:
            print(f"Warning: Could not set app ID: {e}")

    # Enable High DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Initialize the PyQt application
    app = QApplication(sys.argv)
    app.setApplicationName(f"{APP_NAME}")
    app.setApplicationVersion(APP_VERSION)
    
    # Create and show the main window
    main_window = ProjectCreatorApp()
    main_window.show()
    
    # Apply template migration if needed
    TemplateManagerMigration.apply_migration(main_window)
    
    # Apply dark theme to template section
    apply_dark_theme_to_template_section(main_window)
    
    # Start the application main loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 