#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import platform
import sys
import os
import shutil # Ensure shutil is imported
import json
import logging
import struct # For checking if we're running on ARM64

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QCoreApplication, QSettings, QTimer
from PyQt6.QtGui import QIcon
from app.core.app_module_pyqt import ProjectCreatorApp
from app.config.app_config import APP_NAME, APP_VERSION, setup_dpi_awareness, APP_BUILD_NUMBER
from app.ui.app_theme_pyqt import apply_dark_theme_to_template_section, force_app_palette, configure_styles
from app.templates.template_manager_migration import TemplateManagerMigration
from app.ui.tree_styling import apply_styling_to_all_tree_widgets, refresh_all_tree_icons
from app.ui.icon_utilities import clear_icon_cache

# Import the license manager for license checking
from app.utils.security.license_manager import LicenseManager, TrialNagDialog
from PyQt6.QtWidgets import QDialog

# Import the EULA Dialog
from app.dialogs.eula_dialog import EULADialog

# Import for deploying example templates
from app.core.config_manager import get_templates_path, get_settings_path
from app.utils.utils import load_json_file, save_json_file

# Import our new logging system
from app.utils.logging_utils import (
    initialize_logging, debug, info, warning, error, critical, 
    exception, detect_and_set_environment, set_production_mode, set_log_level, enable_console_logging, enable_file_logging
)

# Import the refactored category update manager getter
from app.templates.category_update_manager import get_instance as get_category_update_manager_instance
from app.templates.category_update_manager import ensure_all_combos_have_hover_delegates # For direct call if needed
from app.templates.category_update_manager import diagnose_category_dropdown_issue as deprecated_diagnose_dropdown_issue

# This is the PyQt version of the application
UI_FRAMEWORK = 'pyqt6'

def is_arm64():
    """Check if we're running on ARM64 architecture"""
    try:
        if platform.system() == "Windows":
            # On Windows, check the processor architecture
            return platform.machine().lower() in ["arm64", "aarch64"]
        elif platform.system() == "Darwin":  # macOS
            # On macOS, check using sysctl
            import subprocess
            result = subprocess.run(["sysctl", "-n", "hw.optional.arm64"], 
                                   capture_output=True, text=True, check=False)
            return result.returncode == 0 and result.stdout.strip() == "1"
        else:  # Linux and others
            return platform.machine().lower() in ["arm64", "aarch64"]
    except Exception as e:
        debug(f"Error checking for ARM64: {e}")
        # Default to False if we can't determine
        return False

def deploy_example_templates():
    """
    Copies bundled example templates to the user's template directory,
    placing them inside an 'Examples' subdirectory.
    """
    try:
        base_user_templates_path = get_templates_path() # e.g., $HOME/Library/Application Support/Echelon/Templates
        
        # Define the "Examples" subdirectory
        user_examples_subdirectory_path = os.path.join(base_user_templates_path, "Examples")

        bundled_examples_dir_name = "bundled_example_templates"
        
        source_templates_base_dir = None # Initialize
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            possible_source_paths = [
                os.path.join(sys._MEIPASS, "app", "assets", bundled_examples_dir_name),
                os.path.join(sys._MEIPASS, "assets", bundled_examples_dir_name),
                os.path.join(sys._MEIPASS, bundled_examples_dir_name)
            ]
            for path_attempt in possible_source_paths:
                if os.path.isdir(path_attempt):
                    source_templates_base_dir = path_attempt
                    break
            if source_templates_base_dir is None:
                 error(f"Bundled example templates source directory not found in PyInstaller bundle. Tried: {possible_source_paths}")
                 return
        else:
            project_root = os.path.dirname(os.path.abspath(__file__))
            source_templates_base_dir = os.path.join(project_root, "app", "assets", bundled_examples_dir_name)

        if not os.path.isdir(source_templates_base_dir):
            debug(f"Bundled example templates source directory not found at: {source_templates_base_dir}")
            return

        # Create the base user templates directory if it doesn't exist
        if not os.path.exists(base_user_templates_path):
            try:
                os.makedirs(base_user_templates_path)
            except OSError as e:
                error(f"Could not create base user templates directory: {base_user_templates_path} - {e}")
                return
        
        # Create the "Examples" subdirectory if it doesn't exist
        if not os.path.exists(user_examples_subdirectory_path):
            try:
                os.makedirs(user_examples_subdirectory_path)
            except OSError as e:
                error(f"Could not create user examples subdirectory: {user_examples_subdirectory_path} - {e}")
                return

        example_template_files = [
            "Template_Standard_Video_Project.json",
            "Template_Music_Production_Project.json",
            "Template_VFX_Compositing_Project.json",
            "Template_Generic_Game_Development_Project.json",
            "Template_Python_Web_Application.json",
            "Template_Simple_Python_Script_Project.json"
        ]

        # This list will store the actual UI names of templates successfully deployed or found
        deployed_example_template_ui_names = []

        for template_file_name in example_template_files:
            source_file_path = os.path.join(source_templates_base_dir, template_file_name)
            destination_file_path = os.path.join(user_examples_subdirectory_path, template_file_name) 

            if not os.path.exists(source_file_path):
                error(f"Source example template file not found: {source_file_path}")
                continue

            template_ui_name = None
            try:
                # Read the source template to get its UI name
                with open(source_file_path, 'r', encoding='utf-8') as f_src:
                    template_content = json.load(f_src)
                    if isinstance(template_content, dict) and "name" in template_content:
                        template_ui_name = template_content["name"]
                    else:
                        debug(f"Could not find 'name' key in {source_file_path}. This template may not be correctly listed in the 'Examples' folder.")
                        pass
            except Exception as e_read_name:
                error(f"Could not read UI name from source template {source_file_path}: {e_read_name}")
            
            # Flag to indicate if this template is considered successfully "present" at the destination
            is_template_present_at_dest = False

            if not os.path.exists(destination_file_path):
                try:
                    shutil.copy2(source_file_path, destination_file_path)
                    is_template_present_at_dest = True
                except Exception as e_copy:
                    error(f"Could not copy example template {template_file_name}: {e_copy}")
            else:
                is_template_present_at_dest = True # Already exists
            
            if is_template_present_at_dest and template_ui_name:
                if template_ui_name not in deployed_example_template_ui_names: # Avoid duplicates if filenames somehow led to same UI name
                    deployed_example_template_ui_names.append(template_ui_name)
        
        # Ensure "Examples" folder is registered in folders.json and contains the UI names
        try:
            settings_dir = get_settings_path()
            folders_json_path = os.path.join(settings_dir, "folders.json")
            
            if not os.path.exists(settings_dir):
                os.makedirs(settings_dir, exist_ok=True)

            folders_data = load_json_file(folders_json_path)

            if folders_data is None: 
                folders_data = {}    

            if not isinstance(folders_data, dict):
                debug(f"Content of {folders_json_path} was not a dictionary. Resetting to empty dict.")
                folders_data = {}

            # Ensure "Examples" key exists and its value is a list
            if "Examples" not in folders_data or not isinstance(folders_data["Examples"], list):
                folders_data["Examples"] = []

            # Add UI names of deployed example templates to the list if not already present
            made_changes_to_examples_list = False
            for ui_name in deployed_example_template_ui_names:
                if ui_name not in folders_data["Examples"]:
                    folders_data["Examples"].append(ui_name)
                    made_changes_to_examples_list = True
            
            if made_changes_to_examples_list:
                debug("Updated 'Examples' folder with new templates")

            # Save folders_data back to folders.json
            if save_json_file(folders_json_path, folders_data):
                debug(f"Successfully saved 'Examples' folder to {folders_json_path}")
            else:
                error(f"Failed to save {folders_json_path} after 'Examples' folder processing (save_json_file returned false).")

        except Exception as e_folders_json:
            error(f"Could not update {folders_json_path} for 'Examples' folder registration: {e_folders_json}")
            exception("Exception details:")

    except Exception as e:
        error(f"Failed to deploy example templates into Examples subfolder: {e}")
        exception("Exception details:")

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

def log_system_info():
    """Log important system information for debugging"""
    try:
        info(f"System: {platform.system()} {platform.version()}")
        info(f"Python: {sys.version}")
        info(f"Executable: {sys.executable}")
        info(f"Architecture: {platform.machine()}")
        info(f"ARM64 detected: {is_arm64()}")
        
        # Log PyQt version
        try:
            from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
            info(f"Qt version: {QT_VERSION_STR}")
            info(f"PyQt6 version: {PYQT_VERSION_STR}")
        except ImportError:
            pass
        
        # Log current directory
        info(f"Current working directory: {os.getcwd()}")
        info(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
    except Exception as e:
        error(f"Error logging system info: {e}")

def main():
    """Main entry point for the Echelon application"""
    import faulthandler # Add import here
    faulthandler.enable() # Enable it immediately
    try:
        # Initialize logging system
        initialize_logging()
        
        # Log system information for debugging
        log_system_info()
        
        # Load the user's saved logging preferences instead of forcing production mode
        settings = QSettings()
        if settings.contains('logging/level'):
            # User has set preferences before, load them
            # The set_log_level, enable_console_logging, and enable_file_logging functions
            # will use the values saved in QSettings
            
            # Get the saved log level
            level_name = settings.value('logging/level', 'INFO')
            log_level = getattr(logging, level_name, logging.INFO)
            set_log_level(log_level)
            
            # Get console and file logging settings
            console_enabled = settings.value('logging/console_enabled', False, type=bool)
            file_enabled = settings.value('logging/file_enabled', True, type=bool)
            
            # Apply settings
            enable_console_logging(console_enabled)
            enable_file_logging(file_enabled)
            
            info(f"Starting {APP_NAME} v{APP_VERSION} with user-configured logging settings")
        else:
            # First run or no user preferences, use production mode
            set_production_mode()
            info(f"Starting {APP_NAME} v{APP_VERSION} with production logging settings")
        
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
                
                # Set explicit AppUserModelID for Windows taskbar
                # This MUST match the ID in the manifest file
                app_version_for_id = APP_VERSION.replace('.', '_') # Ensure it's a valid ID component
                myappid = f'cr2creative.echelon.{app_version_for_id}.{APP_BUILD_NUMBER}'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception as e:
                debug(f"Could not set app ID: {e}")
                pass

        # Initialize the PyQt application
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(APP_VERSION)
        
        # Setup has succeeded, show splash window
        # splash_window.hide()  # Commented out as splash_window doesn't exist in this version
        
        # --- EULA Check ---
        if not EULADialog.show_eula_if_needed():
            return 1 # Exit cleanly if EULA declined
        
        # Force application to use our custom palette regardless of system settings
        force_app_palette(app)
        
        # Set application icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "assets", "icon.png")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        else:
            debug(f"Application icon not found at {icon_path}")
            pass
        
        # Apply comprehensive styles from the theme module
        configure_styles(app)
        
        # On macOS, ensure we use our custom styling while maintaining native menu bar
        if platform.system() == "Darwin":  # macOS
            # Use native menu bar for better macOS integration
            app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, False)
            
            # Apply an additional attribute to help prevent macOS from overriding our theme
            app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, True)
        
        # Check license status before proceeding
        license_manager = LicenseManager()
        
        # --- Trial Logic Enhancement ---
        # Check if a license was ever activated on this installation
        settings = QSettings() # This is the QSettings instance used by main.py's logic
        was_ever_licensed = settings.value("license/was_ever_licensed", False, type=bool)

        # Determine if we can proceed based on license status
        can_proceed = False # Default to false, must pass checks

        if license_manager.is_licensed():
            can_proceed = True
            # If licensed now, ensure the 'was_ever_licensed' flag is set
            if not was_ever_licensed:
                settings.setValue("license/was_ever_licensed", True)

        else:
            # --- Check if trial should be bypassed ---
            if was_ever_licensed:
                # Force activation dialog - treat as if trial expired
                time_parts = {'days': 0, 'hours': 0, 'minutes': 0}  # Correct format for time_parts
                trial_dialog = TrialNagDialog(None, license_manager, time_parts=time_parts)  # Pass as named parameter
                dialog_result = trial_dialog.exec()
                if dialog_result == QDialog.DialogCode.Accepted and license_manager.is_licensed():
                    can_proceed = True
                    # Ensure flag is set (should be already, but belt-and-suspenders)
                    if not settings.value("license/was_ever_licensed", False, type=bool):
                         settings.setValue("license/was_ever_licensed", True)
                else:
                    can_proceed = False # Exit if activation fails/cancelled
            else:
                # --- Normal Trial Check (only if never licensed before) ---
                # Ensure trial start/end times are initialized in settings if this is the first run for the trial
                # by calling is_trial_active() first. It will return True if trial is new or ongoing.
                if license_manager.is_trial_active(): 
                    time_parts = license_manager.get_trial_time_remaining_parts()

                    # Show trial nag dialog
                    trial_dialog = TrialNagDialog(None, license_manager, time_parts=time_parts)
                    dialog_result = trial_dialog.exec()

                    # Check status AFTER dialog closes
                    if dialog_result == QDialog.DialogCode.Accepted:
                        if license_manager.is_licensed(): # Check if activation occurred
                             can_proceed = True
                             # Set the flag since activation was successful
                             settings.setValue("license/was_ever_licensed", True)
                        else: # No activation, but accepted means continue trial
                             can_proceed = True
                    else: # Dialog was rejected (Cancel/Exit) or closed
                        can_proceed = False # Stays False
                else: # is_trial_active() returned False, meaning trial has genuinely expired according to its own precise check
                    time_parts = {'days': 0, 'hours': 0, 'minutes': 0} # Ensure time_parts show zero
                    # Trial expired (and never licensed before), show the nag dialog with exit option only
                    trial_dialog = TrialNagDialog(None, license_manager, time_parts=time_parts)
                    dialog_result = trial_dialog.exec()

                    # Check status AFTER dialog closes
                    if dialog_result == QDialog.DialogCode.Accepted and license_manager.is_licensed():
                         can_proceed = True
                         # Set the flag since activation was successful
                         settings.setValue("license/was_ever_licensed", True)
                    else: # Dialog was rejected (Exit) or closed
                        can_proceed = False # Stays False

        # Final decision based on the logic above
        if not can_proceed:
            return 0
        
        # Deploy example templates if necessary
        deploy_example_templates()
        
        # Create and show the main window
        main_window = ProjectCreatorApp()
        # Store the instance for future reference
        ProjectCreatorApp._instance = main_window
        
        # Initialize the CategoryUpdateManager with the app instance
        # from app.templates.category_update_manager import get_instance #, test_category_update_manager # Old import
        category_manager = get_category_update_manager_instance(main_window)
        info(f"Initialized CategoryUpdateManager for the application: {category_manager}")
        
        # Register CategoryUpdateManager with all template forms
        # This logic for finding template forms was previously commented out and can remain so,
        # as the new CategoryUpdateManager updates comboboxes globally.
        # def ensure_template_forms_have_category_manager():
        
        main_window.show()
        
        # Schedule initial category update after main window is shown and UI is likely stable
        # The new manager handles its own logic, but an initial explicit call can be good.
        QTimer.singleShot(1000, category_manager.force_immediate_global_update)
        info("Scheduled initial force_immediate_global_update for categories.")
        
        # Apply template migration if needed
        try:
            TemplateManagerMigration.apply_migration(main_window)
        except Exception as e:
            error(f"Error during template migration: {e}")
            exception("Template migration failure details:")
        
        # Apply dark theme to template section
        try:
            apply_dark_theme_to_template_section(main_window)
        except Exception as e:
            error(f"Error applying theme: {e}")
            exception("Theme application failure details:")
        
        # Apply tree styling to all tree widgets
        styled_count = apply_styling_to_all_tree_widgets(main_window)
        
        # Force a complete icon cache refresh to ensure we're using platform-native icons
        clear_icon_cache()
        
        # Force icon cache refresh and update all tree icons
        refresh_count = refresh_all_tree_icons()
        
        # Schedule another refresh after a short delay to ensure everything is loaded
        QTimer.singleShot(1000, lambda: refresh_all_tree_icons())
        
        # Schedule the category manager's force update (this is the line at 472)
        # This is likely redundant if force_immediate_global_update is called above,
        # but we can ensure delegates are applied after a delay if needed.
        # QTimer.singleShot(1000, category_manager.force_immediate_global_update) # Changed from force_update_all_category_combos
         # QTimer.singleShot(1500, lambda: ensure_all_combos_have_hover_delegates(main_window)) # Explicit delegate check - Call is now commented out
        # info("Scheduled ensure_all_combos_have_hover_delegates after UI stabilization. (Call is now commented out, relying on global theme)")
        
        # Schedule diagnostic run
        # from app.templates.category_update_manager import diagnose_category_dropdown_issue # Old import
        # The diagnose function is now deprecated, logging should be used instead.
        # QTimer.singleShot(2000, lambda: deprecated_diagnose_dropdown_issue(main_window))
        # info("Note: diagnose_category_dropdown_issue is deprecated.")
        
        # Apply hover delegates to ensure category dropdowns have proper hover effects
        # This function is now removed from main.py as its logic is centralized in
        # category_combobox_updater.ensure_all_combos_have_hover_delegates,
        # which is called by the CategoryUpdateManager.
        # def apply_hover_delegates_to_category_dropdowns():
        #     \"\"\"Apply hover delegates to all category dropdown menus for proper hover effects\"\"\"
        #     from app.ui.custom_delegates import apply_hover_delegate
        #     from PyQt6.QtWidgets import QComboBox, QApplication
            
        #     all_widgets = QApplication.allWidgets()
        #     delegate_count = 0
            
        #     # Known category-related combo box names
        #     category_names = ["template_category_combo_box", "project_type_combo_box", "category_combo"]
            
        #     for widget in all_widgets:
        #         if isinstance(widget, QComboBox):
        #             # Check if this is a known category combo
        #             obj_name = widget.objectName().lower()
        #             is_category_combo = any(name in obj_name for name in category_names)
                    
        #             if is_category_combo:
        #                 apply_hover_delegate(widget)
        #                 delegate_count += 1
            
        #     print(f"Applied hover delegates to {delegate_count} category combo boxes")
        
        # Schedule application of hover delegates after UI initialization
        # This is now handled by the CategoryUpdateManager calls like force_immediate_global_update
        # and the explicit ensure_all_combos_have_hover_delegates call scheduled above.
        # QTimer.singleShot(1500, apply_hover_delegates_to_category_dropdowns) 
        
        # --- Connect state saving for TableView --- 
        def save_table_view_state():
            # Access the gallery and then the table view
            # This assumes main_window has access to the gallery which has the table view
            # Adjust the path as necessary based on your application structure
            try:
                # Example path: main_window -> central_widget -> template_gallery -> template_table_view
                gallery = main_window.template_gallery # Assuming gallery is directly accessible
                if hasattr(gallery, 'template_table_view') and gallery.template_table_view:
                    gallery.template_table_view.save_state()
            except AttributeError as ae:
                debug(f"Could not find gallery or table view for state saving: {ae}")
                pass
            except Exception as e:
                error(f"Error saving table view state: {e}")

        app.aboutToQuit.connect(save_table_view_state)
        # ------------------------------------------
        
        return app.exec()
    except Exception as e:
        critical(f"CRITICAL ERROR during application startup: {e}")
        exception("Application startup failure details:")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 