#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import platform
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication
from app.core.app_module_pyqt import ProjectCreatorApp
from app.core.app_config import APP_NAME, APP_VERSION, setup_dpi_awareness
from app.ui.app_theme_pyqt import apply_dark_theme_to_template_section, force_app_palette
from app.templates.template_manager_migration import TemplateManagerMigration

# This is the PyQt version of the application
UI_FRAMEWORK = 'pyqt'

def get_user_home_directory():
    """Get the user's home directory in a cross-platform way"""
    # Default approach for most platforms
    home_dir = os.path.expanduser("~")
    
    # Check if the path is valid/exists
    if not os.path.exists(home_dir):
        # Fallback methods for different platforms
        if platform.system() == "Windows":
            # Windows fallback methods
            home_drive = os.environ.get('HOMEDRIVE')
            home_path = os.environ.get('HOMEPATH')
            if home_drive and home_path:
                home_dir = os.path.join(home_drive, home_path)
            else:
                # Last resort - use current directory
                home_dir = os.getcwd()
        elif platform.system() == "Darwin":  # macOS
            # macOS fallbacks
            home_dir = os.environ.get('HOME', os.getcwd())
        else:  # Linux and others
            # Use environment variables
            home_dir = os.environ.get('HOME', os.getcwd())
    
    return home_dir

def main():
    """Main entry point for the Echelon application"""
    # Setup DPI awareness for Windows
    setup_dpi_awareness()
    
    # For macOS, set the application name before creating QApplication
    # This affects what appears in the menu bar
    QCoreApplication.setApplicationName(APP_NAME)
    QCoreApplication.setOrganizationName("CR2 Creative")
    QCoreApplication.setOrganizationDomain("cr2creative.com")
    
    # Set app ID for Windows taskbar
    if platform.system() == "Windows":
        try:
            import ctypes
            myappid = 'cr2creative.echelon.0.081'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            print(f"Warning: Could not set app ID: {e}")

    # Enable High DPI scaling with better font scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):  # Check if attribute exists
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # Initialize the PyQt application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    # Force application to use our custom palette regardless of system settings
    # This ensures a consistent UI appearance across all platforms
    force_app_palette(app)
    
    # On macOS, ensure we use our custom styling while maintaining native menu bar
    if platform.system() == "Darwin":  # macOS
        # Use native menu bar for better macOS integration
        app.setAttribute(Qt.AA_DontUseNativeMenuBar, False)
        
        # Apply an additional attribute to help prevent macOS from overriding our theme
        app.setAttribute(Qt.AA_DontShowIconsInMenus, True)
    
    # Create and show the main window
    main_window = ProjectCreatorApp()
    # Store the instance for future reference
    ProjectCreatorApp._instance = main_window
    main_window.show()
    
    # Apply template migration if needed
    TemplateManagerMigration.apply_migration(main_window)
    
    # Apply dark theme to template section
    apply_dark_theme_to_template_section(main_window)
    
    # Start the application main loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 