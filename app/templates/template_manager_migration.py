#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
import shutil
from PyQt6.QtCore import QSettings

from app.core import config_manager # Use the new unified config manager

def get_legacy_structures_path():
    """
    Gets the path to the legacy `.forwardflow/structures` directory.
    This is for migration purposes only.
    """
    home_dir = os.path.expanduser('~')
    return os.path.join(home_dir, '.forwardflow', 'structures')

def get_legacy_templates_path():
    """
    Gets the path to the legacy `.forwardflow/templates` directory.
    This is for migration purposes only.
    """
    home_dir = os.path.expanduser('~')
    return os.path.join(home_dir, '.forwardflow', 'templates')

def migrate_legacy_structures(force_remigration=False):
    """
    Migrates standalone `.json` structure files from the old `.forwardflow/structures`
    directory into the new template-centric system.

    Each `.json` file in the legacy folder will be converted into a new template
    in the main user templates directory. The structure data will be embedded
    within the new template file.

    This function is intended to be run once at application startup.
    """
    legacy_structures_path = get_legacy_structures_path()
    
    # Check if the legacy folder exists
    if not os.path.isdir(legacy_structures_path):
        print("INFO: Legacy structures folder not found. No migration needed.")
        return

    # Check if migration has already been done
    settings = QSettings()
    if settings.value("legacy_structures_migrated", False) and not force_remigration:
        print("INFO: Legacy structures already migrated. Skipping.")
        return
        
    structure_files = [f for f in os.listdir(legacy_structures_path) if f.endswith('.json')]
    
    if not structure_files:
        print(f"INFO: Found empty .forwardflow/structures folder. This folder is no longer used.")
        settings.setValue("legacy_structures_migrated", True)
        return
        
    print(f"INFO: Found .forwardflow/structures folder with {len(structure_files)} files to migrate.")
    
    # Get the new central user data path for templates
    new_templates_path = config_manager.get_user_templates_path()
    os.makedirs(new_templates_path, exist_ok=True)
    
    migrated_count = 0
    for file_name in structure_files:
        legacy_file_path = os.path.join(legacy_structures_path, file_name)
        
        try:
            with open(legacy_file_path, 'r') as f:
                structure_data = json.load(f)
            
            # Create a new template name from the structure filename
            template_name = os.path.splitext(file_name)[0].replace('_', ' ').title()
            
            # Create the new template dictionary
            new_template = {
                "name": template_name,
                "description": f"Migrated from legacy structure '{file_name}'.",
                "category": "Migrated",
                "structure": structure_data,
                "custom_options": {},
                "version": "1.0"
            }
            
            # Define the new template file path
            new_file_path = os.path.join(new_templates_path, f"{template_name}.json")
            
            # Avoid overwriting existing templates with the same name
            if os.path.exists(new_file_path):
                print(f"WARNING: Template '{template_name}' already exists. Skipping migration for '{file_name}'.")
                continue

            # Write the new template file
            with open(new_file_path, 'w') as f:
                json.dump(new_template, f, indent=4)
            
            print(f"Successfully migrated '{file_name}' to '{new_file_path}'.")
            migrated_count += 1

        except (json.JSONDecodeError, IOError) as e:
            print(f"ERROR: Could not migrate '{file_name}': {e}")
            
    # Mark migration as complete
    settings.setValue("legacy_structures_migrated", True)
    print(f"INFO: Legacy structure migration complete. Migrated {migrated_count} files.")

    # Optional: Rename the old directory to avoid re-running migration
    try:
        renamed_path = legacy_structures_path + '_migrated'
        os.rename(legacy_structures_path, renamed_path)
        print(f"INFO: Renamed legacy structures folder to '{renamed_path}'.")
    except OSError as e:
        print(f"WARNING: Could not rename legacy structures folder: {e}")

def apply_migration(app=None):
    """
    Main entry point for all migration logic.
    """
    print("INFO: Checking for necessary data migrations...")
    migrate_legacy_structures()
    print("INFO: Migration check finished.")

class TemplateManagerMigration:
    """
    Handles migration from the old dual-system approach to the unified system.
    This is a temporary class that should only be used during the transition.
    """
    
    @staticmethod
    def migrate_enhanced_to_unified(app):
        """
        Migrate data from the enhanced template manager to the unified template manager.
        
        Args:
            app: The application instance with both template managers
        
        Returns:
            bool: True if migration was successful
        """
        if not hasattr(app, 'template_manager_enhanced'):
            # Nothing to migrate
            return True
            
        try:
            # Copy folders from enhanced to unified
            if hasattr(app.template_manager_enhanced, 'folders'):
                app.template_manager.folders = app.template_manager_enhanced.folders.copy()
                app.template_manager.save_folders()
                
            # Set a flag to indicate migration has occurred
            app.template_manager.is_migrated = True
            
            print("Successfully migrated template data to unified system")
            return True
            
        except Exception as e:
            print(f"Error during migration: {e}")
            return False
    
    @staticmethod
    def create_template_manager_enhanced_proxy(app):
        """
        Create a proxy class that forwards all calls to the unified template manager.
        This ensures backward compatibility with code that expects the enhanced manager.
        
        Args:
            app: The application instance
            
        Returns:
            None
        """
        class TemplateManagerEnhancedProxy:
            """Proxy class that forwards calls to the unified template manager"""
            
            def __init__(self, template_manager):
                self.template_manager = template_manager
                # Copy all attributes from the template manager
                self.folders = template_manager.folders
                
            def __getattr__(self, name):
                """Forward any calls to the template manager"""
                return getattr(self.template_manager, name)
                
        # Create the proxy and attach it to the app
        app.template_manager_enhanced = TemplateManagerEnhancedProxy(app.template_manager)
        
    @staticmethod
    def apply_migration(app=None):
        """
        Apply all necessary migrations to templates and structures
        
        Args:
            app: Main application instance (optional)
        """
        # Get home directory
        home_dir = os.path.expanduser("~")
        
        # Path to the base directory
        app_dir = os.path.join(home_dir, '.forwardflow')
        # templates_dir = os.path.join(app_dir, 'templates') # REMOVED old path
        
        # Create base directory if needed
        # os.makedirs(app_dir, exist_ok=True) # Potentially remove if structure check is robust
        
        # Create structures directory if needed
        structures_dir = os.path.join(app_dir, 'structures')
        if os.path.exists(structures_dir):
            # Check if it has any files
            try:
                structure_files = [f for f in os.listdir(structures_dir) if os.path.isfile(os.path.join(structures_dir, f))]
                if structure_files:
                    print(f"INFO: Found .forwardflow/structures folder with {len(structure_files)} files.")
                    print(f"INFO: The structures folder is no longer used. All template data is now stored in the template JSON files.")
                else:
                    print(f"INFO: Found empty .forwardflow/structures folder. This folder is no longer used.")
                
                # Simply delete the directory if it's empty
                if not structure_files:
                    try:
                        os.rmdir(structures_dir)
                        print(f"INFO: Removed empty structures directory: {structures_dir}")
                    except Exception as e:
                        print(f"WARNING: Could not remove structures directory: {e}")
            except Exception as list_err:
                 print(f"WARNING: Could not check or remove structures directory {structures_dir}: {list_err}")
        # Removed the migrate_enhanced_to_unified call as it seemed related to an old refactor
        # success = TemplateManagerMigration.migrate_enhanced_to_unified(app) 
        # Removed the proxy creation as it seemed related to an old refactor
        # if success:
        #    TemplateManagerMigration.create_template_manager_enhanced_proxy(app)
        # return success
        return True # Indicate migration check completed (even if nothing done) 