#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import importlib

from app.templates.template_manager_core import TemplateManagerCore
from app.templates.template_operations import TemplateOperations
from app.templates.structure_operations import StructureOperations
from app.templates.folder_operations import FolderOperations
from app.templates.ui_operations import UIOperations

class TemplateManager(TemplateManagerCore, TemplateOperations, StructureOperations, FolderOperations, UIOperations):
    """
    Manages project templates and custom structures
    
    This class combines functionality from:
    - TemplateManagerCore: Core initialization and basic operations
    - TemplateOperations: Template CRUD operations
    - StructureOperations: Custom structure operations
    - FolderOperations: Folder management operations
    - UIOperations: UI-related operations
    """
    def __init__(self):
        # Initialize the core functionality
        TemplateManagerCore.__init__(self)

    def move_template_to_folder(self, template_name, folder_name):
        """Move a template to a folder, ensuring it's removed from other folders first"""
        print(f"[DEBUG] FolderOps: Moving template '{template_name}' to folder '{folder_name}'")
        
        # Validate input
        if not template_name or not folder_name:
            print(f"[DEBUG] FolderOps: Invalid template or folder name: '{template_name}', '{folder_name}'")
            return False
        
        try:
            # Make sure the template exists
            template = None
            for t in self.templates + self.template_directories:
                if isinstance(t, dict) and t.get('name') == template_name:
                    template = t
                    break
            
            if not template:
                print(f"[DEBUG] FolderOps: Template '{template_name}' not found")
                return False
            
            # Make sure the folder exists
            if folder_name not in self.folders:
                print(f"[DEBUG] FolderOps: Folder '{folder_name}' not found")
                return False
            
            # First, remove the template from all folders to avoid duplicates
            for f in self.folders:
                if template_name in self.folders[f]:
                    print(f"[DEBUG] FolderOps: Removing '{template_name}' from folder '{f}'")
                    self.folders[f].remove(template_name)
            
            # Now add the template to the target folder
            print(f"[DEBUG] FolderOps: Adding '{template_name}' to folder '{folder_name}'")
            if template_name not in self.folders[folder_name]:
                self.folders[folder_name].append(template_name)
            
            # Save the folders to disk
            print(f"[DEBUG] FolderOps: Saving folders after move")
            self.save_folders()
            
            # Return a list of templates actually in the folder after cleaning
            cleaned_list = self.get_templates_in_folder(folder_name)
            print(f"[DEBUG] FolderOps: Returning cleaned template list: {cleaned_list}")
            
            return True
        except Exception as e:
            import traceback
            print(f"[DEBUG] FolderOps: Error moving template to folder: {e}")
            traceback.print_exc()
            return False
