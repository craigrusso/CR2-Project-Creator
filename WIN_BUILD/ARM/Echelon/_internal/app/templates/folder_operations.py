#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

class FolderOperations:
    """
    Operations for managing template folders (categories for organizing templates)
    """
    
    def __init__(self):
        """Initialize folder operations"""
        super().__init__() # Initialize base/next in MRO
        
        # Only initialize folders if it doesn't already exist
        # This is important when inheriting from TemplateManagerCore which already sets self.folders
        if not hasattr(self, 'folders') or self.folders is None:
            print("[DEBUG] FolderOps: Initializing folders attribute")
            self.folders = {}
        else:
            print("[DEBUG] FolderOps: Using existing folders attribute with", len(self.folders), "folders")
    
    def get_folders(self):
        """Get list of all folders"""
        if not hasattr(self, 'folders') or self.folders is None:
            print("[DEBUG] FolderOps: Warning - folders attribute is missing in get_folders()")
            return []
        return list(self.folders.keys())
        
    def create_folder(self, folder_name):
        """Create a new folder with the given name
        
        Args:
            folder_name (str): Name of the folder to create
            
        Returns:
            bool: True if folder was created successfully, False otherwise
        """
        print(f"[DEBUG] FolderOps: Creating folder '{folder_name}'")
        
        # Validate input
        if not folder_name or not isinstance(folder_name, str):
            print(f"[DEBUG] FolderOps: Invalid folder name: '{folder_name}'")
            return False
        
        # Trim whitespace
        folder_name = folder_name.strip()
        
        if not folder_name:
            print(f"[DEBUG] FolderOps: Empty folder name after trimming")
            return False
        
        # Check if folder already exists
        if folder_name in self.folders:
            print(f"[DEBUG] FolderOps: Folder '{folder_name}' already exists")
            return False
        
        try:
            # Create the new folder
            self.folders[folder_name] = []
            
            # Save the folders to disk
            print(f"[DEBUG] FolderOps: Saving folders after creation")
            self.save_folders()
            
            return True
        except Exception as e:
            import traceback
            print(f"[DEBUG] FolderOps: Error creating folder: {e}")
            traceback.print_exc()
            return False
    
    # Alias for backwards compatibility
    add_folder = create_folder
    
    def folder_exists(self, folder_name):
        """Check if a folder exists by name
        
        Args:
            folder_name (str): Name of the folder to check
            
        Returns:
            bool: True if the folder exists, False otherwise
        """
        if not hasattr(self, 'folders') or not isinstance(self.folders, dict):
            return False
            
        return folder_name in self.folders
    
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
        if not folder_name or not template_name:
            print(f"[DEBUG] FolderOps: Invalid folder or template name: '{folder_name}', '{template_name}'")
            return False
        
        # Skip if folder doesn't exist - but return True since the template isn't in the folder
        if folder_name not in self.folders:
            print(f"[DEBUG] FolderOps: Folder '{folder_name}' doesn't exist, template already not in folder")
            return True
        
        # Skip if template is not in folder - also return True since it's already not in the folder
        if template_name not in self.folders[folder_name]:
            print(f"[DEBUG] FolderOps: Template '{template_name}' not in folder '{folder_name}', nothing to remove")
            return True
        
        # Remove template from folder
        print(f"[DEBUG] FolderOps: Removing template '{template_name}' from folder '{folder_name}'")
        self.folders[folder_name].remove(template_name)
        
        # Save folders
        saved = self.save_folders()
        print(f"[DEBUG] FolderOps: Folders saved: {saved}")
        return saved
    
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
            print(f"[DEBUG] FolderOps: Invalid folder for get_templates_in_folder: '{folder_name}'")
            return []
        
        template_names = self.folders[folder_name]
        print(f"[DEBUG] FolderOps: Templates in folder '{folder_name}': {template_names}")
        
        # Remove any Template-# entries that might be duplicates
        real_templates = []
        seen_names = set()
        
        for name in template_names:
            # Skip any Template-# entries if we already have the real template with the same name
            template = self.get_template_by_name(name)
            if not template:
                print(f"[DEBUG] FolderOps: Template not found: '{name}'")
                continue
            
            real_name = template.get('name')
            if real_name in seen_names:
                print(f"[DEBUG] FolderOps: Skipping duplicate template: '{name}' (real name: '{real_name}')")
                continue
            
            seen_names.add(real_name)
            real_templates.append(name)
        
        print(f"[DEBUG] FolderOps: Returning cleaned template list: {real_templates}")
        return real_templates
    
    def move_template_to_folder(self, template_name, folder_name):
        """Move template to a specific folder (removing from all others)"""
        if not template_name:
            print(f"[DEBUG] FolderOps: Invalid template name: '{template_name}'")
            return False
        
        # Check if template exists
        template = self.get_template_by_name(template_name)
        if not template:
            print(f"[DEBUG] FolderOps: Template not found: '{template_name}'")
            return False
        
        # Get the real template name from the template object to ensure consistency
        real_template_name = template.get('name', template_name)
        
        if folder_name is None:
            # When folder_name is None, just remove the template from all folders
            print(f"[DEBUG] FolderOps: Removing template '{real_template_name}' from all folders")
            # Remove template from all folders
            for other_folder in list(self.folders.keys()):
                if template_name in self.folders[other_folder]:
                    print(f"[DEBUG] FolderOps: Removing '{template_name}' from folder '{other_folder}'")
                    self.folders[other_folder].remove(template_name)
                if real_template_name != template_name and real_template_name in self.folders[other_folder]:
                    print(f"[DEBUG] FolderOps: Removing '{real_template_name}' from folder '{other_folder}'")
                    self.folders[other_folder].remove(real_template_name)
            
            # Save folders
            print(f"[DEBUG] FolderOps: Saving folders after removing from all")
            return self.save_folders()
        
        print(f"[DEBUG] FolderOps: Moving template '{real_template_name}' to folder '{folder_name}'")
        
        # Create folder if it doesn't exist
        if folder_name not in self.folders:
            print(f"[DEBUG] FolderOps: Creating new folder '{folder_name}'")
            self.folders[folder_name] = []
        
        # Remove template from all other folders
        for other_folder in list(self.folders.keys()):
            if other_folder != folder_name:
                # Use both the original name and real name for removal
                if template_name in self.folders[other_folder]:
                    print(f"[DEBUG] FolderOps: Removing '{template_name}' from folder '{other_folder}'")
                    self.folders[other_folder].remove(template_name)
                if real_template_name != template_name and real_template_name in self.folders[other_folder]:
                    print(f"[DEBUG] FolderOps: Removing '{real_template_name}' from folder '{other_folder}'")
                    self.folders[other_folder].remove(real_template_name)
                
        # Add to target folder if not already there
        if real_template_name not in self.folders[folder_name]:
            print(f"[DEBUG] FolderOps: Adding '{real_template_name}' to folder '{folder_name}'")
            self.folders[folder_name].append(real_template_name)
        
        # Handle any renamed versions that might exist
        possible_renamed_templates = [t for t in self.folders[folder_name] if t.startswith("Template-") and t != real_template_name]
        for renamed in possible_renamed_templates:
            # Check if this renamed template points to the same template
            renamed_template = self.get_template_by_name(renamed)
            if renamed_template and renamed_template.get('name') == real_template_name:
                print(f"[DEBUG] FolderOps: Removing renamed version '{renamed}' from folder '{folder_name}'")
                self.folders[folder_name].remove(renamed)
        
        # Save folders
        print(f"[DEBUG] FolderOps: Saving folders after move")
        return self.save_folders()
    
    def get_folder_containing_template(self, template_name):
        """Find which folder contains the given template.
        
        Args:
            template_name (str): Name of the template to find
            
        Returns:
            str or None: Name of the folder containing the template, or None if not in any folder
        """
        if not template_name or not hasattr(self, 'folders'):
            return None
        
        # Normalize template name to improve matching
        template_name = template_name.strip()
        if not template_name:
            return None
        
        # Try to find the template in any folder by exact match
        for folder_name, templates in self.folders.items():
            if template_name in templates:
                print(f"[DEBUG] FolderOps: Found template '{template_name}' in folder '{folder_name}'")
                return folder_name
            
        # If we have a template manager with get_template_by_name, try to get the real template name
        template = None
        if hasattr(self, 'get_template_by_name'):
            template = self.get_template_by_name(template_name)
        
        # If we found a template, try with its real name
        if template and isinstance(template, dict) and 'name' in template:
            real_name = template['name']
            if real_name and real_name != template_name:
                print(f"[DEBUG] FolderOps: Using real template name '{real_name}' to find folder")
                for folder_name, templates in self.folders.items():
                    if real_name in templates:
                        print(f"[DEBUG] FolderOps: Found template '{real_name}' in folder '{folder_name}'")
                        return folder_name
        
        # Template not found in any folder
        print(f"[DEBUG] FolderOps: Template '{template_name}' not found in any folder")
        return None 