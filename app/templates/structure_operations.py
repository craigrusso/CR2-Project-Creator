#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Structure Operations
Handles management of folder structures
"""

# print("!!! STRUCTURE_OPERATIONS.PY IS BEING EXECUTED - VERSION CHECK JUNE 3 PM !!!") # <-- REMOVED

import os
import json
import copy
import shutil
from pathlib import Path
import datetime

# Import StructureUtils
try:
    from app.utils.structure_utils import StructureUtils
except ImportError:
    # Fallback if not available
    class StructureUtils:
        @staticmethod
        def normalize_structure(structure):
            return structure
            
        @staticmethod
        def save_structure(structure, file_path, pretty=True):
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(structure, f, indent=2 if pretty else None)
                return True
            except Exception as e:
                print(f"Error saving structure: {e}")
                return False

from app.utils.utils import save_json_file, load_json_file

class StructureOperations:
    """
    Operations for managing custom folder structures
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize paths if not provided by a subclass like TemplateManager
        if not hasattr(self, 'paths'):
            # This path is for standalone instantiation, not typical for Echelon app
            print("SO_INIT: Initializing StructureOperations with default paths (standalone mode?)")
            self.paths = {} 
            # A standalone instance might need to load its own structures if it has a structures_dir
            if hasattr(self, 'structure_ops') and hasattr(self.structure_ops, 'custom_structures_dir'):
                 self.custom_structures_dir = self.structure_ops.custom_structures_dir
                 # self.load_custom_structures() # Standalone might load, but TemplateManager handles its own loading via structure_ops
            elif 'custom_structures_dir' in self.paths: # Check self.paths if set by a subclass before super() call
                 self.custom_structures_dir = self.paths.get("custom_structures_dir")
                 # self.load_custom_structures()
            else:
                 self.custom_structures_dir = None

        # When used as a mixin (e.g., in TemplateManager), self.structure_ops and self.template_io
        # will be set by the main class (TemplateManager -> TemplateOperations).
        # StructureOperations itself should not maintain a separate self.custom_structures dict
        # or load them independently if it's part of a larger manager.

        # Ensure consistent naming of directories if paths are managed here (less common now)
        if hasattr(self, 'paths') and self.paths:
            if "custom_structures_dir" in self.paths and "structures_dir" not in self.paths:
                self.paths["structures_dir"] = self.paths["custom_structures_dir"]
            elif "structures_dir" in self.paths and "custom_structures_dir" not in self.paths:
                self.paths["custom_structures_dir"] = self.paths["structures_dir"]
    
    def save_custom_structure(self, name, structure_data):
        """
        Save a custom folder structure to disk.
        This method now primarily relies on self.structure_ops if available (when mixed into TemplateManager),
        otherwise falls back to its own path logic (for potential standalone use).
        """
        try:
            # Prefer self.structure_ops for saving if it exists (mixin context)
            if hasattr(self, 'structure_ops') and hasattr(self.structure_ops, 'save_custom_structure'):
                print(f"SO_SAVE: Delegating save_custom_structure for '{name}' to self.structure_ops")
                return self.structure_ops.save_custom_structure(name, structure_data)

            # Fallback for standalone or direct use
            print(f"SO_SAVE: Saving custom structure '{name}' using StructureOperations' own logic.")
            structures_dir = self.paths.get('structures_dir', self.paths.get('custom_structures_dir', './structures'))
            if not os.path.exists(structures_dir):
                os.makedirs(structures_dir, exist_ok=True)
                
            file_name = name.replace(' ', '_')
            if not file_name.endswith('.json'):
                file_name += '.json'
                
            if isinstance(structure_data, dict) and 'name' not in structure_data:
                structure_data['name'] = name
                
            structure_path = os.path.join(structures_dir, file_name)
            with open(structure_path, 'w', encoding='utf-8') as f:
                json.dump(structure_data, f, indent=4)
            
            # If this instance is managing its own structures (standalone), update its dict
            if not hasattr(self, 'structure_ops'): 
                if not hasattr(self, 'standalone_custom_structures'): # Use a different name to avoid MRO confusion
                    self.standalone_custom_structures = {}
                self.standalone_custom_structures[name] = structure_data
            
            print(f"[DEBUG] Saved custom structure {name} to {structure_path} (StructureOperations direct save)")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to save custom structure {name} (StructureOperations): {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _validate_structure_format(self, structure_data):
        """
        Validate and ensure a structure can be properly serialized
        
        Args:
            structure_data: The structure data dictionary
            
        Returns:
            dict: Validated structure data or None if validation fails
        """
        try:
            # Basic schema validation
            required_fields = ["name", "directories"]
            for field in required_fields:
                if field not in structure_data:
                    print(f"[ERROR] StructureOps: Missing required field '{field}' in structure data")
                    return None
                    
            # Ensure directories is a list
            if not isinstance(structure_data["directories"], list):
                print(f"[ERROR] StructureOps: 'directories' must be a list, got {type(structure_data['directories'])}")
                if structure_data["directories"] is None:
                    structure_data["directories"] = []
                else:
                    structure_data["directories"] = [structure_data["directories"]]
            
            # Simple serialization test to make sure the structure can be converted to JSON
            try:
                json_str = json.dumps(structure_data)
                # Try to decode back to ensure it's valid
                test_decode = json.loads(json_str)
                return structure_data
            except Exception as e:
                print(f"[ERROR] StructureOps: Structure data is not serializable: {e}")
                
                # Attempt to create a safe serializable version
                safe_structure = self._create_safe_structure(structure_data)
                if safe_structure:
                    print(f"[DEBUG] StructureOps: Created safe serializable version of structure")
                    return safe_structure
                
                return None
                
        except Exception as e:
            print(f"[ERROR] StructureOps: Validation error: {e}")
            import traceback
            traceback.print_exc()
            return None
            
    def _create_safe_structure(self, structure_data):
        """
        Create a safely serializable version of a structure.
        
        Args:
            structure_data (dict): The structure data to sanitize
            
        Returns:
            dict: Sanitized structure data that can be serialized to JSON
        """
        if not structure_data:
            # Return a minimal valid structure
            return {
                "name": "Empty",
                "display_name": "Empty Structure",
                "type": "custom",
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "modified": datetime.now().isoformat(),
                "directories": []
            }
            
        try:
            # If it's already a dict, use it as the base
            if isinstance(structure_data, dict):
                safe_structure = structure_data.copy()
            else:
                # Convert non-dict to a dict
                safe_structure = {"directories": structure_data if isinstance(structure_data, list) else []}
                
            # Ensure required fields exist
            if "name" not in safe_structure:
                safe_structure["name"] = "Unknown"
                
            if "display_name" not in safe_structure:
                safe_structure["display_name"] = safe_structure["name"]
                
            if "type" not in safe_structure:
                safe_structure["type"] = "custom"
                
            if "version" not in safe_structure:
                safe_structure["version"] = "1.0"
                
            if "created" not in safe_structure:
                safe_structure["created"] = datetime.now().isoformat()
                
            if "modified" not in safe_structure:
                safe_structure["modified"] = datetime.now().isoformat()
                
            # Convert datetime objects to strings
            for key in ["created", "modified"]:
                if key in safe_structure and isinstance(safe_structure[key], datetime.datetime):
                    safe_structure[key] = safe_structure[key].isoformat()
                    
            # Ensure directories is a list
            if "directories" not in safe_structure:
                safe_structure["directories"] = []
            elif not isinstance(safe_structure["directories"], list):
                if isinstance(safe_structure["directories"], dict):
                    safe_structure["directories"] = [safe_structure["directories"]]
                else:
                    safe_structure["directories"] = []
                    
            # Test serialization to ensure it works
            json.dumps(safe_structure)
            return safe_structure
            
        except Exception as e:
            print(f"[ERROR] StructureOps: Error creating safe structure: {e}")
            # Return a minimal valid structure as a fallback
            return {
                "name": "Error",
                "display_name": "Error Structure",
                "type": "custom",
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "modified": datetime.now().isoformat(),
                "directories": []
            }
    
    def get_structure(self, structure_name):
        """
        Get the folder structure for a template.
        This method is designed to be used as a mixin. It expects 'self'
        to have 'self.structure_ops' (an instance of TemplateStructureOps)
        and 'self.template_io' (an instance of TemplateIO or similar).
        """
        # print(f"!!! StructureOperations.get_structure CALLED FOR: {structure_name} !!!")
        # print(f"SO_GET: Called with structure_name='{structure_name}'")

        if not structure_name:
            # print("SO_GET: No structure name provided, returning empty structure")
            return []

        # Access custom_structures and templates via the instance it's mixed into
        current_custom_structures = {}
        if hasattr(self, 'structure_ops') and hasattr(self.structure_ops, 'custom_structures'):
            if isinstance(self.structure_ops.custom_structures, dict):
                current_custom_structures = self.structure_ops.custom_structures
            # print(f"SO_GET: Using custom_structures from self.structure_ops (len: {len(current_custom_structures)})")
        else:
            # print("SO_GET: self.structure_ops.custom_structures not found or not a dict")
            pass

        current_templates_dict = {}
        if hasattr(self, 'template_io') and hasattr(self.template_io, 'templates'):
            if isinstance(self.template_io.templates, dict):
                current_templates_dict = self.template_io.templates
            # print(f"SO_GET: Using templates from self.template_io.templates (len: {len(current_templates_dict)})")
        else:
            # print("SO_GET: self.template_io.templates not found or not a dict")
            pass
            
        # print(f"SO_GET: Current custom_structures keys being searched: {list(current_custom_structures.keys())}")
        # print(f"SO_GET: Template names in current_templates_dict being searched: {list(current_templates_dict.keys())}")


        # Try with and without the Template_ prefix, and with spaces replaced by underscores
        name_variations = [structure_name]
        if structure_name.startswith('Template_'):
            name_variations.append(structure_name[9:])
        else:
            name_variations.append(f'Template_{structure_name}')
        
        # Add versions with spaces (common in display names)
        if ' ' in structure_name:
            name_variations.append(structure_name.replace(' ', '_')) # Check for sanitized version too
        if '_' in structure_name:
             name_variations.append(structure_name.replace('_', ' '))


        # print(f"SO_GET: Name variations: {name_variations}")

        for name_to_try in name_variations:
            # 1. Check in-memory custom structures (via structure_ops)
            # print(f"SO_GET: Checking current_custom_structures for variation: '{name_to_try}'")
            if name_to_try in current_custom_structures:
                structure_data = current_custom_structures[name_to_try]
                if isinstance(structure_data, dict) and 'structure' in structure_data:
                    # print(f"SO_GET: Found structure in custom_structures for '{name_to_try}'")
                    return structure_data['structure']
                elif isinstance(structure_data, list): # Legacy direct list?
                    # print(f"SO_GET: Found legacy list structure in custom_structures for '{name_to_try}'")
                    return structure_data


            # 2. Check on-disk custom structures (via structure_ops paths, if necessary - though load_custom_structures should handle this)
            # This part might be redundant if load_custom_structures is comprehensive
            # However, structure_ops itself has a get_structure that checks disk.
            # For StructureOperations mixin, direct disk check is less common if relying on structure_ops state.
            # Consider if direct disk access is needed here or if structure_ops.get_structure should be preferred.

            # 3. Check in-memory template data (via template_io)
            # print(f"SO_GET: Checking current_templates_dict for variation: '{name_to_try}'")
            if name_to_try in current_templates_dict:
                template_data = current_templates_dict[name_to_try]
                if isinstance(template_data, dict):
                    if 'structure' in template_data:
                        # print(f"SO_GET: Found structure in template_data for '{name_to_try}' (via 'structure' key)")
                        return template_data['structure']
                    # Fallback for older templates that might use 'directories'
                    elif 'directories' in template_data:
                        # print(f"SO_GET: Found structure in template_data for '{name_to_try}' (via 'directories' key)")
                        return template_data['directories']

        # print(f"SO_GET: Structure not found for any variation of '{structure_name}'")
        return []
    
    def _get_name_variations(self, structure_name):
        """Generate variations of a structure name for robust lookup
        
        Args:
            structure_name (str): Base structure name
            
        Returns:
            list: List of name variations to try
        """
        # Original name first (after normalization)
        name_variations = [structure_name]
        
        # Add variant with Template_ prefix if not already present
        if not structure_name.startswith("Template_"):
            name_variations.append(f"Template_{structure_name}")
        else:
            # Also try without the prefix
            name_variations.append(structure_name[9:])
        
        # Add variants with spaces converted to underscores and vice versa
        if " " in structure_name:
            name_variations.append(structure_name.replace(" ", "_"))
            if not structure_name.startswith("Template_"):
                name_variations.append(f"Template_{structure_name.replace(' ', '_')}")
        elif "_" in structure_name:
            name_variations.append(structure_name.replace("_", " "))
            if not structure_name.startswith("Template_"):
                name_variations.append(f"Template_{structure_name.replace('_', ' ')}")
                
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = [name for name in name_variations 
                          if not (name.lower() in seen or seen.add(name.lower()))]
        
        return unique_variations
    
    def load_custom_structures(self):
        """
        Load custom folder structures.
        Prioritizes structures embedded within template files in templates_dir.
        Then, loads any additional standalone structure files from structures_dir.
        """
        print("SO_LOAD: Starting load_custom_structures()") # Log start
        self.custom_structures = {}
        loaded_from_templates = 0
        loaded_from_structures_dir = 0

        # 1. Load structures embedded in main template files
        templates_dir = self.paths.get('templates_dir')
        print(f"SO_LOAD: Processing templates_dir: {templates_dir}") # Log path
        if templates_dir and os.path.exists(templates_dir):
            template_files = [f for f in os.listdir(templates_dir) if f.endswith('.json') and not f.startswith('.')]
            for template_file in template_files:
                template_path = os.path.join(templates_dir, template_file)
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                    
                    # --- DETAILED LOGGING ---
                    print(f"SO_LOAD: Processing {template_file} from templates_dir. Name: {template_data.get('name') if isinstance(template_data, dict) else 'N/A'}, HasStructure: {'structure' in template_data if isinstance(template_data, dict) else False}")
                    # --- END DETAILED LOGGING ---

                    if (isinstance(template_data, dict) and
                        template_data.get('structure') and # Ensure structure is not None and not empty
                        template_data.get('name')):
                        
                        template_name_from_file = template_data['name']
                        
                        # If the structure name is not already in custom_structures, add it
                        # This prioritizes items already loaded (e.g., if structures_dir was processed first, though it's second now)
                        if template_name_from_file not in self.custom_structures:
                            self.custom_structures[template_name_from_file] = template_data # Store the WHOLE template_data
                            loaded_from_templates += 1
                            # --- DETAILED LOGGING ---
                            print(f"SO_LOAD: ADDED '{template_name_from_file}' to custom_structures from Templates dir. Keys now: {list(self.custom_structures.keys())}")
                            # --- END DETAILED LOGGING ---
                        else:
                            print(f"SO_LOAD: '{template_name_from_file}' already in custom_structures. Skipping add from Templates dir.")

                except json.JSONDecodeError:
                    print(f"SO_LOAD: Warning: Could not decode JSON from {template_path}")
                except Exception as e:
                    print(f"SO_LOAD: Error loading template data from {template_path}: {e}")
        else:
            print(f"[WARNING] Templates directory not found or not specified: {templates_dir}. Cannot load embedded structures.")

        # 2. Load standalone structure files from structures_dir (custom_structures_dir)
        #    Only add if a structure with the same name wasn't already loaded from a template.
        structures_dir = self.paths.get('custom_structures_dir', self.paths.get('structures_dir'))
        if structures_dir and os.path.exists(structures_dir):
            structure_files = [f for f in os.listdir(structures_dir) if f.endswith('.json')]
            for structure_file in structure_files:
                structure_path = os.path.join(structures_dir, structure_file)
                try:
                    with open(structure_path, 'r', encoding='utf-8') as f:
                        structure_data = json.load(f)
                    
                    structure_name_from_file = os.path.splitext(structure_file)[0]
                    # Use 'name' field in JSON if present, otherwise use filename
                    actual_structure_name = structure_data.get('name', structure_name_from_file) if isinstance(structure_data, dict) else structure_name_from_file

                    if actual_structure_name not in self.custom_structures:
                        if isinstance(structure_data, dict):
                            # Ensure 'name' field is consistent if using filename-derived name
                            if 'name' not in structure_data:
                                structure_data['name'] = actual_structure_name
                            self.custom_structures[actual_structure_name] = structure_data
                            loaded_from_structures_dir += 1
                        else:
                            # Handle cases where the JSON is just a list (old format for pure structures)
                            # We need to wrap it in a dictionary to be consistent with template-derived structures.
                            self.custom_structures[actual_structure_name] = {
                                'name': actual_structure_name,
                                'structure': structure_data,
                                'category': 'Imported Legacy', # Mark as legacy
                                'description': f'Legacy structure: {actual_structure_name}'
                            }
                            loaded_from_structures_dir += 1
                    else:
                        print(f"[DEBUG] Structure '{actual_structure_name}' from {structure_file} already loaded from template. Skipping.")
                        
                except Exception as e:
                    print(f"[ERROR] Failed to load standalone structure file {structure_file}: {e}")
        else:
            print(f"[WARNING] Structures directory not found or not specified: {structures_dir}. Cannot load standalone structures.")
            
        if loaded_from_templates > 0:
            print(f"INFO: Loaded {loaded_from_templates} structures embedded in templates from {templates_dir}.")
        if loaded_from_structures_dir > 0:
            # This log message might be slightly misleading if templates also populate custom_structures
            print(f"INFO: Loaded {loaded_from_structures_dir} standalone structure files from {structures_dir}.")
        
        # --- DETAILED LOGGING ---
        print(f"SO_LOAD: END. Final custom_structures keys: {list(self.custom_structures.keys())}")
        if hasattr(self, 'templates') and self.templates is not None:
            template_names_in_self_templates = [t.get('name') for t in self.templates if isinstance(t, dict)]
            print(f"SO_LOAD: END. Template names in self.templates: {template_names_in_self_templates}")
        else:
            print("SO_LOAD: END. self.templates is not initialized or is None")
        # --- END DETAILED LOGGING ---

        # Fallback if custom_structures is still empty, try to force load from self.templates
        # This could happen if the initial load_templates in TemplateIO didn't populate self.custom_structures correctly
        if not self.custom_structures:
            print("WARNING: custom_structures is empty. Trying to load from self.templates.")
            self.load_custom_structures()
    
    def delete_custom_structure(self, name):
        """Delete a custom folder structure"""
        if not name:
            print(f"DEBUG: Cannot delete structure with empty name")
            return False
            
        # Create different variations of the filename to check
        name_variants = [name]
        if name.startswith("Template_"):
            name_variants.append(name[9:])  # Without Template_ prefix
        else:
            name_variants.append(f"Template_{name}")
            
        # With spaces replaced by underscores
        for variant in list(name_variants):  # Make a copy of the list for iteration
            if " " in variant:
                name_variants.append(variant.replace(" ", "_"))
            elif "_" in variant:
                name_variants.append(variant.replace("_", " "))
        
        deleted = False
        for variant in name_variants:
            # Create a clean filename
            filename = variant.replace(" ", "_").replace("/", "-").replace("\\", "-")
            file_path = os.path.join(self.paths["custom_structures_dir"], f"{filename}.json")
            
            if os.path.exists(file_path):
                try:
                    # Delete the structure file
                    os.remove(file_path)
                    print(f"DEBUG: Successfully deleted structure file for '{variant}': {file_path}")
                    
                    # Delete associated cache directory
                    cache_dir = os.path.join(self.paths["templates_dir"], "cache", filename)
                    if os.path.exists(cache_dir):
                        print(f"DEBUG: Deleting cache directory for structure '{variant}': {cache_dir}")
                        import shutil
                        shutil.rmtree(cache_dir)
                        print(f"DEBUG: Successfully deleted cache directory for structure '{variant}'")
                    
                    deleted = True
                except Exception as e:
                    print(f"ERROR: Failed to delete structure file for '{variant}': {e}")
            else:
                print(f"DEBUG: Structure file not found for '{variant}': {file_path}")
        
        return deleted
    
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
            "created": datetime.now().isoformat()
        }
        
        # Save to file
        return self.save_custom_structure(structure["name"], unique_folders)
    
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
    
    def sanitize_filename(self, name):
        """
        Sanitize a name for use as a filename.
        Args:
            name (str): The name to sanitize
        Returns:
            str: A sanitized filename that is safe to use on the filesystem
        """
        if not name:
            return "untitled"
        # Replace characters not allowed in filenames across platforms
        unsafe_chars = [":", "/", "\\", "?", "*", "\"", "<", ">", "|", "'"]
        safe_filename = name
        for char in unsafe_chars:
            safe_filename = safe_filename.replace(char, "-")
        # Replace spaces with underscores
        safe_filename = safe_filename.replace(" ", "_")
        # Limit length (optional)
        if len(safe_filename) > 100:
            safe_filename = safe_filename[:100]
        # Ensure we don't end with an underscore or period
        safe_filename = safe_filename.rstrip('_').rstrip('.')
        if not safe_filename:
            return "untitled"
        return safe_filename 