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
        
    def sanitize_filename(self, filename):
        """
        Sanitize a filename for cross-platform compatibility.
        Replaces unsafe characters with safe ones.
        """
        # Replace characters not allowed in filenames across platforms
        unsafe_chars = [":", "/", "\\", "?", "*", "\"", "<", ">", "|", "'"]
        safe_filename = filename
        for char in unsafe_chars:
            safe_filename = safe_filename.replace(char, "-")
        
        # Replace spaces with underscores
        safe_filename = safe_filename.replace(" ", "_")
        
        # Trim to a reasonable length
        if len(safe_filename) > 180:
            # Keep extension if any
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:175] + ext
        
        return safe_filename

    def create_template_directory(self, name, source_dir, description=""):
        """Create a template directory structure from a source directory"""
        # Create readable directory name from template name
        dirname = self.sanitize_filename(name)
        
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
        """Validate template data"""
        # Check for required fields
        required_fields = ["name", "path", "type"]
        
        for field in required_fields:
            if field not in template:
                print(f"Error: Missing required field '{field}' in template")
                return False
                
        # Check that name and path are not empty
        if not template.get("name") or not template.get("path"):
            print("Error: Template name or path cannot be empty")
            return False
            
        # Check if structure is present and log its status
        if "structure" in template:
            print(f"INFO: Template '{template['name']}' has a folder structure attached")
            structure_count = self._count_structure_items(template["structure"])
            print(f"INFO: Structure contains {structure_count} items")
        else:
            print(f"INFO: Template '{template['name']}' has no folder structure attached")
            
        return True
        
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
        
    def save_template(self, name, file_path, structure_type, description=None):
        """Save a template to the database"""
        # Validate name
        if not name or name.strip() == "" or name.strip() == "Unnamed" or name.strip() == "Unnamed Template":
            print(f"Error: Invalid template name: {name}")
            return False
            
        # Print debug info about file_path
        print(f"DEBUG: save_template called with path='{file_path}', type={type(file_path).__name__}")
        
        # Check if file path is empty or None
        if not file_path:
            print("WARNING: Template file_path is empty, using current directory as fallback")
            file_path = os.getcwd()
        
        # Get current timestamp
        current_time = time.time()
        
        # Check if template already exists to determine if this is an update
        existing_template = None
        for template in self.templates:
            if template.get("name") == name:
                existing_template = template
                break
                
        # Generate a safe filename from the name
        filename = self.sanitize_filename(name)
        
        # Prepare directory for template files
        template_cache_dir = os.path.join(self.paths["templates_dir"], "cache", filename)
        os.makedirs(template_cache_dir, exist_ok=True)
        
        # Prepare template data
        template = {
            "name": name,
            "path": file_path,  # Store original path for reference
            "cached_path": template_cache_dir,  # Add cached path
            "type": structure_type,
            "description": description or f"Template for {structure_type}",
            "modified": current_time  # Always update modified time
        }
        
        # Copy creation timestamp from existing template if available, otherwise use current time
        if existing_template and "created" in existing_template:
            template["created"] = existing_template["created"]
        else:
            template["created"] = current_time
            
        # Copy other fields from existing template
        if existing_template:
            for key, value in existing_template.items():
                if key not in template and key not in ["path", "cached_path", "type", "description", "modified"]:
                    template[key] = value
            
        # Get folder structure
        folder_structure = None
        if hasattr(self, 'get_folder_structure'):
            folder_structure = self.get_folder_structure(file_path)
        
        # Check if this template has been saved before
        is_update = existing_template is not None
            
        # Copy the file(s) to the cache directory - ONLY if explicitly flagged for caching
        # We won't cache files by default anymore when saving templates
        if existing_template and existing_template.get("should_cache_files", False):
            print(f"DEBUG: Template is explicitly flagged for file caching")
            try:
                self._cache_template_files(file_path, template_cache_dir)
            except Exception as e:
                print(f"Warning: Failed to cache template files: {e}")
        else:
            print(f"DEBUG: Skipping automatic file caching for template '{name}'")
            
        # Save the template to file
        template_file = os.path.join(self.paths["templates_dir"], f"{filename}.json")
        
        try:
            with open(template_file, 'w') as f:
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
            
            # Save the structure as a custom structure if needed
            if folder_structure and hasattr(self, 'save_custom_structure'):
                structure_file_name = f"Template_{filename}"
                self.save_custom_structure(structure_file_name, folder_structure)
                print(f"Saved folder structure to custom structure: {structure_file_name}")
                
            return True
        except Exception as e:
            print(f"Error saving template: {e}")
            return False
    
    def _cache_template_files(self, source_path, cache_dir):
        """
        Cache template files in the application's storage location
        
        Args:
            source_path: Original path to the file or directory
            cache_dir: Cache directory where files should be copied
        """
        print(f"DEBUG: _cache_template_files called with source_path={source_path}, cache_dir={cache_dir}")
        
        if not os.path.exists(source_path):
            print(f"WARNING: Source path does not exist: {source_path}")
            return
            
        # Clean the cache directory first
        try:
            if os.path.exists(cache_dir):
                print(f"DEBUG: Cleaning cache directory: {cache_dir}")
                for item in os.listdir(cache_dir):
                    item_path = os.path.join(cache_dir, item)
                    if os.path.isfile(item_path):
                        print(f"DEBUG: Removing file from cache: {item_path}")
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        print(f"DEBUG: Removing directory from cache: {item_path}")
                        shutil.rmtree(item_path)
            else:
                print(f"DEBUG: Cache directory does not exist, will be created: {cache_dir}")
                os.makedirs(cache_dir, exist_ok=True)
        except Exception as e:
            print(f"WARNING: Failed to clean cache directory: {e}")
        
        # Copy all files to cache directory, not just those with template variables
        try:
            if os.path.isfile(source_path):
                # Cache all files, not just those with template variables
                filename = os.path.basename(source_path)
                print(f"DEBUG: Caching file: {filename}")
                cached_file_path = os.path.join(cache_dir, filename)
                shutil.copy2(source_path, cached_file_path)
                print(f"DEBUG: Copied file to cache: {cached_file_path}")
                
                # Verify file was copied correctly
                if os.path.exists(cached_file_path):
                    source_size = os.path.getsize(source_path)
                    cached_size = os.path.getsize(cached_file_path)
                    print(f"DEBUG: Cached file verified: {cached_file_path} (Size: {source_size} -> {cached_size})")
                else:
                    print(f"ERROR: Failed to cache file: {cached_file_path} does not exist after copy")
            elif os.path.isdir(source_path):
                print(f"DEBUG: Source is a directory: {source_path}")
                # For directories, process all files
                for root, dirs, files in os.walk(source_path):
                    # Create corresponding directories in cache
                    rel_path = os.path.relpath(root, source_path)
                    if rel_path != '.':
                        cache_subdir = os.path.join(cache_dir, rel_path)
                        print(f"DEBUG: Creating cache subdirectory: {cache_subdir}")
                        os.makedirs(cache_subdir, exist_ok=True)
                    
                    # Copy all files, not just those with template variables
                    for file in files:
                        src_file = os.path.join(root, file)
                        dst_dir = cache_dir if rel_path == '.' else os.path.join(cache_dir, rel_path)
                        cached_file_path = os.path.join(dst_dir, file)
                        
                        print(f"DEBUG: Caching file: {src_file} to {cached_file_path}")
                        shutil.copy2(src_file, cached_file_path)
                        
                        # Verify file was copied correctly
                        if os.path.exists(cached_file_path):
                            print(f"DEBUG: Successfully cached file: {cached_file_path}")
                        else:
                            print(f"ERROR: Failed to cache file: {cached_file_path}")
        except Exception as e:
            print(f"ERROR: Failed to cache template files: {e}")
            import traceback
            traceback.print_exc()
    
    def _contains_template_variables(self, file_path, filename):
        """
        Check if a file contains template variables like {{PROJECT_NAME}}
        
        Args:
            file_path: Path to the file
            filename: Name of the file
            
        Returns:
            bool: True if file contains template variables, False otherwise
        """
        print(f"DEBUG: Checking for template variables in file: {filename}")
        
        # Check if filename contains template variables
        if "{{" in filename and "}}" in filename:
            print(f"DEBUG: Filename contains template variables: {filename}")
            return True
            
        # Check if it's a text file that might contain template variables
        if self._is_text_file(file_path):
            print(f"DEBUG: File appears to be a text file, checking content: {filename}")
            try:
                # Only check the first portion of the file (for large files)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(10240)  # Read first 10KB
                    has_variables = "{{" in content and "}}" in content
                    
                    if has_variables:
                        print(f"DEBUG: File content contains template variables: {filename}")
                        
                        # Find and log the template variables for debugging
                        import re
                        template_vars = re.findall(r"{{(.*?)}}", content)
                        if template_vars:
                            print(f"DEBUG: Found template variables: {', '.join(template_vars)}")
                    else:
                        print(f"DEBUG: File content does not contain template variables: {filename}")
                        
                    return has_variables
            except Exception as e:
                print(f"ERROR: Failed to check file content for template variables: {e}")
                
        print(f"DEBUG: File is not a text file or doesn't contain template variables: {filename}")
        return False
        
    def _is_text_file(self, file_path):
        """Check if a file is a text file"""
        text_extensions = ['.txt', '.html', '.css', '.js', '.json', '.xml', '.md', '.csv', '.yml', '.yaml', 
                          '.ini', '.cfg', '.conf', '.py', '.sh', '.bat', '.ps1', '.php', '.rb', '.java', 
                          '.c', '.cpp', '.h', '.cs', '.swift', '.go', '.ts', '.jsx', '.tsx']
        
        # Get the file extension                  
        _, ext = os.path.splitext(file_path.lower())
        
        print(f"DEBUG: Checking if file is text file: {file_path}, extension: {ext}")
        
        # Known text extensions
        if ext in text_extensions:
            print(f"DEBUG: File has a known text extension: {ext}")
            return True
            
        # Try to detect text files without extensions
        if os.path.exists(file_path):
            print(f"DEBUG: File doesn't have a known text extension, testing content...")
            try:
                # Try to open and read a few bytes
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    sample = f.read(1024)
                    # If we can read it as text, it's likely a text file
                    is_text = '\0' not in sample  # Binary files often contain null bytes
                    print(f"DEBUG: Content-based detection result: {'text file' if is_text else 'binary file'}")
                    return is_text
            except Exception as e:
                print(f"DEBUG: Failed to read file for text detection: {e}")
                
        print(f"DEBUG: File is not a text file: {file_path}")
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
        # Find the template by name
        real_template_name = template_name
        template = None
        
        # First check normal templates
        for t in self.templates:
            if t.get('name') == template_name:
                template = t
                break
        
        # If not found, check directory templates
        if not template:
            for t in self.template_directories:
                if t.get('name') == template_name:
                    template = t
                    break
                
        # If we still don't have a template, try the raw template name
        if not template:
            print(f"[DEBUG] Template: Could not find template with name {template_name}")
            return False
        
        print(f"[DEBUG] Template: Deleting template {real_template_name}")
        
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
                template_filename = self.sanitize_filename(real_template_name)
                template_path = os.path.join(self.paths["templates_dir"], f"{template_filename}.json")
                
                if os.path.exists(template_path):
                    print(f"[DEBUG] Template: Deleting file: {template_path}")
                    os.remove(template_path)
                    
                # Remove from in-memory list
                self.templates = [t for t in self.templates if t.get('name') != real_template_name]
            
            # Also delete the associated structure file if it exists
            structure_name = f"Template_{real_template_name}"
            structure_filename = self.sanitize_filename(structure_name)
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
                old_filename = self.sanitize_filename(old_name)
                new_filename = self.sanitize_filename(new_name)
                
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
        filename = self.sanitize_filename(template_name)
        
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
    
    def save_custom_structure(self, name, structure):
        """Save a custom folder structure"""
        if not name or not structure:
            print(f"ERROR: Cannot save custom structure. Invalid name or structure.")
            return False
            
        print(f"INFO: Saving custom structure '{name}'")
        
        # Initialize custom structures if needed
        if not hasattr(self, 'custom_structures'):
            self.custom_structures = []
            
        # Check if structure exists
        existing_structure = None
        for s in self.custom_structures:
            if s.get("name") == name:
                existing_structure = s
                break
                
        # Create or update structure
        structure_data = {
            "name": name,
            "structure": structure,
            "modified": time.time()
        }
        
        if not existing_structure:
            structure_data["created"] = time.time()
            self.custom_structures.append(structure_data)
            print(f"INFO: Added new custom structure '{name}'")
        else:
            # Update existing structure
            structure_data["created"] = existing_structure.get("created", time.time())
            for i, s in enumerate(self.custom_structures):
                if s.get("name") == name:
                    self.custom_structures[i] = structure_data
                    print(f"INFO: Updated existing custom structure '{name}'")
                    break
        
        # Save to disk
        try:
            os.makedirs(self.paths["custom_structures_dir"], exist_ok=True)
            file_path = os.path.join(self.paths["custom_structures_dir"], f"{name.replace(' ', '_')}.json")
            
            with open(file_path, 'w') as f:
                json.dump(structure_data, f, indent=2)
                
            print(f"INFO: Successfully saved custom structure '{name}' to {file_path}")
            return True
        except Exception as e:
            print(f"ERROR: Failed to save custom structure '{name}': {e}")
            return False
    
    def get_custom_structure(self, name):
        """
        Get a custom structure by name
        
        Args:
            name (str): Name of the custom structure
            
        Returns:
            dict: The structure data, or None if not found
        """
        if not hasattr(self, 'custom_structures') or not self.custom_structures:
            self.load_custom_structures()
            
        # Find the structure in the custom structures list
        for structure in self.custom_structures:
            if structure.get("name") == name:
                print(f"INFO: Found custom structure '{name}'")
                return structure.get("structure")
                
        print(f"INFO: Custom structure '{name}' not found")
        return None
        
    def load_custom_structures(self):
        """Load custom structures from disk"""
        if not hasattr(self, 'custom_structures'):
            self.custom_structures = []
            
        if not os.path.exists(self.paths["custom_structures_dir"]):
            os.makedirs(self.paths["custom_structures_dir"], exist_ok=True)
            return
            
        # Load all structure files
        for filename in os.listdir(self.paths["custom_structures_dir"]):
            if filename.endswith(".json"):
                filepath = os.path.join(self.paths["custom_structures_dir"], filename)
                try:
                    with open(filepath, 'r') as f:
                        structure_data = json.load(f)
                        
                    # Check if this structure already exists
                    exists = False
                    for i, s in enumerate(self.custom_structures):
                        if s.get("name") == structure_data.get("name"):
                            self.custom_structures[i] = structure_data
                            exists = True
                            break
                            
                    if not exists:
                        self.custom_structures.append(structure_data)
                        
                    print(f"INFO: Loaded custom structure '{structure_data.get('name')}' from {filename}")
                except Exception as e:
                    print(f"ERROR: Failed to load custom structure from {filename}: {e}")
                    
        print(f"INFO: Loaded {len(self.custom_structures)} custom structures")
        return self.custom_structures
    
    def delete_custom_structure(self, name):
        """Delete a custom folder structure"""
        if name not in self.custom_structures:
            return False
        
        # Create a clean filename
        filename = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        file_path = os.path.join(self.paths["custom_structures_dir"], f"{filename}.json")
        
        try:
            # Delete the structure JSON file
            os.remove(file_path)
            
            # Delete all cached files associated with this structure
            cache_dir = os.path.join(self.paths["templates_dir"], "cache", filename)
            if os.path.exists(cache_dir):
                print(f"DEBUG: Deleting cache directory for structure '{name}': {cache_dir}")
                shutil.rmtree(cache_dir)
                print(f"DEBUG: Successfully deleted cache directory for structure '{name}'")
            
            # Remove from in-memory cache
            del self.custom_structures[name]
            
            return True
        except Exception as e:
            print(f"Error deleting structure {name}: {e}")
            return False 