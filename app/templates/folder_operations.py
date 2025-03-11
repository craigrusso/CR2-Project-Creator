#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

class FolderOperations:
    """
    Operations for managing template folders (categories for organizing templates)
    """
    
    def get_folders(self):
        """Get list of all folders"""
        return list(self.folders.keys())
        
    def create_folder(self, folder_name):
        """Create a new template folder"""
        if not folder_name or folder_name in self.folders:
            return False
        
        self.folders[folder_name] = []
        return self.save_folders()
    
    # Alias for backwards compatibility
    add_folder = create_folder
    
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
    
    # Alias for backwards compatibility
    remove_folder = delete_folder
    
    def add_to_folder(self, folder_name, template_name):
        """Add a template to a folder"""
        if not folder_name or not template_name:
            return False
            
        # Create folder if it doesn't exist
        if folder_name not in self.folders:
            self.folders[folder_name] = []
            
        # Skip if template is already in folder
        if template_name in self.folders[folder_name]:
            return True
            
        # Add template to folder
        self.folders[folder_name].append(template_name)
        
        # Save folders
        return self.save_folders()
    
    def remove_from_folder(self, folder_name, template_name):
        """Remove a template from a folder"""
        if not folder_name or not template_name or folder_name not in self.folders:
            return False
            
        # Skip if template is not in folder
        if template_name not in self.folders[folder_name]:
            return True
            
        # Remove template from folder
        self.folders[folder_name].remove(template_name)
        
        # Save folders
        return self.save_folders()
    
    def get_folder_templates(self, folder_name):
        """Get all templates in a folder"""
        if not folder_name or folder_name not in self.folders:
            return []
            
        template_names = self.folders[folder_name]
        templates = []
        
        # Get template objects for each name
        for name in template_names:
            template = self.get_template_by_name(name)
            if template:
                templates.append(template)
        
        return templates
    
    def get_templates_in_folder(self, folder_name):
        """Get all template names in a folder"""
        if not folder_name or folder_name not in self.folders:
            return []
            
        return self.folders[folder_name]
    
    def move_template_to_folder(self, template_name, folder_name):
        """Move template to a specific folder (removing from all others)"""
        if not template_name or not folder_name:
            return False
            
        # Check if template exists
        template = self.get_template_by_name(template_name)
        if not template:
            return False
            
        # Create folder if it doesn't exist
        if folder_name not in self.folders:
            self.folders[folder_name] = []
            
        # Remove template from all other folders
        for other_folder in self.folders:
            if other_folder != folder_name and template_name in self.folders[other_folder]:
                self.folders[other_folder].remove(template_name)
                
        # Add to target folder if not already there
        if template_name not in self.folders[folder_name]:
            self.folders[folder_name].append(template_name)
            
        # Save folders
        return self.save_folders() 