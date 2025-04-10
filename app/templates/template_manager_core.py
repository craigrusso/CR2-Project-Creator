#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
import datetime
import shutil
import time
from pathlib import Path

from app.utils.utils import load_json_file, save_json_file
from app.core import config_manager
from app.constants import DEFAULT_TEMPLATE_CATEGORIES, APP_VERSION
from app.templates.folder_operations import FolderOperations
from app.templates.structure_operations import StructureOperations
from app.templates.template_operations import TemplateOperations
from app.templates.project_type_manager import ProjectTypeManager

class TemplateManagerCore(TemplateOperations):
    """
    Core functionality for managing project templates and custom structures
    """
    _instance = None  # Singleton instance
    
    def __init__(self, app=None):
        """Initialize the template manager core"""
        # Store the application instance
        self.app = app
        
        # Initialize template storage
        self.templates = []
        self.template_directories = []
        self.selected_template = None
        self.folders = {}  # Map of folder name to list of template names
        self.preferences = {}
        
        # Create a paths dictionary using config_manager
        self._paths = {
            "templates_dir": config_manager.get_templates_path(),
            "cache_dir": config_manager.get_cache_path(), # Use unified cache dir
            "custom_structures_dir": config_manager.get_structures_path(),
            "template_directories_dir": config_manager.get_template_directories_path(),
            "settings_dir": config_manager.get_settings_path(), # For things like folders.json, preferences.json
             # Add other paths if TemplateOperations needs them directly
        }
        # Pass the constructed paths dict to the parent constructor via super()
        super().__init__(paths=self._paths)
        
        # Load folders (folder organization data)
        self.load_folders()
        
        # Load user preferences
        self.load_preferences()
        
        # Clean up any problematic templates (e.g., duplicates based on name)
        self.cleanup_templates()
        
        # Initialize additional managers (like ProjectTypeManager)
        self.project_type_manager = ProjectTypeManager(self)
        
        # --- ADDED: Explicitly load structures after parent init ---
        if self.structure_ops:
            self.structure_ops.load_custom_structures()
            print(f"DEBUG: Explicitly loaded {len(self.structure_ops.custom_structures)} custom structures.")
        else:
            print("WARN: structure_ops not initialized, cannot explicitly load custom structures.")
        # --- END ADDED ---
        
        print(f"DEBUG: TemplateManagerCore Initialized. Loaded {len(self.template_io.templates if self.template_io else 0)} templates via TemplateIO.")
    
    def load_template_directories(self):
        """Load all template directories"""
        self.template_directories = []
        template_directories_dir = config_manager.get_template_directories_path()
        
        if not template_directories_dir or not os.path.exists(template_directories_dir):
            print(f"DEBUG: Template directories path does not exist: {template_directories_dir}")
            return
        
        try:
            # Look for directories that contain a template.json file
            for item in os.listdir(template_directories_dir):
                item_path = os.path.join(template_directories_dir, item)
                if os.path.isdir(item_path):
                    template_json = os.path.join(item_path, "template.json")
                    if os.path.exists(template_json):
                        try:
                            # Use utility to load JSON
                            template_info = load_json_file(template_json)
                            if template_info: # Check if loading was successful
                                template_info['path'] = item_path
                                template_info['type'] = 'directory'
                                self.template_directories.append(template_info)
                            # else: load_json_file would print error
                        except Exception as e:
                            print(f"Error processing template directory {item}: {e}")
        except Exception as e:
            print(f"Error loading template directories from {template_directories_dir}: {e}")
    
    def load_folders(self):
        """Load folder organization from folders.json in the settings directory."""
        settings_dir = config_manager.get_settings_path()
        folders_path = os.path.join(settings_dir, "folders.json")
        self.folders = load_json_file(folders_path)

        # --- ADDED: Ensure default Favorites folder exists --- 
        if not self.folders: # If file didn't exist or was empty
            print(f"DEBUG: folders.json not found or empty at {folders_path}. Creating default.")
            self.folders = {
                "Favorites": []
            }
            self.save_folders() # Save the default immediately
        elif "Favorites" not in self.folders: # If file exists but lacks Favorites
             print(f"DEBUG: 'Favorites' folder missing in {folders_path}. Adding default.")
             self.folders["Favorites"] = []
             self.save_folders() # Save the updated folders
        # --- END ADDED ---
        else:
            print(f"DEBUG: Loaded {len(self.folders)} folder structures from {folders_path}")
    
    def save_folders(self):
        """Save folder organization to folders.json in the settings directory."""
        settings_dir = config_manager.get_settings_path()
        folders_path = os.path.join(settings_dir, "folders.json")
        # Call save_json_file and directly return its result
        success = save_json_file(folders_path, self.folders)
        if success:
             print(f"DEBUG: Save Folders: Successfully saved to {folders_path}")
        else:
             print(f"ERROR: Save Folders: Failed to save to {folders_path} (check utils.save_json_file logs)")
        return success # Return the boolean result
    
    @property
    def folder_manager(self):
        """Return self as a folder manager (since we inherit from FolderOperations)"""
        # We need to make the folder operations accessible via a folder_manager property
        return self
    
    def get_all_templates(self):
        """Returns all loaded templates from TemplateIO."""
        if self.template_io:
            # Return a list of the dictionary values from template_io.templates
            return list(self.template_io.templates.values())
        else:
            print("WARN: TemplateIO not initialized in TemplateManagerCore.")
            return [] # Return empty list if IO not ready
    
    def get_template_by_name(self, template_name):
        """
        Get a template by its name from TemplateIO.

        Args:
            template_name (str): The name of the template to find.

        Returns:
            dict or None: The template data dictionary if found, otherwise None.
        """
        if not template_name or not self.template_io:
            print(f"WARN: TemplateIO not initialized or empty template name. Cannot get template '{template_name}'.")
            return None
            
        # First try exact match (fastest)
        if template_name in self.template_io.templates:
            return self.template_io.templates.get(template_name)
            
        # Try case-insensitive match if exact match fails
        template_name_lower = template_name.lower()
        for key, template in self.template_io.templates.items():
            if key.lower() == template_name_lower:
                print(f"[DEBUG] TemplateManager: Found template '{key}' via case-insensitive match for '{template_name}'")
                return template
                
        # Try partial match as last resort
        for key, template in self.template_io.templates.items():
            if template_name_lower in key.lower() or key.lower() in template_name_lower:
                print(f"[DEBUG] TemplateManager: Found template '{key}' via partial match for '{template_name}'")
                return template
        
        print(f"[DEBUG] TemplateManager: Template '{template_name}' not found after exhaustive search")
        return None
    
    def cleanup_templates(self):
        """Clean up templates, e.g., remove duplicates based on name."""
        if not self.template_io:
            print("WARN: TemplateIO not initialized. Skipping template cleanup.")
            return

        cleaned_templates = {}
        duplicates_found = False
        # Iterate through the templates loaded by TemplateIO (which are in a dict)
        for name, template_data in self.template_io.templates.items():
            if name in cleaned_templates:
                print(f"WARN: Duplicate template name '{name}' detected during cleanup. Keeping first instance found by TemplateIO.")
                duplicates_found = True
            else:
                cleaned_templates[name] = template_data

        if duplicates_found:
            self.template_io.templates = cleaned_templates
            print(f"DEBUG: Template cleanup complete. {len(self.template_io.templates)} unique templates remain.")
        else:
            print("DEBUG: Template cleanup - no duplicates found.")
    
    def load_preferences(self):
        """Load preferences from preferences.json in the settings directory."""
        settings_dir = config_manager.get_settings_path()
        preferences_path = os.path.join(settings_dir, "template_manager_preferences.json")

        # Load preferences using utility, default to empty dict
        self.preferences = load_json_file(preferences_path) or {}
        print(f"DEBUG: Loaded preferences from {preferences_path}")

        # Default preferences if file didn't exist or was empty
        default_prefs = {
            "default_category": "General",
            "show_hidden_files": False,
            "sort_order": "name_asc"
            # Add other relevant preferences here
        }
        # Merge defaults for any missing keys
        updated = False
        for key, value in default_prefs.items():
            if key not in self.preferences:
                self.preferences[key] = value
                updated = True
        if updated:
             print(f"DEBUG: Applied default preferences. Saving updated file.")
             self.save_preferences() # Save back if defaults were added
    
    def save_preferences(self):
        """Save preferences to preferences.json in the settings directory."""
        settings_dir = config_manager.get_settings_path()
        preferences_path = os.path.join(settings_dir, "template_manager_preferences.json")
        if save_json_file(preferences_path, self.preferences): # Use utility
            print(f"DEBUG: Saved preferences to {preferences_path}")
        # else: save_json_file prints error 