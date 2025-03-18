#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

import os
import datetime
import json

from app.utils.utils import save_json_file

class StructureOperations:
    """
    Operations for managing custom folder structures
    """
    
    def save_custom_structure(self, name, structure=None):
        """
        Save a custom folder structure
        - name: the name of the structure
        - structure: the folder structure (list of directory objects)
        
        Returns True if successful, False otherwise
        """
        try:
            # Use empty list as default if no structure provided
            if structure is None:
                structure = []
            
            # Create structure dictionary
            structure = {
                "name": name,
                "directories": structure if isinstance(structure, list) else [structure],
                "created": datetime.datetime.now().isoformat()
            }
            
            # Create a clean filename - replace spaces with underscores and remove any / or \ characters
            # Also remove apostrophes to avoid filename issues
            filename = name.replace(" ", "_").replace("/", "-").replace("\\", "-").replace("'", "")
            
            # Create directory if it doesn't exist
            os.makedirs(self.paths["custom_structures_dir"], exist_ok=True)
            
            # Set file path
            file_path = os.path.join(self.paths["custom_structures_dir"], f"{filename}.json")
            
            print(f"[DEBUG] StructureOps: Saving custom structure '{name}' to file '{file_path}'")
            
            # Save to file
            success = save_json_file(file_path, structure)
            
            if success:
                # Initialize custom_structures as a dictionary if it doesn't exist
                if not hasattr(self, 'custom_structures'):
                    self.custom_structures = {}
                
                # Store in dictionary using name as key
                self.custom_structures[name] = structure
            
            return success
        except Exception as e:
            print(f"[DEBUG] StructureOps: Error saving structure: {e}")
            return False
    
    def delete_custom_structure(self, name):
        """Delete a custom folder structure"""
        if name not in self.custom_structures:
            return False
        
        # Create a clean filename
        filename = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        file_path = os.path.join(self.paths["custom_structures_dir"], f"{filename}.json")
        
        try:
            # Delete the structure file
            os.remove(file_path)
            
            # Delete associated cache directory
            cache_dir = os.path.join(self.paths["templates_dir"], "cache", filename)
            if os.path.exists(cache_dir):
                print(f"DEBUG: Deleting cache directory for structure '{name}': {cache_dir}")
                import shutil
                shutil.rmtree(cache_dir)
                print(f"DEBUG: Successfully deleted cache directory for structure '{name}'")
            
            # Remove from in-memory dictionary
            del self.custom_structures[name]
            return True
        except Exception as e:
            print(f"Error deleting structure {name}: {e}")
            return False
    
    def get_structures(self):
        """Get a list of all available folder structures"""
        # Return the names of all custom structures
        custom_structures = list(self.custom_structures.keys())
        
        # Add built-in structures from constants
        from app.constants import DEFAULT_STRUCTURES
        all_structures = list(DEFAULT_STRUCTURES.keys()) + custom_structures
        
        # Filter out duplicates and sort
        return sorted(list(set(all_structures)))
    
    def delete_structure(self, structure_name):
        """Delete a folder structure by name"""
        # Check if it's a built-in structure (which can't be deleted)
        from app.constants import DEFAULT_STRUCTURES
        if structure_name.lower() in DEFAULT_STRUCTURES:
            print(f"Cannot delete built-in structure: {structure_name}")
            return False
        
        # Try to delete as a custom structure
        return self.delete_custom_structure(structure_name)
    
    def rename_custom_structure(self, old_name, new_name):
        """Rename a custom structure"""
        if old_name == new_name:
            return True
        
        if old_name in self.custom_structures:
            # Create a clean filename for both old and new
            old_filename = old_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
            new_filename = new_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
            
            old_path = os.path.join(self.paths["custom_structures_dir"], f"{old_filename}.json")
            new_path = os.path.join(self.paths["custom_structures_dir"], f"{new_filename}.json")
            
            # Cache directory paths
            old_cache_dir = os.path.join(self.paths["templates_dir"], "cache", old_filename)
            new_cache_dir = os.path.join(self.paths["templates_dir"], "cache", new_filename)
            
            try:
                # Get the structure
                structure = self.custom_structures[old_name]
                
                # Update the name
                structure["name"] = new_name
                
                # Save to new file
                save_json_file(new_path, structure)
                
                # Remove old file
                if os.path.exists(old_path):
                    os.remove(old_path)
                
                # Rename cache directory if it exists
                import shutil
                if os.path.exists(old_cache_dir):
                    print(f"DEBUG: Renaming cache directory from '{old_cache_dir}' to '{new_cache_dir}'")
                    
                    # Create parent directory if needed
                    os.makedirs(os.path.dirname(new_cache_dir), exist_ok=True)
                    
                    # If new directory already exists, remove it first
                    if os.path.exists(new_cache_dir):
                        print(f"DEBUG: Removing existing cache directory: {new_cache_dir}")
                        shutil.rmtree(new_cache_dir)
                    
                    # Rename directory
                    shutil.move(old_cache_dir, new_cache_dir)
                    print(f"DEBUG: Successfully renamed cache directory to {new_cache_dir}")
                
                # Update in-memory dictionary
                self.custom_structures[new_name] = structure
                del self.custom_structures[old_name]
                
                return True
            except Exception as e:
                print(f"Error renaming structure {old_name} to {new_name}: {e}")
                return False
        
        return False
    
    def save_structure_from_folders(self, template_name, folder_list):
        """Save a folder structure from a list of folder names"""
        if not template_name or not folder_list:
            return False
            
        # Process folder list to remove duplicates and sort
        unique_folders = sorted(list(set(folder_list)))
        
        # Create structure with directories
        structure = {
            "name": f"Template_{template_name}",
            "directories": unique_folders,
            "created": datetime.datetime.now().isoformat()
        }
        
        # Save to file
        return self.save_custom_structure(structure["name"], unique_folders)
    
    def get_structure(self, structure_name):
        """Get a folder structure by name"""
        print(f"DEBUG: get_structure called with structure_name='{structure_name}'")
        
        # Try various possible names for the structure
        names_to_try = [structure_name]
        
        # If not starting with Template_, also try with it
        if not structure_name.startswith("Template_"):
            names_to_try.append(f"Template_{structure_name}")
            
        # Try with spaces replaced by underscores and vice versa
        if " " in structure_name:
            names_to_try.append(structure_name.replace(" ", "_"))
        if "_" in structure_name:
            names_to_try.append(structure_name.replace("_", " "))
            
        # Try with apostrophes normalized (both with and without)
        if "'" in structure_name:
            names_to_try.append(structure_name.replace("'", ""))
            
        # Try with filename-safe versions
        safe_name = structure_name.replace(" ", "_").replace("/", "-").replace("\\", "-").replace("'", "")
        if safe_name not in names_to_try:
            names_to_try.append(safe_name)
            
        # Try with Template_ prefix on the safe name
        if not safe_name.startswith("Template_"):
            names_to_try.append(f"Template_{safe_name}")

        # Also try the on-disk filename format
        filename_version = structure_name.replace(" ", "_").replace("/", "-").replace("\\", "-")
        if filename_version not in names_to_try:
            names_to_try.append(filename_version)
            
        print(f"DEBUG: Trying structure names: {names_to_try}")
        
        # Check all possible names
        for name in names_to_try:
            # Check if it's a built-in structure
            from app.constants import DEFAULT_STRUCTURES
            if name in DEFAULT_STRUCTURES:
                print(f"DEBUG: Found built-in structure: {name}")
                structure = DEFAULT_STRUCTURES[name]
                # Ensure the structure is normalized
                return self._normalize_structure_format(structure)
                
            # Check if it's in custom_structures memory
            if hasattr(self, 'custom_structures'):
                if isinstance(self.custom_structures, dict) and name in self.custom_structures:
                    print(f"DEBUG: Found custom structure in memory: {name}")
                    # Get structure data
                    structure_data = self.custom_structures[name]
                    
                    # Handle different possible formats
                    if isinstance(structure_data, dict):
                        # The most common case - a structure data dictionary with 'directories' key
                        if "directories" in structure_data:
                            structure = structure_data.get("directories", [])
                            return self._normalize_structure_format(structure)
                        # Legacy case - directory list directly in the dictionary
                        elif any(isinstance(value, list) for value in structure_data.values()):
                            # Assume first list value is the structure
                            for key, value in structure_data.items():
                                if isinstance(value, list):
                                    print(f"DEBUG: Using '{key}' as structure from legacy format")
                                    return self._normalize_structure_format(value)
                        # If all else fails, treat the entire dictionary as the structure
                        else:
                            print(f"DEBUG: Using entire dictionary as structure")
                            return self._normalize_structure_format([structure_data])
                    elif isinstance(structure_data, list):
                        # If it's already a list, normalize it directly
                        return self._normalize_structure_format(structure_data)
        
        # Also try searching the file system as a last resort
        try:
            custom_dir = self.paths["custom_structures_dir"]
            for filename in os.listdir(custom_dir):
                if filename.endswith('.json'):
                    # Skip known non-template files
                    if filename in ['folders.json', 'preferences.json']:
                        continue
                        
                    # Remove .json extension
                    file_base = filename[:-5]
                    
                    # If any variant of the name matches the file base
                    if file_base in names_to_try or any(name.replace(" ", "_") == file_base for name in names_to_try):
                        print(f"DEBUG: Found structure file on disk: {filename}")
                        file_path = os.path.join(custom_dir, filename)
                        
                        # Load the file
                        try:
                            data = load_json_file(file_path)
                            if data:
                                # Update in-memory cache
                                if not hasattr(self, 'custom_structures'):
                                    self.custom_structures = {}
                                    
                                # Get the name from the file or use filename
                                structure_name = data.get("name", file_base)
                                self.custom_structures[structure_name] = data
                                
                                # Get the structure from the data
                                if isinstance(data, dict) and "directories" in data:
                                    return self._normalize_structure_format(data["directories"])
                                elif isinstance(data, list):
                                    return self._normalize_structure_format(data)
                                else:
                                    # If all else fails, wrap the data in a list
                                    return self._normalize_structure_format([data])
                        except Exception as e:
                            print(f"Error loading structure file {filename}: {e}")
        except Exception as e:
            print(f"Error searching for structure files: {e}")
                    
        # If we get here, structure wasn't found
        for name in names_to_try:
            print(f"DEBUG: Structure not found: {name}")
            
        # Return empty structure if not found
        return []
    
    def _normalize_structure_format(self, structure_items):
        """
        Ensure the structure items are properly formatted.
        - Folders should be dictionaries with arrays: {"folder_name": []}
        - Files should be simple strings
        - Template variables ({{VARIABLE}}) should always remain as strings (files)
        
        This is CRITICAL for ensuring folders are displayed correctly in the UI.
        """
        if not structure_items:
            return []
            
        normalized = []
        
        # Check if structure_items is not a list - this is a critical error
        if not isinstance(structure_items, list):
            print(f"[DEBUG] StructureOps: ERROR - structure_items must be a list, got {type(structure_items).__name__}")
            
            # Special case: if we got structure_name and structure as strings, this indicates a programming error
            # Convert them to a valid structure format instead of failing
            if isinstance(structure_items, dict):
                if 'name' in structure_items and 'directories' in structure_items:
                    print(f"[DEBUG] StructureOps: Detected structure JSON object instead of array - extracting directories")
                    structure_items = structure_items.get('directories', [])
                    
                    # If directories is still not a list, return empty
                    if not isinstance(structure_items, list):
                        print(f"[DEBUG] StructureOps: Invalid structure format - returning empty list")
                        return []
                # If it's a dict but not a structure object, it might be a single folder entry
                else:
                    print(f"[DEBUG] StructureOps: Treating dict as a single folder entry")
                    return [structure_items]  # Return as a list with one item
            else:
                # If not a dict, return empty list
                return []
        
        # Process each item in the structure
        for item in structure_items:
            # If it's already a dictionary, process it as a folder
            if isinstance(item, dict):
                processed_dict = {}
                
                # Get the single folder name and its children
                for folder_name, children in item.items():
                    # Ensure the folder name is a string
                    folder_name = str(folder_name)
                    
                    # Process children recursively if they exist
                    if children is not None:
                        processed_children = self._normalize_structure_format(children) if isinstance(children, list) else []
                        processed_dict[folder_name] = processed_children
                    else:
                        # Make sure empty folders are represented as empty lists
                        processed_dict[folder_name] = []
                
                # Add the processed dictionary to the result
                normalized.append(processed_dict)
            
            # If it's a string, treat it as a filename
            elif isinstance(item, str):
                normalized.append(item)
                
            # Skip invalid types
            else:
                print(f"[DEBUG] StructureOps: Skipping invalid structure item type: {type(item).__name__}")
        
        return normalized
    def get_structure_for_project_type(self, project_type):
        """Get the appropriate structure for a given project type"""
        from app.constants import PROJECT_TYPE_TO_STRUCTURE
        
        # Get the structure name for this project type
        structure_name = PROJECT_TYPE_TO_STRUCTURE.get(project_type)
        
        if structure_name:
            # Get the structure
            return self.get_structure(structure_name)
        
        # Fallback to a default structure
        return self.get_structure("Video Editing - Standard")
    
    def get_default_structure(self, structure_type="standard"):
        """Get a default structure by type"""
        from app.constants import DEFAULT_STRUCTURES
        
        # Map common structure type keywords to our structure names in constants.py
        structure_mapping = {
            "standard": "Video Editing - Standard",
            "basic": "Video Editing - Basic",
            "video": "Video Editing - Standard",
            "motion": "Motion Graphics - Standard",
            "design": "Video Editing - Basic",
            "vfx": "VFX - Standard",
            "audio": "Video Editing - Basic"
        }
        
        # Convert to lowercase for case-insensitive matching
        structure_type_lower = structure_type.lower()
        
        # Check if we have a direct mapping
        if structure_type_lower in structure_mapping:
            structure_key = structure_mapping[structure_type_lower]
        else:
            # Default to basic structure
            structure_key = "Video Editing - Basic"
        
        # Return the structure or an empty list as last resort
        return DEFAULT_STRUCTURES.get(structure_key, []) 