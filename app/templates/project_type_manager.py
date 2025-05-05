#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
from app.constants import DEFAULT_TEMPLATE_CATEGORIES

class ProjectTypeManager:
    """
    Manages project types (categories) and their associated folder structures
    This replaces and enhances the previous category management functionality
    """
    def __init__(self, template_manager):
        self.template_manager = template_manager
        self.custom_project_types = {}
        self.load_custom_project_types()
    
    def load_custom_project_types(self):
        """Load custom project types from configuration"""
        project_types_path = os.path.join(self.template_manager.paths["templates_dir"], "project_types.json")
        
        if os.path.exists(project_types_path):
            try:
                with open(project_types_path, 'r') as f:
                    self.custom_project_types = json.load(f)
            except Exception as e:
                print(f"Error loading project types: {e}")
                self.custom_project_types = {}
        else:
            # Initialize empty custom project types
            self.custom_project_types = {}
            # Create the file on disk
            print(f"Project types file not found at {project_types_path}. Creating new file.")
            # Make sure the directory exists
            os.makedirs(os.path.dirname(project_types_path), exist_ok=True)
            # Save empty project types to create the file
            self.save_custom_project_types()
    
    def save_custom_project_types(self):
        """Save custom project types to configuration"""
        project_types_path = os.path.join(self.template_manager.paths["templates_dir"], "project_types.json")
        
        try:
            # Make sure the directory exists
            os.makedirs(os.path.dirname(project_types_path), exist_ok=True)
            
            with open(project_types_path, 'w') as f:
                json.dump(self.custom_project_types, f, indent=2)
            print(f"Successfully saved {len(self.custom_project_types)} project types to {project_types_path}")
            return True
        except Exception as e:
            print(f"Error saving project types: {e}")
            return False
    
    def get_all_project_types(self):
        """Get all available project types (including default categories)"""
        # Force reload from disk to ensure we have the latest
        self.load_custom_project_types()
        
        # Combine default categories with any used in templates
        project_types = set(DEFAULT_TEMPLATE_CATEGORIES)
        print(f"ProjectTypeManager: Loading default categories: {project_types}")
        
        # Add custom project types
        if hasattr(self, 'custom_project_types') and self.custom_project_types:
            # Add custom types
            for project_type in self.custom_project_types.keys():
                # Validate it's a string and not empty
                if project_type and isinstance(project_type, str):
                    project_types.add(project_type)
        
        # Convert to list, sort and return
        project_types_list = sorted(list(project_types))
        print(f"ProjectTypeManager: Final project types ({len(project_types_list)} types): {project_types_list}")
        return project_types_list
    
    def create_project_type(self, name, structure_name):
        """Create a new project type with associated structure"""
        if not name or not structure_name:
            return False
        
        # Don't allow overwriting default types
        if name in DEFAULT_TEMPLATE_CATEGORIES and name not in self.custom_project_types:
            return False
        
        # Associate the project type with the structure
        self.custom_project_types[name] = {
            "structure_name": structure_name,
            "icon": "📂"  # Default icon
        }
        
        success = self.save_custom_project_types()
        print(f"Created project type '{name}' with structure '{structure_name}'. Save success: {success}")
        return success
    
    def delete_project_type(self, name):
        """Delete a custom project type"""
        # Don't allow deleting default types
        if name in DEFAULT_TEMPLATE_CATEGORIES and name not in self.custom_project_types:
            return False
        
        if name in self.custom_project_types:
            del self.custom_project_types[name]
            return self.save_custom_project_types()
        
        return False
    
    def get_structure_for_project_type(self, project_type):
        """Get the structure name associated with a project type"""
        # Check custom project types first
        if project_type in self.custom_project_types:
            return self.custom_project_types[project_type].get("structure_name")
        
        # PROJECT_TYPE_TO_STRUCTURE mapping removed, as it depended on obsolete constants
        # Maybe add logic here to find a structure matching the project type name?
        # For now, default to a generic name or None
        print(f"ProjectTypeManager: No custom structure found for project type '{project_type}'. Falling back.")
        
        # Fallback: Look for a structure with the same name as the project type
        # This might need access to the structure list from template_manager
        if hasattr(self.template_manager, 'get_structure'):
            structure = self.template_manager.get_structure(project_type)
            if structure:
                # Found a structure with matching name
                return project_type
        
        # Default to standard (or perhaps None is safer?)
        return None # Return None instead of "standard" if no mapping exists
    
    def change_template_project_type(self, template_name, new_project_type):
        """Change the project type of a template"""
        for template in self.template_manager.templates:
            if template["name"] == template_name:
                # Update the type field instead of category
                old_type = template.get("type", "")
                template["type"] = new_project_type
                
                # Save the template file
                filename = template_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
                file_path = os.path.join(self.template_manager.paths["templates_dir"], f"{filename}.json")
                
                try:
                    with open(file_path, 'w') as f:
                        json.dump(template, f, indent=2)
                    return True
                except Exception as e:
                    # Restore old type on error
                    template["type"] = old_type
                    print(f"Error changing template project type: {e}")
                    return False
        
        return False
    
    def sync_with_custom_categories(self):
        """Sync project types with custom categories"""
        # This method is no longer needed as we're only using project types
        pass 