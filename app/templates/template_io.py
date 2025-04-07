import os
import json
import datetime
import shutil
import time
import copy
import re

from app.utils.utils import save_json_file, load_json_file
from app.templates.template_utils import sanitize_filename # Import necessary utils

class TemplateIO:
    """Handles Template Input/Output operations (load, save, delete, etc.)"""

    def __init__(self, paths, file_cache_manager, structure_ops):
        """Initialize with dependencies."""
        self.paths = paths
        self.file_cache_manager = file_cache_manager
        self.structure_ops = structure_ops
        # Initialize the main templates store (using dict as loaded by original load_templates)
        self.templates = {}
        self.load_templates() # Load templates on initialization

    def load_templates(self):
        """Load all templates from the template directory into self.templates dictionary."""
        self.templates = {} # Reset before loading
        template_dir = self.paths.get("templates_dir", "")
        if not template_dir or not os.path.exists(template_dir):
            print(f"Warning: Template directory does not exist: {template_dir}")
            return

        loaded_count = 0
        # Find all template JSON files
        for root, dirs, files in os.walk(template_dir):
            # Avoid walking into cache directories (though structure cache is separate now)
            dirs[:] = [d for d in dirs if d.lower() != 'cache']

            for file in files:
                if file.endswith(".json") and file.lower() not in ["folders.json", "preferences.json"]:
                    template_path = os.path.join(root, file)
                    try:
                        # Use load_json_file utility
                        template_data = load_json_file(template_path)

                        # Add template to dict if it has a name
                        if isinstance(template_data, dict) and 'name' in template_data:
                             template_name = template_data['name']
                             if template_name in self.templates:
                                 print(f"WARN: Duplicate template name '{template_name}' found. Overwriting entry from {self.templates[template_name].get('file_path')} with {template_path}")
                             # Add/overwrite template using its name as the key
                             template_data['file_path'] = template_path # Ensure file_path is stored
                             self.templates[template_name] = template_data
                             loaded_count += 1
                        elif template_data is not None: # Only warn if file loaded but was invalid
                             print(f"WARN: Skipping invalid template data (not dict or no name) in file: {template_path}")

                    except Exception as e:
                        print(f"Error loading template file {template_path}: {e}") # load_json_file handles decode errors

        print(f"Loaded {loaded_count} templates from {template_dir}. Total in memory: {len(self.templates)}")

    def get_template(self, template_name):
        """Get a template by name from the in-memory dictionary."""
        if not template_name:
            print("DEBUG: get_template called with empty name")
            return None

        # Ensure templates are loaded if dict is empty
        if not self.templates:
             print("WARN: Templates dictionary is empty. Attempting to load.")
             self.load_templates()

        # Try exact match first
        template = self.templates.get(template_name)
        if template:
            return template

        # Try case-insensitive match if exact match fails
        template_name_lower = template_name.lower()
        for key, value in self.templates.items():
            if key.lower() == template_name_lower:
                return value

        print(f"DEBUG: Template not found: {template_name}")
        return None

    def filter_templates(self, search_term=None, category=None):
        """Filter templates based on search term and category."""
        # Ensure templates are loaded
        if not self.templates:
             self.load_templates()

        filtered_templates = []
        search_term_lower = search_term.lower() if search_term else None
        category_lower = category.lower() if category else None

        for template in self.templates.values(): # Iterate through template dict values
            match = True
            # Filter by search term (in name or description or tags)
            if search_term_lower:
                name_match = search_term_lower in template.get("name", "").lower()
                desc_match = search_term_lower in template.get("description", "").lower()
                tag_match = any(search_term_lower in tag.lower() for tag in template.get("tags", []))
                if not (name_match or desc_match or tag_match):
                     match = False
                     continue # Skip if search term doesn't match

            # Filter by category
            if category_lower:
                 # Allow filtering by "All" or "Uncategorized"
                template_category = template.get("category", "Uncategorized").lower()
                if category_lower not in ["all", template_category]:
                     # Special check for "Uncategorized" filter when template has no category
                     if not (category_lower == "uncategorized" and template_category == "uncategorized"):
                          match = False
                          continue # Skip if category doesn't match

            if match:
                 filtered_templates.append(template)

        # Sort results alphabetically by name
        filtered_templates.sort(key=lambda x: x.get('name', '').lower())
        return filtered_templates

    def save_template(self, template_data):
        """
        Save a template dictionary to the templates directory and cache its files
        
        Args:
            template_data (dict): The template data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not isinstance(template_data, dict):
                print("ERROR: Template data must be a dictionary")
                return False
                
            # Get template name
            name = template_data.get("name")
            if not name:
                print("ERROR: Template name is required")
                return False
                
            # Start debug message
            print(f"DEBUG: TemplateIO: Starting save_template for '{name}'")
            
            # Skip extraction of files if this is called from import_template
            # Files would have already been processed and added to the template_data
            if 'files' not in template_data or not template_data.get('files'):
                # Extract all files from the structure and cache them
                files_array = []
                
                # Try to extract files from the structure and if provided, any files_to_cache
                structure = template_data.get("structure")
                files_to_cache = template_data.get("files_to_cache", {})
                
                # Extract folder structure to process reference files
                self.structure_ops._extract_files_from_structure(structure, files_array, files_to_cache)
                print(f"DEBUG: TemplateIO: Extracted {len(files_array)} file entries from structure and files_to_cache.")
                
                # Set of already processed file paths to avoid duplicates
                processed_files = set()
                
                # Process the files - cache them to appropriate directories
                updated_files_array = []
                if self.file_cache_manager:
                    # Get a clean template name for filesystem use
                    safe_name = name.replace(' ', '_').replace('/', '_').replace('\\', '_')
                    print(f"DEBUG: TemplateIO: Caching files for template '{safe_name}'")
                    
                    for file_info in files_array:
                        # Skip if we've already processed this file
                        file_path = file_info.get('path', '')
                        if file_path in processed_files:
                            print(f"DEBUG: TemplateIO: Skipping duplicate file path: {file_path}")
                            continue
                        
                        # Get original file path and folder information
                        original_path = file_info.get('original_path', '')
                        folder_path = file_info.get('folder', '')
                        
                        # If no folder path but we have a file_path with directories, extract folder from path
                        if not folder_path and '/' in file_path:
                            folder_path = os.path.dirname(file_path)
                            file_info['folder'] = folder_path
                        
                        # Check if this is a valid file path or an import reference
                        is_import_reference = isinstance(original_path, str) and original_path.startswith("Imported from:")
                        if is_import_reference:
                            print(f"DEBUG: TemplateIO: Skipping cached file from import: {original_path}")
                            # For imported files, just add to the updated array without re-caching
                            updated_files_array.append(file_info)
                            processed_files.add(file_path)
                            continue
                        
                        # Skip invalid files
                        if not original_path or not os.path.exists(original_path):
                            print(f"DEBUG: TemplateIO: Skipping file with invalid original path: {original_path}")
                            continue
                        
                        # Cache the file to the hierarchical structure in cache
                        cached_path = self.file_cache_manager.cache_file(
                            file_path=original_path,
                            template_name=safe_name,
                            folder_path=folder_path,
                            rename_flag=file_info.get('rename_flag', False),
                            file_metadata=file_info
                        )
                        
                        if cached_path:
                            # Update file info with cached path
                            file_info['cached_path'] = cached_path
                            updated_files_array.append(file_info)
                            processed_files.add(file_path)
                        else:
                            print(f"DEBUG: TemplateIO: Failed to cache file: {original_path}")
                else:
                    updated_files_array = files_array
                    
                print(f"DEBUG: TemplateIO: Final files_array count for JSON: {len(updated_files_array)}")
                
                # Update the template data with the cached files only if we extracted new files
                if updated_files_array:
                    template_data["files"] = updated_files_array
            else:
                # Even when files are already in the template_data, we need to process imported files correctly
                files_array = template_data.get("files", [])
                structure = template_data.get("structure", [])
                
                # Function to find original path in structure
                def find_original_path_in_structure(items, file_name, folder_path):
                    if not items:
                        return None
                        
                    for item in items:
                        if item.get('type') == 'folder' and item.get('name') == folder_path.split('/')[0]:
                            # Check children of this folder
                            children = item.get('children', [])
                            
                            # If this is a multi-level folder path, recurse into the structure
                            folder_parts = folder_path.split('/')
                            if len(folder_parts) > 1:
                                sub_folder_path = '/'.join(folder_parts[1:])
                                return find_original_path_in_structure(children, file_name, sub_folder_path)
                            
                            # Otherwise look for the file in this folder's direct children
                            for child in children:
                                if child.get('type') == 'file' and child.get('name') == file_name:
                                    return child.get('original_path')
                        
                        # Also check if this is a top-level file
                        if item.get('type') == 'file' and item.get('name') == file_name and not folder_path:
                            return item.get('original_path')
                    
                    return None
                
                for file_info in files_array:
                    file_name = file_info.get('file_name', '')
                    folder_path = file_info.get('folder', '')
                    original_path = file_info.get('original_path', '')
                    
                    # Check if this is from an import (starts with "Imported from:")
                    if isinstance(original_path, str) and original_path.startswith("Imported from:"):
                        # Try to find the true original path in the structure
                        true_original_path = find_original_path_in_structure(structure, file_name, folder_path)
                        
                        if true_original_path:
                            print(f"DEBUG: TemplateIO: Updating original path for {file_name} from '{original_path}' to '{true_original_path}'")
                            file_info['original_path'] = true_original_path
                        
                    # Make sure cached_path is accurate and exists
                    cached_path = file_info.get('cached_path', '')
                    if cached_path and not os.path.exists(cached_path):
                        print(f"WARNING: TemplateIO: Cached file doesn't exist at expected path: {cached_path}")
                        # You could take additional actions here if needed
            
            # Set the template's cached_path to the base cache directory
            template_data["cached_path"] = self.paths.get("cache_dir")
            
            # Preserve creation time if template already exists
            sanitized_name = name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            file_path = os.path.join(self.paths["templates_dir"], f"{sanitized_name}.json")
            
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        existing_data = json.load(f)
                        if existing_data and 'created' in existing_data:
                            template_data['created'] = existing_data['created']
                            print(f"DEBUG: TemplateIO: Preserved creation time from {file_path}")
                except Exception as e:
                    print(f"WARNING: Could not read existing template file: {e}")
            
            # If no creation time is set, add it now
            if 'created' not in template_data:
                template_data['created'] = time.time()
                
            # Always update modification time
            template_data['modified'] = time.time()
            
            # Save the template to disk
            template_data['file_path'] = file_path
            success = save_json_file(file_path, template_data)
            
            if success:
                # Add or update template in memory dictionary
                self.templates[name] = template_data
                print(f"DEBUG: TemplateIO: Added/Updated template '{name}' in memory dict.")
                print(f"✅ TemplateIO: Successfully saved template '{name}'")
                return True
            else:
                print(f"ERROR: TemplateIO: Failed to save template '{name}' to {file_path}")
                return False
                
        except Exception as e:
            print(f"ERROR: TemplateIO: Error saving template: {e}")
            import traceback
            traceback.print_exc()
            return False

    def delete_template(self, template_name):
        """Deletes a template's JSON file, its cache directory, and removes it from memory."""
        if not template_name:
            print("ERROR: TemplateIO: Cannot delete template with empty name.")
            return False, "Template name is required."

        print(f"DEBUG: TemplateIO: Attempting to delete template '{template_name}'")

        # 1. Find the template data (case-insensitive)
        template_data = self.get_template(template_name)
        actual_name_in_dict = None
        sanitized_name = None

        if template_data:
            actual_name_in_dict = template_data.get('name')
            sanitized_name = sanitize_filename(actual_name_in_dict) if actual_name_in_dict else None
            print(f"DEBUG: TemplateIO: Found template in memory. Actual name: '{actual_name_in_dict}', Sanitized: '{sanitized_name}'")
        else:
            # If not found in memory, still attempt deletion using sanitized provided name
            print(f"WARN: TemplateIO: Template '{template_name}' not found in memory. Attempting filesystem delete based on sanitized provided name.")
            sanitized_name = sanitize_filename(template_name)

        if not sanitized_name:
             print("ERROR: TemplateIO: Could not determine a valid sanitized name for deletion.")
             return False, "Invalid template name for deletion."

        # Define paths based on sanitized name
        template_file_path = os.path.join(self.paths.get('templates_dir', ''), f"{sanitized_name}.json")
        cache_dir_path = None
        if self.file_cache_manager and self.file_cache_manager.cache_dir:
             cache_dir_path = os.path.join(self.file_cache_manager.cache_dir, sanitized_name)

        file_deleted = False
        cache_deleted = False
        memory_deleted = False
        structure_deleted = False # Track structure deletion attempt

        # 2. Delete Template JSON file
        if os.path.exists(template_file_path):
            try:
                os.remove(template_file_path)
                print(f"DEBUG: TemplateIO: Deleted template file: {template_file_path}")
                file_deleted = True
            except OSError as e:
                print(f"ERROR: TemplateIO: Failed to delete template file '{template_file_path}': {e}")
                # Proceed to delete other parts
        else:
            print(f"WARN: TemplateIO: Template file not found at {template_file_path}. Might be already deleted or name mismatch.")

        # 3. Delete Template Cache Directory
        if cache_dir_path and os.path.isdir(cache_dir_path):
            try:
                shutil.rmtree(cache_dir_path)
                print(f"DEBUG: TemplateIO: Deleted template cache directory: {cache_dir_path}")
                cache_deleted = True
            except Exception as e:
                print(f"WARN: TemplateIO: Failed to delete template cache directory '{cache_dir_path}': {e}")
        elif cache_dir_path:
             print(f"DEBUG: TemplateIO: Template cache directory not found at {cache_dir_path}. Skipping deletion.")
        else:
             print("DEBUG: TemplateIO: Cache directory path not determined or cache manager unavailable. Skipping deletion.")

        # 4. Delete Structure File (using structure_ops)
        # Use the actual name if found, otherwise the provided name for structure deletion attempt
        name_for_structure_delete = actual_name_in_dict if actual_name_in_dict else template_name
        try:
             # Assuming delete_custom_structure returns True on success, False otherwise
             if self.structure_ops.delete_custom_structure(name_for_structure_delete):
                 print(f"DEBUG: TemplateIO: StructureOps confirmed deletion attempt for '{name_for_structure_delete}'.")
                 structure_deleted = True # Record the attempt/success
             else:
                 print(f"DEBUG: TemplateIO: StructureOps reported no deletion needed or failure for '{name_for_structure_delete}'.")
        except Exception as e:
             print(f"ERROR: TemplateIO: Exception during structure deletion call for '{name_for_structure_delete}': {e}")


        # 5. Delete from In-Memory Dictionary (if it was found initially)
        key_to_remove = None
        if template_data and actual_name_in_dict:
             # Find the actual key (could differ in case from template_name)
             name_lower = template_name.lower()
             for key in list(self.templates.keys()): # Use list to avoid runtime dict size change error
                  if key.lower() == name_lower:
                       key_to_remove = key
                       break
        if key_to_remove:
            del self.templates[key_to_remove]
            print(f"DEBUG: TemplateIO: Removed template '{key_to_remove}' from memory dict.")
            memory_deleted = True
        elif template_data: # Found data but couldn't find key? Should not happen with get_template logic
            print(f"WARN: TemplateIO: Template data for '{template_name}' existed but key not found in memory dict for deletion.")
        # No else needed if template_data was None initially

        # Return True if *any* part of the deletion was successful (or attempted)
        deleted_overall = file_deleted or cache_deleted or memory_deleted or structure_deleted
        if deleted_overall:
            print(f"INFO: TemplateIO: Finished deletion process for '{template_name}'. Success status: File={file_deleted}, Cache={cache_deleted}, Memory={memory_deleted}, Structure={structure_deleted}")
            return True, f"Template '{template_name}' deleted."
        else:
            print(f"ERROR: TemplateIO: Template '{template_name}' could not be found or no parts could be deleted.")
            return False, f"Template '{template_name}' not found or deletion failed."

    def rename_template(self, old_name, new_name):
        """Renames a template including its file, cache, structure, and memory entry."""
        print(f"DEBUG: TemplateIO: Renaming template '{old_name}' to '{new_name}'")

        if not old_name or not new_name:
            return False, "Old and new names are required."
        if old_name.strip().lower() == new_name.strip().lower():
            print(f"INFO: TemplateIO: Rename request invalid (names '{old_name}' and '{new_name}' are effectively the same). Skipping.")
            # If only case changed, could update metadata, but save_template handles this via is_rename=True
            return False, "New name is the same as the old name (case-insensitive)."

        old_name_clean = old_name.strip()
        new_name_clean = new_name.strip()

        # 1. Find the template using case-insensitive search
        template_data = self.get_template(old_name_clean)
        if not template_data:
             print(f"ERROR: TemplateIO: Template '{old_name_clean}' not found for renaming.")
             return False, f"Template '{old_name_clean}' not found."

        # Get the exact original name as stored in the dictionary key/data
        exact_old_name = template_data.get('name')
        if not exact_old_name:
             print("ERROR: TemplateIO: Found template data has no 'name' field. Cannot proceed.")
             return False, "Template data is missing the 'name' field."

        # 2. Use save_template to handle the rename logic
        # Pass the exact old name as original_name
        # Keep other metadata from the existing template
        save_success, message = self.save_template(
            template_name=new_name_clean,
            structure=template_data.get('structure'),
            category=template_data.get('category'),
            description=template_data.get('description'),
            tags=template_data.get('tags'),
            template_type=template_data.get('type'),
            original_name=exact_old_name, # Crucial: pass the original name for cleanup
            files_to_cache=None # Let save_template re-evaluate files based on structure
        )

        if save_success:
            print(f"✅ TemplateIO: Successfully renamed template '{exact_old_name}' to '{new_name_clean}' via save_template.")
            return True, message
        else:
            print(f"ERROR: TemplateIO: Rename failed during save_template call for '{exact_old_name}' -> '{new_name_clean}'. Message: {message}")
            # save_template should ideally handle its own rollback if possible,
            # but state might be inconsistent here.
            return False, f"Failed to rename: {message}"


    def duplicate_template(self, original_template_name):
        """Duplicates an existing template, creating new files, cache, and memory entry."""
        print(f"[DEBUG] TemplateIO: Attempting to duplicate template: '{original_template_name}'")

        # 1. Get original template data
        original_data = self.get_template(original_template_name)
        if not original_data:
            print(f"[ERROR] TemplateIO: Original template '{original_template_name}' not found for duplication.")
            return False, f"Original template '{original_template_name}' not found."

        exact_original_name = original_data.get('name', original_template_name) # Fallback just in case

        # 2. Determine new unique name
        existing_names_lower = {name.lower() for name in self.templates.keys()}
        base_name = exact_original_name
        # Regex to find ' copy' or ' copy N' at the end (case-insensitive)
        match_copy = re.match(r"^(.*?) copy(?: (\d+))?$", exact_original_name, re.IGNORECASE)
        start_counter = 1
        if match_copy:
             base_name = match_copy.group(1).strip()
             num_str = match_copy.group(2)
             start_counter = int(num_str) + 1 if num_str else 2 # Start with 'copy 2' or N+1
             print(f"[DEBUG] TemplateIO: Detected copy name: Base='{base_name}', Next counter={start_counter}")

        counter = start_counter
        new_name = "" # Initialize new_name
        while True:
            suffix = f" copy"
            if counter > 1:
                 suffix += f" {counter}"
            potential_new_name = f"{base_name}{suffix}"

            if potential_new_name.lower() not in existing_names_lower:
                new_name = potential_new_name
                break
            counter += 1
            if counter > 1000: # Safety break
                 print("[ERROR] TemplateIO: Could not find a unique name after 1000 attempts.")
                 return False, "Could not determine a unique name for the duplicate."

        new_sanitized_name = sanitize_filename(new_name)
        print(f"[DEBUG] TemplateIO: Determined new name: '{new_name}' (Sanitized: '{new_sanitized_name}')")

        # 3. Create new template data (deep copy)
        try:
            new_data = copy.deepcopy(original_data)
        except Exception as e:
            print(f"[ERROR] TemplateIO: Failed to deep copy template data: {e}")
            return False, f"Failed to copy template data: {e}"

        # 4. Use save_template to create the new template
        # This leverages the file caching, structure extraction, and saving logic
        # We pass the deep-copied structure and other relevant fields.
        # Crucially, original_name is None, indicating a new save, not a rename.
        save_success, message = self.save_template(
            template_name=new_name, # The newly generated unique name
            structure=new_data.get('structure'), # The copied structure
            category=new_data.get('category'),
            description=new_data.get('description'),
            tags=new_data.get('tags'),
            template_type=new_data.get('type'),
            original_name=None, # Indicate this is a new template save
            files_to_cache=None # Let save_template find files from structure (important for cache copy)
        )

        if save_success:
             print(f"[INFO] TemplateIO: Successfully duplicated template '{original_template_name}' as '{new_name}' using save_template.")
             # The save_template call already updated self.templates
             # Fetch the created template data again for the return value.
             created_template_data = self.get_template(new_name)
             return True, new_name # Return success and the new name
        else:
             print(f"[ERROR] TemplateIO: Duplication failed during save_template call for new template '{new_name}'. Message: {message}")
             # Rollback is difficult here as save_template might have partially completed.
             # Attempt to delete the potentially created template as cleanup.
             self.delete_template(new_name) # Use delete_template which handles file/cache/memory
             return False, f"Failed to save duplicated template: {message}" 