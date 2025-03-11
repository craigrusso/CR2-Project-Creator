#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
import datetime
import shutil

from app.utils.utils import load_json_file, save_json_file, get_config_paths
from app.constants import DEFAULT_STRUCTURES, PROJECT_TYPE_TO_STRUCTURE, DEFAULT_TEMPLATE_CATEGORIES

class TemplateManagerCore:
    """
    Core functionality for managing project templates and custom structures
    """
    def __init__(self):
        self.paths = get_config_paths()
        self.custom_structures = {}
        self.templates = []
        self.template_directories = []
        
        # Add folder management
        self.folders = {}
        self.current_folder = None
        
        # Create required directories if they don't exist
        self._ensure_directories_exist()
        
        # Load templates and structures
        self.load_templates()
        self.load_custom_structures()
        self.load_template_directories()
        self.load_folders()
    
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
                        self.templates.append(template)
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
    
    def get_categories(self):
        """Get a list of all template categories"""
        # Get categories from existing templates
        categories = set()
        
        # Add from file templates
        for template in self.templates:
            category = template.get("category")
            if category:
                categories.add(category)
        
        # Add from directory templates
        for template in self.template_directories:
            category = template.get("category")
            if category:
                categories.add(category)
        
        # Add default categories
        for category in DEFAULT_TEMPLATE_CATEGORIES:
            categories.add(category)
        
        return sorted(list(categories))
        
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