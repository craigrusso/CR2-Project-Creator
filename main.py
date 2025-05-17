#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import platform
import sys
import os
import shutil # Ensure shutil is imported
import json

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication, QSettings, QTimer
from app.core.app_module_pyqt import ProjectCreatorApp
from app.config.app_config import APP_NAME, APP_VERSION, setup_dpi_awareness
from app.ui.app_theme_pyqt import apply_dark_theme_to_template_section, force_app_palette, configure_styles
from app.templates.template_manager_migration import TemplateManagerMigration
from app.ui.tree_styling import apply_styling_to_all_tree_widgets, refresh_all_tree_icons
from app.ui.icon_utilities import clear_icon_cache
from PyQt5.QtGui import QIcon

# Import the license manager for license checking
from app.utils.security.license_manager import LicenseManager, TrialNagDialog
from PyQt5.QtWidgets import QDialog

# Import the EULA Dialog
from app.dialogs.eula_dialog import EulaDialog

# Import for deploying example templates
from app.core.config_manager import get_templates_path, get_settings_path
from app.utils.utils import load_json_file, save_json_file

# This is the PyQt version of the application
UI_FRAMEWORK = 'pyqt'

def deploy_example_templates():
    """
    Copies bundled example templates to the user's template directory,
    placing them inside an 'Examples' subdirectory.
    """
    print("DEBUG: Checking and deploying example templates into 'Examples' subdirectory...")
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
                 print(f"WARNING: Bundled example templates source directory not found in PyInstaller bundle. Tried: {possible_source_paths}")
                 return
        else:
            project_root = os.path.dirname(os.path.abspath(__file__))
            source_templates_base_dir = os.path.join(project_root, "app", "assets", bundled_examples_dir_name)

        if not os.path.isdir(source_templates_base_dir):
            print(f"WARNING: Bundled example templates source directory not found at: {source_templates_base_dir}")
            print(f"INFO: Current CWD: {os.getcwd()}")
            print(f"INFO: sys.frozen: {getattr(sys, 'frozen', False)}")
            if hasattr(sys, '_MEIPASS'):
                print(f"INFO: sys._MEIPASS: {sys._MEIPASS}")
                print(f"INFO: Contents of sys._MEIPASS: {os.listdir(sys._MEIPASS) if os.path.exists(sys._MEIPASS) else 'Not found or not listable'}")
            print(f"INFO: Absolute path of __file__ (main.py): {os.path.abspath(__file__)}")
            return

        # Create the base user templates directory if it doesn't exist
        if not os.path.exists(base_user_templates_path):
            try:
                os.makedirs(base_user_templates_path)
                print(f"DEBUG: Created base user templates directory: {base_user_templates_path}")
            except OSError as e:
                print(f"ERROR: Could not create base user templates directory: {base_user_templates_path} - {e}")
                return
        
        # Create the "Examples" subdirectory if it doesn't exist
        if not os.path.exists(user_examples_subdirectory_path):
            try:
                os.makedirs(user_examples_subdirectory_path)
                print(f"DEBUG: Created user examples subdirectory: {user_examples_subdirectory_path}")
            except OSError as e:
                print(f"ERROR: Could not create user examples subdirectory: {user_examples_subdirectory_path} - {e}")
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
                print(f"WARNING: Source example template file not found: {source_file_path}")
                continue

            template_ui_name = None
            try:
                # Read the source template to get its UI name
                with open(source_file_path, 'r', encoding='utf-8') as f_src:
                    template_content = json.load(f_src)
                    if isinstance(template_content, dict) and "name" in template_content:
                        template_ui_name = template_content["name"]
                    else:
                        print(f"WARNING: Could not find 'name' key in {source_file_path}")
            except Exception as e_read_name:
                print(f"ERROR: Could not read UI name from source template {source_file_path}: {e_read_name}")
            
            # Flag to indicate if this template is considered successfully "present" at the destination
            is_template_present_at_dest = False

            if not os.path.exists(destination_file_path):
                try:
                    shutil.copy2(source_file_path, destination_file_path)
                    print(f"INFO: Deployed example template: {template_file_name} to {destination_file_path}")
                    is_template_present_at_dest = True
                except Exception as e_copy:
                    print(f"ERROR: Could not copy example template {template_file_name}: {e_copy}")
            else:
                print(f"DEBUG: Example template already exists in Examples subfolder, skipping copy: {template_file_name}")
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
                print(f"DEBUG: Created settings directory for folders.json: {settings_dir}")

            folders_data = load_json_file(folders_json_path)

            if folders_data is None: 
                folders_data = {}    
                print(f"DEBUG: Initialized folders_data for {folders_json_path} as new dict (file was missing/invalid).")
            
            if not isinstance(folders_data, dict): 
                print(f"WARNING: Content of {folders_json_path} was not a dictionary. Resetting to empty dict.")
                folders_data = {}

            # Ensure "Examples" key exists and its value is a list
            if "Examples" not in folders_data or not isinstance(folders_data["Examples"], list):
                folders_data["Examples"] = []
                print(f"INFO: Initialized/Reset 'Examples' entry in {folders_json_path} as a list.")

            # Add UI names of deployed example templates to the list if not already present
            made_changes_to_examples_list = False
            for ui_name in deployed_example_template_ui_names:
                if ui_name not in folders_data["Examples"]:
                    folders_data["Examples"].append(ui_name)
                    made_changes_to_examples_list = True
            
            if made_changes_to_examples_list:
                print(f"INFO: Added UI names of deployed example templates to 'Examples' list in {folders_json_path}.")
            else:
                print(f"DEBUG: 'Examples' list in {folders_json_path} already contains all deployed example UI names, or no new names were added.")

            # Save folders_data back to folders.json
            if save_json_file(folders_json_path, folders_data):
                print(f"INFO: Successfully ensured {folders_json_path} is updated for 'Examples' folder and its template names.")
            else:
                print(f"ERROR: Failed to save {folders_json_path} after 'Examples' folder processing (save_json_file returned false).")

        except Exception as e_folders_json:
            print(f"ERROR: Could not update {folders_json_path} for 'Examples' folder registration: {e_folders_json}")
            import traceback
            traceback.print_exc()

        print("DEBUG: Example template deployment (into Examples subfolder) and folder registration check complete.")

    except Exception as e:
        print(f"ERROR: Failed to deploy example templates into Examples subfolder: {e}")
        import traceback
        traceback.print_exc()

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
    print("DEBUG: Starting application initialization")
    
    # Setup DPI awareness for Windows
    setup_dpi_awareness()
    print("DEBUG: DPI awareness configured")
    
    # For macOS, set the application name before creating QApplication
    # This affects what appears in the menu bar
    QCoreApplication.setApplicationName(APP_NAME)
    QCoreApplication.setOrganizationName("CR2 Creative")
    QCoreApplication.setOrganizationDomain("cr2creative.com")
    print("DEBUG: Application core info set")
    
    # --- QSettings Debug --- 
    # Early check to see QSettings path and initial critical values
    # Ensure QSettings is initialized here if not already implicitly by LicenseManager constructor for this test
    # However, LicenseManager will create its own instance. This is for an early peek.
    temp_settings_for_debug = QSettings("CR2 Creative", "Echelon")
    print(f"DEBUG QSETTINGS: File path: {temp_settings_for_debug.fileName()}")
    print(f"DEBUG QSETTINGS: Initial 'license/trial_start': {temp_settings_for_debug.value('license/trial_start', 'NOT FOUND')}")
    print(f"DEBUG QSETTINGS: Initial 'license/trial_end_time': {temp_settings_for_debug.value('license/trial_end_time', 'NOT FOUND')}")
    print(f"DEBUG QSETTINGS: Initial 'license/was_ever_licensed': {temp_settings_for_debug.value('license/was_ever_licensed', 'NOT FOUND')}")
    del temp_settings_for_debug # Clean up temporary instance
    # --- End QSettings Debug ---
    
    # Set app ID for Windows taskbar
    if platform.system() == "Windows":
        try:
            import ctypes
            
            # Set explicit AppUserModelID for Windows taskbar
            myappid = 'cr2creative.echelon.0.95'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            print("DEBUG: Windows app ID set")
            
            # Additional Windows-specific icon handling
            # This ensures all windows (including dialogs) use the same icon
            import ctypes.wintypes
            try:
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "assets", "icon.png")
                if os.path.exists(icon_path):
                    print("DEBUG: Setting Windows-specific application icon")
                    # Use the same icon for all windows
                    app.setWindowIcon(QIcon(icon_path))
            except Exception as e:
                print(f"WARNING: Windows-specific icon setting failed: {e}")
        except Exception as e:
            print(f"WARNING: Could not set app ID: {e}")

    # Enable High DPI scaling
    print("DEBUG: Configuring high DPI settings")
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Initialize the PyQt application
    print("DEBUG: Creating QApplication instance")
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    # --- EULA Check ---
    # Must happen after QApplication is created so dialogs can function
    print("DEBUG: Checking EULA acceptance.")
    if not EulaDialog.show_eula_if_needed():
        print("DEBUG: EULA not accepted. Exiting application.")
        return 1 # Exit cleanly if EULA declined
    
    print("DEBUG: EULA check passed.")
    
    # Force application to use our custom palette regardless of system settings
    print("DEBUG: Applying custom palette")
    force_app_palette(app)
    
    # Set application icon
    print("DEBUG: Setting application icon")
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "assets", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        print(f"DEBUG: Application icon set from {icon_path}")
    else:
        print(f"WARNING: Application icon not found at {icon_path}")
    
    # Apply comprehensive styles from the theme module
    print("DEBUG: Configuring global styles")
    configure_styles(app)
    
    # On macOS, ensure we use our custom styling while maintaining native menu bar
    if platform.system() == "Darwin":  # macOS
        print("DEBUG: Configuring macOS-specific settings")
        # Use native menu bar for better macOS integration
        app.setAttribute(Qt.AA_DontUseNativeMenuBar, False)
        
        # Apply an additional attribute to help prevent macOS from overriding our theme
        app.setAttribute(Qt.AA_DontShowIconsInMenus, True)
    
    # Check license status before proceeding
    print("DEBUG: Checking license status")
    license_manager = LicenseManager()
    
    # --- Trial Logic Enhancement ---
    # Check if a license was ever activated on this installation
    settings = QSettings() # This is the QSettings instance used by main.py's logic
    print(f"DEBUG MAIN.PY: Settings file in use by main logic: {settings.fileName()}")
    was_ever_licensed_val = settings.value("license/was_ever_licensed", "NOT FOUND (using default False next)")
    print(f"DEBUG MAIN.PY: Value read for 'license/was_ever_licensed' before bool conversion: {was_ever_licensed_val}")
    was_ever_licensed = settings.value("license/was_ever_licensed", False, type=bool)
    print(f"DEBUG: Was license ever activated? {was_ever_licensed}")

    # Determine if we can proceed based on license status
    can_proceed = False # Default to false, must pass checks

    if license_manager.is_licensed():
        print("DEBUG: Application is licensed (initial check)")
        can_proceed = True
        # If licensed now, ensure the 'was_ever_licensed' flag is set
        if not was_ever_licensed:
            settings.setValue("license/was_ever_licensed", True)
            print("DEBUG: Setting 'was_ever_licensed' flag to True.")
    else:
        # --- Check if trial should be bypassed ---
        if was_ever_licensed:
            print("DEBUG: License previously activated but now invalid/expired. Bypassing trial.")
            # Force activation dialog - treat as if trial expired
            trial_dialog = TrialNagDialog(None, license_manager, 0) # 0 days forces activation
            dialog_result = trial_dialog.exec_()
            if dialog_result == QDialog.Accepted and license_manager.is_licensed():
                print("DEBUG: Re-activation successful after previous license expired/revoked.")
                can_proceed = True
                # Ensure flag is set (should be already, but belt-and-suspenders)
                if not settings.value("license/was_ever_licensed", False, type=bool):
                     settings.setValue("license/was_ever_licensed", True)
            else:
                print("DEBUG: Did not re-activate after previous license expired/revoked.")
                can_proceed = False # Exit if activation fails/cancelled
        else:
            # --- Normal Trial Check (only if never licensed before) ---
            print("DEBUG: Checking trial status (never licensed before).")
            # Ensure trial start/end times are initialized in settings if this is the first run for the trial
            # by calling is_trial_active() first. It will return True if trial is new or ongoing.
            if license_manager.is_trial_active(): 
                print("DEBUG: Trial is active (either new or ongoing).")
                time_parts = license_manager.get_trial_time_remaining_parts()
                print(f"DEBUG: Trial time remaining: {time_parts['days']}d, {time_parts['hours']}h, {time_parts['minutes']}m")

                # Show trial nag dialog
                trial_dialog = TrialNagDialog(None, license_manager, time_parts=time_parts)
                dialog_result = trial_dialog.exec_()

                # Check status AFTER dialog closes
                if dialog_result == QDialog.Accepted:
                    if license_manager.is_licensed(): # Check if activation occurred
                         print("DEBUG: Trial dialog accepted, and now licensed (activation successful).")
                         can_proceed = True
                         # Set the flag since activation was successful
                         settings.setValue("license/was_ever_licensed", True)
                         print("DEBUG: Setting 'was_ever_licensed' flag to True after trial activation.")
                    else: # No activation, but accepted means continue trial
                         print("DEBUG: Trial dialog accepted, continuing trial.")
                         can_proceed = True
                else: # Dialog was rejected (Cancel/Exit) or closed
                    print("DEBUG: User cancelled the trial dialog or exited.")
                    can_proceed = False # Stays False
            else: # is_trial_active() returned False, meaning trial has genuinely expired according to its own precise check
                print("DEBUG: Trial has genuinely expired (is_trial_active is False).")
                time_parts = {'days': 0, 'hours': 0, 'minutes': 0} # Ensure time_parts show zero
                # Trial expired (and never licensed before), show the nag dialog with exit option only
                trial_dialog = TrialNagDialog(None, license_manager, time_parts=time_parts)
                dialog_result = trial_dialog.exec_()

                # Check status AFTER dialog closes
                if dialog_result == QDialog.Accepted and license_manager.is_licensed():
                     print("DEBUG: Trial expired dialog accepted, and now licensed (activation successful).")
                     can_proceed = True
                     # Set the flag since activation was successful
                     settings.setValue("license/was_ever_licensed", True)
                     print("DEBUG: Setting 'was_ever_licensed' flag to True after expired trial activation.")
                else: # Dialog was rejected (Exit) or closed
                    print("DEBUG: Trial expired and user did not activate.")
                    can_proceed = False # Stays False

    # Final decision based on the logic above
    if not can_proceed:
        print("DEBUG: Exiting application due to license/trial constraints")
        return 0
    
    # Deploy example templates if necessary
    print("DEBUG: Deploying example templates if necessary")
    deploy_example_templates()
    
    # Create and show the main window
    print("DEBUG: Creating main application window")
    try:
        main_window = ProjectCreatorApp()
        # Store the instance for future reference
        ProjectCreatorApp._instance = main_window
        print("DEBUG: Main window created successfully")
        
        # Add license management to the help menu
        if hasattr(main_window, 'help_menu'):
            from app.dialogs.license_management import LicenseManagementDialog
            
            # Create the license action
            license_action = main_window.help_menu.addAction("License Management...")
            license_action.triggered.connect(lambda: LicenseManagementDialog(main_window, license_manager).exec_())
            
            # Add a separator before the action
            main_window.help_menu.insertSeparator(license_action)
            
            print("DEBUG: Added license management to help menu")
        
        print("DEBUG: Showing main window")
        main_window.show()
        
        # Apply template migration if needed
        print("DEBUG: Applying template migration")
        try:
            TemplateManagerMigration.apply_migration(main_window)
            print("DEBUG: Template migration completed")
        except Exception as e:
            print(f"ERROR during template migration: {e}")
            import traceback
            traceback.print_exc()
        
        # Apply dark theme to template section
        print("DEBUG: Applying dark theme to template section")
        try:
            apply_dark_theme_to_template_section(main_window)
            print("DEBUG: Theme applied to template section")
        except Exception as e:
            print(f"ERROR applying theme: {e}")
            import traceback
            traceback.print_exc()
        
        # Apply tree styling to all tree widgets
        print("DEBUG: Applying tree styling to all tree widgets")
        styled_count = apply_styling_to_all_tree_widgets(main_window)
        print(f"DEBUG: Tree styling applied to all tree widgets ({styled_count} widgets styled)")
        
        # Force a complete icon cache refresh to ensure we're using platform-native icons
        print("DEBUG: Forcefully clearing and refreshing icon cache")
        clear_icon_cache()
        
        # Force icon cache refresh and update all tree icons
        print("DEBUG: Refreshing all tree icons with native platform icons")
        refresh_count = refresh_all_tree_icons()
        print(f"DEBUG: Refreshed icons for {refresh_count} tree widgets")
        
        # Schedule another refresh after a short delay to ensure everything is loaded
        QTimer.singleShot(1000, lambda: refresh_all_tree_icons())
        
        # --- Connect state saving for TableView --- 
        def save_table_view_state():
            # Access the gallery and then the table view
            # This assumes main_window has access to the gallery which has the table view
            # Adjust the path as necessary based on your application structure
            try:
                # Example path: main_window -> central_widget -> template_gallery -> template_table_view
                gallery = main_window.template_gallery # Assuming gallery is directly accessible
                if hasattr(gallery, 'template_table_view') and gallery.template_table_view:
                    print("DEBUG: Saving TemplateTableView state on exit...")
                    gallery.template_table_view.save_state()
                else:
                    print("DEBUG: TemplateTableView not found, skipping state save.")
            except AttributeError as ae:
                print(f"DEBUG: Could not find gallery or table view for state saving: {ae}")
            except Exception as e:
                print(f"ERROR saving table view state: {e}")

        app.aboutToQuit.connect(save_table_view_state)
        print("DEBUG: Connected aboutToQuit signal for saving TableView state.")
        # ------------------------------------------
        
        print("DEBUG: Starting application main loop")
        return app.exec_()
    except Exception as e:
        print(f"CRITICAL ERROR during application startup: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 