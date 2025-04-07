import os
import json
import shutil
import time
from pathlib import Path

from app.templates.template_utils import _guess_file_type # Import necessary utils

# Import utility functions
try:
    from app.utils.utils import normalize_path_for_storage
except ImportError:
    # Fallback if not available
    def normalize_path_for_storage(path):
        """Normalize a path for storage with forward slashes"""
        if not path:
            return ""
        norm_path = os.path.normpath(path)
        return norm_path.replace('\\', '/')

class TemplateStructureOps:
    """Handles operations related to template folder structures."""

    def __init__(self, paths):
        """Initialize with required paths."""
        self.paths = paths
        # Initialize custom structures list/dict
        self.custom_structures = [] 
        # self.load_custom_structures() # REMOVED: Prevent auto-load on init

    def get_default_structure(self, project_type):
        """Get the default directory structure for a project type (OBSOLETE)

        Returns an empty list as default structures are no longer centrally defined.
        Templates should manage their own structures.
        """
        print(f"WARN: get_default_structure called for type '{project_type}'. This method is obsolete and returns an empty structure.")
        # Return an empty list as default structures are no longer defined here
        return []

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
            # Adjust check for list format
            found_in_memory = None
            for struct_data in self.custom_structures:
                if isinstance(struct_data, dict) and struct_data.get('name') == name_to_try:
                     found_in_memory = struct_data
                     break
            
            if found_in_memory:
                print(f"DEBUG: Found custom structure in memory: {name_to_try}")
                # Return the 'structure' field which holds the actual list/dict
                return found_in_memory.get('structure', [])

            # Check on disk
            custom_structure_path = os.path.join(self.paths["custom_structures_dir"], f"{name_to_try}.json")
            if os.path.exists(custom_structure_path):
                try:
                    with open(custom_structure_path, 'r') as f:
                        structure_data = json.load(f)
                        print(f"DEBUG: Found custom structure on disk: {name_to_try}")
                        # Return the 'structure' field if it exists
                        return structure_data.get('structure', [])
                except Exception as e:
                    print(f"Error loading structure {name_to_try}: {e}")

        print(f"DEBUG: Structure not found: {structure_name}")
        return []

    def _extract_files_from_structure(self, structure, files_array, files_to_cache=None, parent_path=""):
        """
        Recursively extract file items from a structure and add them to the files array
        
        Args:
            structure: The structure to extract files from
            files_array: Array to append the files to
            files_to_cache (dict, optional): Dictionary of files staged for caching (e.g., from editor).
            parent_path: Parent path for nested items
        """
        if not structure:
            return

        files_to_cache = files_to_cache or {} # Ensure it's a dict
            
        # Print debug information
        print(f"DEBUG: Extracting files from structure at folder '{parent_path}'")
        print(f"DEBUG: Structure at this level has {len(structure)} items")
        
        # First, check files_to_cache directly if at the root level and provided
        if parent_path == "" and files_to_cache:
            print(f"DEBUG: Root level - checking provided files_to_cache ({len(files_to_cache)} items)")
            
            # Process each file in files_to_cache
            for rel_path, file_data in files_to_cache.items():
                if isinstance(file_data, dict) and 'original_path' in file_data and file_data['original_path']:
                    original_path = file_data['original_path']
                    if os.path.exists(original_path):
                        file_name = os.path.basename(original_path)
                        
                        # Determine folder path from relative_path if available
                        folder = file_data.get('relative_path', "")
                        if folder: # Ensure trailing slash if not empty
                            folder += '/' 
                        elif '/' in rel_path: # Fallback to dirname from rel_path
                            folder = os.path.dirname(rel_path) + '/'
                        
                        print(f"DEBUG: Adding file from files_to_cache: {file_name} in folder {folder}")
                        
                        # Create file info
                        file_info = {
                            'file_name': file_name,
                            'folder': folder,
                            'original_path': original_path,
                            'file_type': _guess_file_type(file_name),
                            'size': os.path.getsize(original_path),
                            'is_binary': file_data.get('is_binary', False),
                            'path': normalize_path_for_storage(os.path.join(folder, file_name))
                        }
                        
                        # Add rename flag if filename contains project name variable
                        if '${PROJECT_NAME}' in file_name:
                            file_info['rename_flag'] = True
                            file_info['uses_project_name'] = True
                        
                        # Check if this file is already in files_array (prevent duplicates)
                        exists = any(existing.get('original_path') == original_path for existing in files_array)
                        
                        if not exists:
                            files_array.append(file_info)
        
        # Debug dump the complete structure at this level
        # print(f"DEBUG: Content of structure at level '{parent_path}':")
        # for i, item in enumerate(structure):
        #     if isinstance(item, dict):
        #         print(f"DEBUG: Item {i}: type={item.get('type')}, name={item.get('name')}")
        #     else:
        #         print(f"DEBUG: Item {i}: {item}")
        
        # Loop through the items in the structure list/dict
        items_to_process = []
        if isinstance(structure, list):
            items_to_process = structure
        elif isinstance(structure, dict): # Handle dict format like {"Folder": [...]} 
            for folder_name, children in structure.items():
                 # Treat as a folder entry
                 items_to_process.append({'name': folder_name, 'type': 'folder', 'children': children})

        for item in items_to_process:
            if not isinstance(item, dict): # Skip non-dict items (e.g., simple filenames not yet converted)
                 print(f"DEBUG: Skipping non-dict item in structure: {item}")
                 continue

            if item.get('type') == 'file':
                folder = parent_path # Folder path relative to template root
                file_name = item.get('name', '')
                
                print(f"DEBUG: Processing file item: {file_name} with user_data: {item.get('user_data', 'None')}")
                
                # Get the file's original path if available directly in the item
                original_path = item.get('original_path', '')
                
                # If no original path in item, check user_data (common in UI drag/drop)
                if not original_path and 'user_data' in item:
                    user_data = item['user_data']
                    if isinstance(user_data, dict):
                        original_path = user_data.get('original_path', '')
                
                # If still no original path and we have files_to_cache, try to find it there
                if not original_path and files_to_cache:
                    # Construct the relative path as known within the structure
                    rel_path_in_structure = normalize_path_for_storage(os.path.join(parent_path, file_name))
                    
                    # Check if this relative path exists in files_to_cache
                    if rel_path_in_structure in files_to_cache:
                        cache_data = files_to_cache[rel_path_in_structure]
                        original_path = cache_data.get('original_path', '')
                        print(f"DEBUG: Found file in files_to_cache via rel_path: {rel_path_in_structure} -> {original_path}")
                    
                    # Fallback: Check by filename only (less reliable)
                    if not original_path and file_name in files_to_cache:
                         cache_data = files_to_cache[file_name]
                         original_path = cache_data.get('original_path', '')
                         print(f"DEBUG: Found file in files_to_cache via filename only: {file_name} -> {original_path}")

                # Skip if no original path could be determined or file doesn't exist
                if not original_path:
                    print(f"DEBUG: No original path could be determined for file item: {file_name}, skipping")
                    continue
                if not os.path.exists(original_path):
                    print(f"DEBUG: Original path file does not exist: {original_path}, skipping {file_name}")
                    continue
                
                print(f"DEBUG: Adding file item from structure: {file_name} to folder: {folder}")
                
                # Get file info
                file_info = {
                    'file_name': file_name,
                    'folder': folder,
                    'original_path': original_path,
                    'file_type': _guess_file_type(file_name),
                    'size': os.path.getsize(original_path),
                    'is_binary': item.get('is_binary', False),
                    'path': normalize_path_for_storage(os.path.join(folder, file_name))
                }
                
                # Add rename flag if filename contains project name variable
                if '${PROJECT_NAME}' in file_name:
                    file_info['rename_flag'] = True
                    file_info['uses_project_name'] = True
                
                # Check if the file (by original_path) is already in the files_array to prevent duplicates
                exists = any(existing.get('original_path') == original_path for existing in files_array)
                
                if not exists:
                    files_array.append(file_info)
            
            # If folder with children, recursively process
            elif item.get('type') == 'folder' and 'children' in item:
                folder_name = item.get('name', '')
                if folder_name: # Only append folder name if it exists
                    new_parent = normalize_path_for_storage(os.path.join(parent_path, folder_name))
                    self._extract_files_from_structure(item.get('children', []), files_array, files_to_cache, new_parent)
                else:
                     print(f"WARN: Folder item without a name encountered at path '{parent_path}'")
                     # Process children at the current path if no folder name
                     self._extract_files_from_structure(item.get('children', []), files_array, files_to_cache, parent_path)

    def _clean_structure_files(self, structure):
        """
        Clean up file details in the structure, leaving only essential information
        
        Args:
            structure: The structure dictionary or list
        """
        if not structure:
            return structure # Return structure as is if None or empty
        
        # Handle list format
        if isinstance(structure, list):
            cleaned_list = []
            for item in structure:
                cleaned_item = self._clean_structure_files(item) # Recursively clean items
                if cleaned_item is not None: # Avoid adding None if cleaning fails
                    cleaned_list.append(cleaned_item)
            return cleaned_list
        
        # Handle dictionary format
        elif isinstance(structure, dict):
            # Case 1: Modern format {'type': 'folder'/'file', 'name': ..., ...}
            if 'type' in structure and 'name' in structure:
                item_type = structure.get('type')
                if item_type == 'folder' and 'children' in structure:
                     # Clean children recursively
                     structure['children'] = self._clean_structure_files(structure.get('children', []))
                     # Keep essential folder keys (can add more if needed)
                     keys_to_keep = ['name', 'type', 'children']
                     return {k: v for k, v in structure.items() if k in keys_to_keep}
                elif item_type == 'file':
                    # Keep essential file keys
                    keys_to_keep = ['name', 'type', 'rename_flag', 'uses_project_name', 'original_name', 'original_extension']
                    return {k: v for k, v in structure.items() if k in keys_to_keep}
                else: # Unknown type or folder without children
                    return structure # Return as is
            # Case 2: Legacy format {'FolderName': [...children...]}
            elif len(structure) == 1:
                folder_name = list(structure.keys())[0]
                children = list(structure.values())[0]
                if isinstance(children, list):
                    # Clean children and return in the same format
                    return {folder_name: self._clean_structure_files(children)}
                else: # Malformed legacy format
                    return {folder_name: []} # Return with empty children list
            else: # Unknown dictionary format
                return structure # Return as is
        
        # Handle simple string items (usually filenames in legacy lists)
        elif isinstance(structure, str):
             return structure # Keep simple strings as they are
        
        # Return None or original for unexpected types to avoid errors
        print(f"WARN: _clean_structure_files encountered unexpected type: {type(structure)}")
        return structure 


    def save_custom_structure(self, name, structure):
        """Save a custom folder structure to disk and update in-memory list."""
        if not name or not structure:
            print(f"ERROR: Cannot save custom structure. Invalid name or structure provided.")
            return False
            
        print(f"INFO: Saving custom structure '{name}'")
        
        # Ensure custom_structures is initialized as a list
        if not hasattr(self, 'custom_structures') or not isinstance(self.custom_structures, list):
            self.custom_structures = []
            
        # Prepare a safe structure (deep copy and basic validation)
        try:
            # Use json dumps/loads for serialization check and deep copy
            safe_structure = json.loads(json.dumps(structure))
        except (TypeError, json.JSONDecodeError, RecursionError) as e:
            print(f"ERROR: Failed to save custom structure '{name}': Structure is not serializable or too deep. Error: {e}")
            return False
        except Exception as e:
            print(f"ERROR: Failed to process custom structure '{name}' for saving: {e}")
            return False
            
        # Sanitize the filename for disk operations
        # Use the utility function for consistency if available, otherwise basic replace
        try:
            from .template_utils import sanitize_filename
            sanitized_name = sanitize_filename(name) 
        except ImportError:
            print("WARN: template_utils not found, using basic sanitization for structure filename.")
            sanitized_name = name.replace(' ', '_').replace('/', '-').replace('\\', '-')
        
        if not sanitized_name:
            print(f"ERROR: Structure name '{name}' resulted in empty sanitized name. Cannot save.")
            return False

        existing_creation_time = None
        existing_found_index = -1
        
        # Check if it exists in the in-memory list
        for i, s in enumerate(self.custom_structures):
            if isinstance(s, dict) and s.get("name") == name:
                existing_creation_time = s.get("created", time.time())
                existing_found_index = i
                break
                
        file_path = os.path.join(self.paths["custom_structures_dir"], f"{sanitized_name}.json")
        
        # If not found in memory, check if file exists on disk to preserve creation time
        if existing_found_index == -1 and os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    existing_data = json.load(f)
                    existing_creation_time = existing_data.get("created", time.time())
            except Exception as e:
                print(f"WARNING: Error reading existing structure file '{file_path}': {e}")
                existing_creation_time = time.time() # Default to now if read fails
        elif existing_found_index == -1:
            # It's a new structure (not in memory, not on disk)
            existing_creation_time = time.time()
            
        # Prepare data to save (both in memory and file)
        structure_data_to_save = {
            "name": name,
            "structure": safe_structure,
            "modified": time.time(),
            "created": existing_creation_time
        }
            
        # Save to disk
        try:
            os.makedirs(self.paths["custom_structures_dir"], exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(structure_data_to_save, f, indent=2)
                
            status = "Updated" if existing_found_index != -1 else "Created"
            print(f"INFO: Successfully {status.lower()} custom structure '{name}' to {file_path}")
            
            # Update in-memory list
            if existing_found_index != -1:
                self.custom_structures[existing_found_index] = structure_data_to_save
                print(f"INFO: Updated in-memory custom structure '{name}'")
            else:
                self.custom_structures.append(structure_data_to_save)
                print(f"INFO: Added new custom structure '{name}' to memory")

            # Optional: Cleanup old file if name sanitized differently (rare for structures)
            # if existing_found_index != -1 and name != sanitized_name: ...
            
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to save custom structure '{name}' to disk path '{file_path}': {e}")
            # Attempt to rollback memory change if add failed
            if existing_found_index == -1:
                self.custom_structures = [s for s in self.custom_structures if s.get("name") != name]
            return False

    def get_custom_structure(self, name):
        """
        Get a custom structure by name from the in-memory list.
        Ensures structures are loaded if the list is empty.
        
        Args:
            name (str): Name of the custom structure
            
        Returns:
            dict: The structure data (the actual list/dict), or None if not found
        """
        # Ensure structures are loaded if the list is currently empty
        if not hasattr(self, 'custom_structures') or not self.custom_structures:
            print("INFO: Custom structures list is empty, attempting to load.")
            self.load_custom_structures()
            
        # Find the structure in the custom structures list (which contains dicts)
        for structure_data in self.custom_structures:
            if isinstance(structure_data, dict) and structure_data.get("name") == name:
                print(f"INFO: Found custom structure '{name}' in memory.")
                # Return the actual structure part
                return structure_data.get("structure") 
                
        print(f"INFO: Custom structure '{name}' not found in memory.")
        return None
        
    def save_structure(self, name, structure):
        """
        Save a structure (alias for save_custom_structure).
        Adds basic check for recursion before saving.
        
        Args:
            name (str): Name of the structure
            structure (list or dict): The structure data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Basic check for self-reference (simplistic, might not catch all cases)
            if isinstance(structure, list) and structure in structure:
                 print(f"ERROR: Potential recursion detected in structure '{name}'. Cannot save.")
                 return False
            # Add more complex recursion checks if needed

            # Attempt to save using the main method
            return self.save_custom_structure(name, structure)
            
        except RecursionError:
             print(f"ERROR: RecursionError while trying to save structure '{name}'.")
             return False
        except Exception as e:
            print(f"ERROR: Unexpected error during save_structure '{name}': {e}")
            return False
            
    def _create_safe_structure(self, structure):
        """Convert structure to a safely serializable format using JSON."""
        try:
            # Using json dumps/loads is a robust way to check serializability
            # and create a deep copy without complex object references.
            return json.loads(json.dumps(structure))
        except (TypeError, RecursionError) as e:
             print(f"WARN: Structure could not be made safe via JSON: {e}. Returning original structure.")
             return structure # Fallback to original if conversion fails
        except Exception as e:
             print(f"WARN: Unexpected error in _create_safe_structure: {e}. Returning original structure.")
             return structure
        
    def load_custom_structures(self):
        """Load custom structures from the dedicated directory into memory."""
        # Ensure the target attribute exists and is a list
        if not hasattr(self, 'custom_structures') or not isinstance(self.custom_structures, list):
            self.custom_structures = []
        else:
             # Clear existing list before loading to avoid duplicates if called multiple times
             self.custom_structures.clear()
            
        structures_dir = self.paths.get("custom_structures_dir")
        if not structures_dir:
             print("ERROR: 'custom_structures_dir' not found in paths config. Cannot load structures.")
             return self.custom_structures # Return empty list

        if not os.path.exists(structures_dir):
            try:
                os.makedirs(structures_dir, exist_ok=True)
                print(f"INFO: Created custom structures directory: {structures_dir}")
            except OSError as e:
                 print(f"ERROR: Failed to create custom structures directory '{structures_dir}': {e}")
                 return self.custom_structures # Return empty list
            return self.custom_structures
            
        # Load all structure JSON files
        loaded_count = 0
        for filename in os.listdir(structures_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(structures_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        structure_data = json.load(f)
                        
                    # Basic validation: check if it has 'name' and 'structure' keys
                    if isinstance(structure_data, dict) and 'name' in structure_data and 'structure' in structure_data:
                        # Check for duplicates by name before adding
                        if not any(s.get('name') == structure_data['name'] for s in self.custom_structures):
                            self.custom_structures.append(structure_data)
                            loaded_count += 1
                            print(f"INFO: Loaded custom structure '{structure_data.get('name')}' from {filename}")
                        else:
                            print(f"WARN: Duplicate custom structure name '{structure_data.get('name')}' found in {filename}. Skipping.")
                    else:
                         print(f"WARN: Skipping invalid structure file (missing name/structure): {filename}")
                except json.JSONDecodeError as e:
                    print(f"ERROR: Failed to decode JSON from {filename}: {e}")
                except Exception as e:
                    print(f"ERROR: Failed to load custom structure from {filename}: {e}")
                    
        print(f"INFO: Loaded {loaded_count} new custom structures from {structures_dir}. Total in memory: {len(self.custom_structures)}")
        return self.custom_structures
    
    def delete_custom_structure(self, name):
        """Delete a custom folder structure file and remove from memory."""
        
        structure_to_delete = None
        index_to_delete = -1
        for i, s in enumerate(self.custom_structures):
            if isinstance(s, dict) and s.get("name") == name:
                 structure_to_delete = s
                 index_to_delete = i
                 break

        if index_to_delete == -1:
            print(f"WARN: Custom structure '{name}' not found in memory. Cannot delete.")
            # Try to delete file anyway? For robustness, let's try.
            # return False 
        
        # Determine filename (use sanitization)
        try:
            from .template_utils import sanitize_filename
            sanitized_name = sanitize_filename(name) 
        except ImportError:
            sanitized_name = name.replace(' ', '_').replace('/', '-').replace('\\', '-')

        if not sanitized_name:
             print(f"ERROR: Could not determine sanitized filename for structure '{name}'. Cannot delete file.")
             # If we found it in memory, still remove it from memory
             if index_to_delete != -1:
                 del self.custom_structures[index_to_delete]
                 print(f"INFO: Removed structure '{name}' from memory despite file deletion issues.")
             return False

        file_path = os.path.join(self.paths["custom_structures_dir"], f"{sanitized_name}.json")
        file_deleted = False
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"INFO: Deleted custom structure file: {file_path}")
                file_deleted = True
            else:
                 print(f"WARN: Custom structure file not found at {file_path}. It might have been already deleted or never saved correctly.")
                 # If it wasn't found in memory either, it likely didn't exist
                 if index_to_delete == -1:
                     return False # Indicate structure wasn't found anywhere

            # Delete associated legacy cache dir (templates_dir/cache/filename)
            # This cache seems unused/deprecated based on current code, but clean up if exists
            # cache_dir = os.path.join(self.paths.get("templates_dir", ""), "cache", sanitized_name)
            # if os.path.exists(cache_dir) and os.path.isdir(cache_dir):
            #     print(f"DEBUG: Deleting legacy cache directory for structure '{name}': {cache_dir}")
            #     shutil.rmtree(cache_dir)
            #     print(f"DEBUG: Successfully deleted legacy cache directory for structure '{name}'")
            
            # Remove from in-memory list if found
            if index_to_delete != -1:
                del self.custom_structures[index_to_delete]
                print(f"INFO: Removed custom structure '{name}' from in-memory list.")
            
            # Return True if either file was deleted or memory entry was removed
            return file_deleted or (index_to_delete != -1)

        except OSError as e:
            print(f"ERROR: Failed to delete structure file {file_path}: {e}")
            return False
        except Exception as e:
            print(f"ERROR: Unexpected error deleting structure {name}: {e}")
            return False

    def _normalize_structure_format(self, structure_items):
        """Normalize the structure format to ensure consistency.
        
        Converts various formats (list of strings, list of dicts, dict) 
        into a list of dicts: [{'type': 'file'/'folder', 'name': ...}, ...]
        
        Args:
            structure_items (list or dict): Structure items to normalize
            
        Returns:
            list: Normalized structure items as a list of dicts.
        """
        if not structure_items:
            return []
            
        normalized = []
        items_to_process = []

        if isinstance(structure_items, list):
            items_to_process = structure_items
        elif isinstance(structure_items, dict):
             # Convert {"Folder": [...]} to [{'name': 'Folder', 'type':'folder', 'children': [...]}]
             for name, children in structure_items.items():
                 items_to_process.append({'name': name, 'type': 'folder', 'children': children if isinstance(children, list) else []})

        for item in items_to_process:
            # Handle dictionaries directly (already in new format or close)
            if isinstance(item, dict):
                # Ensure 'type' exists, guess if possible
                if 'type' not in item:
                     if 'children' in item: # Assume folder if it has children
                         item['type'] = 'folder'
                     elif 'name' in item: # Assume file if it has a name but no children
                         # Basic check for extension, default to file
                         item['type'] = 'folder' if '.' not in item['name'] else 'file' 
                     else:
                          # Cannot determine type, skip?
                          print(f"WARN: Skipping dict item without type/name: {item}")
                          continue 
                
                # Ensure 'name' exists
                if 'name' not in item:
                    print(f"WARN: Skipping dict item without name: {item}")
                    continue
                
                # Recursively normalize children if it's a folder
                if item.get('type') == 'folder':
                    item['children'] = self._normalize_structure_format(item.get('children', []))
                
                normalized.append(item)

            # Handle string items (assume file or maybe folder)
            elif isinstance(item, str):
                # Simple approach: treat as file unless it clearly looks like a folder name (no extension)
                # More robust checks could involve looking for slashes, etc.
                item_type = 'folder' if '.' not in item and '/' not in item and '\\' not in item else 'file'
                entry = {'name': item, 'type': item_type}
                if item_type == 'folder':
                    entry['children'] = [] # Add empty children list for folders
                normalized.append(entry)
            
            else:
                print(f"WARN: Skipping unrecognized item type in structure: {type(item)} - {item}")
                
        return normalized 