#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import json
import datetime
import shutil
import time
import hashlib
import re
import uuid

from app.utils.utils import save_json_file, get_config_paths, load_json_file
from app.utils.file_cache_manager import FileCacheManager

class TemplateOperations:
    """
    Core operations for managing template data (loading, saving, structures, files)
    Intended to be inherited by TemplateManagerCore.
    """
    
    def __init__(self):
        """Initialize template operations"""
        self.paths = get_config_paths()
        
        # Initialize templates list
        self.templates = []
        
        # Add flag for auto-creating structure files (default to false)
        self.auto_create_structure = False
        
        # Try to load templates if needed
        try:
            self.load_templates()
        except Exception as e:
            print(f"Warning: Could not load templates: {e}")
        
        self.preferences = getattr(self, 'preferences', {})
        
        # Ensure we have a valid template cache directory
        if 'templates_cache_dir' not in self.paths or not self.paths.get('templates_cache_dir'):
            try:
                # Try to get cache location from preferences first
                from app.utils.cache_preferences import CachePreferences
                import os  # Import os module here
                cache_prefs = CachePreferences()
                self.paths['templates_cache_dir'] = cache_prefs.get_cache_location()
                print(f"DEBUG: Set templates_cache_dir from cache preferences: {self.paths['templates_cache_dir']}")
            except Exception as e:
                print(f"WARNING: Failed to get cache location from preferences: {e}")
                # Fallback to a default location in user's home directory
                import os  # Import os module here
                default_cache_dir = os.path.join(os.path.expanduser("~"), ".echelon", "template_cache")
                self.paths['templates_cache_dir'] = default_cache_dir
                print(f"DEBUG: Set templates_cache_dir to default location: {default_cache_dir}")
            
            # Ensure the cache directory exists
            os.makedirs(self.paths['templates_cache_dir'], exist_ok=True)
        
        # Initialize file cache manager
        cache_dir = self.paths.get('templates_cache_dir')
        if cache_dir:
            self.file_cache_manager = FileCacheManager(cache_dir)
        else:
            print("Warning: No template cache directory specified in paths")
            self.file_cache_manager = None
    
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
        
        print(f"DEBUG: get_structure called with structure_name='{structure_name}'")
        
        if not structure_name:
            print("DEBUG: No structure name provided, returning empty structure")
            return []
        
      
        
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
    
    def get_template(self, template_name):
        """Get a template by name"""
        if not template_name:
            print(f"DEBUG: get_template called with empty name")
            return None
            
        # Handle dictionary format (used by TemplateManagerCore)
        if isinstance(self.templates, dict):
            # Try exact match first
            template = self.templates.get(template_name)
            if template:
                return template
            # Try case-insensitive match
            for key, value in self.templates.items():
                if key.lower() == template_name.lower():
                    return value
            # If not found in dict, proceed to check list format (shouldn't happen with TemplateManagerCore)
            # but keep as fallback

        # Handle list format
        elif isinstance(self.templates, list):
            # Try to find the template by exact name
            for template in self.templates:
                # Make sure template is a dict before using get()
                if not isinstance(template, dict):
                    print(f"WARNING: Template item is not a dict, it's a {type(template)}: {template}")
                    continue
                    
                if template.get("name") == template_name:
                    return template
                    
            # If not found with exact match, try case-insensitive match
            for template in self.templates:
                # Make sure template is a dict before using get()
                if not isinstance(template, dict):
                    continue
                    
                if template.get("name", "").lower() == template_name.lower():
                    return template
        else:
            print(f"WARNING: self.templates is neither a list nor a dict ({type(self.templates)}), cannot get template.")
            return None
            
        print(f"DEBUG: Template not found: {template_name}")
        return None
        
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
        
    def save_folders(self):
        """Save template folders to disk"""
        # This is a dummy implementation to avoid errors when called
        # The actual folder saving is implemented in the TemplateManager class
        print("[DEBUG] TemplateOperations.save_folders called - this is a stub implementation")
        
        # If we have a folders attribute, try to save it
        if hasattr(self, 'folders') and self.folders:
            try:
                folders_path = os.path.join(self.paths["templates_dir"], "folders.json")
                with open(folders_path, 'w') as f:
                    json.dump(self.folders, f, indent=2)
                print(f"[DEBUG] Saved {len(self.folders)} folders to {folders_path}")
                return True
            except Exception as e:
                print(f"[ERROR] Failed to save folders: {e}")
                return False
        
        return False
        
    def save_template(self, template_name, structure, category=None, description="", tags=None, template_type="Standard", original_name=None):
        """Saves a template JSON file with structure, metadata, and derived file info."""
        print(f"DEBUG: Starting save_template for '{template_name}'")
        
        if tags is None:
            tags = []
            
        # Ensure structure is not None
        if structure is None:
            print("ERROR: Structure cannot be None when saving a template.")
            return False
            
        # Derive files_array from the final structure
        print(f"DEBUG: Deriving files_array from final structure for '{template_name}'")
        files_array = [] # Initialize an empty list
        try:
            # Call the correct method, passing the list to populate
            self._extract_files_from_structure(structure, files_array)
            print(f"DEBUG: Derived {len(files_array)} files from structure")
        except Exception as e:
            print(f"ERROR deriving files from structure: {e}")
            import traceback
            traceback.print_exc()
            # Decide if we should proceed with an empty files array or fail
            # For now, let's proceed but log the error
            files_array = [] 

        # Prepare template data
        timestamp = time.time()
        template_data = {
            "name": template_name,
            "structure_name": f"Template_{template_name.replace(' ', '_')}", # Assume structure name matches template name
            "structure": structure, 
            "category": category or "",
            "description": description or "",
            "created": timestamp, 
            "modified": timestamp,
            "tags": tags or [],
            "files": files_array, # Use derived files_array
            "type": template_type or "Standard" # Ensure type is set
        }

        # Sanitize template name for filename
        sanitized_name = self.sanitize_filename(template_name)
        file_path = os.path.join(self.paths["templates_dir"], f"{sanitized_name}.json")
        template_data['file_path'] = file_path # Store the intended file path
        
        # Check if this is a rename operation
        if original_name and original_name != template_name:
            original_sanitized_name = self.sanitize_filename(original_name)
            original_file_path = os.path.join(self.paths["templates_dir"], f"{original_sanitized_name}.json")
            # Preserve creation time if renaming
            if os.path.exists(original_file_path):
                try:
                    original_data = load_json_file(original_file_path)
                    if original_data and 'created' in original_data:
                        template_data['created'] = original_data['created']
                        print(f"DEBUG: Preserved creation time from original template '{original_name}'")
                except Exception as e:
                    print(f"WARN: Could not read original template file '{original_file_path}' to preserve creation time: {e}")
            # Delete the old file
            if os.path.exists(original_file_path):
                try:
                    os.remove(original_file_path)
                    print(f"DEBUG: Removed old template file due to rename: {original_file_path}")
                except OSError as e:
                    print(f"ERROR: Could not remove old template file '{original_file_path}': {e}")
                    # Decide if we should proceed or return False. Proceeding might leave orphans.
                    # For now, let's proceed but log the error.
            # Also delete the old cache directory if it exists
            if self.file_cache_manager and hasattr(self.file_cache_manager, 'cache_dir'):
                old_template_cache_path = os.path.join(self.file_cache_manager.cache_dir, original_sanitized_name)
                if os.path.isdir(old_template_cache_path):
                    try:
                        shutil.rmtree(old_template_cache_path)
                        print(f"DEBUG: Removed old template cache directory: {old_template_cache_path}")
                    except Exception as e:
                        print(f"ERROR: Failed to remove old template cache directory '{old_template_cache_path}': {e}")
                else:
                    print(f"DEBUG: Old template cache directory not found, skipping removal: {old_template_cache_path}")
            elif not self.file_cache_manager:
                 print("WARN: File cache manager not available, cannot clear old cache.")
        else:
            # If not renaming, but the file exists, preserve creation time
            if os.path.exists(file_path):
                try:
                    existing_data = load_json_file(file_path)
                    if existing_data and 'created' in existing_data:
                        template_data['created'] = existing_data['created']
                except Exception as e:
                    print(f"WARN: Could not read existing template file '{file_path}' to preserve creation time: {e}")

        # Cache any binary files associated with the template
        if self.file_cache_manager:
            print(f"DEBUG: Caching {len(files_array)} files for template '{sanitized_name}'")
            # Iterate through derived files and cache each one individually
            for file_info in files_array:
                original_path = file_info.get('original_path')
                folder_path = file_info.get('folder', '') # Relative folder within template
                
                if original_path and os.path.exists(original_path):
                    try:
                        # Call cache_file for each file
                        cached_path = self.file_cache_manager.cache_file(
                            file_path=original_path,
                            template_name=sanitized_name, # Use the sanitized template name for the cache folder
                            folder_path=folder_path # Pass the relative folder path
                            # Optional: Add rename_flag or file_metadata if needed based on file_info
                        )
                        # if cached_path:
                        #     print(f"DEBUG: Successfully cached '{original_path}' to '{cached_path}'")
                        # else:
                        #     print(f"WARN: Failed to cache '{original_path}'")
                    except Exception as e:
                        print(f"ERROR during caching file '{original_path}': {e}")
                        import traceback
                        traceback.print_exc()
                elif not original_path:
                     print(f"WARN: Skipping cache for file entry with no original_path: {file_info.get('file_name')}")
                else: # original_path exists but file doesn't
                     print(f"WARN: Skipping cache, source file not found: {original_path}")
        
        # Save the template JSON file
        try:
            save_json_file(file_path, template_data)
            print(f"DEBUG: Template saved successfully to {file_path}")
        except Exception as e:
            print(f"ERROR: Failed to save template file '{file_path}': {e}")
            return False

        # ----- Update In-Memory Cache ----- 
        # Update the in-memory cache (self.templates is a list of dicts)
        updated = False
        if original_name and original_name != template_name:  # Handle rename
            # Find and remove the old template entry by original name
            original_found = False
            new_templates_list = []
            for t in self.templates:
                if isinstance(t, dict) and t.get('name') == original_name:
                    original_found = True # Mark as found, but don't add to new list
                else:
                    new_templates_list.append(t) 
            self.templates = new_templates_list
            
            if original_found:
                 print(f"DEBUG: Removed old template '{original_name}' from memory.")
            else:
                print(f"WARN: Could not find original template '{original_name}' in memory to remove during rename.")
                
            # Add the new template data
            self.templates.append(template_data)
            updated = True
            print(f"DEBUG: Appended renamed template '{template_name}' to memory.")

        else: # Handle update or new template
            index_to_update = -1
            for i, t in enumerate(self.templates):
                if isinstance(t, dict) and t.get('name') == template_name:
                    index_to_update = i
                    break
            
            if index_to_update != -1:
                # Update existing template in place
                self.templates[index_to_update] = template_data
                updated = True
                print(f"DEBUG: Updated template in memory: '{template_name}'")
            else:
                # Append new template if not found
                self.templates.append(template_data)
                updated = True
                print(f"DEBUG: Appended new template to memory: '{template_name}'")

        if not updated:
             # This case should ideally not be reached with the logic above
             print(f"WARN: Template '{template_name}' was not updated or added in memory list during save. State might be inconsistent.")
        # ----- End In-Memory Cache Update -----
            
        # Optionally trigger a signal or callback if needed for UI updates
        # We should emit a signal *after* the in-memory list is updated.
        # Example:
        # if hasattr(self, 'templates_updated_signal') and callable(getattr(self, 'templates_updated_signal', None)):
        #     # Check if the signal exists and is callable (like a QSignal) 
        #     try:
        #         self.templates_updated_signal.emit() # Assuming it takes no arguments
        #         print(f"DEBUG: Emitted templates_updated_signal after saving '{template_name}'")
        #     except Exception as e:
        #         print(f"WARN: Failed to emit templates_updated_signal: {e}")
        # elif hasattr(self, 'parent_gallery') and hasattr(self.parent_gallery, 'populate_gallery'):
        #     print("DEBUG: Calling parent gallery populate_gallery directly")
        #     self.parent_gallery.populate_gallery() # Example of direct call if signal not available

        # --- Reloading vs Direct Update --- 
        # The direct update logic above *should* keep the list in sync.
        # Reloading (self.load_templates()) is safer as it reads fresh from disk,
        # but less efficient. Let's stick with the direct update for now and test.
        # If inconsistencies appear, uncommenting self.load_templates() is the fallback.
        # print(f"DEBUG: Reloading templates after save to ensure consistency.")
        # self.load_templates() 
        # --- End Reloading Section ---
            
        print(f"✅ Successfully saved template \'{template_name}\'")
        return True
    
    def _extract_files_from_structure(self, structure, files_array, parent_path=""):
        """
        Recursively extract file items from a structure and add them to the files array
        
        Args:
            structure: The structure to extract files from
            files_array: Array to append the files to
            parent_path: Parent path for nested items
        """
        if not structure:
            return
            
        # Print debug information
        print(f"DEBUG: Extracting files from structure at folder '{parent_path}'")
        print(f"DEBUG: Structure at this level has {len(structure)} items")
        
        # First, check files_to_cache directly if at the root level
        if parent_path == "" and hasattr(self, 'editor') and hasattr(self.editor, 'files_to_cache'):
            files_to_cache = self.editor.files_to_cache
            print(f"DEBUG: Root level - checking editor's files_to_cache ({len(files_to_cache)} items)")
            
            # Debug: print all keys and values
            for key, val in files_to_cache.items():
                print(f"DEBUG: files_to_cache[{key}] = {val}")
            
            # Process each file in files_to_cache
            for rel_path, file_data in files_to_cache.items():
                if isinstance(file_data, dict) and 'original_path' in file_data and file_data['original_path']:
                    original_path = file_data['original_path']
                    if os.path.exists(original_path):
                        file_name = os.path.basename(original_path)
                        
                        # Determine folder path
                        folder = ""
                        if 'relative_path' in file_data:
                            folder = file_data['relative_path'] + '/'
                        elif '/' in rel_path:
                            folder = os.path.dirname(rel_path) + '/'
                        
                        print(f"DEBUG: Adding file from editor's files_to_cache: {file_name} in folder {folder}")
                        
                        # Create file info
                        file_info = {
                            'file_name': file_name,
                            'folder': folder,
                            'original_path': original_path,
                            'file_type': self._guess_file_type(file_name),
                            'size': os.path.getsize(original_path),
                            'is_binary': file_data.get('is_binary', False)
                        }
                        
                        # Add rename flag if filename contains project name variable
                        if '${PROJECT_NAME}' in file_name:
                            file_info['rename_flag'] = True
                            file_info['uses_project_name'] = True
                        
                        # Check if this file is already in files_array
                        exists = False
                        for existing in files_array:
                            if existing.get('file_name') == file_name and existing.get('folder') == folder:
                                exists = True
                                break
                        
                        if not exists:
                            files_array.append(file_info)
        
        # Debug dump the complete structure at this level
        print(f"DEBUG: Content of structure at level '{parent_path}':")
        for i, item in enumerate(structure):
            if isinstance(item, dict):
                print(f"DEBUG: Item {i}: type={item.get('type')}, name={item.get('name')}")
            else:
                print(f"DEBUG: Item {i}: {item}")
        
        # Loop through the items in the structure
        for item in structure:
            if item.get('type') == 'file':
                folder = parent_path
                file_name = item.get('name', '')
                
                print(f"DEBUG: Processing file item: {file_name} with user_data: {item.get('user_data', 'None')}")
                
                # Get the file's original path if available
                original_path = item.get('original_path', '')
                
                # If no original path, check user_data
                if not original_path and 'user_data' in item:
                    user_data = item['user_data']
                    if isinstance(user_data, dict):
                        original_path = user_data.get('original_path', '')
                
                # If no original path in item but we have a files_to_cache, check there
                if not original_path and hasattr(self, 'editor') and hasattr(self.editor, 'files_to_cache'):
                    # Try the file name at the current path
                    rel_path = (parent_path + '/' + file_name).strip('/')
                    if rel_path in self.editor.files_to_cache:
                        cache_data = self.editor.files_to_cache[rel_path]
                        print(f"DEBUG: Found file in files_to_cache: {rel_path}")
                        original_path = cache_data.get('original_path', '')
                    
                    # Try without parent path
                    if not original_path:
                        # Try with just the filename
                        if file_name in self.editor.files_to_cache:
                            cache_data = self.editor.files_to_cache[file_name]
                            print(f"DEBUG: Found file in files_to_cache by name only: {file_name}")
                            original_path = cache_data.get('original_path', '')
                    
                    # Try parent path as a key
                    if not original_path and parent_path in self.editor.files_to_cache:
                        cache_data = self.editor.files_to_cache[parent_path]
                        print(f"DEBUG: Found file in files_to_cache by parent path: {parent_path}")
                        if file_name == os.path.basename(cache_data.get('original_path', '')):
                            original_path = cache_data.get('original_path', '')
                
                # Skip if no original path
                if not original_path:
                    print(f"DEBUG: No original path for file: {file_name}, skipping")
                    continue
                
                print(f"DEBUG: Adding file item: {file_name} to folder: {folder}")
                
                # Check if file exists
                if not os.path.exists(original_path):
                    print(f"DEBUG: File does not exist: {original_path}, skipping")
                    continue
                
                # Get file info
                file_info = {
                    'file_name': file_name,
                    'folder': folder,
                    'original_path': original_path,
                    'file_type': self._guess_file_type(file_name),
                    'size': os.path.getsize(original_path),
                    'is_binary': item.get('is_binary', False)
                }
                
                # Add rename flag if filename contains project name variable
                if '${PROJECT_NAME}' in file_name:
                    file_info['rename_flag'] = True
                    file_info['uses_project_name'] = True
                
                # Check if the file is already in the files_array
                exists = False
                for existing in files_array:
                    if existing.get('file_name') == file_name and existing.get('folder') == folder:
                        exists = True
                        break
                
                if not exists:
                    files_array.append(file_info)
            
            # Special handling for 1_Premiere Project folder
            elif parent_path == "" and item.get('name') == "1_Premiere Project":
                print(f"DEBUG: Special handling for 1_Premiere Project folder")
                
            # If folder with children, recursively process
            if item.get('type') == 'folder' and 'children' in item:
                new_parent = parent_path
                if item.get('name'):
                    if new_parent:
                        new_parent += '/'
                    new_parent += item.get('name')
                
                self._extract_files_from_structure(item.get('children', []), files_array, new_parent)
    
    def _clean_structure_files(self, structure):
        """
        Clean up file details in the structure, leaving only essential information
        
        Args:
            structure: The structure dictionary or list
        """
        if not structure:
            return
        
        # Handle different structure formats
        items = []
        
        # Case 1: Dictionary with 'root' key (common format)
        if isinstance(structure, dict) and 'root' in structure:
            items = structure['root']
        # Case 2: List of items (array format)
        elif isinstance(structure, list):
            items = structure
        # Case 3: Dictionary with folder keys mapping to children (legacy format)
        elif isinstance(structure, dict) and not any(k in structure for k in ['type', 'name']):
            # Convert to items
            for folder_name, children in structure.items():
                items.append({
                    'name': folder_name,
                    'type': 'folder',
                    'children': children if isinstance(children, list) else []
                })
        # Case 4: Single item dictionary with type/name fields
        elif isinstance(structure, dict) and 'type' in structure and 'name' in structure:
            items = [structure]
        
        for item in items:
            if not isinstance(item, dict):
                continue
            
            item_type = item.get('type', '')
            
            # Handle different folder formats
            if item_type == 'folder' and 'children' in item and item['children']:
                # Recursively process child folders
                self._clean_structure_files(item['children'])
                
            # Handle different file formats
            elif item_type == 'file':
                # Remove unnecessary file details but keep essential ones
                # Keep name, type, and optionally rename_flag
                keys_to_keep = ['name', 'type', 'rename_flag', 'uses_project_name', 'original_name', 'original_extension']
                keys_to_remove = [k for k in list(item.keys()) if k not in keys_to_keep]
                
                for key in keys_to_remove:
                    if key in item:
                        del item[key]
            
            # Handle legacy format where item might be a single-key dictionary representing a folder
            elif len(item) == 1 and not item_type:
                folder_name = list(item.keys())[0]
                children = list(item.values())[0]
                if isinstance(children, list):
                    self._clean_structure_files(children)

    def _guess_file_type(self, file_name):
        """
        Guess the file type based on the file extension
        
        Args:
            file_name: The file name
        
        Returns:
            str: The file type
        """
        _, ext = os.path.splitext(file_name)
        ext = ext.lower()
        
        # Video extensions
        if ext in ['.mp4', '.mov', '.avi', '.mkv', '.prproj', '.aep']:
            return 'video'
        # Audio extensions
        elif ext in ['.mp3', '.wav', '.aac', '.flac']:
            return 'audio'
        # Image extensions
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.psd']:
            return 'image'
        # Document extensions
        elif ext in ['.doc', '.docx', '.pdf', '.txt', '.rtf', '.csv', '.xls', '.xlsx']:
            return 'document'
        # Code extensions
        elif ext in ['.py', '.js', '.html', '.css', '.json', '.xml']:
            return 'code'
        else:
            return 'other'

    def _sanitize_template_name(self, name):
        """
        Sanitize a template name for use as a filename
        
        Args:
            name: The template name to sanitize
            
        Returns:
            str: The sanitized template name
        """
        if not name:
            return "unnamed_template"
            
        # Remove special characters and replace spaces with underscores
        sanitized = re.sub(r'[^\w\s-]', '', name)
        sanitized = re.sub(r'[\s-]+', '_', sanitized)
        
        # Ensure it's not too long (max 100 chars)
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
            
        # Ensure we have a valid name after sanitizing
        if not sanitized:
            return "unnamed_template"
            
        return sanitized
    
    def _clean_structure_data(self, structure):
        """
        Clean structure data to remove empty arrays and ensure all item names are strings
        
        Args:
            structure (dict): Structure data
            
        Returns:
            dict: Cleaned structure data
        """
        if not isinstance(structure, dict):
            return structure
            
        cleaned = {}
        for key, value in structure.items():
            # Skip empty arrays
            if isinstance(value, list) and not value:
                continue
                
            # Convert arrays to strings
            if isinstance(key, list):
                if not key:  # Skip empty arrays as keys
                    continue
                key = str(key)
            
            # Skip empty keys
            if not key or key.strip() == "" or key == "[]":
                continue
                
            # Clean nested structures recursively
            if isinstance(value, dict):
                cleaned_value = self._clean_structure_data(value)
                if cleaned_value:  # Only add if the cleaned value is not empty
                    cleaned[key] = cleaned_value
            elif isinstance(value, list):
                # Handle list values - typically for directories with children
                if value:  # Only process non-empty lists
                    cleaned_list = []
                    for item in value:
                        if isinstance(item, dict):
                            cleaned_item = self._clean_structure_data(item)
                            if cleaned_item:  # Only add if the cleaned item is not empty
                                cleaned_list.append(cleaned_item)
                        else:
                            # For non-dict items in lists (string, etc), keep them if not empty
                            if item:
                                cleaned_list.append(item)
                    
                    if cleaned_list:  # Only add if the cleaned list is not empty
                        cleaned[key] = cleaned_list
            else:
                # For non-dict, non-list values (string, bool, etc), keep them
                cleaned[key] = value
                
        return cleaned
    
    def _cache_template_files(self, template_name, template_path, structure_data, save_to_storage=True):
        """Cache all template files in the structure data"""
        # Cache all files in the structure data
        # This will be called when the template is loaded/updated
        
        import time
        start_time = time.time()
        
        if not template_name or not template_path:
            return structure_data
        
        # Ensure cache paths exist
        if "templates_cache_dir" not in self.paths:
            from app.utils.cache_preferences import CachePreferences
            cache_prefs = CachePreferences()
            self.paths["templates_cache_dir"] = cache_prefs.get_cache_location()
            print(f"DEBUG: Missing templates_cache_dir, setting to: {self.paths['templates_cache_dir']}")
            
        cache_dir = os.path.join(self.paths["templates_cache_dir"], template_name)
        print(f"DEBUG: Using cache directory: {cache_dir}")
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        files_dir = os.path.join(cache_dir, "files")
        os.makedirs(files_dir, exist_ok=True)
        
        # Initialize files array to store file metadata
        files_array = []
        
        # Update all cache paths in the structure data and collect file metadata
        structure_data, new_files = self._update_cache_paths_and_collect_files(
            template_name, template_path, structure_data, files_dir, files_array
        )
        
        # Save the updated structure data if requested
        if save_to_storage:
            template_data = self.get_template(template_name)
            
            # Check if template_data is valid (not None or a string)
            if template_data and isinstance(template_data, dict):
                # Update the cache_path in the template data
                template_data["cache_path"] = cache_dir
                
                # Add files array to template data
                if new_files:
                    template_data["files"] = new_files
                
                # Save the metadata
                metadata_path = os.path.join(cache_dir, "metadata.json")
                metadata = {
                    "cached_at": datetime.datetime.now().isoformat(),
                    "template_name": template_name,
                    "template_path": template_path,
                    "files_count": len(new_files) if new_files else self._count_files_in_structure(structure_data),
                }
                save_json_file(metadata_path, metadata)
                print(f"DEBUG: Saved cache metadata to {metadata_path}")
                
                # Save the template with updated cache path
                self.save_template(template_name, template_data)
            else:
                print(f"WARNING: Cannot update template cache - invalid template data for {template_name}")
            
        # Calculate and log the time taken
        end_time = time.time()
        print(f"DEBUG: Template caching took {end_time - start_time:.2f} seconds")
        
        return structure_data
        
    def _update_cache_paths_and_collect_files(self, template_name, template_path, structure_data, files_dir, files_array=None, current_folder=""):
        """
        Update cache paths in a structure and collect file metadata
        
        Args:
            template_name: Template name
            template_path: Path to the template
            structure_data: Structure data
            files_dir: Cache directory for files
            files_array: List to collect file metadata
            current_folder: Current folder path within the structure
            
        Returns:
            Tuple of (structure_data with updated cache paths, files array)
        """
        if files_array is None:
            files_array = []
            
        # Handle string (file path)
        if isinstance(structure_data, str):
            # Check if it's a file path
            if os.path.isabs(structure_data) and os.path.exists(structure_data):
                # Cache the file and return the cache path
                cache_path = self._cache_file(structure_data, files_dir)
                if cache_path:
                    # Add file metadata to files array
                    file_name = os.path.basename(structure_data)
                    files_array.append({
                        "file_name": file_name,
                        "original_path": structure_data,
                        "cached_path": cache_path,
                        "rename_flag": False,
                        "folder": current_folder,
                        "file_type": self._get_file_type(structure_data),
                        "size": os.path.getsize(structure_data),
                        "last_modified": datetime.datetime.fromtimestamp(os.path.getmtime(structure_data)).isoformat()
                    })
                    return cache_path, files_array
            # If caching failed, keep original string
        
        # Handle file dictionary format
        elif isinstance(structure_data, dict) and structure_data.get('type') == 'file' and 'path' in structure_data:
            file_path = structure_data['path']
            if os.path.exists(file_path):
                # Cache the file
                cache_path = self._cache_file(file_path, files_dir)
                if cache_path:
                    # Update cache_path but preserve the original path
                    structure_data['cache_path'] = cache_path
                    
                    # Add file metadata to files array
                    file_name = structure_data.get('name', os.path.basename(file_path))
                    rename_flag = '$' in file_name or '${' in file_name  # Check if file should be renamed with project name
                    
                    files_array.append({
                        "file_name": file_name,
                        "original_path": file_path,
                        "cached_path": cache_path,
                        "rename_flag": rename_flag,
                        "folder": current_folder,
                        "file_type": self._get_file_type(file_path),
                        "size": os.path.getsize(file_path),
                        "last_modified": datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })
            return structure_data, files_array
        
        # Handle folder format
        elif isinstance(structure_data, dict) and structure_data.get('type') == 'folder' and 'name' in structure_data:
            folder_name = structure_data['name']
            new_current_folder = os.path.join(current_folder, folder_name) if current_folder else folder_name
            
            # Process children if any
            if 'children' in structure_data and isinstance(structure_data['children'], list):
                for i, child in enumerate(structure_data['children']):
                    result, files_array = self._update_cache_paths_and_collect_files(
                        template_name, template_path, child, files_dir, files_array, new_current_folder
                    )
                    structure_data['children'][i] = result
                    
            return structure_data, files_array
        
        elif isinstance(structure_data, list):
            # Process a list of items
            for i, item in enumerate(structure_data):
                result, files_array = self._update_cache_paths_and_collect_files(
                    template_name, template_path, item, files_dir, files_array, current_folder
                )
                structure_data[i] = result
                
            return structure_data, files_array
        
        return structure_data, files_array
    
    def _get_file_type(self, file_path):
        """Determine the file type based on extension"""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Video extensions
        if ext in ['.mp4', '.mov', '.avi', '.mkv', '.prproj', '.aep']:
            return 'video'
        # Audio extensions
        elif ext in ['.mp3', '.wav', '.aac', '.flac']:
            return 'audio'
        # Image extensions
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.psd']:
            return 'image'
        # Document extensions
        elif ext in ['.doc', '.docx', '.pdf', '.txt', '.rtf', '.csv', '.xls', '.xlsx']:
            return 'document'
        # Code extensions
        elif ext in ['.py', '.js', '.html', '.css', '.json', '.xml']:
            return 'code'
        else:
            return 'other'

    def _cache_file(self, file_path, files_dir):
        """
        Cache a file and return the cache path
        
        Args:
            file_path: Path to the file to cache
            files_dir: Directory to cache the file in
            
        Returns:
            str: Path to the cached file, or None if caching failed
        """
        if not file_path or not os.path.exists(file_path):
            print(f"ERROR: Cannot cache file - path does not exist: {file_path}")
            return None
        
        try:
            # Get the file name and extension
            file_name = os.path.basename(file_path)
            
            # Create a unique file hash based on path and modification time
            file_stats = os.stat(file_path)
            file_hash = f"{hash(file_path)}_{file_stats.st_mtime}"
            
            # Cache the file with its original name
            cache_path = os.path.join(files_dir, file_name)
            
            # Create the cache directory if it doesn't exist
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            
            # Check if the file is already cached and up to date
            if os.path.exists(cache_path):
                # If the file is already cached, check if it's the same
                try:
                    cached_stats = os.stat(cache_path)
                    if cached_stats.st_size == file_stats.st_size and cached_stats.st_mtime >= file_stats.st_mtime:
                        print(f"DEBUG: File already cached and up to date: {file_name}")
                        return cache_path
                except Exception as e:
                    print(f"ERROR: Failed to check cached file stats: {str(e)}")
            
            # Copy the file to the cache
            try:
                shutil.copy2(file_path, cache_path)
                print(f"DEBUG: Cached file {file_path} to {cache_path}")
                
                # Get the metadata file path - store it at the template level, not in each directory
                root_cache_dir = os.path.dirname(files_dir)
                metadata_path = os.path.join(root_cache_dir, "metadata.json")
                
                # Load existing metadata if it exists
                metadata = {}
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                    except Exception as e:
                        print(f"ERROR: Failed to load metadata: {str(e)}")
                        metadata = {}
                
                # Ensure files dictionary exists
                if "files" not in metadata:
                    metadata["files"] = {}
                
                # Get relative path from files_dir to cache_path
                relative_to_cache = os.path.relpath(cache_path, os.path.dirname(files_dir))
                
                # Store file metadata
                metadata["files"][relative_to_cache] = {
                    "original_path": file_path,
                    "cache_path": cache_path,
                    "relative_path": os.path.dirname(relative_to_cache),
                    "file_name": file_name,
                    "size": file_stats.st_size,
                    "hash": hashlib.sha256(file_path.encode()).hexdigest(),
                    "cached_date": time.time()
                }
                
                # Update last_updated timestamp
                metadata["last_updated"] = time.time()
                
                # Create created timestamp if it doesn't exist
                if "created" not in metadata:
                    metadata["created"] = time.time()
                
                # Save the metadata
                try:
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata, f, indent=2)
                except Exception as e:
                    print(f"ERROR: Failed to save metadata: {str(e)}")
                
                return cache_path
            except Exception as e:
                print(f"Error caching file: {str(e)}")
                return None
        except Exception as e:
            print(f"Error caching file: {str(e)}")
            return None
            
    def _count_files_in_structure(self, structure_data):
        """Count the number of files in a structure"""
        count = 0
        
        if isinstance(structure_data, dict):
            if structure_data.get("type") == "file":
                count += 1
            else:
                # Process all children
                for key, value in structure_data.items():
                    if isinstance(value, (dict, list)):
                        count += self._count_files_in_structure(value)
        elif isinstance(structure_data, list):
            for item in structure_data:
                count += self._count_files_in_structure(item)
                
        return count
    
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
        """
        Delete a template and all associated files
        
        Args:
            template_name: Name of the template to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not template_name:
            return False
        
        # Normalize template name for file and directory names
        normalized_name = template_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        
        # Check if template exists in memory
        template_index = None
        template_data = None
        
        for i, template in enumerate(self.templates):
            if isinstance(template, dict) and template.get('name') == template_name:
                template_index = i
                template_data = template
                break
            
        # Get template path and structure name
        template_path = None
        structure_name = None
        structured_format = False
        
        if template_data:
            template_path = template_data.get('path') or template_data.get('file_path')
            structure_name = template_data.get('structure_name')
            structured_format = 'structure' in template_data or structure_name
            
            # Print debug info on what we're deleting
            print(f"[DEBUG] TemplateOps: Deleting template '{template_name}'")
            print(f"[DEBUG] TemplateOps: Template path: {template_path}")
            print(f"[DEBUG] TemplateOps: Structure name: {structure_name}")
            print(f"[DEBUG] TemplateOps: Structured format: {structured_format}")
        
        # Try to determine template path if not found in template data
        if not template_path and template_name:
            # Check the most likely file paths based on template name
            possible_paths = [
                # Direct template name
                os.path.join(self.paths.get('templates_dir', ''), f"{normalized_name}.json"),
                # Template_ prefix
                os.path.join(self.paths.get('templates_dir', ''), f"Template_{normalized_name}.json"),
                # Original name with spaces
                os.path.join(self.paths.get('templates_dir', ''), f"{template_name}.json")
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    template_path = path
                    print(f"[DEBUG] TemplateOps: Found template file at {template_path}")
                    break
            
        # Delete from filesystem if template file exists
        template_file_deleted = False
        if template_path and os.path.exists(template_path):
            try:
                # Don't try to delete the entire directory
                if os.path.isdir(template_path):
                    # Only delete json file if it exists
                    json_path = os.path.join(template_path, f"{template_name}.json")
                    if os.path.exists(json_path):
                        os.remove(json_path)
                        template_file_deleted = True
                        print(f"[DEBUG] TemplateOps: Deleted template file '{json_path}'")
                else:
                    # Delete the file directly
                    os.remove(template_path)
                    template_file_deleted = True
                    print(f"[DEBUG] TemplateOps: Deleted template file '{template_path}'")
            
            except Exception as e:
                print(f"[ERROR] TemplateOps: Failed to delete template file '{template_path}': {e}")
        elif not template_path:
            # Try to delete based on template name
            try:
                # Check templates directory for matching files
                templates_dir = self.paths.get('templates_dir')
                if templates_dir and os.path.exists(templates_dir):
                    # Look for template_name.json and normalized_name.json
                    template_files = [
                        f"{template_name}.json",
                        f"{normalized_name}.json",
                        f"Template_{normalized_name}.json"
                    ]
                    
                    for filename in template_files:
                        file_path = os.path.join(templates_dir, filename)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            template_file_deleted = True
                            print(f"[DEBUG] TemplateOps: Deleted template file '{file_path}'")
                            break
            except Exception as e:
                print(f"[ERROR] TemplateOps: Failed to delete template file by name '{template_name}': {e}")
        
        # Check if structures_dir exists in paths and is valid before trying to delete structure files
        structure_file_deleted = False
        if 'structures_dir' in self.paths and self.paths['structures_dir'] and os.path.exists(self.paths['structures_dir']):
            # Delete associated structure files
            # Try different possible structure names
            structure_paths = [
                # Direct matching
                os.path.join(self.paths['structures_dir'], f"{template_name}.json"),
                # Template_ prefix
                os.path.join(self.paths['structures_dir'], f"Template_{template_name}.json"),
                # Normalized name (spaces to underscores)
                os.path.join(self.paths['structures_dir'], f"{normalized_name}.json"),
                # Template_ prefix with normalized name
                os.path.join(self.paths['structures_dir'], f"Template_{normalized_name}.json")
            ]
            
            # If we know the structure name, add it
            if structured_format and structure_name:
                structure_paths.append(os.path.join(self.paths['structures_dir'], f"{structure_name}.json"))
            
            # Try deleting each possible structure file
            for structure_path in structure_paths:
                if os.path.exists(structure_path):
                    try:
                        os.remove(structure_path)
                        print(f"DEBUG: Successfully deleted structure file for '{template_name}': {structure_path}")
                        structure_file_deleted = True
                    except Exception as e:
                        print(f"ERROR: Failed to delete structure file: {e}")
            
            # If no structure was deleted, log it
            if not structure_file_deleted:
                print(f"DEBUG: No structure file found for '{template_name}'")
        else:
            print(f"DEBUG: Skipping structure file deletion - structures_dir not found or invalid")
        
        # Ensure we have a templates_cache_dir in paths
        if 'templates_cache_dir' not in self.paths or not self.paths['templates_cache_dir']:
            try:
                from app.utils.cache_preferences import CachePreferences
                cache_prefs = CachePreferences()
                self.paths['templates_cache_dir'] = cache_prefs.get_cache_location()
                print(f"[DEBUG] TemplateOps: Setting templates_cache_dir to {self.paths['templates_cache_dir']}")
            except Exception as e:
                print(f"[WARNING] TemplateOps: Failed to get cache location: {e}")
                # Fallback to a default location
                self.paths['templates_cache_dir'] = os.path.join(os.path.expanduser("~"), ".echelon", "template_cache")
        
        # Delete template cache directory - check all possible cache locations
        cache_paths = []
        
        # Only add paths if we have a valid templates_cache_dir
        if 'templates_cache_dir' in self.paths and self.paths['templates_cache_dir']:
            # Add commonly used cache path variations
            cache_paths = [
                # Original name
                os.path.join(self.paths['templates_cache_dir'], template_name),
                # Normalized name
                os.path.join(self.paths['templates_cache_dir'], normalized_name),
                # Template cache subdirectory
                os.path.join(self.paths['templates_cache_dir'], "template_cache", template_name),
                # Template cache subdirectory with normalized name
                os.path.join(self.paths['templates_cache_dir'], "template_cache", normalized_name),
            ]
        
        # Check the cached_path from template if available
        if template_data and 'cached_path' in template_data:
            cached_path = template_data['cached_path']
            if cached_path:
                if os.path.isdir(cached_path):
                    cache_paths.append(cached_path)
                
                # Also check parent directory (in case cached_path points to a file)
                parent_dir = os.path.dirname(cached_path)
                if os.path.isdir(parent_dir):
                    cache_paths.append(parent_dir)
        
        # Also check for cached files in template files list
        if template_data and 'files' in template_data and isinstance(template_data['files'], list):
            for file_data in template_data['files']:
                if isinstance(file_data, dict) and 'cached_path' in file_data:
                    cached_path = file_data['cached_path']
                    if cached_path:
                        # Get the directory containing the cached file
                        cache_dir = os.path.dirname(cached_path)
                        if os.path.isdir(cache_dir) and cache_dir not in cache_paths:
                            cache_paths.append(cache_dir)
                        
                        # Try the parent directory too
                        parent_dir = os.path.dirname(cache_dir)
                        if os.path.isdir(parent_dir) and parent_dir not in cache_paths:
                            cache_paths.append(parent_dir)
        
        # Try to delete each cache directory
        cache_deleted = False
        import shutil
        for cache_path in cache_paths:
            if cache_path and os.path.exists(cache_path) and os.path.isdir(cache_path):
                try:
                    shutil.rmtree(cache_path)
                    print(f"[DEBUG] TemplateOps: Deleted template cache directory: {cache_path}")
                    cache_deleted = True
                except Exception as e:
                    print(f"[WARNING] TemplateOps: Failed to delete template cache: {e}")
        
        if not cache_deleted:
            print(f"[INFO] TemplateOps: No cache directory found for '{template_name}'")
        
        # Use all available CachePreferences locations to check for template caches
        try:
            from app.utils.cache_preferences import CachePreferences
            cache_prefs = CachePreferences()
            cache_locations = [
                cache_prefs.get_cache_location(), 
                os.path.join(os.path.expanduser("~"), ".echelon", "template_cache")
            ]
            
            for cache_base in cache_locations:
                if cache_base and os.path.exists(cache_base):
                    # Check for template cache in various forms
                    template_cache_paths = [
                        os.path.join(cache_base, template_name),
                        os.path.join(cache_base, normalized_name),
                        os.path.join(cache_base, 'template_cache', template_name),
                        os.path.join(cache_base, 'template_cache', normalized_name)
                    ]
                    
                    for template_cache_dir in template_cache_paths:
                        if os.path.exists(template_cache_dir) and os.path.isdir(template_cache_dir):
                            try:
                                shutil.rmtree(template_cache_dir)
                                print(f"[DEBUG] TemplateOps: Deleted template cache directory: {template_cache_dir}")
                                cache_deleted = True
                            except Exception as e:
                                print(f"[WARNING] TemplateOps: Failed to delete template cache: {e}")
        except Exception as e:
            print(f"[WARNING] TemplateOps: Error checking additional cache locations: {e}")
        
        # Remove from templates list if found
        if template_index is not None:
            try:
                del self.templates[template_index]
                print(f"[DEBUG] TemplateOps: Removed template \'{template_name}\' from in-memory list.")
                
                # --- Start Logging Addition ---
                print(f"[DEBUG] TemplateOps (Delete): State AFTER removal: {len(self.templates)} templates.")
                if template_name in [t.get('name') for t in self.templates if isinstance(t, dict)]:
                     print(f"[WARNING] TemplateOps (Delete): Template '{template_name}' still found in list after deletion attempt!")
                # --- End Logging Addition ---
                
            except IndexError:
                print(f"[ERROR] TemplateOps: Index {template_index} out of range when deleting \'{template_name}\'")
        else:
            # Also attempt removal by name if index not found
            initial_len = len(self.templates)
            self.templates = [t for t in self.templates if not (isinstance(t, dict) and t.get('name') == template_name)]
            if len(self.templates) < initial_len:
                print(f"[DEBUG] TemplateOps: Removed template \'{template_name}\' from in-memory list by name match.")
                
                # --- Start Logging Addition ---
                print(f"[DEBUG] TemplateOps (Delete): State AFTER removal by name: {len(self.templates)} templates.")
                # --- End Logging Addition ---
                
            else:
                 print(f"[WARNING] TemplateOps: Template \'{template_name}\' not found in in-memory list for deletion.")
                 
        # --- Start Logging Addition ---
        # Log state before reloading
        print(f"[DEBUG] TemplateOps (Delete): State BEFORE reloading templates: {len(self.templates)} templates.")
        # --- End Logging Addition ---

        # Reload templates from disk to reflect the change
        # Use reload_templates if available, otherwise fallback to load_templates
        if hasattr(self, 'reload_templates') and callable(self.reload_templates):
            self.reload_templates()
            print(f"[DEBUG] TemplateOps: Called reload_templates()")
        elif hasattr(self, 'load_templates') and callable(self.load_templates):
            self.load_templates()
            print(f"[DEBUG] TemplateOps: Called load_templates() as fallback")
        else:
            print(f"[WARNING] TemplateOps: No reload_templates or load_templates method found!")
        
        # --- Start Logging Addition ---
        # Log state after reloading
        print(f"[DEBUG] TemplateOps (Delete): State AFTER reloading templates: {len(self.templates)} templates.")
        if template_name in [t.get('name') for t in self.templates if isinstance(t, dict)]:
             print(f"[ERROR] TemplateOps (Delete): Template '{template_name}' STILL found in list after reload!")
        else:
             print(f"[DEBUG] TemplateOps (Delete): Template '{template_name}' confirmed removed after reload.")
        # --- End Logging Addition ---

        # Get template path and structure name
        template_path = None
        structure_name = None
        structured_format = False
        
        if template_data:
            template_path = template_data.get('path') or template_data.get('file_path')
            structure_name = template_data.get('structure_name')
            structured_format = 'structure' in template_data or structure_name
            
            # Print debug info on what we're deleting
            print(f"[DEBUG] TemplateOps: Deleting template '{template_name}'")
            print(f"[DEBUG] TemplateOps: Template path: {template_path}")
            print(f"[DEBUG] TemplateOps: Structure name: {structure_name}")
            print(f"[DEBUG] TemplateOps: Structured format: {structured_format}")
        
        # Mark as successful even if we couldn't find the template in memory
        # Since we still attempted to delete from filesystem
        deleted = template_file_deleted or structure_file_deleted or cache_deleted or template_index is not None
        if deleted:
            print(f"[INFO] TemplateOps: Successfully deleted template '{template_name}'")
        else:
            print(f"[WARNING] TemplateOps: Template '{template_name}' may not have been fully deleted")
        
        return True
    
    def _clean_template_caches(self, template_name, normalized_name=None):
        """
        Clean up any template caches that might exist in various managers
        
        Args:
            template_name: The name of the template to remove from caches
            normalized_name: Optional normalized version of the template name
        """
        if normalized_name is None:
            normalized_name = template_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
            
        # Try to clean up template-related caches in memory
        try:
            # Clear from remembered templates if found
            if hasattr(self, 'recent_templates') and isinstance(self.recent_templates, list):
                self.recent_templates = [t for t in self.recent_templates 
                                      if (isinstance(t, dict) and t.get('name') != template_name)
                                      or (isinstance(t, str) and t != template_name)]
                print(f"[DEBUG] TemplateOps: Cleaned up recent_templates list")
            
            # Clear folder references
            if hasattr(self, 'folders') and isinstance(self.folders, dict):
                for folder, templates in list(self.folders.items()):
                    if isinstance(templates, list) and template_name in templates:
                        self.folders[folder] = [t for t in templates if t != template_name]
                        print(f"[DEBUG] TemplateOps: Removed template from folder '{folder}'")
                # Save the updated folders
                if hasattr(self, 'save_folders'):
                    self.save_folders()
                    print(f"[DEBUG] TemplateOps: Saved updated folders")
            
            # Update any selectors or UI components that might be caching the template
            if hasattr(self, 'update_selectors'):
                self.update_selectors()
                print(f"[DEBUG] TemplateOps: Updated template selectors")
                
        except Exception as e:
            print(f"[WARNING] TemplateOps: Error cleaning template caches: {e}")
    
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
        """
        Rename a template and its associated structure.
        
        Args:
            old_name (str): The current name of the template
            new_name (str): The new name for the template
            
        Returns:
            bool: True if the template was successfully renamed, False otherwise
        """
        print(f"DEBUG: rename_template called - old_name='{old_name}', new_name='{new_name}'")
        
        # If the names are identical, return success
        if old_name == new_name:
            return True
            
        try:
            # Normalize names - strip any extra whitespace
            old_name = old_name.strip()
            new_name = new_name.strip()
            
            # Find the template by the old name
            template = None
            for t in self.templates:
                # Use case-insensitive comparison for better matching
                if t.get('name', '').strip().lower() == old_name.lower():
                    template = t
                    break
                    
            if not template:
                print(f"WARNING: Template not found with name '{old_name}' for renaming")
                return False
                
            # Save the old and new file paths
            old_file_path = os.path.join(self.paths.get('templates_dir', ''), self.sanitize_filename(old_name) + ".json")
            new_file_path = os.path.join(self.paths.get('templates_dir', ''), self.sanitize_filename(new_name) + ".json")
            
            # Look for any associated structure files
            structure_name = template.get('structure_name')
            if not structure_name:
                # Try to find structure using various naming patterns
                possible_structure_names = [
                    f"Template_{old_name}",
                    old_name,
                    f"Template_{old_name.replace(' ', '_')}",
                    old_name.replace(' ', '_')
                ]
                
                # Remove duplicates while preserving order
                seen = set()
                structure_names_to_try = [name for name in possible_structure_names 
                                        if not (name.lower() in seen or seen.add(name.lower()))]
                
                print(f"DEBUG: Looking for associated structures with names: {structure_names_to_try}")
                
                # Try each name variation
                for name in structure_names_to_try:
                    structure = self.get_structure(name)
                    if structure:
                        structure_name = name
                        print(f"DEBUG: Found associated structure with name '{name}'")
                        break
            
            # Update the template in memory
            old_template_data = template.copy()
            template['name'] = new_name
            
            # If there's a structure associated with this template, update its name too
            if structure_name:
                print(f"DEBUG: Updating associated structure from '{structure_name}' to '{new_name}'")
                
                # Create the new structure name
                if structure_name.startswith("Template_"):
                    new_structure_name = f"Template_{new_name}"
                else:
                    new_structure_name = new_name
                    
                # Update structure name in the template
                template['structure_name'] = new_structure_name
                
                # Get the structure data
                structure = self.get_structure(structure_name)
                if structure:
                    # Copy the structure with the new name 
                    if isinstance(structure, dict) and 'name' in structure:
                        structure['name'] = new_structure_name
                    
                    # Save the structure with the new name
                    from app.templates.structure_operations import StructureOperations
                    structure_ops = StructureOperations()
                    saved = structure_ops.save_custom_structure(new_structure_name, structure)
                    
                    if saved:
                        print(f"DEBUG: Successfully saved structure with new name '{new_structure_name}'")
                        
                        # Try to delete the old structure file if it exists
                        if structure_name != new_structure_name:
                            structure_ops.delete_custom_structure(structure_name)
                    else:
                        print(f"WARNING: Failed to save structure with new name '{new_structure_name}'")
            
            # Save the template with the new name and delete the old one
            save_result = self.save_template_to_file(template, new_file_path)
            if not save_result:
                print(f"ERROR: Failed to save template with new name to {new_file_path}")
                return False
                
            # Update the template in the templates list - first remove the old one, then add the new one
            # Find and remove the old template
            for i in range(len(self.templates) - 1, -1, -1):  # Iterate backwards to safely remove
                t = self.templates[i]
                if isinstance(t, dict) and t.get('name', '').strip().lower() == old_name.lower():
                    print(f"DEBUG: Removing old template '{old_name}' from templates list at index {i}")
                    self.templates.pop(i)
            
            # Add the new template
            self.templates.append(template.copy())
            print(f"DEBUG: Added new template '{new_name}' to templates list")
            
            # Remove the old template file
            if os.path.exists(old_file_path) and old_file_path != new_file_path:
                try:
                    os.remove(old_file_path)
                    print(f"DEBUG: Removed old template file: {old_file_path}")
                except Exception as e:
                    print(f"WARNING: Failed to remove old template file: {e}")
            
            # Update any references in folders
            for folder in self.folders:
                if 'templates' in folder:
                    # Update template references in the folder
                    for i, tmpl_name in enumerate(folder['templates']):
                        if tmpl_name.strip() == old_name:
                            folder['templates'][i] = new_name
                            print(f"DEBUG: Updated template reference in folder '{folder.get('name', 'Unknown')}'")
            
            # Save the updated folders
            self.save_folders()
            
            # Force reload of templates
            self.reload_templates()
            
            # Refresh UI if possible
            if hasattr(self, 'refresh_ui') and callable(self.refresh_ui):
                self.refresh_ui()
                
            # Try to select the renamed template in the UI
            if hasattr(self, 'gallery') and getattr(self, 'gallery', None):
                print(f"🔶 SELECT AFTER RENAME: Trying gallery.select_template('{new_name}')")
                # Make multiple attempts with different variations of the name
                success = self.gallery.select_template(new_name)
                
                if not success:
                    print("🔶 SELECT AFTER RENAME: Direct selection failed for all name variations")
                    print("🔶 SELECT AFTER RENAME: Direct selection failed, trying fallbacks")
                    
                    # Try different variations of the name
                    variations = [
                        new_name,
                        new_name.strip(),
                        f"Template_{new_name}",
                        new_name.replace(' ', '_'),
                        new_name.replace('_', ' ')
                    ]
                    
                    # Try to find the template in the template manager
                    template_found = False
                    for variation in variations:
                        print(f"🔶 SELECT AFTER RENAME: Looking for template '{variation}' in template manager")
                        for template in self.templates:
                            if template.get('name', '').strip() == variation.strip():
                                template_found = True
                                break
                                
                        if template_found:
                            break
                            
                    if not template_found:
                        print("🔶 SELECT AFTER RENAME: Template not found in template manager with any name variation")
                        
                        # Last resort - try to manually select from visible cards
                        print(f"🔶 SELECT AFTER RENAME: Attempting manual selection from {len(self.gallery.template_cards)} template cards")
                        for card in self.gallery.template_cards:
                            card_name = getattr(card, 'template_name', None) or card.template.get('name', '')
                            print(f"🔶 SELECT AFTER RENAME: Checking card '{card_name}' against '{new_name}'")
                            # Fuzzy match - check if one name contains the other or vice versa
                            if (card_name.strip().lower() in new_name.lower() or 
                                new_name.lower() in card_name.strip().lower()):
                                if hasattr(card, 'select') and callable(card.select):
                                    card.select()
                                    print(f"🔶 SELECT AFTER RENAME: Selected card '{card_name}' as a fallback")
                                    return True
                    
                    print(f"🔶 SELECT AFTER RENAME: All selection methods failed for '{new_name}'")
            
            return True
            
        except Exception as e:
            print(f"ERROR renaming template: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def update_template(self, template):
        """Update a template's metadata"""
        if not template or not template.get('name'):
            return False
            
        template_name = template.get('name')
        
        # Different handling based on template type
        if template.get('type') == 'directory':
            return self.update_directory_template(template)
        else:
            # For file templates, use the save_template method to ensure consistent handling
            # Extract the structure from the template
            structure = template.get('structure')
            
            # Any files that are part of the template
            source_files = template.get('files', [])
            
            # Get the original template name from the file path if available
            original_name = template_name
            file_path = template.get('file_path', '')
            if file_path:
                import os
                # Extract original name from file path
                file_name = os.path.basename(file_path)
                if file_name.endswith('.json'):
                    original_name = file_name[:-5]  # Remove .json extension
                print(f"[DEBUG] TemplateOperations: Updating template {template_name}, original file: {original_name}")
            
            # Use save_template to ensure consistent handling of file caching
            return self.save_template(
                template_name=template_name,
                structure=structure,
                template_data=template,
                source_files=source_files,
                cache_files=True,  # Always cache files during update
                is_update=True,    # Mark this as an update
                original_name=original_name  # Pass the original name for file path consistency
            )
    
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
            self.custom_structures = {}
            
        # Prepare a safe structure by converting to string and back
        try:
            # Use json.dumps/loads to ensure it's serializable
            safe_structure_str = json.dumps(structure)
            safe_structure = json.loads(safe_structure_str)
            
            # Sanitize the filename for disk operations
            sanitized_name = name.replace(' ', '_').replace('/', '-').replace('\\', '-')
            
            # Check if we already have this structure loaded
            existing_creation_time = None
            existing_found = False
            
            # First check if it exists in our in-memory structures
            for i, s in enumerate(self.custom_structures):
                if isinstance(s, dict) and s.get("name") == name:
                    existing_creation_time = s.get("created", time.time())
                    existing_found = True
                    # Update the in-memory structure
                    self.custom_structures[i] = {
                        "name": name,
                        "structure": safe_structure,
                        "modified": time.time(),
                        "created": existing_creation_time
                    }
                    print(f"INFO: Updated existing in-memory custom structure '{name}'")
                    break
                
            # If not found in memory, check if file exists on disk
            if not existing_found:
                file_path = os.path.join(self.paths["custom_structures_dir"], f"{sanitized_name}.json")
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            existing_data = json.load(f)
                            existing_creation_time = existing_data.get("created", time.time())
                            existing_found = True
                            print(f"INFO: Found existing on-disk custom structure '{name}'")
                    except Exception as e:
                        print(f"WARNING: Error reading existing structure file: {e}")
                        # Continue with creation time of now
                        existing_creation_time = time.time()
                else:
                    # No existing structure, use current time
                    existing_creation_time = time.time()
                    
                # Add to our in-memory structures
                structure_data = {
                    "name": name,
                    "structure": safe_structure,
                    "modified": time.time(),
                    "created": existing_creation_time
                }
                self.custom_structures.append(structure_data)
                    
            # Save to disk
            try:
                os.makedirs(self.paths["custom_structures_dir"], exist_ok=True)
                file_path = os.path.join(self.paths["custom_structures_dir"], f"{sanitized_name}.json")
                
                # Write file
                with open(file_path, 'w') as f:
                    json.dump({
                        "name": name,
                        "structure": safe_structure,
                        "modified": time.time(),
                        "created": existing_creation_time
                    }, indent=2)
                    
                status = "Updated" if existing_found else "Created"
                print(f"INFO: Successfully {status.lower()} custom structure '{name}' to {file_path}")
                
                # If this was an update and name differs from sanitized name, clean up old file
                if existing_found and name != sanitized_name:
                    old_path = os.path.join(self.paths["custom_structures_dir"], f"{name}.json")
                    if os.path.exists(old_path) and old_path != file_path:
                        try:
                            os.remove(old_path)
                            print(f"INFO: Removed old structure file at {old_path}")
                        except Exception as e:
                            print(f"WARNING: Failed to remove old structure file: {e}")
                
                return True
            except Exception as e:
                print(f"ERROR: Failed to save custom structure '{name}' to disk: {e}")
                return False
                
        except RecursionError:
            print(f"ERROR: Failed to save custom structure '{name}': Recursion detected in structure")
            return False
        except Exception as e:
            print(f"ERROR: Failed to process custom structure '{name}': {e}")
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
        
    def save_structure(self, name, structure):
        """
        Save a structure (alias for save_custom_structure)
        
        Args:
            name (str): Name of the structure
            structure (list): The structure data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First attempt to save normally
            result = self.save_custom_structure(name, structure)
            if result:
                return True
                
            # If that failed, try a more robust approach
            print(f"INFO: First save attempt failed, trying with simplified approach")
            
            # Create a safe serializable structure
            safe_structure = self._create_safe_structure(structure)
            return self.save_custom_structure(name, safe_structure)
            
        except Exception as e:
            print(f"ERROR: Failed to save structure: {e}")
            return False
            
    def _create_safe_structure(self, structure):
        """Convert structure to a safely serializable format"""
        if not structure:
            return []
            
        # Handle both list and dict formats safely
        if isinstance(structure, dict):
            result = {}
            # Copy basic fields that are definitely serializable
            for key in ['name', 'type']:
                if key in structure:
                    result[key] = structure[key]
                    
            # Handle children separately
            if 'children' in structure and structure['children']:
                result['children'] = self._create_safe_structure(structure['children'])
            return result
            
        elif isinstance(structure, list):
            result = []
            # Process each item
            for item in structure:
                if isinstance(item, (dict, list)):
                    result.append(self._create_safe_structure(item))
                else:
                    result.append(item)
            return result
            
        # For any other type, return as is
        return structure
        
    def save_template_info(self, template_name, template_info):
        """
        Save template information
        
        Args:
            template_name (str): Name of the template
            template_info (dict): Dictionary containing template information
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the template if it exists
            existing_template = self.get_template(template_name)
            
            if existing_template:
                # Update existing template with new info
                for key, value in template_info.items():
                    existing_template[key] = value
                    
                # Save the updated template
                self.update_template(existing_template)
                print(f"INFO: Updated template info for '{template_name}'")
                return True
            else:
                # Create a new template entry
                template_info['name'] = template_name
                template_info['created'] = time.time()
                template_info['modified'] = time.time()
                
                # Save as a new template
                self.templates.append(template_info)
                
                # Save to disk
                template_file = os.path.join(self.paths["templates_dir"], f"{template_name.replace(' ', '_')}.json")
                with open(template_file, 'w') as f:
                    json.dump(template_info, f, indent=2)
                    
                print(f"INFO: Created new template info for '{template_name}'")
                return True
        except Exception as e:
            print(f"ERROR: Failed to save template info for '{template_name}': {e}")
            return False
        
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
    
    def load_templates(self):
        """Load all templates from template directory"""
        self.templates = {}
        
        # Get template directory
        template_dir = self.paths.get("templates_dir", "")
        if not template_dir or not os.path.exists(template_dir):
            print(f"Warning: Template directory does not exist: {template_dir}")
            return
            
        # Find all template files
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                if file.endswith(".json") and file != "folders.json" and file != "preferences.json":
                    try:
                        # Load template file
                        template_path = os.path.join(root, file)
                        with open(template_path, 'r') as f:
                            template_data = json.load(f)
                            
                        # Add template to list if it has required fields
                        if 'name' in template_data:
                            self.templates[template_data['name']] = template_data
                    except Exception as e:
                        print(f"Error loading template file {file}: {e}")
                        
        print(f"Loaded {len(self.templates)} templates from {template_dir}")

    def _normalize_structure_format(self, structure_items):
        """Normalize the structure format to ensure consistency.
        
        This method ensures folders are represented as dictionaries with empty arrays 
        for consistency with the rest of the application: {"folder_name": []}
        
        Args:
            structure_items (list): List of structure items to normalize
            
        Returns:
            list: Normalized structure items
        """
        if not structure_items:
            return []
            
        normalized = []
        
        for item in structure_items:
            # Handle dictionaries (folders with possible children)
            if isinstance(item, dict):
                # If the item is already a dictionary with a key and a list value,
                # we can use it directly or process its children
                if list(item.keys()) == 1 and isinstance(list(item.values())[0], list):
                    folder_name = list(item.keys())[0]
                    children = list(item.values())[0]
                    normalized.append({folder_name: self._normalize_structure_format(children)})
                # Handle the {"name": "folder_name", "type": "folder"} format
                elif "name" in item and "type" in item and item["type"] == "folder":
                    folder_name = item["name"]
                    children = []
                    if "children" in item and isinstance(item["children"], list):
                        children = self._normalize_structure_format(item["children"])
                    normalized.append({folder_name: children})
                # Handle the {"folder_name": []} format
                else:
                    processed_dict = {}
                    for folder_name, children in item.items():
                        if isinstance(children, list):
                            processed_dict[folder_name] = self._normalize_structure_format(children)
                        else:
                            # Ensure empty folders are represented as empty lists
                            processed_dict[folder_name] = []
                    normalized.append(processed_dict)
            # Handle string items (files or folders without format)
            elif isinstance(item, str):
                # String items are treated as file names
                normalized.append(item)
                
        return normalized 

    def save_template_to_file(self, template, file_path):
        """
        Save a template object to a specific file path
        
        Args:
            template (dict): The template object to save
            file_path (str): The file path where the template should be saved
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write the template to the file
            with open(file_path, 'w') as f:
                json.dump(template, f, indent=2)
                
            print(f"DEBUG: Successfully saved template to file: {file_path}")
            return True
        except Exception as e:
            print(f"ERROR: Failed to save template to file {file_path}: {e}")
            import traceback
            traceback.print_exc()
            return False 

    def get_templates_dir(self):
        """
        Get the templates directory path
        
        Returns:
            str: Path to the templates directory
        """
        # Try different ways to get the templates directory
        templates_dir = None
        
        # Method 1: Check if we have a paths attribute
        if hasattr(self, 'paths') and isinstance(self.paths, dict):
            templates_dir = self.paths.get('templates_dir')
            
        # Method 2: Get from config paths
        if not templates_dir:
            paths = get_config_paths()
            templates_dir = paths.get('templates_dir')
            
        # Method 3: Fallback to default location
        if not templates_dir:
            home_dir = os.path.expanduser("~")
            templates_dir = os.path.join(home_dir, '.echelon', 'templates')
            
        # Ensure the directory exists
        os.makedirs(templates_dir, exist_ok=True)
        
        return templates_dir