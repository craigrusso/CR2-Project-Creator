#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
import datetime
import shutil
import time
from pathlib import Path

from app.utils.utils import load_json_file, save_json_file, get_config_paths
from app.constants import DEFAULT_STRUCTURES, PROJECT_TYPE_TO_STRUCTURE, DEFAULT_TEMPLATE_CATEGORIES, APP_VERSION
from app.templates.folder_operations import FolderOperations
from app.templates.structure_operations import StructureOperations
from app.templates.template_operations import TemplateOperations
from app.templates.project_type_manager import ProjectTypeManager
from app.utils.cache_preferences import CachePreferences

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
        
        # Add the cache_location path from CachePreferences
        cache_prefs = CachePreferences()
        self.paths["templates_cache_dir"] = cache_prefs.get_cache_location()
        print(f"DEBUG: Set templates_cache_dir path to: {self.paths['templates_cache_dir']}")
        
        # Create template directory if it doesn't exist
        self._ensure_directories_exist()
        
        # Load templates, structures, and folders
        self.load_template_directories()
        self.load_templates()
        
        # Load custom structures and ensure they're properly stored
        if not hasattr(self, 'custom_structures'):
            self.custom_structures = {}
        
        self.load_custom_structures()
        
        # Make sure structures reference the same dictionary as custom_structures for backward compatibility
        if not hasattr(self, 'structures'):
            self.structures = self.custom_structures
        else:
            # Update structures with custom_structures values
            for key, value in self.custom_structures.items():
                self.structures[key] = value
        
        # Load folders
        self.load_folders()
        
        # Load user preferences
        self.load_preferences()
        
        # Clean up any problematic templates
        self.cleanup_templates()
        
        # Initialize additional managers
        self.init_managers()
        
        # For project types (replacing categories)
        self.project_type_manager = ProjectTypeManager(self)
        
        # Debug check to make sure structures are properly loaded
        print(f"DEBUG: After initialization: {len(self.custom_structures)} custom structures available")
        print(f"DEBUG: Structure keys: {list(self.custom_structures.keys())}")
    
    def _ensure_directories_exist(self):
        """Ensure all required directories exist"""
        # Add templates_cache_dir to the list of directories to ensure it exists
        for path_key in ["templates_dir", "custom_structures_dir", "template_directories_dir", "templates_cache_dir"]:
            if path_key in self.paths:
                os.makedirs(self.paths[path_key], exist_ok=True)
                print(f"DEBUG: Ensured directory exists: {self.paths[path_key]}")
    
    def load_templates(self):
        """Load all templates from the templates directory"""
        self.templates = []
        
        try:
            # Get all JSON files in the templates directory
            templates_dir = self.paths.get("templates_dir", "")
            if not templates_dir or not os.path.exists(templates_dir):
                print(f"WARNING: Templates directory does not exist: {templates_dir}")
                return
                
            template_files = [f for f in os.listdir(templates_dir) 
                              if f.endswith('.json') and not f.startswith('.')]
            
            # Some system files we should never load as templates
            excluded_files = ['preferences.json', 'folders.json', 'colors.json', 'settings.json', 'settings.json.bak', 'project_types.json']
            
            # Keep track of loaded template names to avoid duplicates
            loaded_templates = set()
            
            for file in template_files:
                if file in excluded_files:
                    print(f"Skipping template with invalid name: {file}")
                    continue
                    
                try:
                    # Load the template JSON file
                    file_path = os.path.join(templates_dir, file)
                    
                    # Check if the file is valid JSON
                    try:
                        with open(file_path, 'r') as f:
                            template_data = json.load(f)
                    except json.JSONDecodeError as e:
                        print(f"ERROR: Invalid JSON in template file {file}: {e}")
                        continue
                    except Exception as e:
                        print(f"ERROR: Failed to read template file {file}: {e}")
                        continue
                    
                    # Make sure it's a dictionary
                    if not isinstance(template_data, dict):
                        print(f"WARNING: Template file {file} contains invalid data (not a dictionary)")
                        continue
                        
                    # Extract template name, handling missing name and Template_ prefix
                    template_name = template_data.get('name', '')
                    
                    # Handle the case where 'name' field is missing but the filename gives us a clue
                    if not template_name and file.endswith('.json'):
                        # Extract name from filename
                        base_name = file[:-5]  # Remove .json extension
                        if base_name.startswith('Template_'):
                            base_name = base_name[9:]  # Remove Template_ prefix
                        template_name = base_name.replace('_', ' ')  # Convert underscores to spaces
                        
                        # Update the template data with the extracted name
                        template_data['name'] = template_name
                        print(f"[DEBUG] TemplateManagerCore: Extracted name '{template_name}' from filename '{file}'")
                    
                    # Skip templates with empty or default names
                    if not template_name or template_name == "Unnamed" or template_name == "Unnamed Template":
                        print(f"Skipping template with invalid name: {file}")
                        continue
                    
                    # Skip duplicate templates (same name)
                    if template_name in loaded_templates:
                        print(f"WARNING: Skipping duplicate template '{template_name}' from file {file}")
                        continue
                    
                    # Check for Template_ prefix in name and handle it correctly
                    if template_name.startswith("Template_"):
                        # For display purposes, also store the clean name without prefix
                        clean_name = template_name[9:]  # Remove Template_ prefix
                        
                        # Update the template data with the clean name if needed
                        if not template_data.get('display_name'):
                            template_data['display_name'] = clean_name
                    
                    # Ensure template has a type (default to "Standard" if missing)
                    if 'type' not in template_data or not template_data['type']:
                        template_data['type'] = 'Standard'
                        print(f"[DEBUG] TemplateManagerCore: Added default type 'Standard' to template: {template_name}")
                        
                    # Ensure template structure is in correct format
                    if 'structure' in template_data and template_data['structure']:
                        # Structure is already present, make sure it's properly formatted
                        print(f"[DEBUG] TemplateManagerCore: Template '{template_name}' has structure")
                    
                    # Validate files array exists
                    if 'files' not in template_data:
                        template_data['files'] = []
                        print(f"[DEBUG] TemplateManagerCore: Added empty files array to template: {template_name}")
                    
                    # Store the file path in the template data for future reference
                    template_data['file_path'] = file_path
                        
                    # Add the template to our list
                    self.templates.append(template_data)
                    loaded_templates.add(template_name)
                    print(f"[DEBUG] TemplateManagerCore: Loaded template: {template_name}")
                except Exception as e:
                    print(f"Error loading template {file}: {e}")
                    import traceback
                    traceback.print_exc()
                    
            print(f"[DEBUG] TemplateManagerCore: Loaded {len(self.templates)} templates")
        except Exception as e:
            print(f"Error loading templates: {e}")
            import traceback
            traceback.print_exc()
        
        # Also load structures as templates for seamless integration
        self.load_structures_as_templates()
    
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
        """Load custom structures from structures directory and store in both dictionaries"""
        # First call the parent method to load structures
        result = super().load_custom_structures()
        
        # Make sure the custom_structures dictionary is populated
        if not self.custom_structures:
            print("WARNING: custom_structures dictionary is empty after load, attempting to force load")
            # Try to directly load the structures
            structures_dir = self.paths.get('custom_structures_dir')
            if structures_dir and os.path.exists(structures_dir):
                print(f"DEBUG: Loading structures from {structures_dir}")
                structure_files = [f for f in os.listdir(structures_dir) if f.endswith('.json')]
                
                # Files that should not be treated as structures
                excluded_files = ['project_types.json']
                
                for filename in structure_files:
                    if filename in excluded_files:
                        print(f"DEBUG: Skipping {filename} - it's not a structure file")
                        continue
                        
                    try:
                        structure_path = os.path.join(structures_dir, filename)
                        with open(structure_path, 'r') as f:
                            structure_data = json.load(f)
                            
                        if structure_data:
                            structure_name = filename.replace('.json', '')
                            # Convert underscores to spaces in the structure name
                            display_name = structure_name.replace('_', ' ')
                            if display_name.startswith('Template '):
                                display_name = display_name[len('Template '):]
                                
                            # Store in both dictionaries
                            self.custom_structures[structure_name] = structure_data
                            if 'name' in structure_data:
                                self.custom_structures[structure_data['name']] = structure_data
                                
                            print(f"DEBUG: Directly loaded structure {structure_name}")
                    except Exception as e:
                        print(f"WARNING: Failed to load structure {filename}: {e}")
        
        print(f"DEBUG: Loaded {len(self.custom_structures)} custom structures")
        
        # Ensure both dictionaries have the same data
        if hasattr(self, 'structures'):
            for key, value in self.custom_structures.items():
                self.structures[key] = value
                
        return result
    
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
        # We no longer use the category manager - only the project type manager
        pass
    
    def get_categories(self):
        """
        Get all available categories/project types
        """
        # Get all categories from project_type_manager
        if hasattr(self, 'project_type_manager'):
            return self.project_type_manager.get_all_project_types()
        
        # Fallback to default categories if project_type_manager not available
        from app.constants import DEFAULT_TEMPLATE_CATEGORIES
        return list(DEFAULT_TEMPLATE_CATEGORIES)
        
    def get_all_templates(self):
        """Get all templates (both file and directory-based)"""
        return self.templates + self.template_directories
    
    def get_template_by_name(self, template_name):
        """
        Get a template by its name, handling various name formats.
        
        Args:
            template_name (str): Name of the template to find
            
        Returns:
            dict: Template object if found, None otherwise
        """
        if not template_name:
            print(f"[DEBUG] TemplateManagerCore: get_template_by_name called with empty name")
            return None
        
        # Generate name variations to try
        template_name = str(template_name).strip()
        name_variations = [
            template_name,                                 # Original name
            template_name.lower(),                         # Lowercase
            template_name.upper(),                         # Uppercase
        ]
        
        # Add variations with and without Template_ prefix
        if template_name.startswith("Template_"):
            # Add version without prefix
            clean_name = template_name[9:]  # Remove Template_ prefix
            name_variations.append(clean_name)
            name_variations.append(clean_name.lower())
        else:
            # Add version with prefix
            name_variations.append(f"Template_{template_name}")
        
        # Try with spaces converted to underscores and vice versa
        name_variations.append(template_name.replace(" ", "_"))
        name_variations.append(template_name.replace("_", " "))
        
        # Debug template search
        print(f"[DEBUG] TemplateManagerCore: Looking for template '{template_name}' with {len(name_variations)} variations")
        print(f"[DEBUG] TemplateManagerCore: We have {len(self.templates)} templates loaded")
        
        # Print the first few template names for debugging
        template_names = [t.get('name', 'unnamed') for t in self.templates]
        debug_names = template_names[:5] if len(template_names) > 5 else template_names
        print(f"[DEBUG] TemplateManagerCore: Available templates: {debug_names}{'...' if len(template_names) > 5 else ''}")
        
        # First try exact match in file templates
        for template in self.templates:
            template_name_from_obj = template.get('name', '')
            if template_name_from_obj and template_name_from_obj in name_variations:
                print(f"[DEBUG] TemplateManagerCore: Found template by exact name match: {template_name_from_obj}")
                return template
        
        # Then try more flexible matching in file templates
        for template in self.templates:
            template_name_from_obj = template.get('name', '')
            if not template_name_from_obj:
                continue
            
            # Try case insensitive match
            if template_name_from_obj.lower() in [v.lower() for v in name_variations]:
                print(f"[DEBUG] TemplateManagerCore: Found template by case-insensitive match: {template_name_from_obj}")
                return template
            
            # Try with/without Template_ prefix
            if template_name_from_obj.startswith("Template_"):
                clean_obj_name = template_name_from_obj[9:]
                if clean_obj_name.lower() in [v.lower() for v in name_variations]:
                    print(f"[DEBUG] TemplateManagerCore: Found template by prefix-stripped match: {template_name_from_obj}")
                    return template
            else:
                prefixed_obj_name = f"Template_{template_name_from_obj}"
                if prefixed_obj_name.lower() in [v.lower() for v in name_variations]:
                    print(f"[DEBUG] TemplateManagerCore: Found template by prefix-added match: {template_name_from_obj}")
                    return template
        
        # Try same approach with directory templates
        if hasattr(self, 'template_directories'):
            for template in self.template_directories:
                template_name_from_obj = template.get('name', '')
                if template_name_from_obj and template_name_from_obj in name_variations:
                    print(f"[DEBUG] TemplateManagerCore: Found directory template by name: {template_name_from_obj}")
                    return template
                
                # Try more flexible matching
                if template_name_from_obj and template_name_from_obj.lower() in [v.lower() for v in name_variations]:
                    print(f"[DEBUG] TemplateManagerCore: Found directory template by flexible match: {template_name_from_obj}")
                    return template
        
        # Try to find by filename match (for templates saved with different internal name)
        for template in self.templates:
            if 'file_path' in template:
                file_path = template['file_path']
                if file_path:
                    # Extract filename without extension
                    filename = os.path.basename(file_path)
                    if filename.endswith('.json'):
                        filename = filename[:-5]  # Remove .json extension
                    
                    # Check if filename matches any of our variations
                    if filename.lower() in [v.lower() for v in name_variations]:
                        print(f"[DEBUG] TemplateManagerCore: Found template by filename match: {filename} -> {template.get('name', '')}")
                        return template
                        
        # If not found anywhere
        template_variations_str = ", ".join(name_variations[:3]) + (", ..." if len(name_variations) > 3 else "")
        print(f"[DEBUG] TemplateManagerCore: Template not found for name '{template_name}' (tried variations: {template_variations_str})")
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
    
    def load_structures_as_templates(self):
        """Load custom structures as templates if they don't exist as templates"""
        try:
            # Make sure we have custom structures loaded
            if not hasattr(self, 'custom_structures') or not self.custom_structures:
                if hasattr(self, 'load_custom_structures'):
                    self.load_custom_structures()
                else:
                    print("[WARNING] TemplateManagerCore: Cannot load structures, no load_custom_structures method")
                    return
            
            # Track how many structures were converted to templates
            converted_count = 0
            
            # Handle different custom_structures formats
            if isinstance(self.custom_structures, dict):
                # Dictionary format - iterate over keys and values
                for structure_name, structure_data in self.custom_structures.items():
                    # Process each structure by name and data
                    if self._convert_structure_to_template(structure_name, structure_data):
                        converted_count += 1
            elif isinstance(self.custom_structures, list):
                # List format - each item should be a dict with a name
                for structure_item in self.custom_structures:
                    if isinstance(structure_item, dict) and 'name' in structure_item:
                        structure_name = structure_item['name']
                        # Process the structure using its name and data
                        if self._convert_structure_to_template(structure_name, structure_item):
                            converted_count += 1
                    else:
                        print(f"[WARNING] TemplateManagerCore: Skipping structure item without name: {structure_item}")
            else:
                print(f"[ERROR] TemplateManagerCore: custom_structures has unknown type: {type(self.custom_structures)}")
                return
            
            print(f"[DEBUG] TemplateManagerCore: Added {converted_count} structures as templates")
            
        except Exception as e:
            print(f"[ERROR] TemplateManagerCore: Error loading structures as templates: {e}")
            import traceback
            traceback.print_exc()
            
    def _convert_structure_to_template(self, structure_name, structure_data):
        """
        Convert a structure to a template
        
        Args:
            structure_name: Name of the structure
            structure_data: Structure data
            
        Returns:
            bool: True if converted, False otherwise
        """
        # Skip if not a proper structure dictionary
        if not isinstance(structure_data, dict):
            return False
            
        # Skip project_types.json file - it's not meant to be a template
        if structure_name == "project_types":
            return False
            
        # Skip if we already have a template with this name
        template_name = structure_name
        if structure_name.startswith("Template_"):
            # Extract the template name without the Template_ prefix
            template_name = structure_name[9:]
        
        # Check if we already have this template by name
        template_exists = False
        if isinstance(self.templates, dict):
            template_exists = template_name in self.templates
        else:
            for template in self.templates:
                if isinstance(template, dict) and template.get('name') == template_name:
                    template_exists = True
                    break
                    
        if template_exists:
            return False
            
        # Create a template object from the structure data
        template = {
            'name': template_name,
            'description': structure_data.get('description', f'Template for {template_name}'),
            'structure_name': structure_name,
            'type': 'custom',
            'tags': structure_data.get('tags', []),
            'category': structure_data.get('category', 'Custom'),
            'created': structure_data.get('created', time.time()),
            'modified': structure_data.get('modified', time.time())
        }
        
        # Add the structure data to the template if available
        if 'structure' in structure_data:
            template['structure'] = structure_data['structure']
            
        # Add the template to our list
        if isinstance(self.templates, dict):
            self.templates[template_name] = template
        else:
            self.templates.append(template)
            
        return True 
    
    def save_structure(self, structure_name, structure_data):
        """
        Save a structure to the custom structures directory
        
        Args:
            structure_name: Name of the structure
            structure_data: Structure data to save (array of folders/files or object with structure property)
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        print(f"DEBUG: Saving structure '{structure_name}'")
        
        # Normalize structure data by converting to dictionary if array
        if isinstance(structure_data, list):
            structure_data = {
                'name': structure_name,
                'structure': structure_data,
                'created': datetime.datetime.now().timestamp(),
                'modified': datetime.datetime.now().timestamp()
            }
        elif isinstance(structure_data, dict):
            # Make sure required fields exist
            if 'name' not in structure_data:
                structure_data['name'] = structure_name
                
            if 'structure' not in structure_data and not any(k in structure_data for k in ['directories', 'layout']):
                # If we have a dictionary with folder names as keys, convert to structure format
                if any(isinstance(v, list) for v in structure_data.values()):
                    # Format is {folder_name: [contents]}
                    structure_list = []
                    for folder, contents in structure_data.items():
                        if isinstance(contents, list):
                            structure_list.append({folder: contents})
                    structure_data = {
                        'name': structure_name,
                        'structure': structure_list,
                        'created': datetime.datetime.now().timestamp(),
                        'modified': datetime.datetime.now().timestamp()
                    }
                else:
                    # Not a recognizable structure format
                    print(f"ERROR: Structure data is not in a valid format: {structure_data}")
                    return False
            
            # Update timestamps
            structure_data['modified'] = datetime.datetime.now().timestamp()
            if 'created' not in structure_data:
                structure_data['created'] = datetime.datetime.now().timestamp()
        
        # Make sure category information is preserved
        if 'category' in structure_data and hasattr(self, 'project_type_manager'):
            category = structure_data['category']
            print(f"DEBUG: Structure has category '{category}', setting as project type")
            self.project_type_manager.create_project_type(category, structure_name)
        
        # Generate filename
        filename = structure_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        if not filename.endswith('.json'):
            filename += '.json'
            
        # Generate path
        file_path = os.path.join(self.paths["custom_structures_dir"], filename)
        
        # Save the structure
        try:
            with open(file_path, 'w') as f:
                json.dump(structure_data, f, indent=2)
                
            # Update in-memory structure
            self.custom_structures[structure_name] = structure_data
            if hasattr(self, 'structures'):
                self.structures[structure_name] = structure_data
                
            print(f"DEBUG: Successfully saved structure '{structure_name}' to {file_path}")
            
            # Save as template for template gallery
            self._save_as_template(structure_name, structure_data)
            
            return True
        except Exception as e:
            print(f"ERROR saving structure: {e}")
            import traceback
            traceback.print_exc()
            return False 
    
    def _save_as_template(self, structure_name, structure_data):
        """
        Save a structure as a template in the templates directory
        
        Args:
            structure_name: Name of the structure
            structure_data: Structure data to save
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        # Skip if structure data is invalid
        if not structure_data:
            print(f"TemplateManagerCore: Cannot save template - structure_data is invalid")
            return False
            
        try:
            # Create a template file path
            filename = structure_name.replace(' ', '_')
            if not filename.endswith('.json'):
                filename += '.json'
            template_file = os.path.join(self.paths["templates_dir"], filename)
            
            # Extract structure from the data
            structure = None
            if isinstance(structure_data, list):
                structure = structure_data
            elif isinstance(structure_data, dict):
                structure = structure_data.get('structure', [])
                
            # Get the category from the structure data with detailed logging
            # We support both 'category' and 'template_category' fields
            category = None
            if isinstance(structure_data, dict):
                # Check all possible category field names in priority order
                for field in ['category', 'template_category', 'type']:
                    if field in structure_data and structure_data[field]:
                        category = structure_data[field]
                        print(f"TemplateManagerCore: Found category '{category}' in field '{field}'")
                        break
            
            # Default to 'Custom' if no category found
            if not category:
                category = 'Custom'
                print(f"TemplateManagerCore: No category found in structure_data, defaulting to 'Custom'")
            
            # Get valid categories
            valid_categories = self.get_categories()
            print(f"TemplateManagerCore: Validating category '{category}' against valid categories: {valid_categories}")
            
            # If the category is not valid, use 'Custom' but log a warning
            if category not in valid_categories:
                print(f"WARNING: Category '{category}' is not in valid categories, using 'Custom' instead")
                category = 'Custom'
                
            # Create template data
            template_data = {
                'name': structure_name,
                'description': structure_data.get('description', structure_data.get('template_info', '')),
                'category': category,
                'created': structure_data.get('created', time.time()),
                'modified': time.time(),
                'files': structure_data.get('files', [])
            }
            
            # Add structure if we have it
            if structure:
                template_data['structure'] = structure
                
            # Save the template file
            with open(template_file, 'w') as f:
                json.dump(template_data, f, indent=2)
                
            print(f"TemplateManagerCore: Saved template '{structure_name}' with category '{category}' to {template_file}")
            
            # Add to project type manager if needed
            if hasattr(self, 'project_type_manager'):
                self.project_type_manager.create_project_type(category, "Video Editing - Standard")
                print(f"TemplateManagerCore: Added category '{category}' to project_type_manager")
                
            return True
        except Exception as e:
            print(f"ERROR saving template: {e}")
            import traceback
            traceback.print_exc()
            return False 