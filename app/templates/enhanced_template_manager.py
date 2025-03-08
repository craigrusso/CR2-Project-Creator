#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json

class TemplateManagerEnhanced:
    """
    Enhanced template manager with folder organization
    """
    def __init__(self, template_manager):
        # Store reference to original template manager
        self.template_manager = template_manager
        
        # Add folders support
        self.folders = {}
        self.current_folder = None
        
        # Load folders from configuration
        self.load_folders()
    
    def load_folders(self):
        """Load template folders from configuration"""
        # Path to folders configuration file
        folders_path = os.path.join(self.template_manager.paths["templates_dir"], "folders.json")
        
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
        folders_path = os.path.join(self.template_manager.paths["templates_dir"], "folders.json")
        
        try:
            with open(folders_path, 'w') as f:
                json.dump(self.folders, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving folders: {e}")
            return False
    
    def create_folder(self, folder_name):
        """Create a new template folder"""
        if not folder_name or folder_name in self.folders:
            return False
        
        self.folders[folder_name] = []
        return self.save_folders()
    
    def rename_folder(self, old_name, new_name):
        """Rename a template folder"""
        if old_name not in self.folders or new_name in self.folders:
            return False
        
        # Get templates in the folder
        templates = self.folders[old_name]
        
        # Create new folder with same templates
        self.folders[new_name] = templates
        
        # Delete old folder
        del self.folders[old_name]
        
        return self.save_folders()
    
    def delete_folder(self, folder_name):
        """Delete a template folder"""
        if folder_name not in self.folders:
            return False
        
        # Remove folder (templates will still exist, just not in a folder)
        del self.folders[folder_name]
        
        return self.save_folders()
    
    def add_to_folder(self, folder_name, template_name):
        """Add a template to a folder"""
        if folder_name not in self.folders:
            return False
        
        # Make sure template exists
        template = None
        for t in self.template_manager.templates:
            if t["name"] == template_name:
                template = t
                break
        
        if not template:
            return False
        
        # Add to folder if not already there
        if template_name not in self.folders[folder_name]:
            self.folders[folder_name].append(template_name)
            return self.save_folders()
        
        return True
    
    def remove_from_folder(self, folder_name, template_name):
        """Remove a template from a folder"""
        if folder_name not in self.folders:
            return False
        
        # Remove from folder if present
        if template_name in self.folders[folder_name]:
            self.folders[folder_name].remove(template_name)
            return self.save_folders()
        
        return True
    
    def get_folder_templates(self, folder_name):
        """Get templates in a folder"""
        if folder_name not in self.folders:
            return []
        
        # Get template names in the folder
        template_names = self.folders[folder_name]
        
        # Find the actual template objects
        templates = []
        for name in template_names:
            for template in self.template_manager.templates:
                if template["name"] == name:
                    templates.append(template)
                    break
        
        return templates
