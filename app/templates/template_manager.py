#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import importlib
import json
import datetime

from app.templates.template_manager_core import TemplateManagerCore
from app.templates.template_operations import TemplateOperations
from app.templates.structure_operations import StructureOperations
from app.templates.folder_operations import FolderOperations
from app.templates.ui_operations import UIOperations
from app.utils.utils import get_config_paths

class TemplateManager(TemplateManagerCore, StructureOperations, FolderOperations, UIOperations):
    """
    Manages project templates and custom structures.
    
    This class combines functionality from:
    - TemplateManagerCore: Core initialization and basic operations
    - StructureOperations: Custom structure operations
    - FolderOperations: Folder management operations
    - UIOperations: UI-related operations
    
    The inheritance order is important for proper initialization.
    """
    def __init__(self):
        """Initialize the template manager"""
        # Initialize core first to set up paths and basic attributes
        TemplateManagerCore.__init__(self)
        
        # Initialize mixins after core initialization
        StructureOperations.__init__(self)
        FolderOperations.__init__(self)
        UIOperations.__init__(self)
        
        # Initialize additional attributes for multi-selection
        self.multi_selected_templates = []

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

    def create_folder(self, folder_name):
        """Create a new folder with the given name.
        
        Args:
            folder_name (str): Name of the folder to create
            
        Returns:
            bool: True if folder was created successfully, False otherwise
        """
        print(f"[DEBUG] FolderOps: Creating folder '{folder_name}'")
        
        # Validate input
        if not folder_name or not isinstance(folder_name, str):
            print(f"[DEBUG] FolderOps: Invalid folder name: '{folder_name}'")
            return False
        
        # Trim whitespace
        folder_name = folder_name.strip()
        
        if not folder_name:
            print(f"[DEBUG] FolderOps: Empty folder name after trimming")
            return False
        
        # Check if folder already exists
        if folder_name in self.folders:
            print(f"[DEBUG] FolderOps: Folder '{folder_name}' already exists")
            return False
        
        try:
            # Create the new folder
            self.folders[folder_name] = []
            
            # Save the folders to disk
            print(f"[DEBUG] FolderOps: Saving folders after creation")
            self.save_folders()
            
            return True
        except Exception as e:
            import traceback
            print(f"[DEBUG] FolderOps: Error creating folder: {e}")
            traceback.print_exc()
            return False

    def save_custom_structure(self, name, directories):
        """Save a custom folder structure.
        
        Args:
            name (str): Name of the structure
            directories (list): List of directory objects to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"[DEBUG] StructureOps: Saving custom structure '{name}'")
        
        if not name or not directories:
            print(f"[DEBUG] StructureOps: Invalid name or directories")
            return False
        
        # Ensure directories are properly formatted
        directories = self._normalize_structure_format(directories) if hasattr(self, '_normalize_structure_format') else directories
        
        structure = {
            "name": name,
            "directories": directories,
            "created": datetime.datetime.now().isoformat()
        }
        
        # Create a clean filename - always replace spaces with underscores
        filename = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        
        # Save the structure to the custom_structures directory
        structure_path = os.path.join(self.paths["custom_structures_dir"], f"{filename}.json")
        
        try:
            with open(structure_path, 'w') as f:
                json.dump(structure, f, indent=2)
            
            # Update the in-memory custom structures
            self.custom_structures[name] = structure
            
            print(f"[DEBUG] StructureOps: Successfully saved structure '{name}'")
            return True
        except Exception as e:
            import traceback
            print(f"[DEBUG] StructureOps: Error saving structure: {e}")
            traceback.print_exc()
            return False

    def _normalize_structure_format(self, structure_items):
        """Normalize the structure format to ensure consistency.
        
        Args:
            structure_items (list): List of structure items to normalize
            
        Returns:
            list: Normalized structure items
        """
        normalized = []
        
        for item in structure_items:
            if isinstance(item, str):
                # Convert simple string to object format
                normalized.append({"name": item, "type": "folder"})
            elif isinstance(item, dict):
                # Ensure required fields exist
                normalized_item = {
                    "name": item.get("name", "Untitled"),
                    "type": item.get("type", "folder")
                }
                
                # Include children if they exist
                if "children" in item and isinstance(item["children"], list):
                    normalized_item["children"] = self._normalize_structure_format(item["children"])
                
                normalized.append(normalized_item)
        
        return normalized
