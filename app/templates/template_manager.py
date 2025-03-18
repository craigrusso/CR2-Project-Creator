#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import importlib
import json
import datetime
import time

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
            
            # Update UI if we have a template gallery
            if hasattr(self, 'app') and hasattr(self.app, 'template_gallery'):
                # Schedule a UI update on the main thread
                from PyQt5.QtCore import QTimer
                from PyQt5.QtWidgets import QApplication
                
                def update_ui():
                    self.app.template_gallery.populate_gallery(force_refresh=True)
                    self.app.template_gallery.update()
                    
                    # Process events to ensure UI updates
                    QApplication.processEvents()
                
                # Use a very short timer to ensure this happens after current event processing
                QTimer.singleShot(10, update_ui)
            
            return True
        except Exception as e:
            import traceback
            print(f"[DEBUG] FolderOps: Error creating folder: {e}")
            traceback.print_exc()
            return False

    def save_custom_structure(self, name, structure):
        """
        Save a custom folder structure.
        
        Args:
            name (str): Name of the structure
            structure (list): List of structure items (folders and files)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not name:
            print(f"[DEBUG] StructureOps: Cannot save structure with empty name")
            return False
            
        # Ensure we have a custom_structures dictionary
        if not hasattr(self, 'custom_structures'):
            self.custom_structures = {}  # Initialize as a dictionary
        
        # The structure object should be stored directly with the name as the key
        try:
            # Ensure structure is a list, not a dict
            if isinstance(structure, dict):
                # If we somehow got a dict with structure data instead of the actual structure list
                if 'directories' in structure:
                    structure = structure.get('directories', [])
                    print(f"[DEBUG] StructureOps: Extracted directories from structure dict")
                else:
                    # Otherwise wrap it in a list as a folder
                    structure = [structure]
                    print(f"[DEBUG] StructureOps: Wrapped dict in list to make valid structure")
                    
            # Normalize the structure format to ensure consistent handling of folders and template variables
            normalized_structure = self._normalize_structure_format(structure) if structure else []
            
            # Create the structure data to store
            structure_data = {
                "name": name,
                "directories": normalized_structure,
                "created": datetime.datetime.now().isoformat()
            }
            
            # Store in memory - important to store the whole structure_data object
            self.custom_structures[name] = structure_data
            
            # Create a clean filename
            filename = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
            file_path = os.path.join(self.paths["custom_structures_dir"], f"{filename}.json")
            
            # Make sure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(structure_data, f, indent=2)
                
            print(f"[DEBUG] StructureOps: Successfully saved custom structure '{name}'")
            return True
        except Exception as e:
            print(f"[DEBUG] StructureOps: Error saving structure: {e}")
            return False

    def _normalize_structure_format(self, structure_items):
        """Normalize the structure format to ensure consistency.
        
        This method ensures folders are represented as dictionaries with empty arrays 
        for consistency with the rest of the application: {"folder_name": []}
        
        Args:
            structure_items (list): List of structure items to normalize
            
        Returns:
            list: Normalized structure items
        """
        if not structure_items:
            return []
            
        normalized = []
        
        for item in structure_items:
            # Handle dictionaries (folders with possible children)
            if isinstance(item, dict):
                # Handle the {"name": "folder_name", "type": "folder"} format
                if "name" in item and "type" in item and item["type"] == "folder":
                    folder_name = item["name"]
                    children = []
                    if "children" in item and isinstance(item["children"], list):
                        children = self._normalize_structure_format(item["children"])
                    normalized.append({folder_name: children})
                # Handle the {"folder_name": []} format
                else:
                    processed_dict = {}
                    for folder_name, children in item.items():
                        if isinstance(children, list):
                            processed_dict[folder_name] = self._normalize_structure_format(children)
                        else:
                            # Ensure empty folders are represented as empty lists
                            processed_dict[folder_name] = []
                    normalized.append(processed_dict)
            # Handle string items (files or folders without format)
            elif isinstance(item, str):
                # If it ends with a slash, it's a folder
                if item.endswith('/'):
                    folder_name = item[:-1]  # Remove trailing slash
                    normalized.append({folder_name: []})
                else:
                    # It's a file, keep as is
                    normalized.append(item)
            else:
                # Unknown type, add as is
                normalized.append(item)
            
        return normalized
