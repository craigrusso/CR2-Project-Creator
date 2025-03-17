#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
import datetime
import shutil
import time

from app.utils.utils import save_json_file
from app.constants import PROJECT_TYPE_TO_STRUCTURE

class TemplateOperations:
    """
    Operations for managing templates (create, read, update, delete)
    """
    
    def __init__(self):
        """Initialize template operations"""
        from app.utils.utils import get_config_paths
        self.paths = get_config_paths()
    
    def get_default_structure(self, project_type):
        """Get the default directory structure for a project type"""
        from app.constants import DEFAULT_STRUCTURES
        structure_key = PROJECT_TYPE_TO_STRUCTURE.get(project_type, "Video Editing - Basic")
        
        # If structure_key is not in DEFAULT_STRUCTURES, use a fallback
        if structure_key not in DEFAULT_STRUCTURES:
            # Try different fallback keys based on common values
            if structure_key == "Basic":
                structure_key = "Video Editing - Basic"
            elif structure_key == "Standard":
                structure_key = "Video Editing - Standard"
            else:
                # Default fallback to a structure that definitely exists
                structure_key = "Video Editing - Basic"
        
        # Return the structure or an empty list as last resort
        return DEFAULT_STRUCTURES.get(structure_key, [])
    
    def get_structure(self, structure_name):
        """Get the folder structure for a template."""
        from app.constants import DEFAULT_STRUCTURES
        print(f"DEBUG: get_structure called with structure_name='{structure_name}'")
        
        if not structure_name:
            print("DEBUG: No structure name provided, returning empty structure")
            return []
        
        # Check if it's a built-in structure
        structure_name_lower = structure_name.lower()
        for default_name in DEFAULT_STRUCTURES.keys():
            if structure_name_lower == default_name.lower():
                print(f"DEBUG: Found built-in structure: {default_name}")
                return DEFAULT_STRUCTURES[default_name]
        
        # Try with and without the Template_ prefix, and with spaces replaced by underscores
        structure_names_to_try = [structure_name]
        
        # If the name starts with Template_, try also without it
        if structure_name.startswith('Template_'):
            structure_names_to_try.append(structure_name[9:])  # Remove Template_ prefix
        # If the name doesn't start with Template_, try also with it
        else:
            structure_names_to_try.append(f'Template_{structure_name}')
        
        # Add versions with spaces replaced by underscores
        space_versions = []
        for name in structure_names_to_try:
            if ' ' in name:
                space_versions.append(name.replace(' ', '_'))
            elif '_' in name:
                space_versions.append(name.replace('_', ' '))
        structure_names_to_try.extend(space_versions)
        
        print(f"DEBUG: Trying structure names: {structure_names_to_try}")
        
        # Check custom structures for all variations
        for name_to_try in structure_names_to_try:
            # Check in self.custom_structures first (in-memory cache)
            if name_to_try in self.custom_structures:
                print(f"DEBUG: Found custom structure in memory: {name_to_try}")
                # Return the 'directories' field if it exists, otherwise the whole structure
                if 'directories' in self.custom_structures[name_to_try]:
                    return self.custom_structures[name_to_try]['directories']
                return self.custom_structures[name_to_try]
            
            # Check on disk
            custom_structure_path = os.path.join(self.paths["custom_structures_dir"], f"{name_to_try}.json")
            if os.path.exists(custom_structure_path):
                try:
                    with open(custom_structure_path, 'r') as f:
                        structure_data = json.load(f)
                        print(f"DEBUG: Found custom structure on disk: {name_to_try}")
                        # Return the 'directories' field if it exists, otherwise the whole structure
                        if 'directories' in structure_data:
                            return structure_data['directories']
                        return structure_data
                except Exception as e:
                    print(f"Error loading structure {name_to_try}: {e}")
        
        print(f"DEBUG: Structure not found: {structure_name}")
        return []
    
    def filter_templates(self, search_term=None, category=None):
        """Filter templates based on search term and category"""
        filtered_templates = []
        
        for template in self.templates:
            # Filter by search term if specified
            if search_term and search_term.lower() not in template.get("name", "").lower():
                continue
                
            filtered_templates.append(template)
            
        return filtered_templates
        
    def create_template_directory(self, name, source_dir, description=""):
        """Create a template directory structure from a source directory"""
        # Create readable directory name from template name
        dirname = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        
        # Generate the template directory path
        template_dir = os.path.join(self.paths["templates_dir"], dirname)
        
        # Create the directory if it doesn't exist
        if not os.path.exists(template_dir):
            os.makedirs(template_dir)
        
        # Create the template JSON file
        template_file = os.path.join(template_dir, "template.json")
        
        # Create the template data
        template_data = {
            "name": name,
            "description": description or f"Template based on {os.path.basename(source_dir)}",
            "type": "template",
            "path": source_dir
        }
        
        # Write the template JSON file
        try:
            with open(template_file, 'w') as f:
                json.dump(template_data, f, indent=2)
        except Exception as e:
            print(f"Error creating template directory: {e}")
            return False
            
        return True
    
    def _validate_template(self, template):
        """Validate that a template has all required fields
        
        Args:
            template (dict): Template to validate
            
        Returns:
            bool: True if template is valid, False otherwise
        """
        try:
            # Check if template is a dictionary
            if not isinstance(template, dict):
                print(f"[DEBUG] Template: Invalid template - not a dictionary")
                return False
            
            # Check for required fields
            required_fields = ['name', 'created']
            for field in required_fields:
                if field not in template:
                    print(f"[DEBUG] Template: Invalid template - missing required field '{field}'")
                    return False
                
            # Check that name is a string
            if not isinstance(template['name'], str):
                print(f"[DEBUG] Template: Invalid template - name is not a string")
                return False
            
            # Check that name is not empty
            if not template['name'].strip():
                print(f"[DEBUG] Template: Invalid template - name is empty")
                return False
            
            return True
        except Exception as e:
            print(f"[DEBUG] Template: Error validating template: {e}")
            return False

    def save_template(self, name, file_path, structure_type, description=None):
        """Save a template to the database"""
        # Validate name
        if not name or name.strip() == "" or name.strip() == "Unnamed" or name.strip() == "Unnamed Template":
            print(f"Error: Invalid template name: {name}")
            return False
            
        # Get current timestamp
        current_time = time.time()
        
        # Check if template already exists to determine if this is an update
        existing_template = None
        for template in self.templates:
            if template.get("name") == name:
                existing_template = template
                break
                
        # Prepare template data
        template = {
            "name": name,
            "path": file_path,
            "type": structure_type,
            "description": description or f"Template for {structure_type}",
            "modified": current_time  # Always update modified time
        }
        
        # If it's a new template, set created time
        if not existing_template:
            template["created"] = current_time
        else:
            # Preserve the original creation time
            template["created"] = existing_template.get("created", current_time)
        
        # Determine icon based on structure_type
        if structure_type == "Folder":
            template["icon"] = "📁"
        else:
            template["icon"] = "📄"
            
        # Validate template before saving
        if not self._validate_template(template):
            print(f"Error: Template validation failed for {name}")
            return False
        
        # Save the template to file
        filename = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        file_path = os.path.join(self.paths["templates_dir"], f"{filename}.json")
        
        try:
            with open(file_path, 'w') as f:
                json.dump(template, f, indent=2)
            
            # Update or add to in-memory list
            if existing_template:
                # Update existing template
                for i, t in enumerate(self.templates):
                    if t.get("name") == name:
                        self.templates[i] = template
                        break
            else:
                # Add new template
                self.templates.append(template)
            return True
        except Exception as e:
            print(f"Error saving template: {e}")
            return False
    
    def import_template_file(self, file_path, name=None, structure_type=None):
        """Import a template from a file"""
        # Check if the file exists
        if not os.path.exists(file_path):
            print(f"Error: Template file does not exist: {file_path}")
            return False
            
        # Determine name from file path if not provided
        if not name:
            name = os.path.splitext(os.path.basename(file_path))[0].replace("_", " ")
            
        # Determine structure type from file extension if not provided
        if not structure_type:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext in (".prproj", ".xml"):
                structure_type = "Video Editing"
            elif ext in (".aep", ".aet"):
                structure_type = "Motion Graphics"
            elif ext in (".psd", ".ai", ".indd"):
                structure_type = "Design"
            else:
                structure_type = "Custom"
            
        # Save the template
        return self.save_template(name, file_path, structure_type)
    
    def delete_template(self, template_name):
        """Delete a template by name"""
        if not template_name:
            print(f"[DEBUG] Template: Cannot delete empty template name")
            return False
        
        # Special handling for "Unnamed" templates that may be stuck in the system
        if template_name == "Unnamed" or template_name == "Unnamed Template":
            print(f"[DEBUG] Template: Removing unnamed template: {template_name}")
            # Force removal from in-memory list without trying to delete files
            self.templates = [t for t in self.templates if t.get('name') != template_name]
            
            # Remove from any folders
            for folder_name in self.folders:
                if template_name in self.folders[folder_name]:
                    self.folders[folder_name].remove(template_name)
            
            # Save updated folders
            self.save_folders()
            return True
        
        # Find the template - need to handle both the original name and potentially renamed versions (Template-#)
        template = self.get_template_by_name(template_name)
        
        # If template not found with the exact name, check if it's a renamed version (Template-#)
        if not template and template_name.startswith("Template-"):
            print(f"[DEBUG] Template: Looking for original template for renamed version: {template_name}")
            # Try to find the actual template in memory
            for t in self.templates:
                if t.get('name') == template_name or t.get('display_name') == template_name:
                    template = t
                    break
                
            # Also check directory templates
            if not template:
                for t in self.template_directories:
                    if t.get('name') == template_name or t.get('display_name') == template_name:
                        template = t
                        break
            
            if template:
                print(f"[DEBUG] Template: Found original template: {template.get('name')} for renamed version: {template_name}")
            else:
                print(f"[DEBUG] Template: Original template not found for renamed version: {template_name}")
        
        if not template:
            print(f"[DEBUG] Template: Template not found for deletion: {template_name}")
            return False
        
        # Store the real template name for later use
        real_template_name = template.get('name', template_name)
        print(f"[DEBUG] Template: Deleting template: {real_template_name} (requested as: {template_name})")
        
        try:
            # Handle different template types
            if template.get('type') == 'directory':
                # For directory templates, delete the directory
                template_dir = template.get('path', '')
                if os.path.exists(template_dir) and os.path.isdir(template_dir):
                    print(f"[DEBUG] Template: Deleting directory: {template_dir}")
                    shutil.rmtree(template_dir)
                    
                # Remove from in-memory list
                self.template_directories = [t for t in self.template_directories if t.get('name') != real_template_name]
            else:
                # For file templates, delete the JSON file
                template_filename = real_template_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
                template_path = os.path.join(self.paths["templates_dir"], f"{template_filename}.json")
                
                if os.path.exists(template_path):
                    print(f"[DEBUG] Template: Deleting file: {template_path}")
                    os.remove(template_path)
                    
                # Remove from in-memory list
                self.templates = [t for t in self.templates if t.get('name') != real_template_name]
            
            # Also delete the associated structure file if it exists
            structure_name = f"Template_{real_template_name}"
            structure_filename = structure_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
            structure_path = os.path.join(self.paths["custom_structures_dir"], f"{structure_filename}.json")
            
            if os.path.exists(structure_path):
                print(f"[DEBUG] Template: Deleting associated structure file: {structure_path}")
                os.remove(structure_path)
                
                # Remove from in-memory cache if present
                if structure_name in self.custom_structures:
                    del self.custom_structures[structure_name]
            
            # Remove from any folders - handle both original name and requested name
            names_to_remove = {real_template_name, template_name}
            for folder_name in self.folders:
                for name in names_to_remove:
                    if name in self.folders[folder_name]:
                        print(f"[DEBUG] Template: Removing '{name}' from folder '{folder_name}'")
                        self.folders[folder_name].remove(name)
                
                # Also check for any Template-# versions that might be duplicates
                template_prefix_items = [t for t in self.folders[folder_name] if t.startswith("Template-")]
                for prefix_item in template_prefix_items:
                    # Check if this is a renamed version of our template
                    prefix_template = self.get_template_by_name(prefix_item)
                    if prefix_template and prefix_template.get('name') == real_template_name:
                        print(f"[DEBUG] Template: Removing renamed version '{prefix_item}' from folder '{folder_name}'")
                        self.folders[folder_name].remove(prefix_item)
            
            # Save updated folders
            print(f"[DEBUG] Template: Saving folders after template deletion")
            self.save_folders()
            
            return True
        except Exception as e:
            print(f"[DEBUG] Template: Error deleting template {template_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def delete_template_directory(self, template):
        """Delete a directory-based template"""
        if not template or template.get('type') != 'directory':
            return False
            
        template_path = template.get('path')
        if not template_path or not os.path.isdir(template_path):
            return False
            
        template_name = template.get('name')
        
        try:
            # Delete the template directory
            shutil.rmtree(template_path)
            
            # Remove from in-memory list
            self.template_directories.remove(template)
            
            # Reload template directories to refresh the list
            self.load_template_directories()
            
            return True
        except Exception as e:
            print(f"Error deleting template directory {template_name}: {e}")
            return False
    
    def rename_template(self, old_name, new_name):
        """Rename a template"""
        if old_name == new_name:
            return True
        
        for template in self.templates:
            if template["name"] == old_name:
                # Create a clean filename for both old and new
                old_filename = old_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
                new_filename = new_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
                
                old_path = os.path.join(self.paths["templates_dir"], f"{old_filename}.json")
                new_path = os.path.join(self.paths["templates_dir"], f"{new_filename}.json")
                
                try:
                    # Update the template in memory
                    template["name"] = new_name
                    
                    # Save to new file
                    save_json_file(new_path, template)
                    
                    # Remove old file
                    if os.path.exists(old_path):
                        os.remove(old_path)
                    
                    return True
                except Exception as e:
                    print(f"Error renaming template {old_name} to {new_name}: {e}")
                    return False
        
        return False
    
    def update_template(self, template):
        """Update a template's metadata"""
        if not template or not template.get('name'):
            return False
            
        template_name = template.get('name')
        
        # Create a clean filename
        filename = template_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        
        # Different handling based on template type
        if template.get('type') == 'directory':
            return self.update_directory_template(template)
        else:
            # For file templates, update the JSON file
            template_path = os.path.join(self.paths["templates_dir"], f"{filename}.json")
            
            try:
                save_json_file(template_path, template)
                
                # Update in-memory copy
                for i, t in enumerate(self.templates):
                    if t.get('name') == template_name:
                        self.templates[i] = template
                        break
                
                return True
            except Exception as e:
                print(f"Error updating template {template_name}: {e}")
                return False
    
    def update_directory_template(self, template):
        """Update a directory-based template's metadata"""
        if not template or not template.get('name') or template.get('type') != 'directory':
            return False
            
        template_name = template.get('name')
        template_path = template.get('path', '')
        
        if not template_path or not os.path.isdir(template_path):
            return False
            
        try:
            # Update template.json inside the directory
            template_json_path = os.path.join(template_path, "template.json")
            
            # Create a copy without the 'path' attribute for saving
            template_copy = dict(template)
            if 'path' in template_copy:
                del template_copy['path']
            
            save_json_file(template_json_path, template_copy)
            
            # Update in-memory copy
            for i, t in enumerate(self.template_directories):
                if t.get('name') == template_name:
                    self.template_directories[i] = template
                    break
            
            return True
        except Exception as e:
            print(f"Error updating directory template {template_name}: {e}")
            return False 