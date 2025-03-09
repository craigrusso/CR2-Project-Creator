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
    def apply_migration(app):
        """
        Apply the full migration process:
        1. Migrate data from enhanced to unified
        2. Create a proxy for backward compatibility
        
        Args:
            app: The application instance
            
        Returns:
            bool: True if migration was successful
        """
        success = TemplateManagerMigration.migrate_enhanced_to_unified(app)
        if success:
            TemplateManagerMigration.create_template_manager_enhanced_proxy(app)
        return success 