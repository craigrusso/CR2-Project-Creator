#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
import shutil

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
        
        # Path to the base old directory
        echelon_dir = os.path.join(home_dir, '.echelon')
        # templates_dir = os.path.join(echelon_dir, 'templates') # REMOVED old path
        
        # Ensure base directory exists (only needed for structure check)
        # os.makedirs(echelon_dir, exist_ok=True) # Potentially remove if structure check is robust
        # os.makedirs(templates_dir, exist_ok=True) # REMOVED - Do not create old templates dir
        
        # Check for old structures directory and remove the warning
        # No need to migrate or rename it since we're moving away from it
        structures_dir = os.path.join(echelon_dir, 'structures')
        if os.path.exists(structures_dir):
            # Check if it has any files
            try:
                structure_files = [f for f in os.listdir(structures_dir) if os.path.isfile(os.path.join(structures_dir, f))]
                if structure_files:
                    print(f"INFO: Found .echelon/structures folder with {len(structure_files)} files.")
                    print(f"INFO: The structures folder is no longer used. All template data is now stored in the template JSON files.")
                else:
                    print(f"INFO: Found empty .echelon/structures folder. This folder is no longer used.")
                
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