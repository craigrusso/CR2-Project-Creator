#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
import datetime
import shutil
import time
import hashlib
import re
import uuid
import copy # Add copy import

from app.utils.utils import save_json_file, load_json_file # Keep for JSON ops
from app.core import config_manager # ADDED
from app.utils.file_cache_manager import FileCacheManager
# --- ADDED --- 
from .template_utils import sanitize_filename, _guess_file_type, _sanitize_template_name
from .template_structure_ops import TemplateStructureOps # Import the new class
from .template_io import TemplateIO # Import the new IO class
# --- END ADDED ---

class TemplateOperations:
    """
    Core operations for managing template data (loading, saving, structures, files)
    Intended to be inherited by TemplateManagerCore.
    Relies on TemplateStructureOps and TemplateIO for detailed logic.
    """
    
    def __init__(self, paths=None):
        """Initialize template operations, accepting paths from subclass."""
        super().__init__() # Initialize base object
        
        # --- MODIFIED: Accept paths dict, remove old path logic --- 
        if paths and isinstance(paths, dict):
            self.paths = paths
        else:
            # Fallback if subclass doesn't provide paths (log warning)
            print("WARN: TemplateOperations initialized without paths dict. Attempting fallback.")
            # Construct paths using config_manager directly (less ideal)
            self.paths = {
                "templates_dir": config_manager.get_templates_path(),
                "cache_dir": config_manager.get_cache_path(), 
                "custom_structures_dir": config_manager.get_structures_path(),
                "template_directories_dir": config_manager.get_template_directories_path(),
                "settings_dir": config_manager.get_settings_path()
            }
            
        # self.paths = get_config_paths() # REMOVED
        
        # Initialize templates list/dict (managed by TemplateIO)
        # self.templates = {} # REMOVED (TemplateIO holds the state)
        
        # Add flag for auto-creating structure files (default to false)
        self.auto_create_structure = False # Keep as instance state? Or move?
        
        # Preferences attribute (Can subclass set this?)
        self.preferences = getattr(self, 'preferences', {}) # Keep for now
        
        # Remove old cache path logic
        # if 'templates_cache_dir' not in self.paths or not self.paths.get('templates_cache_dir'):
        #    ... try CachePreferences ... REMOVED ...
        #    default_cache_dir = os.path.join(os.path.expanduser("~"), ".echelon", "template_cache") # REMOVED
        #    self.paths['templates_cache_dir'] = default_cache_dir # REMOVED
        # os.makedirs(self.paths['templates_cache_dir'], exist_ok=True) # REMOVED
        
        # Initialize file cache manager using the unified cache path
        cache_dir = self.paths.get('cache_dir') # Use unified 'cache_dir' key
        if cache_dir:
            self.file_cache_manager = FileCacheManager(cache_dir)
        else:
            print("ERROR: No cache directory specified in paths for TemplateOperations")
            self.file_cache_manager = None
            
        # Instantiate Helper Classes, passing the paths dict
        # Ensure these classes are updated to accept/use the paths dict correctly
        self.structure_ops = TemplateStructureOps(self.paths) 
        self.template_io = TemplateIO(self.paths, self.file_cache_manager, self.structure_ops)
        # --- END MODIFIED ---

        # Initial state (templates) are loaded by TemplateIO constructor now
    
    # --- Structure Method Delegation --- 
    def get_default_structure(self, project_type):
        """Get the default directory structure for a project type (Delegated)"""
        return self.structure_ops.get_default_structure(project_type)

    def save_custom_structure(self, name, structure):
        """Save a custom folder structure (Delegated)"""
        return self.structure_ops.save_custom_structure(name, structure)

    def get_custom_structure(self, name):
        """Get a custom structure by name (Delegated)"""
        return self.structure_ops.get_custom_structure(name)

    def save_structure(self, name, structure):
        """Save a structure (alias for save_custom_structure) (Delegated)"""
        return self.structure_ops.save_structure(name, structure)

    def load_custom_structures(self):
        """Load custom structures from disk (Delegated)"""
        return self.structure_ops.load_custom_structures()

    def delete_custom_structure(self, name):
        """Delete a custom folder structure (Delegated)"""
        return self.structure_ops.delete_custom_structure(name)
    # --- End Structure Method Delegation ---
    
    # --- Template Data Access/Manipulation (Delegated to TemplateIO) ---
    # Access template data directly via self.template_io.templates
    # Call methods like self.template_io.save_template(), self.template_io.get_template(), etc.

    # --- Methods operating on specific types or utilities (Review/Refactor Paths) ---

    def create_template_directory(self, name, source_dir, description=""):
        """Create metadata for a directory-based template in the TemplateDirectories path."""
        # --- MODIFIED: Use config_manager path for template directories ---
        # This method doesn't create the *main* template JSON, but the metadata
        # for a *directory* that acts as a template.
        dirname = sanitize_filename(name) 
        # template_dir = os.path.join(self.paths["templates_dir"], dirname) # OLD: Put metadata in main templates dir
        template_meta_dir = self.paths.get("template_directories_dir") # NEW: Put metadata in its dedicated dir
        if not template_meta_dir:
            print("ERROR: template_directories_dir not configured.")
            return False
            
        # The actual directory structure is assumed to exist at `source_dir`
        # We only save a JSON file pointing to it.
        template_meta_file = os.path.join(template_meta_dir, f"{dirname}.json") 

        # if not os.path.exists(template_dir):
        #     os.makedirs(template_dir) # We don't create the source dir here
        # template_file = os.path.join(template_dir, "template.json") # OLD: json inside the dir itself

        template_data = {
            "name": name,
            "description": description or f"Template based on {os.path.basename(source_dir)}",
            "type": "directory", # Mark as directory type
            "source_path": source_dir # Store the path to the actual directory
        }
        try:
            # Save the metadata JSON file
            save_json_file(template_meta_file, template_data)
            print(f"DEBUG: Saved directory template metadata to {template_meta_file}")
            # This type is not managed by template_io by default
            return True
        except Exception as e:
            print(f"Error creating template directory metadata file: {e}")
            return False
        # --- END MODIFIED ---
            
    def _validate_template(self, template):
        """Validate template data (Seems generic, could be utility or stay here)"""
        # This looks generally okay, doesn't directly use paths.
        required_fields = ["name", "type"]
        if not isinstance(template, dict):
            print("Error: Template data is not a dictionary.")
            return False
        for field in required_fields:
            if field not in template:
                print(f"Error: Missing required field '{field}' in template {template.get('name', '(unknown name)')}")
                return False
        if not template.get("name"):
            print("Error: Template name cannot be empty")
            return False
        return True
        
    def _count_structure_items(self, structure):
        """Count items in a structure (Simple utility, can stay or move)"""
        # This looks generally okay, doesn't directly use paths.
        if not structure:
             return 0
        
        count = 0
        if isinstance(structure, list):
            for item in structure:
                count += 1 # Count the item
                if isinstance(item, dict):
                    # Check if it represents a folder with children in various formats
                    if item.get('type') == 'folder' and 'children' in item:
                         count += self._count_structure_items(item['children'])
                    elif len(item) == 1 and isinstance(list(item.values())[0], list):
                         # Legacy format: {"FolderName": [contents...]}
                         count += self._count_structure_items(list(item.values())[0])
        elif isinstance(structure, dict):
             # Handle dict format: { "folderName": [...], "fileName": "..." }
             for key, value in structure.items():
                 count += 1 # Count the key (folder/file name)
                 if isinstance(value, (list, dict)): # If value is structure, recurse
                      count += self._count_structure_items(value)
                      
        return count
        
    def delete_template_directory(self, template):
        """Delete the metadata file for a directory-based template."""
        # --- MODIFIED: Delete the metadata JSON, not the source directory --- 
        # This method should only delete the JSON file in template_directories_dir
        # that *points* to the source directory. It should NOT delete the source itself.
        if not template or not isinstance(template, dict) or template.get('type') != 'directory':
            print("DEBUG: Invalid template data for delete_template_directory")
            return False
            
        template_name = template.get('name')
        if not template_name:
             print("DEBUG: Cannot delete directory template metadata without a name.")
             return False
             
        dirname = sanitize_filename(template_name)
        template_meta_dir = self.paths.get("template_directories_dir")
        if not template_meta_dir:
            print("ERROR: template_directories_dir not configured.")
            return False
            
        template_meta_file = os.path.join(template_meta_dir, f"{dirname}.json") 

        # template_path = template.get('path') # OLD: referred to the template dir itself
        # source_path = template.get('source_path') # NEW: path to the actual content

        if os.path.exists(template_meta_file):
            try:
                os.remove(template_meta_file)
                print(f"DEBUG: Deleted template directory metadata: {template_meta_file}")
                # Remove from specific list if tracked separately?
                # This depends on how TemplateManagerCore uses this list
                if hasattr(self, 'template_directories') and template in self.template_directories:
                     self.template_directories.remove(template)
                return True
            except Exception as e:
                print(f"Error deleting template directory metadata {template_meta_file}: {e}")
                return False
        else:
             print(f"DEBUG: Template directory metadata not found for deletion: {template_meta_file}")
             return False
        # --- END MODIFIED ---

    def update_directory_template(self, template):
        """Update the metadata file for a directory-based template."""
        # --- MODIFIED: Update metadata JSON in template_directories_dir --- 
        if not template or not isinstance(template, dict) or template.get('type') != 'directory': 
            print("DEBUG: Invalid data for update_directory_template")
            return False
            
        template_name = template.get('name')
        if not template_name:
            print("DEBUG: Cannot update directory template metadata without name.")
            return False

        # template_path = template.get('path', '') # OLD
        # if not template_path or not os.path.isdir(template_path): return False # OLD Check

        dirname = sanitize_filename(template_name)
        template_meta_dir = self.paths.get("template_directories_dir")
        if not template_meta_dir:
            print("ERROR: template_directories_dir not configured.")
            return False
            
        template_meta_file = os.path.join(template_meta_dir, f"{dirname}.json") 

        try:
            # template_json_path = os.path.join(template_path, "template.json") # OLD
            template_copy = dict(template)
            # Remove keys that shouldn't be saved in the metadata file if they exist
            # For example, runtime state or redundant paths.
            # if 'path' in template_copy: del template_copy['path'] 
            
            save_json_file(template_meta_file, template_copy) # Save updated data
            print(f"DEBUG: Updated directory template metadata: {template_meta_file}")

            # Update specific list if tracked separately?
            if hasattr(self, 'template_directories'):
                 for i, t in enumerate(self.template_directories):
                      # Match by name, as the object reference might be different
                      if t.get('name') == template_name:
                           self.template_directories[i] = template # Update in-memory list
                           print(f"DEBUG: Updated in-memory template_directories list for {template_name}")
                           break
            return True
        except Exception as e:
            print(f"Error updating directory template metadata {template_meta_file}: {e}")
            return False
        # --- END MODIFIED ---

    # REMOVED - Path logic now centralized in config_manager
    # def get_templates_dir(self):
    #    ...

# --- REMOVED Methods now handled by TemplateIO ---
# filter_templates, get_template, save_folders, save_template,
# delete_template, _clean_template_caches, rename_template,

# --- REMOVED Methods moved to TemplateStructureOps (already removed) ---
# ...

# --- REMOVED Methods moved to template_utils (already removed) ---
# ...