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
        self.custom_structures = []
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
        """Load all custom folder structures"""
        self.custom_structures = {}
        structures_dir = self.paths["custom_structures_dir"]
        
        try:
            structure_files = [f for f in os.listdir(structures_dir) if f.endswith('.json')]
            
            for file in structure_files:
                try:
                    with open(os.path.join(structures_dir, file), 'r') as f:
                        structure = json.load(f)
                        name = structure.get("name", os.path.splitext(file)[0])
                        self.custom_structures[name] = structure
                except Exception as e:
                    print(f"Error loading structure {file}: {e}")
        except Exception as e:
            print(f"Error loading custom structures: {e}")
    
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
                "Recent": [],
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
        preferences_path = os.path.join(self.paths["templates_dir"], "preferences.json")
        
        # Load preferences if file exists
        if os.path.exists(preferences_path):
            try:
                with open(preferences_path, 'r') as f:
                    self.preferences = json.load(f)
            except Exception as e:
                print(f"Error loading preferences: {e}")
                self.preferences = {}
        else:
            # Create default preferences
            self.preferences = {
                "show_default_structures": True,
                "structure_categories": {},
                "structure_assignments": {}
            }
            self.save_preferences()
    
    def save_preferences(self):
        """Save user preferences"""
        preferences_path = os.path.join(self.paths["templates_dir"], "preferences.json")
        
        try:
            with open(preferences_path, 'w') as f:
                json.dump(self.preferences, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving preferences: {e}")
            return False 