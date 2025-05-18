#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

# PATH FIX: Add explicit path handling for PyInstaller
import os
import sys
import platform

# Determine if we're running in a PyInstaller bundle
if getattr(sys, 'frozen', False):
    # Get the directory where the executable is located
    bundle_dir = os.path.dirname(sys.executable)
    
    # Add paths to sys.path to find modules
    if os.path.exists(os.path.join(bundle_dir, 'app')):
        sys.path.insert(0, os.path.join(bundle_dir, 'app'))
        print(f"Added {os.path.join(bundle_dir, 'app')} to sys.path")
    
    # Add the bundle dir itself
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)
        print(f"Added {bundle_dir} to sys.path")
    
    # Try alternate path for deeper bundling
    if os.path.exists(os.path.join(bundle_dir, '_internal', 'app')):
        sys.path.insert(0, os.path.join(bundle_dir, '_internal', 'app'))
        print(f"Added {os.path.join(bundle_dir, '_internal', 'app')} to sys.path")
        
    # For debugging in console
    print(f"Python path: {sys.path}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Bundle directory: {bundle_dir}")
    print(f"app directory exists: {os.path.exists(os.path.join(bundle_dir, 'app'))}")

# Now proceed with the original imports
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication
from app.core.app_module_pyqt import ProjectCreatorApp
from app.config.app_config import APP_NAME, APP_VERSION, setup_dpi_awareness
from app.ui.app_theme_pyqt import apply_dark_theme_to_template_section, force_app_palette, configure_styles
from app.templates.template_manager_migration import TemplateManagerMigration
from app.ui.tree_styling import apply_styling_to_all_tree_widgets
# Import QSettings if not already imported (might be handled by PyQt5 import)
from PyQt5.QtCore import QSettings 

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
    # print("DEBUG: Starting application initialization")
    
    # Setup DPI awareness for Windows
    setup_dpi_awareness()
    # print("DEBUG: DPI awareness configured")
    
    # For macOS, set the application name before creating QApplication
    # This affects what appears in the menu bar
    QCoreApplication.setApplicationName(APP_NAME)
    QCoreApplication.setOrganizationName("CR2 Creative")
    QCoreApplication.setOrganizationDomain("cr2creative.com")
    # print("DEBUG: Application core info set")
    
    # Set app ID for Windows taskbar
    if platform.system() == "Windows":
        try:
            import ctypes
            myappid = 'cr2creative.echelon.0.95'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            # print("DEBUG: Windows app ID set")
        except Exception as e:
            print(f"WARNING: Could not set app ID: {e}")

    # Enable High DPI scaling
    # print("DEBUG: Configuring high DPI settings")
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Initialize the PyQt application
    # print("DEBUG: Creating QApplication instance")
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    # Force application to use our custom palette regardless of system settings
    # print("DEBUG: Applying custom palette")
    force_app_palette(app)
    
    # Apply comprehensive styles from the theme module
    # print("DEBUG: Configuring global styles")
    configure_styles(app)
    
    # On macOS, ensure we use our custom styling while maintaining native menu bar
    if platform.system() == "Darwin":  # macOS
        # print("DEBUG: Configuring macOS-specific settings")
        # Use native menu bar for better macOS integration
        app.setAttribute(Qt.AA_DontUseNativeMenuBar, False)
        
        # Apply an additional attribute to help prevent macOS from overriding our theme
        app.setAttribute(Qt.AA_DontShowIconsInMenus, True)
    
    # Create and show the main window
    # print("DEBUG: Creating main application window")
    try:
        main_window = ProjectCreatorApp()
        # Store the instance for future reference
        ProjectCreatorApp._instance = main_window
        # print("DEBUG: Main window created successfully")
        
        # print("DEBUG: Showing main window")
        main_window.show()
        
        # Apply template migration if needed
        # print("DEBUG: Applying template migration")
        try:
            TemplateManagerMigration.apply_migration(main_window)
            # print("DEBUG: Template migration completed")
        except Exception as e:
            print(f"ERROR during template migration: {e}")
            import traceback
            traceback.print_exc()
        
        # Apply dark theme to template section
        # print("DEBUG: Applying dark theme to template section")
        try:
            apply_dark_theme_to_template_section(main_window)
            # print("DEBUG: Theme applied to template section")
        except Exception as e:
            print(f"ERROR applying theme: {e}")
            import traceback
            traceback.print_exc()
        
        # Apply tree styling to all tree widgets
        # print("DEBUG: Applying tree styling to all tree widgets")
        styled_count = apply_styling_to_all_tree_widgets(main_window)
        # print(f"DEBUG: Tree styling applied to all tree widgets ({styled_count} widgets styled)")
        
        # --- Connect state saving for TableView --- 
        def save_table_view_state():
            # Access the gallery and then the table view
            # This assumes main_window has access to the gallery which has the table view
            # Adjust the path as necessary based on your application structure
            try:
                # Example path: main_window -> central_widget -> template_gallery -> template_table_view
                gallery = main_window.template_gallery # Assuming gallery is directly accessible
                if hasattr(gallery, 'template_table_view') and gallery.template_table_view:
                    # print("DEBUG: Saving TemplateTableView state on exit...")
                    gallery.template_table_view.save_state()
                else:
                    # print("DEBUG: TemplateTableView not found, skipping state save.")
                    pass
            except AttributeError as ae:
                # print(f"DEBUG: Could not find gallery or table view for state saving: {ae}")
                pass
            except Exception as e:
                print(f"ERROR saving table view state: {e}")

        app.aboutToQuit.connect(save_table_view_state)
        # print("DEBUG: Connected aboutToQuit signal for saving TableView state.")
        # ------------------------------------------
        
        # print("DEBUG: Starting application main loop")
        return app.exec_()
    except Exception as e:
        print(f"CRITICAL ERROR during application startup: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 