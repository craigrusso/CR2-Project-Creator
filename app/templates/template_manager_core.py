#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
import datetime
import shutil
import time
from pathlib import Path

from app.utils.utils import load_json_file, save_json_file, get_config_paths
from app.constants import DEFAULT_STRUCTURES, PROJECT_TYPE_TO_STRUCTURE, DEFAULT_TEMPLATE_CATEGORIES
from app.templates.folder_operations import FolderOperations
from app.templates.structure_operations import StructureOperations
from app.templates.template_operations import TemplateOperations
from app.templates.project_type_manager import ProjectTypeManager
from app.core.app_config import APP_VERSION

class TemplateManagerCore(TemplateOperations):
    """
    Core functionality for managing project templates and custom structures
    """
    _instance = None  # Singleton instance
    
    def __init__(self, app=None):
        """Initialize the template manager core"""
        TemplateOperations.__init__(self)
        
        # Store the application instance
        self.app = app
        
        # Initialize template storage
        self.templates = []
        self.template_directories = []
        self.custom_structures = {}  # Dictionary mapping structure name to structure data
        self.selected_template = None
        self.folders = {}  # Map of folder name to list of template names
        self.preferences = {}  # User preferences
        
        # Create template directory if it doesn't exist
        self._ensure_directories_exist()
        
        # Load templates, structures, and folders
        self.load_template_directories()
        self.load_templates()
        self.load_custom_structures()
        self.load_folders()
        
        # Load user preferences
        self.load_preferences()
        
        # Clean up any problematic templates
        self.cleanup_templates()
        
        # Initialize additional managers
        self.init_managers()
        
        # For project types (replacing categories)
        self.project_type_manager = ProjectTypeManager(self)
    
    def _ensure_directories_exist(self):
        """Ensure all required directories exist"""
        for path_key in ["templates_dir", "custom_structures_dir", "template_directories_dir"]:
            if path_key in self.paths:
                os.makedirs(self.paths[path_key], exist_ok=True)
    
    def load_templates(self):
        """Load all templates from the templates directory"""
        self.templates = []
        
        try:
            template_files = [f for f in os.listdir(self.paths["templates_dir"]) if f.endswith('.json')]
            
            for file in template_files:
                try:
                    with open(os.path.join(self.paths["templates_dir"], file), 'r') as f:
                        template = json.load(f)
                        # Filter out templates with invalid names
                        name = template.get('name', '')
                        if name and name != "Unnamed" and name != "Unnamed Template":
                            self.templates.append(template)
                        else:
                            print(f"Skipping template with invalid name: {file}")
                except Exception as e:
                    print(f"Error loading template {file}: {e}")
        except Exception as e:
            print(f"Error loading templates: {e}")
    
    def load_template_directories(self):
        """Load all template directories"""
        self.template_directories = []
        template_directories_dir = self.paths.get("template_directories_dir")
        
        if not template_directories_dir or not os.path.exists(template_directories_dir):
            return
        
        try:
            # Look for directories that contain a template.json file
            for item in os.listdir(template_directories_dir):
                item_path = os.path.join(template_directories_dir, item)
                if os.path.isdir(item_path):
                    template_json = os.path.join(item_path, "template.json")
                    if os.path.exists(template_json):
                        try:
                            with open(template_json, 'r') as f:
                                template_info = json.load(f)
                                template_info['path'] = item_path
                                template_info['type'] = 'directory'
                                self.template_directories.append(template_info)
                        except Exception as e:
                            print(f"Error loading template directory {item}: {e}")
        except Exception as e:
            print(f"Error loading template directories: {e}")
    
    def load_custom_structures(self):
        """Load custom structures from the custom structures directory"""
        self.custom_structures = {}  # Initialize as empty dictionary
        
        custom_structures_dir = self.paths.get("custom_structures_dir")
        if not custom_structures_dir or not os.path.exists(custom_structures_dir):
            return
        
        try:
            structure_files = [f for f in os.listdir(custom_structures_dir) if f.endswith('.json')]
            
            for file in structure_files:
                try:
                    filepath = os.path.join(custom_structures_dir, file)
                    with open(filepath, 'r') as f:
                        structure_data = json.load(f)
                    
                    # Get the structure name
                    structure_name = structure_data.get('name', 'Unknown')
                    
                    # Add the structure to our dictionary
                    self.custom_structures[structure_name] = structure_data
                    print(f"INFO: Loaded custom structure '{structure_name}' from {file}")
                except Exception as e:
                    print(f"ERROR: Failed to load custom structure {file}: {e}")
                    
            print(f"INFO: Loaded {len(self.custom_structures)} custom structures")
        except Exception as e:
            print(f"ERROR: Failed to load custom structures: {e}")
            
        return self.custom_structures
    
    def load_folders(self):
        """Load template folders from configuration"""
        # Path to folders configuration file
        folders_path = os.path.join(self.paths["templates_dir"], "folders.json")
        
        # Load folders if file exists
        if os.path.exists(folders_path):
            try:
                with open(folders_path, 'r') as f:
                    self.folders = json.load(f)
            except Exception as e:
                print(f"Error loading folders: {e}")
                self.folders = {}
        else:
            # Create default folders configuration
            self.folders = {
                "Favorites": []
            }
            self.save_folders()
    
    def save_folders(self):
        """Save folder configuration"""
        folders_path = os.path.join(self.paths["templates_dir"], "folders.json")
        
        try:
            with open(folders_path, 'w') as f:
                json.dump(self.folders, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving folders: {e}")
            return False
    
    def init_managers(self):
        """Initialize additional managers"""
        # Legacy attribute for backward compatibility, can be removed in future
        self.category_manager = None
    
    def get_categories(self):
        """
        Get all used categories in templates
        This is a deprecated method kept for backward compatibility
        It now returns project types instead of categories
        """
        # Delegate to project type manager
        return self.project_type_manager.get_all_project_types()
        
    def get_all_templates(self):
        """Get all templates (both file and directory-based)"""
        return self.templates + self.template_directories
    
    def get_template_by_name(self, template_name):
        """Get a template by its name"""
        if not template_name:
            return None
            
        # Look in file templates
        for template in self.templates:
            if template.get('name') == template_name:
                return template
                
        # Look in directory templates
        for template in self.template_directories:
            if template.get('name') == template_name:
                return template
                
        return None 
    
    def cleanup_templates(self):
        """Clean up any problematic templates with invalid names"""
        # Remove any templates with empty or "Unnamed" names from in-memory list
        self.templates = [t for t in self.templates if 
                          t.get('name') and 
                          t.get('name') != "Unnamed" and 
                          t.get('name') != "Unnamed Template"]
        
        # Remove references to "Unnamed" templates from folders
        for folder_name in self.folders:
            self.folders[folder_name] = [t for t in self.folders[folder_name] 
                                        if t != "Unnamed" and t != "Unnamed Template"]
        
        # Save updated folders
        self.save_folders() 
    
    def load_preferences(self):
        """Load user preferences"""
        # Path to preferences configuration file
        prefs_path = os.path.join(self.paths["templates_dir"], "preferences.json")
        
        # Load preferences if file exists
        if os.path.exists(prefs_path):
            try:
                with open(prefs_path, 'r') as f:
                    self.preferences = json.load(f)
            except Exception as e:
                print(f"Error loading preferences: {e}")
                self.preferences = {}
        else:
            # Initialize default preferences
            self.preferences = {
                "auto_refresh": True,
                "recent_templates": [],
                "default_template": None,
                "default_structure": "Video Editing - Standard",
                "show_default_structures": True,
                "app_version": APP_VERSION
            }
            
            # Save default preferences
            self.save_preferences()
    
    def get_structure_types(self):
        """Get all available structure types from built-in and custom structures"""
        # Get structure types from DEFAULT_STRUCTURES
        structure_types = list(DEFAULT_STRUCTURES.keys())
        
        # Add structure types from PROJECT_TYPE_TO_STRUCTURE
        for project_type, structure_name in PROJECT_TYPE_TO_STRUCTURE.items():
            if project_type not in structure_types:
                structure_types.append(project_type)
        
        # Custom structures - access as a dictionary
        if hasattr(self, 'custom_structures'):
            for name in self.custom_structures.keys():
                if name not in structure_types:
                    structure_types.append(name)
        
        # Return sorted list
        return sorted(structure_types)
        
    def map_project_type_to_structure(self, project_type):
        """Map a project type to its corresponding structure name"""
        print(f"DEBUG: map_project_type_to_structure called with project_type='{project_type}'")
        
        # First check direct match in DEFAULT_STRUCTURES
        if project_type in DEFAULT_STRUCTURES:
            print(f"DEBUG: Found direct match in DEFAULT_STRUCTURES: {project_type}")
            return project_type
            
        # Next check PROJECT_TYPE_TO_STRUCTURE mapping
        if project_type in PROJECT_TYPE_TO_STRUCTURE:
            structure_name = PROJECT_TYPE_TO_STRUCTURE[project_type]
            print(f"DEBUG: Found mapping in PROJECT_TYPE_TO_STRUCTURE: {project_type} -> {structure_name}")
            return structure_name
            
        # Try different naming conventions (with or without spaces)
        names_to_try = [
            project_type, 
            f"Template_{project_type}", 
            f"Template {project_type}"
        ]
        print(f"DEBUG: Trying structure names: {names_to_try}")
        
        for name in names_to_try:
            if name in DEFAULT_STRUCTURES:
                print(f"DEBUG: Found structure with alternative name: {name}")
                return name
        
        # Default fallback to a standard structure
        print(f"DEBUG: Structure not found: {project_type}")
        return "Video Editing - Standard"
    
    def save_preferences(self):
        """Save user preferences"""
        prefs_path = os.path.join(self.paths["templates_dir"], "preferences.json")
        
        try:
            with open(prefs_path, 'w') as f:
                json.dump(self.preferences, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving preferences: {e}")
            return False 
    
    def diagnose_templates(self):
        """
        Run diagnostics on templates and structures to help with debugging
        """
        print("\n===== Template Diagnostics =====")
        print(f"Total templates: {len(self.templates)}")
        print(f"Total directory templates: {len(self.template_directories)}")
        print(f"Total custom structures: {len(self.custom_structures)}")
        print(f"Total folders: {len(self.folders)}")
        
        # Check templates for structure data
        templates_with_structure = 0
        for template in self.templates + self.template_directories:
            if "structure" in template:
                templates_with_structure += 1
                structure_size = self._count_structure_items(template["structure"]) if hasattr(self, '_count_structure_items') else "unknown"
                print(f"Template '{template.get('name')}' has structure with {structure_size} items")
                
        print(f"Templates with attached structures: {templates_with_structure}")
        
        # Check custom structures
        for structure in self.custom_structures:
            structure_size = "unknown"
            if hasattr(self, '_count_structure_items') and "structure" in structure:
                structure_size = self._count_structure_items(structure["structure"])
            print(f"Custom structure '{structure.get('name')}' has {structure_size} items")
            
        print("===== End Diagnostics =====\n")
    
    def _count_structure_items(self, structure):
        """Count items in a structure to help with debugging"""
        if not structure or not isinstance(structure, list):
            return 0
            
        count = 0
        for item in structure:
            if isinstance(item, dict):
                count += len(item)
                # Count nested items
                for key, value in item.items():
                    if isinstance(value, list):
                        count += self._count_structure_items(value)
        
        return count 