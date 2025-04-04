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

from app.utils.utils import save_json_file, get_config_paths, load_json_file
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
    
    def __init__(self):
        """Initialize template operations"""
        self.paths = get_config_paths()
        
        # Initialize templates list/dict (will be managed by TemplateIO)
        # self.templates = [] # Keep this? Or move entirely to TemplateIO?
        # Let's keep it here for now for compatibility, but TemplateIO will be the source of truth.
        self.templates = {} # Changed to dict to match load_templates logic
        
        # Add flag for auto-creating structure files (default to false)
        self.auto_create_structure = False
        
        # Preferences attribute
        self.preferences = getattr(self, 'preferences', {})
        
        # Ensure we have a valid template cache directory
        # (Logic for finding/creating cache dir remains here)
        if 'templates_cache_dir' not in self.paths or not self.paths.get('templates_cache_dir'):
            try:
                from app.utils.cache_preferences import CachePreferences
                cache_prefs = CachePreferences()
                self.paths['templates_cache_dir'] = cache_prefs.get_cache_location()
                print(f"DEBUG: Set templates_cache_dir from cache preferences: {self.paths['templates_cache_dir']}")
            except Exception as e:
                print(f"WARNING: Failed to get cache location from preferences: {e}")
                default_cache_dir = os.path.join(os.path.expanduser("~"), ".echelon", "template_cache")
                self.paths['templates_cache_dir'] = default_cache_dir
                print(f"DEBUG: Set templates_cache_dir to default location: {default_cache_dir}")
            os.makedirs(self.paths['templates_cache_dir'], exist_ok=True)
        
        # Initialize file cache manager
        cache_dir = self.paths.get('templates_cache_dir')
        if cache_dir:
            self.file_cache_manager = FileCacheManager(cache_dir)
        else:
            print("Warning: No template cache directory specified in paths")
            self.file_cache_manager = None
            
        # --- Instantiate Helper Classes --- 
        self.structure_ops = TemplateStructureOps(self.paths)
        self.template_io = TemplateIO(self.paths, self.file_cache_manager, self.structure_ops) # Instantiate IO class
        # --- END Instantiate Helper Classes ---

        # Load initial state (will be delegated to TemplateIO)
        # try:
        #    self.load_templates() # Call delegated method later
        # except Exception as e:
        #    print(f"Warning: Could not load templates during init: {e}")
    
    # --- Structure Method Delegation --- 
    def get_default_structure(self, project_type):
        """Get the default directory structure for a project type (Delegated)"""
        # No internal state needed, directly call structure_ops
        return self.structure_ops.get_default_structure(project_type)

    def get_structure(self, structure_name):
        """Get the folder structure for a template (Delegated)"""
        # No internal state needed, directly call structure_ops
        return self.structure_ops.get_structure(structure_name)

    def save_custom_structure(self, name, structure):
        """Save a custom folder structure (Delegated)"""
        # StructureOps manages its own custom_structures list
        return self.structure_ops.save_custom_structure(name, structure)

    def get_custom_structure(self, name):
        """Get a custom structure by name (Delegated)"""
        # StructureOps manages its own custom_structures list
        return self.structure_ops.get_custom_structure(name)

    def save_structure(self, name, structure):
        """Save a structure (alias for save_custom_structure) (Delegated)"""
        return self.structure_ops.save_structure(name, structure)

    def load_custom_structures(self):
        """Load custom structures from disk (Delegated)"""
        # StructureOps manages its own custom_structures list
        return self.structure_ops.load_custom_structures()

    def delete_custom_structure(self, name):
        """Delete a custom folder structure (Delegated)"""
        # StructureOps manages its own custom_structures list
        return self.structure_ops.delete_custom_structure(name)
    # --- End Structure Method Delegation ---
    
    # --- Template Data Access/Manipulation (Delegated to TemplateIO) ---
    # Access template data directly via self.template_io.templates
    # Call methods like self.template_io.save_template(), self.template_io.get_template(), etc.

    # --- Methods operating on specific types or utilities (Kept) ---

    def create_template_directory(self, name, source_dir, description=""):
        """Create a template directory structure from a source directory (Likely stays or moves to IO)"""
        # This creates the template.json *within* a directory structure.
        # It doesn't seem directly related to managing the main template definitions.
        # Keep here for now, maybe move to IO if it manages directory-type templates.
        dirname = sanitize_filename(name) 
        template_dir = os.path.join(self.paths["templates_dir"], dirname)
        if not os.path.exists(template_dir):
            os.makedirs(template_dir)
        template_file = os.path.join(template_dir, "template.json")
        template_data = {
            "name": name,
            "description": description or f"Template based on {os.path.basename(source_dir)}",
            "type": "directory", # Mark as directory type
            "path": source_dir
        }
        try:
            save_json_file(template_file, template_data)
            # This type is not managed by template_io by default
            return True
        except Exception as e:
            print(f"Error creating template directory metadata file: {e}")
            return False
            
    def _validate_template(self, template):
        """Validate template data (Seems generic, could be utility or stay here)"""
        required_fields = ["name", "type"] # Path might not be required for JSON templates
        if not isinstance(template, dict):
            print("Error: Template data is not a dictionary.")
            return False
        for field in required_fields:
            if field not in template:
                print(f"Error: Missing required field '{field}' in template")
                return False
        if not template.get("name"):
            print("Error: Template name cannot be empty")
            return False
            
        # Optional: Check structure validity if present?
        # structure = template.get('structure')
        # if structure: ... validation ...
            
        return True
        
    def _count_structure_items(self, structure):
        """Count items in a structure (Simple utility, can stay or move)"""
        # This was used by _validate_template, keep it nearby for now.
        if not structure or not isinstance(structure, list):
             if isinstance(structure, dict): # Handle dict structures too
                 count = 0
                 for key, value in structure.items():
                     count += 1 # Count the folder itself
                     if isinstance(value, list): 
                          count += self._count_structure_items(value)
                 return count
             return 0
        count = 0
        for item in structure:
            if isinstance(item, dict):
                count += 1 # Count the item itself
                # If it's a folder with children, count children
                if item.get('type') == 'folder' and 'children' in item:
                     count += self._count_structure_items(item['children'])
                # If it's legacy dict format {"name": [...]} count children
                elif len(item) == 1 and isinstance(list(item.values())[0], list):
                     count += self._count_structure_items(list(item.values())[0])
            else: # Count string items (files)
                count += 1
        return count
        
    def delete_template_directory(self, template):
        """Delete a directory-based template (Likely stays or moves to IO)"""
        # Similar to create_template_directory, manages a specific type.
        # Keep here for now.
        if not template or not isinstance(template, dict) or template.get('type') != 'directory':
            print("DEBUG: Invalid template data for delete_template_directory")
            return False
        template_path = template.get('path')
        if not template_path or not os.path.isdir(template_path):
            print(f"DEBUG: Template path invalid or not a directory: {template_path}")
            return False
        template_name = template.get('name')
        try:
            shutil.rmtree(template_path)
            print(f"DEBUG: Deleted template directory {template_path}")
            # Remove from specific list if tracked separately?
            if hasattr(self, 'template_directories') and template in self.template_directories:
                 self.template_directories.remove(template)
            # Does NOT remove from self.templates - intended?
            return True
        except Exception as e:
            print(f"Error deleting template directory {template_name}: {e}")
            return False
    
    def update_directory_template(self, template):
        """Update a directory-based template's metadata (Likely stays or moves to IO)"""
        # Manages metadata *inside* a directory template.
        if not template or not isinstance(template, dict) or template.get('type') != 'directory': return False
        template_name = template.get('name')
        template_path = template.get('path', '')
        if not template_path or not os.path.isdir(template_path): return False
        try:
            template_json_path = os.path.join(template_path, "template.json")
            template_copy = dict(template)
            if 'path' in template_copy: del template_copy['path'] # Don't save path inside json
            save_json_file(template_json_path, template_copy)
            # Update specific list if tracked separately?
            if hasattr(self, 'template_directories'):
                 for i, t in enumerate(self.template_directories):
                      if t.get('name') == template_name:
                           self.template_directories[i] = template # Update in-memory list
                           break
            return True
        except Exception as e:
            print(f"Error updating directory template {template_name}: {e}")
            return False

    def get_templates_dir(self):
        """Get the templates directory path (Utility, can stay or move)"""
        # Doesn't depend on template state, just paths config.
        templates_dir = self.paths.get('templates_dir')
        if not templates_dir:
            home_dir = os.path.expanduser("~")
            templates_dir = os.path.join(home_dir, '.echelon', 'templates')
            self.paths['templates_dir'] = templates_dir # Update paths if determined here
        os.makedirs(templates_dir, exist_ok=True)
        return templates_dir

# --- REMOVED Methods now handled by TemplateIO ---
# filter_templates, get_template, save_folders, save_template,
# delete_template, _clean_template_caches, rename_template,
# update_template, save_template_info, load_templates,
# save_template_to_file, duplicate_template

# --- REMOVED Methods moved to TemplateStructureOps (already removed) ---
# ...

# --- REMOVED Methods moved to template_utils (already removed) ---
# ...