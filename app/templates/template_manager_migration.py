#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
import logging

logger = logging.getLogger(__name__)

class TemplateManagerMigration:
    """
    Manages migrations for the template manager system
    """
    
    @staticmethod
    def migrate_enhanced_to_unified(app):
        """
        Migrate from the enhanced template system to the unified folder/template system
        
        Args:
            app: The application instance (either legacy or MVC architecture)
            
        Returns:
            bool: True if migration was performed, False if not needed
        """
        # Get template manager depending on architecture
        template_manager = TemplateManagerMigration._get_template_manager(app)
        if not template_manager:
            logger.warning("Cannot perform migration: Template manager not found")
            return False
            
        # Check if migration has already been performed
        if template_manager.folders and "Recent" in template_manager.folders:
            # Migration already done
            return False
        
        # Create new folder structure
        logger.info("Performing template manager migration to unified system")
        
        # Create default folders if they don't exist
        if not hasattr(template_manager, 'folders') or not template_manager.folders:
            template_manager.folders = {
                "Favorites": [],
                "Recent": []
            }
        
        # Save folders
        template_manager.save_folders()
        
        return True
    
    @staticmethod
    def create_template_manager_enhanced_proxy(app):
        """
        Create a proxy for the template manager for backward compatibility
        
        Args:
            app: The application instance (either legacy or MVC architecture)
        """
        # Get template manager depending on architecture
        template_manager = TemplateManagerMigration._get_template_manager(app)
        if not template_manager:
            logger.warning("Cannot create enhanced proxy: Template manager not found")
            return
            
        # Create a proxy class to provide backward compatibility
        class TemplateManagerEnhancedProxy:
            """Proxy class for backward compatibility with the enhanced template manager"""
            
            def __init__(self, template_manager):
                self.template_manager = template_manager
                # Copy all attributes from the template manager
                self.folders = template_manager.folders
                
            def __getattr__(self, name):
                """Forward any calls to the template manager"""
                return getattr(self.template_manager, name)
                
        # Create the proxy and attach it to the app
        app.template_manager_enhanced = TemplateManagerEnhancedProxy(template_manager)
        
    @staticmethod
    def apply_migration(app):
        """
        Apply the full migration process:
        1. Migrate data from enhanced to unified
        2. Create a proxy for backward compatibility
        
        Args:
            app: The application instance (either legacy or MVC architecture)
            
        Returns:
            bool: True if migration was successful
        """
        logger.info("Applying template manager migration")
        success = TemplateManagerMigration.migrate_enhanced_to_unified(app)
        if success:
            TemplateManagerMigration.create_template_manager_enhanced_proxy(app)
        else:
            # Even if migration wasn't needed, still create the proxy
            # as it's needed for backward compatibility
            TemplateManagerMigration.create_template_manager_enhanced_proxy(app)
        return success
        
    @staticmethod
    def _get_template_manager(app):
        """Get template manager from app instance"""
        # First try new MVC architecture
        if hasattr(app, 'model') and hasattr(app.model, 'template_manager'):
            return app.model.template_manager
            
        # Then try legacy architecture
        if hasattr(app, 'template_manager'):
            return app.template_manager
            
        # Try template_gallery as a fallback
        if hasattr(app, 'template_gallery'):
            return app.template_gallery.template_manager
            
        # No template manager found
        return None 