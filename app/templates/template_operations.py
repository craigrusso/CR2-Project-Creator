#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
import datetime
import shutil

from app.utils.utils import save_json_file
from app.constants import PROJECT_TYPE_TO_STRUCTURE

class TemplateOperations:
    """
    Operations for managing templates (create, read, update, delete)
    """
    
    def get_default_structure(self, project_type):
        """Get the default directory structure for a project type"""
        from app.constants import DEFAULT_STRUCTURES
        structure_key = PROJECT_TYPE_TO_STRUCTURE.get(project_type, "Basic")
        
        # If structure_key is not in DEFAULT_STRUCTURES, use "Basic" as fallback
        if structure_key not in DEFAULT_STRUCTURES:
            structure_key = "Basic"
        
        return DEFAULT_STRUCTURES[structure_key]
    
    def get_structure(self, structure_name):
        """Get the folder structure for a template."""
        from app.constants import DEFAULT_STRUCTURES
        print(f"DEBUG: get_structure called with structure_name='{structure_name}'")
        
        # Check if it's a built-in structure
        if structure_name.lower() in DEFAULT_STRUCTURES:
            print(f"DEBUG: Found built-in structure: {structure_name}")
            return DEFAULT_STRUCTURES[structure_name.lower()]
        
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
            custom_structure_path = os.path.join(self.paths["custom_structures_dir"], f"{name_to_try}.json")
            if os.path.exists(custom_structure_path):
                try:
                    with open(custom_structure_path, 'r') as f:
                        structure = json.load(f)
                        print(f"DEBUG: Found custom structure: {name_to_try}")
                        return structure
                except Exception as e:
                    print(f"Error loading structure {name_to_try}: {e}")
        
        print(f"DEBUG: Structure not found: {structure_name}")
        return []
    
    def filter_templates(self, search_term=None, category=None):
        """Filter templates based on search term and category"""
        all_templates = self.get_all_templates()
        filtered = []
        
        for template in all_templates:
            # Filter by category if specified
            if category and category != "All" and template.get("category") != category:
                continue
            
            # Filter by search term if specified
            if search_term:
                search_term = search_term.lower()
                name = template.get("name", "").lower()
                desc = template.get("description", "").lower()
                
                if search_term not in name and search_term not in desc:
                    continue
            
            filtered.append(template)
        
        return filtered
        
    def create_template_directory(self, name, category, source_dir, description=""):
        """Create a template directory from a source directory"""
        if not name or not source_dir or not os.path.isdir(source_dir):
            return False, "Invalid template name or source directory"
        
        # Create a clean directory name
        dir_name = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        template_dir = os.path.join(self.paths["template_directories_dir"], dir_name)
        
        # Check if template directory already exists
        if os.path.exists(template_dir):
            return False, f"Template '{name}' already exists"
        
        try:
            # Create template directory
            os.makedirs(template_dir, exist_ok=True)
            
            # Copy contents from source directory
            for item in os.listdir(source_dir):
                source_item = os.path.join(source_dir, item)
                target_item = os.path.join(template_dir, item)
                
                if os.path.isdir(source_item):
                    shutil.copytree(source_item, target_item)
                else:
                    shutil.copy2(source_item, target_item)
            
            # Create template.json
            template_info = {
                "name": name,
                "category": category,
                "description": description,
                "created": datetime.datetime.now().isoformat(),
                "type": "directory"
            }
            
            with open(os.path.join(template_dir, "template.json"), 'w') as f:
                json.dump(template_info, f, indent=2)
            
            # Update in-memory templates
            template_info["path"] = template_dir
            self.template_directories.append(template_info)
            
            return True, template_dir
            
        except Exception as e:
            error_msg = f"Failed to create template directory: {str(e)}"
            print(error_msg)
            return False, error_msg
    
    def save_template(self, name, category, file_path, structure_type, description=None):
        """Save a template"""
        if not name or not category:
            return False
        
        # Create template info
        template = {
            "name": name,
            "category": category,
            "file": file_path if file_path else "",
            "type": structure_type,
            "description": description or f"{category} template",
            "structure_type": structure_type,
            "created": datetime.datetime.now().isoformat()
        }
        
        # Determine icon based on category
        icons = {
            "Video Editing": "🎬",
            "Motion Graphics": "✨",
            "Design": "📷",
            "Audio": "🎧",
            "Custom": "📂"
        }
        template["icon"] = icons.get(category, "📂")
        
        # Save to file
        filename = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        file_path = os.path.join(self.paths["templates_dir"], f"{filename}.json")
        
        success = save_json_file(file_path, template)
        if success:
            # Update in-memory cache
            self.templates.append(template)
        
        return success
    
    def import_template_file(self, file_path, name=None, category=None):
        """Import a file as a template"""
        if not file_path or not os.path.exists(file_path):
            return False
        
        # Get filename as default name if not provided
        if not name:
            name = os.path.basename(file_path)
            name = os.path.splitext(name)[0]  # Remove extension
        
        # Determine project type from file extension
        _, ext = os.path.splitext(file_path)
        if not category:
            if ext.lower() in ['.prproj']:
                category = "Video Editing"
                structure_type = "Video Editing"
            elif ext.lower() in ['.aep', '.aepx']:
                category = "Motion Graphics"
                structure_type = "Motion Graphics"
            elif ext.lower() in ['.psd', '.ai']:
                category = "Design"
                structure_type = "Design"
            else:
                category = "Custom"
                structure_type = "Standard"
        else:
            structure_type = category
        
        # Save template
        return self.save_template(name, category, file_path, structure_type)
    
    def delete_template(self, template_name):
        """Delete a template by name"""
        if not template_name:
            return False
        
        # Find the template
        template = self.get_template_by_name(template_name)
        if not template:
            print(f"Template not found: {template_name}")
            return False
        
        try:
            # Handle different template types
            if template.get('type') == 'directory':
                # For directory templates, delete the directory
                template_dir = template.get('path', '')
                if os.path.exists(template_dir) and os.path.isdir(template_dir):
                    shutil.rmtree(template_dir)
                    
                # Remove from in-memory list
                self.template_directories = [t for t in self.template_directories if t.get('name') != template_name]
            else:
                # For file templates, delete the JSON file
                template_filename = template_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
                template_path = os.path.join(self.paths["templates_dir"], f"{template_filename}.json")
                
                if os.path.exists(template_path):
                    os.remove(template_path)
                    
                # Remove from in-memory list
                self.templates = [t for t in self.templates if t.get('name') != template_name]
            
            # Also delete the associated structure file if it exists
            structure_name = f"Template_{template_name}"
            structure_filename = structure_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
            structure_path = os.path.join(self.paths["custom_structures_dir"], f"{structure_filename}.json")
            
            if os.path.exists(structure_path):
                print(f"DEBUG: Deleting associated structure file: {structure_path}")
                os.remove(structure_path)
                
                # Remove from in-memory cache if present
                if structure_name in self.custom_structures:
                    del self.custom_structures[structure_name]
            
            # Remove from any folders
            for folder_name in self.folders:
                if template_name in self.folders[folder_name]:
                    self.folders[folder_name].remove(template_name)
                    
            # Save updated folders
            self.save_folders()
            
            return True
        except Exception as e:
            print(f"Error deleting template {template_name}: {e}")
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