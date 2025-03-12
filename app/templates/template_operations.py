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
        # Prevent empty, "Unnamed", or "Unnamed Template" templates from being created
        if not name or not category or name.strip() == "" or name.strip() == "Unnamed" or name.strip() == "Unnamed Template":
            print(f"Rejecting invalid template name: '{name}'")
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