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
import copy # Add copy import

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

        # --- Validation --- 
        if not template_name:
            print("ERROR: Cannot save template without a name.")
            return False, "Template name is required."
        # --- REMOVED structure validation ---
        # --- END Validation ---

        # --- MOVED: Ensure sanitized_name is defined early ---
        sanitized_name = self.sanitize_filename(template_name)
        if not sanitized_name:
            print(f"ERROR: Template name '{template_name}' resulted in an empty sanitized name.")
            return False, "Invalid template name after sanitization."
        # --- END MOVED ---
        
        # Sanitize original name if provided
        original_sanitized_name = self.sanitize_filename(original_name) if original_name else None
        
        # Handle template rename or deletion if original_name is provided
        if original_name and original_sanitized_name and original_sanitized_name != sanitized_name:
            print(f"DEBUG: Renaming template from '{original_sanitized_name}' to '{sanitized_name}'")
            # Delete the old template file
            old_file_path = os.path.join(self.paths["templates_dir"], f"{original_sanitized_name}.json")
            if os.path.exists(old_file_path):
                try:
                    os.remove(old_file_path)
                    print(f"DEBUG: Removed old template file: {old_file_path}")
                except Exception as e:
                    print(f"ERROR: Failed to remove old template file '{old_file_path}': {e}")
            
            # Also delete the old cache directory if it exists
            if self.file_cache_manager and hasattr(self.file_cache_manager, 'cache_dir'):
                old_template_cache_path = os.path.join(self.file_cache_manager.cache_dir, original_sanitized_name)
                if os.path.isdir(old_template_cache_path):
                    try:
                        shutil.rmtree(old_template_cache_path)
                        print(f"DEBUG: Removed old template cache directory: {old_template_cache_path}")
                    except Exception as e:
                        print(f"ERROR: Failed to remove old template cache directory '{old_template_cache_path}': {e}")
                elif not self.file_cache_manager:
                    print("WARN: File cache manager not available, cannot clear old cache.")

        # Extract files from structure
        files_array = []
        if structure:
            self._extract_files_from_structure(structure, files_array)
        
        print(f"DEBUG: Extracted {len(files_array)} file entries from structure before caching.")

        # --- ADDED: Cache files and update files_array with cached_path ---
        updated_files_array = []
        if self.file_cache_manager:
            print(f"DEBUG: Caching files for template '{sanitized_name}'")
            for file_info in files_array:
                # Make a copy to avoid modifying the original dict if skipping
                current_file_info = file_info.copy()
                original_path = current_file_info.get('original_path')
                
                # Only process entries that look like files with an original path
                if original_path: 
                    if os.path.exists(original_path):
                        folder = current_file_info.get('folder', '')
                        rename_flag = current_file_info.get('rename_flag', False)
                        # Pass existing info as file_metadata
                        file_metadata_to_pass = current_file_info 

                        print(f"  Attempting to cache: {original_path} for template: {sanitized_name}")
                        
                        # Call cache_file 
                        cached_path = self.file_cache_manager.cache_file(
                            file_path=original_path, 
                            template_name=sanitized_name, # Use the sanitized template name for the cache folder
                            folder_path=folder, # Pass folder path for metadata consistency
                            rename_flag=rename_flag,
                            file_metadata=file_metadata_to_pass
                        )
                        
                        if cached_path:
                            print(f"  Successfully cached '{original_path}' to '{cached_path}'")
                            # *** ADD cached_path to the file_info dictionary ***
                            current_file_info['cached_path'] = cached_path 
                            updated_files_array.append(current_file_info) # Add the updated info
                        else:
                            print(f"  WARN: Failed to cache '{original_path}'. Skipping this file in the final template.")
                            # Skip files that failed to cache
                            
                    else: # Original path provided but doesn't exist
                        print(f"  WARN: Skipping file entry, source file not found: {original_path}")
                        # Skip files that don't exist

                else: # No original_path found, likely a folder or placeholder
                    print(f"  DEBUG: Skipping entry, no original_path: {current_file_info.get('name', 'N/A')}")
                    # Keep folder structure definitions or other non-file entries
                    updated_files_array.append(current_file_info) 
                
        else: # No file cache manager
            print("WARN: File cache manager not available. Cannot cache files. Using files directly from structure.")
            updated_files_array = files_array # Use original array if cache manager is missing

        # Use the updated array with cached paths (or original if caching failed/skipped)
        files_array_for_json = updated_files_array 
        print(f"DEBUG: Final files_array count for JSON: {len(files_array_for_json)}")
        # --- END ADDED ---

        # --- ADDED: Get the template cache directory path ---
        template_cache_directory = None
        if self.file_cache_manager:
            try:
                # CORRECTED: Construct the path manually using cache_dir and sanitized_name
                if hasattr(self.file_cache_manager, 'cache_dir') and self.file_cache_manager.cache_dir:
                    template_cache_directory = os.path.join(self.file_cache_manager.cache_dir, sanitized_name)
                    print(f"DEBUG: Determined template cache directory: {template_cache_directory}")
                else:
                    print("WARN: FileCacheManager exists but has no cache_dir attribute.")
            except Exception as e:
                print(f"WARN: Failed to get template cache directory path: {e}")
        # --- END ADDED ---

        # Prepare template data dictionary
        template_data = {
            'name': template_name,
            'structure_name': self.sanitize_filename(template_name), # Use sanitized name for consistency
            'structure': structure,
            'category': category or "Uncategorized",
            'description': description,
            'created': datetime.datetime.now().timestamp(),
            'modified': datetime.datetime.now().timestamp(),
            'tags': tags or [],
            'files': files_array_for_json, 
            'type': template_type,
            # --- ADDED: Store the template cache directory path ---
            'cached_path': template_cache_directory 
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
            
            # --- CORRECTED CALL TO save_template ---
            # Extract required arguments from the input template dictionary
            structure = template.get('structure')
            category = template.get('category')
            description = template.get('description')
            tags = template.get('tags')
            template_type = template.get('type', 'Standard') # Use 'type' key, fallback to 'Standard'
            
            # Check if 'files' key exists, needed by save_template logic indirectly
            # Even if cache_files=True isn't passed, save_template extracts files from structure
            if 'files' not in template:
                 template['files'] = [] # Ensure files key exists

            # Call save_template with extracted keyword arguments
            return self.save_template(
                template_name=template_name,
                structure=structure,
                category=category,
                description=description,
                tags=tags,
                template_type=template_type,
                original_name=original_name # Pass original name for rename handling
            )
            # --- END CORRECTION ---
            
            # --- REMOVED INCORRECT CALL ---
            # return self.save_template(
            #     template_name=template_name,
            #     structure=structure,
            #     template_data=template,  # Incorrect argument
            #     source_files=source_files, # Incorrect argument
            #     cache_files=True,  # Incorrect argument
            #     is_update=True,    # Incorrect argument
            #     original_name=original_name  # Pass the original name for file path consistency
            # )
            # --- END REMOVAL ---
    
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

    def duplicate_template(self, original_template_name):
        """Duplicates an existing template, including its data and cached files."""
        print(f"[DEBUG] Attempting to duplicate template: '{original_template_name}'")

        # 1. Reload templates to ensure we have the latest list
        try:
            self.load_templates()
        except Exception as e:
            return False, f"Failed to reload templates before duplication: {e}"
            
        # 2. Get original template data
        original_data = self.get_template(original_template_name)
        if not original_data:
            print(f"[ERROR] Original template '{original_template_name}' not found for duplication.")
            return False, f"Original template '{original_template_name}' not found."
            
        original_sanitized_name = self.sanitize_filename(original_template_name)

        # 3. Determine new unique name
        # Handle both list and dict formats for self.templates
        if isinstance(self.templates, dict):
            existing_names = set(self.templates.keys())
        elif isinstance(self.templates, list):
            existing_names = {t.get('name') for t in self.templates if isinstance(t, dict) and t.get('name')}
        else:
            print(f"[ERROR] self.templates is neither list nor dict ({type(self.templates)}). Cannot determine existing names.")
            return False, "Internal error: Could not read existing template names."
        
        # --- New Naming Logic ---
        base_name = original_template_name
        start_counter = 1 # Default: start with " copy", then " copy 2"

        # Check if the original name already ends with " copy N"
        match_numbered = re.match(r"^(.*?) copy (\d+)$", original_template_name)
        if match_numbered:
            base_name = match_numbered.group(1)
            # If duplicating "Name copy 5", start checking from "Name copy 6"
            start_counter = int(match_numbered.group(2)) + 1
            print(f"[DEBUG] Detected numbered copy: Base='{base_name}', Next counter={start_counter}")
        else:
            # Check if the original name ends with " copy" (no number)
            match_simple = re.match(r"^(.*?) copy$", original_template_name)
            if match_simple:
                base_name = match_simple.group(1)
                # If duplicating "Name copy", start checking from "Name copy 2"
                start_counter = 2 
                print(f"[DEBUG] Detected simple copy: Base='{base_name}', Next counter={start_counter}")
            # else: original name doesn't end with " copy" or " copy N", 
            # use original_template_name as base_name and start_counter = 1 (default)
            else:
                 print(f"[DEBUG] Original name is the base: Base='{base_name}', Start counter={start_counter}")
                 

        # Find the next available name using the base_name and start_counter
        counter = start_counter
        while True:
            if counter == 1:
                # First copy attempt for a base name is always " copy"
                new_name = f"{base_name} copy"
            else:
                new_name = f"{base_name} copy {counter}"
            
            if new_name not in existing_names:
                break # Found a unique name
            counter += 1
        # --- End New Naming Logic ---

        new_sanitized_name = self.sanitize_filename(new_name)
        print(f"[DEBUG] Determined new name: '{new_name}' (Sanitized: '{new_sanitized_name}'")

        # 4. Create new template data (deep copy)
        try:
            new_data = copy.deepcopy(original_data)
        except Exception as e:
            print(f"[ERROR] Failed to deep copy template data: {e}")
            return False, f"Failed to copy template data: {e}"

        # 5. Update metadata
        new_data['name'] = new_name
        now = time.time()
        new_data['created'] = now
        new_data['modified'] = now
        new_json_path = os.path.join(self.get_templates_dir(), f"{new_sanitized_name}.json")
        new_data['file_path'] = new_json_path

        # Update structure name if it exists and matches the old sanitized name
        if new_data.get('structure_name') == original_sanitized_name:
             new_data['structure_name'] = new_sanitized_name
             print(f"[DEBUG] Updated structure_name to '{new_sanitized_name}'")

        # 6. Handle Cached Files and Paths
        new_cache_path = None
        original_cache_path = original_data.get('cached_path')
        
        if self.file_cache_manager and original_cache_path and os.path.isdir(original_cache_path):
            new_cache_base_dir = self.file_cache_manager.cache_dir
            new_cache_path = os.path.join(new_cache_base_dir, new_sanitized_name)
            new_data['cached_path'] = new_cache_path
            print(f"[DEBUG] Original cache path: {original_cache_path}")
            print(f"[DEBUG] New cache path: {new_cache_path}")

            # Copy cache directory
            try:
                if os.path.exists(new_cache_path):
                     print(f"[WARNING] Target cache path {new_cache_path} already exists. Removing before copy.")
                     shutil.rmtree(new_cache_path)
                shutil.copytree(original_cache_path, new_cache_path, dirs_exist_ok=False) # dirs_exist_ok=False to ensure clean copy
                print(f"[DEBUG] Copied cache directory from {original_cache_path} to {new_cache_path}")
            except Exception as e:
                print(f"[ERROR] Failed to copy cache directory: {e}")
                # Decide if this is a critical error. Maybe proceed without cached files?
                # For now, let's return failure.
                return False, f"Failed to copy cached files: {e}"

            # Update cached_path within the 'files' array
            updated_files_count = 0
            if 'files' in new_data and isinstance(new_data['files'], list):
                for file_info in new_data['files']:
                    if isinstance(file_info, dict) and 'cached_path' in file_info:
                        old_file_cache_path = file_info['cached_path']
                        # Replace the old sanitized name part with the new one
                        # Assumes path structure like /.../cache_dir/ORIGINAL_SANITIZED/files/file.ext
                        try:
                            # More robustly replace the segment corresponding to the template name
                            parts = old_file_cache_path.split(os.sep)
                            if original_sanitized_name in parts:
                                idx = parts.index(original_sanitized_name)
                                parts[idx] = new_sanitized_name
                                file_info['cached_path'] = os.sep.join(parts)
                                updated_files_count += 1
                            else:
                                print(f"[WARNING] Could not find '{original_sanitized_name}' segment in file cache path: {old_file_cache_path}")
                        except Exception as path_e:
                             print(f"[ERROR] Failed to update file cache path '{old_file_cache_path}': {path_e}")
                print(f"[DEBUG] Updated cached_path for {updated_files_count} entries in the files array.")
        else:
            print("[DEBUG] No original cache directory found or file cache manager unavailable. Skipping cache copy.")
            # Ensure new template doesn't point to a non-existent cache
            if 'cached_path' in new_data:
                 del new_data['cached_path']
            # Clear file cache paths if they exist but source wasn't copied
            if 'files' in new_data and isinstance(new_data['files'], list):
                 for file_info in new_data['files']:
                     if isinstance(file_info, dict) and 'cached_path' in file_info:
                         del file_info['cached_path']


        # 7. Save the new template JSON file
        save_success = self.save_template_to_file(new_data, new_json_path)
        if not save_success:
            print(f"[ERROR] Failed to save new template file: {new_json_path}")
            # Cleanup potentially copied cache?
            if new_cache_path and os.path.exists(new_cache_path):
                try:
                    shutil.rmtree(new_cache_path)
                    print(f"[DEBUG] Cleaned up copied cache directory: {new_cache_path}")
                except Exception as clean_e:
                    print(f"[ERROR] Failed to cleanup cache directory {new_cache_path}: {clean_e}")
            return False, f"Failed to save duplicated template file."

        # 8. Reload templates in memory
        self.load_templates()
        
        print(f"[INFO] Successfully duplicated template '{original_template_name}' as '{new_name}'")
        return True, new_name